"""Servicio principal del gateway WREWS (Raspberry Pi).

    ESP32 --MQTT--> Mosquitto (Pi) --> este servicio --> SQLite
                                              |            |
                                              |      procesamiento local
                                              |      (validacion, agregados,
                                              |       vigilancia del enlace)
                                              |            |
                                              |        modulo de IA
                                              v            v
                              ESP32 <-- comandos <-- Ubidots (MQTT, TLS)

Hilos:
  - red local (paho)  : recibe los mensajes del ESP32 y los pone en una cola.
  - trabajador        : saca de la cola, GUARDA EN SQLITE y luego procesa.
  - periodico (1 s)   : cierra ventanas y vigila el enlace con el ESP32.
  - nube              : vacia la cola de SQLite hacia Ubidots (puede esperar).
  - ia                : prediccion + recomendacion (puede tardar: va aparte).
  - telegram          : avisos al celular cuando cambia el estado (opcional).
  - red Ubidots (paho): sube datos y recibe la orden de silenciar.
El trabajador y el periodico comparten el estado del enlace y el agregador:
lo tocan siempre con self._lock tomado.

Uso:  python -m wrews_gw.gateway      (config por variables de entorno)
"""
import json
import logging
import queue
import signal
import threading
import time

import paho.mqtt.client as mqtt

from . import ia
from .almacen import Almacen, ahora_ms
from .config import Config
from .nube import PuenteUbidots
from .procesamiento import Agregador, Validador, limpiar_contexto, payload_ubidots
from .telegram import Telegram, texto_estado

log = logging.getLogger("gateway")


