"""Puente MQTT con Ubidots (nube), en los dos sentidos.

Subida:  el gateway publica en /v1.6/devices/<dispositivo> un JSON
         {"variable": {"value": x, "timestamp": ms, "context": {...}}}.
         Ubidots crea el dispositivo y las variables solas con el primer dato.
Bajada:  el gateway se suscribe a /v1.6/devices/<dispositivo>/silenciar
         (variable "silenciar", que se mueve con un widget Switch del
         tablero). Cuando llega 1, manda el comando al ESP32 por el broker
         local y devuelve el switch a 0.

Autenticacion de Ubidots por MQTT: usuario = token, clave = cualquier texto.
Con TLS (puerto 8883) el token no viaja en claro. El certificado de
industrial.api.ubidots.com es de Let's Encrypt: lo valida el almacen de
certificados del sistema, no hay que descargar nada.
"""
import json
import logging
import ssl
import threading
import time

import paho.mqtt.client as mqtt

log = logging.getLogger("nube")

# Una orden de silenciar con marca de tiempo mas vieja que esto no se ejecuta:
# es el valor que quedo guardado en Ubidots, no alguien pulsando el switch.
ORDEN_VIGENTE_MS = 120_000


def leer_switch(payload):
    """(valor, timestamp_ms o None) de un mensaje de Ubidots.

    Acepta el JSON del topico de la variable ({"value": 1, "timestamp": ...})
    y tambien el numero plano del topico /lv. None si no se entiende.
    """
    txt = payload.decode("utf-8", "replace").strip()
    try:
        d = json.loads(txt)
    except ValueError:
        return None
    if isinstance(d, dict):
        try:
            return float(d.get("value")), d.get("timestamp")
        except (TypeError, ValueError):
            return None
    if isinstance(d, (int, float)) and not isinstance(d, bool):
        return float(d), None
    return None


class FiltroOrdenes:
    """Decide si un valor del switch es una orden nueva de silenciar.

    - Con marca de tiempo: se ejecuta si es reciente y no se ejecuto ya.
      Asi una orden dada mientras la Pi estaba sin Internet se cumple al
      reconectar (si tiene menos de 2 min) y un 1 viejo no se repite.
    - Sin marca (topico /lv): se ignora lo que llega en los primeros 2 s
      despues de suscribirse, que es el valor guardado, no una orden.
    """

    def __init__(self):
        self.ultimo_ts = None
        self.t_suscripcion = 0.0

    def suscrito(self):
        self.t_suscripcion = time.time()

    def es_orden(self, valor, ts_ms, ahora_s=None):
        ahora_s = time.time() if ahora_s is None else ahora_s
        if valor < 0.5:
            return False
        if ts_ms is not None:
            if ts_ms == self.ultimo_ts or ahora_s * 1000 - ts_ms > ORDEN_VIGENTE_MS:
                return False
            self.ultimo_ts = ts_ms
            return True
        return ahora_s - self.t_suscripcion >= 2.0


class PuenteUbidots:
    def __init__(self, cfg, al_recibir_silenciar):
        self.cfg = cfg
        self.dispositivo = cfg.ubidots_dispositivo
        self.top_subida = f"/v1.6/devices/{self.dispositivo}"
        self.top_silenciar = f"/v1.6/devices/{self.dispositivo}/silenciar"
        self.al_recibir_silenciar = al_recibir_silenciar
        self.conectado = threading.Event()
        self.filtro = FiltroOrdenes()

        self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                             client_id=f"wrews-gw-{self.dispositivo}-{int(time.time()) % 100000}")
        self.c.username_pw_set(cfg.ubidots_token, "x")
        if cfg.ubidots_tls:
            self.c.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        # Maximo 10 s entre reintentos: cuando vuelve Internet, Ubidots se
        # recupera rapido (con 60 s la prueba de caida se veia lenta).
        self.c.reconnect_delay_set(min_delay=2, max_delay=10)
        self.c.on_connect = self._on_connect
        self.c.on_disconnect = self._on_disconnect
        self.c.on_message = self._on_message

    def iniciar(self):
        log.info("Ubidots: conectando a %s:%s (TLS %s), dispositivo '%s'",
                 self.cfg.ubidots_host, self.cfg.ubidots_port,
                 "si" if self.cfg.ubidots_tls else "no", self.dispositivo)
        # connect_async + loop_start: si no hay Internet al arrancar, paho
        # sigue reintentando solo; el gateway mientras tanto guarda en SQLite.
        self.c.connect_async(self.cfg.ubidots_host, self.cfg.ubidots_port, keepalive=30)
        self.c.loop_start()

    def detener(self):
        self.c.disconnect()
        self.c.loop_stop()

    def _on_connect(self, c, ud, flags, rc, props):
        if rc.is_failure:
            log.error("Ubidots rechazo la conexion: %s (revise UBIDOTS_TOKEN)", rc)
            return
        log.info("Ubidots: conectado")
        self.filtro.suscrito()
        c.subscribe(self.top_silenciar, qos=1)
        self.conectado.set()

    def _on_disconnect(self, c, ud, flags, rc, props):
        if self.conectado.is_set():
            log.warning("Ubidots: desconectado (%s); los datos quedan en la cola de SQLite", rc)
        self.conectado.clear()

    def _on_message(self, c, ud, msg):
        if msg.topic != self.top_silenciar:
            return
        leido = leer_switch(msg.payload)
        if leido is None:
            log.warning("Ubidots: valor raro en silenciar: %r", msg.payload[:100])
            return
        valor, ts = leido
        if self.filtro.es_orden(valor, ts):
            log.info("Ubidots: orden de silenciar la alarma")
            self.al_recibir_silenciar()
            self._apagar_switch()
        elif valor >= 0.5:
            log.info("Ubidots: silenciar=1 viejo o repetido; se pone en 0 sin actuar")
            self._apagar_switch()

    def _apagar_switch(self):
        # Sin esperar el PUBACK: esto corre en el hilo de red de paho, que es
        # el mismo que procesaria el PUBACK (esperar aqui lo bloquearia).
        self.c.publish(self.top_subida, json.dumps({"silenciar": 0}), qos=1)

    def publicar(self, payload, espera_s=8.0):
        """Publica con QoS 1 y espera el PUBACK. True si Ubidots lo confirmo."""
        if not self.conectado.is_set():
            return False
        try:
            info = self.c.publish(self.top_subida, json.dumps(payload), qos=1)
            info.wait_for_publish(timeout=espera_s)
            return info.is_published()
        except (RuntimeError, ValueError) as e:
            log.warning("Ubidots: no se pudo publicar (%s)", e)
            return False