class Gateway:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.dev = cfg.dispositivo
        self.base = f"wrews/{self.dev}"
        self.db = Almacen(cfg.db_path)
        self.validador = Validador(z_max=cfg.z_max)
        self.agregador = Agregador(cfg.ventana_s, cfg.periodo_tel_s)
        self.cola = queue.Queue()
        self.parar = threading.Event()
        self._lock = threading.RLock()

        self.t_ultimo_dato = None
        self.boot = None                     # arranque del ESP32 de la ultima muestra
        self.enlace_caido = False
        self.estado = None
        self.ia_pedida = threading.Event()   # se activa cuando cambia el estado
        self.t_ultima_ia = 0.0
        self.ultimo_dato = {}                # ultima telemetria valida (para los avisos)
        self._lock_llm = threading.Lock()    # una sola consulta al LLM a la vez
        self._ultima_llm = None              # (hora, texto) de la ultima a pedido
        self.estado_avisado = None           # ultimo estado avisado por Telegram
        self.telegram = Telegram(cfg.telegram_token, cfg.telegram_chat_id, self.db,
                                 cfg.telegram_clave, self._texto_estado_actual,
                                 cfg.telegram_admin, grafica=self._grafica_png,
                                 dashboard=self._dashboard_png,
                                 tablero_url=cfg.ubidots_tablero_url,
                                 recomendar=self.recomendacion_a_pedido)

        self.local = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                 client_id=f"wrews-gateway-{self.dev}")
        self.local.username_pw_set(cfg.mqtt_user, cfg.mqtt_pass)
        self.local.will_set(f"{self.base}/gateway", "offline", qos=1, retain=True)
        # El broker esta en la misma Pi: reintentar seguido no cuesta nada y,
        # cuando vuelve, el gateway se reconecta en pocos segundos.
        self.local.reconnect_delay_set(1, 5)
        self.local.on_connect = self._local_conectado
        self.local.on_disconnect = lambda *a: log.warning("Broker local: desconectado")
        self.local.on_message = lambda c, ud, m: self.cola.put((m.topic, m.payload, ahora_ms()))

        self.nube = PuenteUbidots(cfg, self._silenciar_desde_nube) if cfg.nube_activa else None

    # ---- Arranque y parada -------------------------------------------------
    def iniciar(self):
        log.info("Gateway WREWS: dispositivo %s, base de datos %s", self.dev, self.cfg.db_path)
        self.local.connect_async(self.cfg.mqtt_host, self.cfg.mqtt_port, keepalive=30)
        self.local.loop_start()
        if self.nube:
            self.nube.iniciar()
        else:
            log.warning("UBIDOTS_TOKEN vacio: modo solo local (los datos quedan en la cola)")
        for nombre, fn in (("trabajador", self._trabajador), ("periodico", self._periodico),
                           ("nube", self._hilo_nube), ("ia", self._hilo_ia)):
            threading.Thread(target=fn, name=nombre, daemon=True).start()

    def detener(self):
        self.parar.set()
        self.local.publish(f"{self.base}/gateway", "offline", qos=1, retain=True)
        self.local.disconnect()
        self.local.loop_stop()
        if self.nube:
            self.nube.detener()
        time.sleep(0.5)   # que los hilos suelten la base antes de cerrarla
        self.db.cerrar()

    def _local_conectado(self, c, ud, flags, rc, props):
        if rc.is_failure:
            log.error("Broker local rechazo la conexion: %s (revise MQTT_USER/MQTT_PASS)", rc)
            return
        log.info("Broker local: conectado a %s:%s", self.cfg.mqtt_host, self.cfg.mqtt_port)
        c.subscribe(f"{self.base}/#", qos=1)
        c.publish(f"{self.base}/gateway", "online", qos=1, retain=True)

    # ---- Mensajes del ESP32 (hilo trabajador) -------------------------------
    def _trabajador(self):
        while not self.parar.is_set():
            try:
                topico, crudo, ts = self.cola.get(timeout=1)
            except queue.Empty:
                continue
            try:
                with self._lock:
                    self._procesar(topico[len(self.base) + 1:],
                                   crudo.decode("utf-8", "replace"), ts)
            except Exception:
                log.exception("Error procesando %s: %r", topico, crudo[:200])

    def _procesar(self, sub, texto, ts):
        if sub == "telemetria":
            datos = json.loads(texto)
            id_med = self.db.guardar_medicion(self.dev, datos, ts)        # 1. guardar
            # Tras una caida del enlace o un reinicio del ESP32 el nivel pudo
            # cambiar de verdad: no se compara contra la historia vieja.
            if self.enlace_caido or datos.get("boot") != self.boot:
                self.validador = Validador(z_max=self.cfg.z_max)
                self.boot = datos.get("boot")
            datos, fuera = self.validador.limpiar(datos)                  # 2. procesar
            if fuera:
                txt = ", ".join(f"{k}={v}" for k, v in fuera.items())
                self._evento_gw(1, f"Variable fuera de rango descartada: {txt}")
            anomalia = self.validador.revisar(datos)
            if anomalia:
                self.db.marcar_anomalia(id_med, anomalia)
                self._evento_gw(1, f"Muestra descartada por el gateway: {anomalia}")
            self.agregador.agregar(datos, ts, anomalia)
            if not anomalia:
                self.ultimo_dato = datos
            self.t_ultimo_dato = time.time()
            if self.enlace_caido:
                self.enlace_caido = False
                self._evento_gw(0, "Datos del ESP32 de nuevo en el gateway")
                if datos.get("estado") is not None:
                    self._encolar_estado(datos["estado"], datos.get("silenciado", 0), ts, "esp32")
        elif sub == "estado":
            datos = json.loads(texto)
            self.db.guardar_estado(self.dev, datos, ts)
            nuevo = datos.get("estado")
            if nuevo != self.estado:
                log.info("Estado %s -> %s", ia.NOMBRE_EST.get(self.estado),
                         datos.get("estado_txt"))
                if self.estado is not None:
                    self.ia_pedida.set()
                self.estado = nuevo
            self._encolar_estado(nuevo, datos.get("silenciado", 0), ts, "esp32")
        elif sub == "eventos":
            e = json.loads(texto)
            if self.db.guardar_evento(self.dev, "esp32", e.get("texto", ""), e.get("gravedad", 0),
                                      e.get("boot"), e.get("id"), ts - int(e.get("hace_ms", 0))):
                log.info("Evento ESP32: %s", e.get("texto"))
        elif sub == "disponibilidad":
            if texto == "offline":
                self._enlace_perdido("el broker reporto al ESP32 desconectado (LWT)")
            else:
                self._evento_gw(0, "ESP32 en linea con el broker")
        elif sub == "cmd":
            try:
                accion = json.loads(texto)
                origen, nombre = accion.get("origen", "local"), accion.get("accion", "?")
            except (ValueError, AttributeError):
                origen, nombre = "local", texto
            self.db.guardar_comando(self.dev, origen, nombre)
        elif sub == "cmd/resp":
            r = json.loads(texto)
            self.db.guardar_respuesta_comando(self.dev, r)
            log.info("Respuesta del ESP32 al comando: %s", r)
        # ia, ia/texto y gateway son mensajes propios: ya estan en SQLite

    def _evento_gw(self, gravedad, texto):
        log.info("Evento gateway: %s", texto)
        self.db.guardar_evento(self.dev, "gateway", texto, gravedad)

    def _encolar_estado(self, estado, silenciado, ts, origen, motivo=None):
        ctx = limpiar_contexto({"estado_txt": ia.NOMBRE_EST.get(estado, str(estado)),
                                "origen": origen, "motivo": motivo})
        self.db.encolar_nube({
            "estado": {"value": estado, "timestamp": ts, "context": ctx},
            "silenciado": {"value": silenciado, "timestamp": ts},
        }, ts)
        self._avisar_estado(estado, motivo)

    def _texto_estado_actual(self):
        """Respuesta al comando /estado del bot de Telegram."""
        estado = 3 if self.enlace_caido else (self.estado if self.estado is not None else 0)
        d = self.ultimo_dato
        txt = texto_estado(estado, d.get("nivel"), d.get("riesgo"))
        ult = self.db._consultar("SELECT proveedor, texto FROM ia WHERE dispositivo = ? "
                                 "ORDER BY id DESC LIMIT 1", (self.dev,))
        if ult:
            txt += f"\n\n🤖 Última recomendación ({ult[0]['proveedor']}):\n{ult[0]['texto']}"
        return txt

    def _grafica_png(self, minutos=60):
        """PNG con el nivel y el riesgo de la ultima hora (comando /grafica)."""
        from .grafica import grafica_png
        desde = ahora_ms() - minutos * 60_000
        filas = self.db._consultar(
            "SELECT ts_ms, nivel, riesgo, estado FROM mediciones WHERE dispositivo = ? "
            "AND ts_ms >= ? AND anomalia IS NULL ORDER BY ts_ms", (self.dev, desde))
        estado = 3 if self.enlace_caido else (self.estado if self.estado is not None else 0)
        return grafica_png(filas, estado, self.cfg.ia_umbral_precaucion,
                           self.cfg.ia_umbral_critico, minutos)

    def _dashboard_png(self, minutos=60):
        """Tablero completo en una imagen (comando /dashboard)."""
        from .grafica import dashboard_png
        desde = ahora_ms() - minutos * 60_000
        filas = self.db._consultar(
            "SELECT ts_ms, nivel, riesgo, temp, hum FROM mediciones WHERE dispositivo = ? "
            "AND ts_ms >= ? AND anomalia IS NULL ORDER BY ts_ms", (self.dev, desde))
        ia_reg = self.db._consultar("SELECT proveedor, min_a_critico, tendencia, texto "
                                    "FROM ia WHERE dispositivo = ? ORDER BY id DESC LIMIT 1",
                                    (self.dev,))
        ag = self.db._consultar("SELECT completitud FROM agregados WHERE dispositivo = ? "
                                "ORDER BY id DESC LIMIT 1", (self.dev,))
        estado = 3 if self.enlace_caido else (self.estado if self.estado is not None else 0)
        return dashboard_png(filas, self.db.ultima_medicion(self.dev), estado,
                             ia_reg[0] if ia_reg else None,
                             ag[0]["completitud"] if ag else None,
                             self.cfg.ia_umbral_precaucion, self.cfg.ia_umbral_critico,
                             minutos)

    def _avisar_estado(self, estado, motivo=None):
        """Telegram solo cuando el estado cambia (no al arrancar en NORMAL)."""
        if estado == self.estado_avisado or (self.estado_avisado is None and estado == 0):
            self.estado_avisado = estado
            return
        self.estado_avisado = estado
        d = self.ultimo_dato
        self.telegram.enviar(texto_estado(estado, d.get("nivel"), d.get("riesgo"), motivo))
        self.telegram.refrescar.set()        # el dashboard en vivo cambia de color ya

    def _enlace_perdido(self, motivo):
        if self.enlace_caido:
            return
        self.enlace_caido = True
        self._evento_gw(2, f"Sin datos del ESP32: {motivo}")
        # El ESP32 ya no puede avisar a la nube: el gateway sube FALLO por el,
        # asi el evento de Ubidots de FALLO tambien cubre la caida del enlace.
        ts = ahora_ms()
        self.db.guardar_estado(self.dev, {"estado": 3, "estado_txt": "FALLO", "motivo": motivo},
                               ts, origen="gateway")
        self._encolar_estado(3, 0, ts, "gateway", motivo)
        self.ia_pedida.set()

    # ---- Comandos -----------------------------------------------------------
    def _silenciar_desde_nube(self):
        self.mandar_comando("silenciar", "Ubidots")

    def mandar_comando(self, accion, origen):
        msg = json.dumps({"accion": accion, "origen": origen})
        self.local.publish(f"{self.base}/cmd", msg, qos=1)
        log.info("Comando al ESP32: %s", msg)

    # ---- Tareas periodicas --------------------------------------------------
    def _periodico(self):
        while not self.parar.wait(1.0):
            try:
                with self._lock:
                    self._cerrar_ventana(ahora_ms())
                    if (self.t_ultimo_dato is not None
                            and time.time() - self.t_ultimo_dato > self.cfg.sin_datos_s):
                        self._enlace_perdido(f"mas de {self.cfg.sin_datos_s} s sin telemetria")
            except Exception:
                log.exception("Error en la tarea periodica")

    def _cerrar_ventana(self, ahora):
        if not self.agregador.lista(ahora):
            return
        ag = self.agregador.cerrar(ahora)
        if ag and (ag["n"] or ag["anomalias"]):
            self.db.guardar_agregado(self.dev, ag)
            self.db.encolar_nube(payload_ubidots(ag, self.cfg.ubidots_variables, ahora), ahora)
            log.info("Ventana: %d muestras, %d anomalas, completitud %.0f %%",
                     ag["n"], ag["anomalias"], ag["completitud"])
        elif ag and self.enlace_caido:
            # Sin ningun dato en la ventana: la calidad del enlace es 0 %
            self.db.encolar_nube({"gw_calidad": {
                "value": 0, "timestamp": ahora,
                "context": {"n": 0, "esperadas": ag["n_esperadas"]}}}, ahora)

    def _hilo_nube(self):
        """Vacia la cola de SQLite hacia Ubidots, del mas viejo al mas nuevo."""
        pausa = 1.0 / max(self.cfg.ubidots_msg_por_s, 0.1)
        while not self.parar.wait(1.0):
            if not self.nube or not self.nube.conectado.is_set():
                continue
            try:
                pendientes = self.db.pendientes_nube(20)
                for fila in pendientes:
                    if self.parar.is_set() or not self.nube.publicar(fila["payload"]):
                        self.db.sumar_intento(fila["id"])
                        break
                    self.db.marcar_enviado(fila["id"])
                    if len(pendientes) > 1:
                        time.sleep(pausa)   # no saturar a Ubidots al ponerse al dia
                if len(pendientes) == 20:
                    log.info("Cola hacia Ubidots: %d pendientes", self.db.contar_pendientes())
            except Exception:
                log.exception("Error vaciando la cola hacia Ubidots")

    # ---- Modulo de IA -------------------------------------------------------
    def _hilo_ia(self):
        self.parar.wait(15)        # que haya algo de historia antes de la primera
        while not self.parar.is_set():
            ahora = time.time()
            # Automatico: prediccion propia + recomendacion, al cambiar el estado
            # (ia_pedida), cada IA_CADA_S en alerta y cada IA_CADA_S_NORMAL en
            # NORMAL. Por defecto (IA_LLM_AUTO=0) esa recomendacion automatica es
            # la tabla de reglas, que no cuesta nada: el LLM se usa solo cuando
            # alguien la pide (/recomendacion en Telegram).
            periodo = (self.cfg.ia_cada_s_normal if self.estado in (None, 0)
                       else self.cfg.ia_cada_s)
            vencida = (not self.enlace_caido
                       and ahora - self.t_ultima_ia >= periodo)
            pedida = (self.ia_pedida.is_set()
                      and ahora - self.t_ultima_ia >= self.cfg.ia_min_entre_llamadas_s)
            if vencida or pedida:
                self.ia_pedida.clear()
                try:
                    usar_llm = self.cfg.ia_llm_auto and not self.enlace_caido
                    if self.correr_ia(avisar=pedida, usar_llm=usar_llm):
                        self.t_ultima_ia = ahora
                    else:   # sin datos todavia: probar de nuevo en 15 s
                        self.t_ultima_ia = ahora - periodo + 15
                except Exception:
                    self.t_ultima_ia = ahora
                    log.exception("Error en el modulo de IA")
            self.parar.wait(2)

    def correr_ia(self, avisar=False, usar_llm=False):
        ultima = self.db.ultima_medicion(self.dev)
        if not ultima:
            log.info("IA: todavia no hay mediciones")
            return None
        desde = ahora_ms() - int(self.cfg.ia_ventana_min * 60_000)
        pred = ia.predecir(self.db.serie_nivel(self.dev, desde), self.cfg.ia_umbral_critico)
        estado = 3 if self.enlace_caido else (self.estado if self.estado is not None
                                               else ultima.get("estado", 0))
        reg = ia.recomendar(pred, estado, ultima, self.db.eventos_recientes(self.dev, 5),
                            self.cfg, usar_llm=usar_llm)
        self.db.guardar_ia(self.dev, reg)
        ts = ahora_ms()
        self.local.publish(f"{self.base}/ia", ia.mensaje_local(reg), qos=1, retain=True)
        self.local.publish(f"{self.base}/ia/texto", reg["texto"], qos=1, retain=True)
        self.db.encolar_nube(ia.payload_ubidots(reg, ts), ts)
        log.info("IA (%s, %d ms): %s | %s", reg["proveedor"], reg["latencia_ms"],
                 pred, reg["texto"])
        if reg.get("error"):
            log.warning("IA: se uso el respaldo por reglas (%s)", reg["error"])
        if avisar:   # corrio porque cambio el estado: va al celular tambien
            self.telegram.enviar(self._texto_recomendacion(reg))
        return reg

    @staticmethod
    def _texto_recomendacion(reg):
        if reg["proveedor"] == "reglas":
            txt = f"📋 Recomendación (tabla de reglas):\n{reg['texto']}"
            if reg.get("error"):
                txt += "\n(No se pudo consultar a la IA; se usó el respaldo.)"
            return txt + "\n\nPara un análisis de la IA con los datos actuales: /recomendacion"
        fuente = "Claude" if reg["proveedor"] == "claude" else reg["proveedor"]
        return f"🤖 Recomendación de la IA ({fuente}):\n{reg['texto']}"

    def recomendacion_a_pedido(self):
        """Comando /recomendacion del bot: aqui si se llama al LLM.

        Como maximo una llamada cada IA_MIN_ENTRE_LLAMADAS_S: si la piden varios
        a la vez, se devuelve la ultima en vez de gastar otra.
        """
        with self._lock_llm:
            ahora = time.time()
            if self._ultima_llm and ahora - self._ultima_llm[0] < self.cfg.ia_min_entre_llamadas_s:
                hace = int(ahora - self._ultima_llm[0])
                return f"{self._ultima_llm[1]}\n\n(recomendación de hace {hace} s)"
            reg = self.correr_ia(usar_llm=True)
            if not reg:
                return "Todavía no hay mediciones para analizar."
            texto = self._texto_recomendacion(reg)
            if reg["proveedor"] != "reglas":
                self._ultima_llm = (ahora, texto)
            return texto


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    gw = Gateway(Config.desde_entorno())
    fin = threading.Event()
    signal.signal(signal.SIGTERM, lambda *a: fin.set())
    signal.signal(signal.SIGINT, lambda *a: fin.set())
    gw.iniciar()
    fin.wait()
    log.info("Deteniendo el gateway")
    gw.detener()


if __name__ == "__main__":
    main()
