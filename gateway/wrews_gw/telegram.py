"""Avisos al celular por Telegram (gratis, sin limite de mensajes).

Acceso restringido a personal autorizado (requisito del reto): quien le
escribe /start al bot queda como SOLICITUD PENDIENTE y el administrador
(TELEGRAM_ADMIN, p. ej. el responsable de la alcaldia) recibe un mensaje
para aprobarla o rechazarla. Solo los aprobados reciben alertas y pueden
consultar el estado. Opcionalmente se exige ademas una clave de registro.
Todo queda en la tabla suscriptores de SQLite.

Comandos de cualquier usuario:
    /start [CLAVE]  pedir acceso (la clave solo si se define TELEGRAM_CLAVE)
    /stop           dejar de recibir alertas
    /estado         estado actual, ultimo dato y ultima recomendacion (aprobados)
    /recomendacion  analisis de la IA (Claude) con los datos actuales (aprobados)
    /dashboard      tablero completo en una imagen: tarjetas, graficas y la IA (aprobados)
    /envivo         fija el dashboard arriba del chat y lo actualiza cada minuto
    /detener        quita el dashboard en vivo
    /grafica        imagen de la ultima hora: nivel, riesgo y umbrales (aprobados)
    /tablero        enlace al tablero de Ubidots (pide iniciar sesion) (aprobados)
Comandos del administrador (las solicitudes traen botones Aprobar/Rechazar):
    /usuarios   lista con comandos tocables: /aprobar_ID /rechazar_ID /quitar_ID

El gateway avisa cada vez que cambia el estado (NORMAL, PRECAUCION, CRITICO,
FALLO) y enseguida manda la recomendacion de la IA. Todo va en hilos propios:
si no hay Internet, reintenta y nunca frena al gateway.

Configuracion (gateway.env):
    TELEGRAM_TOKEN=<token que da @BotFather>
    TELEGRAM_ADMIN=<chat id del administrador: aprueba a los demas>
    TELEGRAM_CLAVE=<opcional: clave de registro, /start CLAVE>
    TELEGRAM_CHAT_ID=<opcional: chats fijos que siempre reciben, separados por coma>
Sin TELEGRAM_ADMIN ni TELEGRAM_CLAVE el bot queda ABIERTO (no recomendado).

Probar desde la consola:  python -m wrews_gw.telegram --probar
Ojo: Telegram admite UN solo programa leyendo los mensajes de un bot. Si el
gateway corre en el Mac y en la Pi a la vez, uno de los dos recibe error 409.
"""
import json
import logging
import queue
import sys
import threading
import time

import requests

log = logging.getLogger("telegram")
API = "https://api.telegram.org/bot{token}/{metodo}"

ICONO = {0: "✅", 1: "⚠️", 2: "🚨", 3: "❌"}
TITULO = {0: "NORMAL", 1: "PRECAUCIÓN", 2: "CRÍTICO", 3: "FALLO"}
ACCION = {
    0: "El reservorio volvió a la normalidad.",
    1: "Nivel ≤ 50 % o descenso sostenido. Promover el ahorro y vigilar.",
    2: "Nivel ≤ 15 %. Activar el plan de racionamiento por sectores.",
    3: "El equipo no está midiendo (sensor o conexión). Revisar en sitio.",
}
MAX_INTENTOS_CLAVE = 5
VIVO_CADA_S = 60          # cada cuanto se actualiza el dashboard en vivo
BLOQUEO_CLAVE_S = 600
MENSAJE_VIGENTE_S = 600   # mensajes mas viejos (gateway apagado) se ignoran
BIENVENIDA = ("✅ Acceso aprobado: quedaste suscrito a las alertas de WREWS (sistema de alerta temprana "
              "de riesgo hídrico).\nTe aviso cada vez que cambie el estado del reservorio, "
              "con una recomendación.\n\n/estado  ver el estado actual\n"
              "/recomendacion  pedir el análisis de la IA\n"
              "/dashboard  tablero completo en imagen\n"
              "/envivo  fijar el dashboard arriba del chat, actualizado solo\n"
              "/grafica  gráfica de la última hora\n/tablero  tablero global (Ubidots)\n"
              "/stop  dejar de recibir alertas")


def texto_estado(estado, nivel=None, riesgo=None, motivo=None):
    lineas = [f"{ICONO.get(estado, '•')} WREWS: {TITULO.get(estado, estado)}",
              ACCION.get(estado, "")]
    datos = []
    if nivel is not None:
        datos.append(f"nivel {nivel:.0f} %")
    if riesgo is not None:
        datos.append(f"riesgo {riesgo:.0f}/100")
    if datos:
        lineas.append("Último dato: " + " · ".join(datos))
    if motivo:
        lineas.append(f"Detalle: {motivo}")
    lineas.append(time.strftime("%Y-%m-%d %H:%M:%S"))
    return "\n".join(lineas)


class Telegram:
    def __init__(self, token, chat_ids="", db=None, clave="", estado_actual=None, admin="",
                 grafica=None, tablero_url="", recomendar=None, dashboard=None):
        """estado_actual: funcion -> texto de /estado. grafica: funcion -> (png, pie)."""
        self.grafica = grafica
        self.dashboard = dashboard
        self.recomendar = recomendar
        self.tablero_url = tablero_url
        self.token = token
        self.fijos = [c.strip() for c in chat_ids.split(",") if c.strip()]
        self.db = db
        self.clave = clave
        self.admin = int(admin) if str(admin).strip().lstrip("-").isdigit() else None
        self.estado_actual = estado_actual
        self.intentos = {}                 # chat -> (fallos de clave, hora del ultimo)
        if token and not (self.admin or clave):
            log.warning("Telegram: bot ABIERTO (sin TELEGRAM_ADMIN ni TELEGRAM_CLAVE): "
                        "cualquiera que escriba /start recibe las alertas")
        self.cola = queue.Queue(maxsize=50)
        self.refrescar = threading.Event()    # actualizar ya el dashboard en vivo
        if token:
            threading.Thread(target=self._hilo_envio, name="telegram", daemon=True).start()
            if db is not None:
                threading.Thread(target=self._hilo_bot, name="telegram-bot",
                                 daemon=True).start()
                threading.Thread(target=self._hilo_vivo, name="telegram-vivo",
                                 daemon=True).start()
                self._api("setMyCommands", commands=[
                    {"command": "estado", "description": "Estado actual del reservorio"},
                    {"command": "recomendacion", "description": "Pedir el análisis de la IA (Claude)"},
                    {"command": "dashboard", "description": "Tablero completo en imagen"},
                    {"command": "envivo", "description": "Fijar el dashboard arriba (se actualiza solo)"},
                    {"command": "detener", "description": "Quitar el dashboard en vivo"},
                    {"command": "grafica", "description": "Gráfica de la última hora"},
                    {"command": "tablero", "description": "Tablero global (Ubidots)"},
                    {"command": "stop", "description": "Dejar de recibir alertas"},
                ])

    @property
    def activo(self):
        return bool(self.token)

    def destinatarios(self):
        subs = self.db.suscriptores() if self.db is not None else []
        admin = [self.admin] if self.admin else []
        return list(dict.fromkeys([str(c) for c in admin + self.fijos + subs]))

    def enviar(self, texto):
        """No bloquea: deja el aviso en la cola del hilo de Telegram."""
        if not self.activo:
            return
        try:
            self.cola.put_nowait((texto, time.time()))
        except queue.Full:
            log.warning("Telegram: cola llena, se descarta un aviso")

    # ---- Envio de avisos ------------------------------------------------------
    def _hilo_envio(self):
        while True:
            texto, t0 = self.cola.get()
            pendientes = self.destinatarios()
            if not pendientes:
                log.info("Telegram: nadie suscrito todavia (escribale /start al bot)")
                continue
            # Reintenta hasta 10 min (p. ej. mientras vuelve Internet)
            while pendientes:
                pendientes = [c for c in pendientes if not self._mandar_a(c, texto)]
                if not pendientes:
                    log.info("Telegram: aviso enviado")
                elif time.time() - t0 > 600:
                    log.warning("Telegram: aviso descartado tras 10 min sin Internet")
                    break
                else:
                    time.sleep(15)

    def _mandar_a(self, chat, texto, botones=None):
        """True si se envio o si no tiene sentido reintentar.

        botones: [[("texto", "dato"), ...], ...] -> botones dentro del mensaje.
        """
        cuerpo = {"chat_id": chat, "text": texto}
        if botones:
            cuerpo["reply_markup"] = {"inline_keyboard": [
                [{"text": t, "callback_data": d} for t, d in fila] for fila in botones]}
        try:
            r = requests.post(API.format(token=self.token, metodo="sendMessage"),
                              json=cuerpo, timeout=10)
        except requests.RequestException as e:
            log.warning("Telegram: sin conexion (%s)", type(e).__name__)
            return False
        if r.status_code == 200:
            return True
        log.warning("Telegram rechazo el mensaje a %s (%s): %s", chat, r.status_code,
                    r.text[:150])
        if r.status_code == 403 and self.db is not None:   # el usuario bloqueo el bot
            self.db.desuscribir(int(chat))
        return r.status_code in (400, 401, 403, 404)

    def _mandar_grafica(self, cid, fuente=None):
        """Imagen generada en el gateway: /grafica (por defecto) o /dashboard.

        Devuelve el message_id de la foto enviada, o None.
        """
        fuente = fuente or self.grafica
        if not fuente:
            self._mandar_a(cid, "La gráfica no está disponible en este gateway.")
            return None
        try:
            png, pie = fuente()
        except ImportError:
            self._mandar_a(cid, "Falta matplotlib en el gateway (pip install matplotlib).")
            return None
        try:
            r = requests.post(API.format(token=self.token, metodo="sendPhoto"),
                              data={"chat_id": cid, "caption": pie},
                              files={"photo": ("wrews.png", png, "image/png")}, timeout=20)
            if r.status_code != 200:
                log.warning("Telegram no acepto la grafica: %s", r.text[:150])
                return None
            return r.json()["result"]["message_id"]
        except (requests.RequestException, ValueError, KeyError) as e:
            log.warning("Telegram: sin conexion para la grafica (%s)", type(e).__name__)
            return None

    # ---- Dashboard en vivo: un mensaje fijado que se actualiza solo ----------
    def _iniciar_vivo(self, cid):
        if not self.dashboard:
            self._mandar_a(cid, "El dashboard no está disponible en este gateway.")
            return
        anterior = dict(self.db.vivos()).get(cid)
        if anterior:
            self._api("unpinChatMessage", chat_id=cid, message_id=anterior)
        msg = self._mandar_grafica(cid, self.dashboard)
        if msg is None:
            return
        self._api("pinChatMessage", chat_id=cid, message_id=msg, disable_notification=True)
        self.db.poner_vivo(cid, msg)
        self._mandar_a(cid, f"📌 Dashboard en vivo fijado arriba del chat: se actualiza solo "
                            f"cada {VIVO_CADA_S} s y apenas cambia el estado. /detener para quitarlo.")

    def _detener_vivo(self, cid):
        msg = dict(self.db.vivos()).get(cid)
        if msg:
            self._api("unpinChatMessage", chat_id=cid, message_id=msg)
        self.db.poner_vivo(cid, None)
        self._mandar_a(cid, "Listo, el dashboard en vivo ya no se actualiza. /envivo para volver.")

    def _hilo_vivo(self):
        while True:
            self.refrescar.wait(VIVO_CADA_S)
            self.refrescar.clear()
            try:
                vivos = self.db.vivos()
                if vivos and self.dashboard:
                    png, pie = self.dashboard()
                    pie = f"{pie} · actualizado {time.strftime('%H:%M:%S')} (en vivo)"
                    self._actualizar_vivos(vivos, png, pie)
            except Exception:
                log.exception("Error actualizando el dashboard en vivo")

    def _actualizar_vivos(self, vivos, png, pie):
        for chat, msg in vivos:
            r = self._editar_foto(chat, msg, png, pie)
            if r is not None and r.status_code == 400 and "not found" in r.text:
                self.db.poner_vivo(chat, None)       # el usuario borro el mensaje

    def _editar_foto(self, chat, msg, png, pie):
        try:
            return requests.post(
                API.format(token=self.token, metodo="editMessageMedia"),
                data={"chat_id": chat, "message_id": msg, "media": json.dumps(
                    {"type": "photo", "media": "attach://foto", "caption": pie})},
                files={"foto": ("wrews.png", png, "image/png")}, timeout=20)
        except requests.RequestException as e:
            log.debug("Telegram: sin conexion para el dashboard en vivo (%s)", e)
            return None

    def _api(self, metodo, **cuerpo):
        try:
            requests.post(API.format(token=self.token, metodo=metodo), json=cuerpo, timeout=10)
        except requests.RequestException as e:
            log.warning("Telegram %s: %s", metodo, type(e).__name__)

    # ---- Comandos que le escriben al bot ------------------------------------
    def _hilo_bot(self):
        offset = None
        while True:
            try:
                r = requests.get(API.format(token=self.token, metodo="getUpdates"),
                                 params={"timeout": 30, "offset": offset}, timeout=40)
                d = r.json()
                if not d.get("ok"):
                    log.warning("Telegram getUpdates: %s", d.get("description"))
                    time.sleep(30)
                    continue
                for u in d["result"]:
                    offset = u["update_id"] + 1
                    if "callback_query" in u:
                        self._atender_boton(u["callback_query"])
                        continue
                    msg = u.get("message") or {}
                    # Lo que escribieron con el gateway apagado no se contesta tarde.
                    if time.time() - msg.get("date", 0) > MENSAJE_VIGENTE_S:
                        continue
                    self._atender(msg)
            except (requests.RequestException, ValueError) as e:
                log.debug("Telegram getUpdates sin conexion: %s", e)
                time.sleep(10)
            except Exception:
                log.exception("Error atendiendo comandos de Telegram")
                time.sleep(10)

    @staticmethod
    def _cmd(nombre, cid):
        """Comando que se toca de una vez: /aprobar_123 (sin espacio).

        Los ids de grupos son negativos y el '-' no vale en un comando: ahi
        quedan los botones o escribir el comando con espacio.
        """
        return f"/{nombre}_{cid}" if cid > 0 else f"/{nombre} {cid}"

    def _atender(self, m):
        texto = (m.get("text") or "").strip()
        chat = m.get("chat") or {}
        if not texto or "id" not in chat:
            return
        cid = chat["id"]
        nombre = (chat.get("title") or " ".join(filter(None, [chat.get("first_name"),
                  chat.get("last_name")])) or chat.get("username") or str(cid))
        partes = texto.split()
        cmd = partes[0].split("@")[0]            # en grupos llega /start@WREWS_Alertasbot
        arg = partes[1] if len(partes) > 1 else ""
        if "_" in cmd:                           # /aprobar_123 -> /aprobar 123
            cmd, arg = cmd.split("_", 1)
        elif cmd.lower().startswith("/start") and len(cmd) > 6:
            cmd, arg = cmd[:6], cmd[6:]          # clave pegada: /startCLAVE
        cmd = cmd.lower()                        # la clave conserva mayusculas
        es_admin = self.admin is not None and cid == self.admin

        if cmd == "/start":
            self._pedir_acceso(cid, nombre, arg, es_admin)
        elif cmd == "/stop":
            if es_admin:
                self._mandar_a(cid, "Eres el administrador: siempre recibes las alertas. "
                                    "Para cambiar de administrador se edita TELEGRAM_ADMIN "
                                    "en la configuracion del gateway.")
                return
            self.db.desuscribir(cid)
            self._mandar_a(cid, "Listo, ya no recibirás alertas. /start para volver a pedir acceso.")
        elif cmd in ("/estado", "/grafica", "/dashboard", "/tablero", "/recomendacion",
                     "/envivo", "/detener"):
            if not es_admin and cid not in self.db.suscriptores():
                self._mandar_a(cid, "🔒 Solo el personal autorizado puede consultar el sistema.")
                return
            if cmd == "/estado":
                self._mandar_a(cid, self.estado_actual() if self.estado_actual else "Sin datos.")
            elif cmd == "/grafica":
                self._mandar_grafica(cid)
            elif cmd == "/dashboard":
                self._mandar_grafica(cid, self.dashboard)
            elif cmd == "/envivo":
                self._iniciar_vivo(cid)
            elif cmd == "/detener":
                self._detener_vivo(cid)
            elif cmd == "/recomendacion":
                if not self.recomendar:
                    self._mandar_a(cid, "La IA no está disponible en este gateway.")
                    return
                self._mandar_a(cid, "🤖 Consultando a la IA con los datos actuales…")
                self._mandar_a(cid, self.recomendar())
            elif self.tablero_url:
                self._mandar_a(cid, "📊 Tablero global de WREWS (inicie sesión con su "
                                    f"usuario de Ubidots):\n{self.tablero_url}")
            else:
                self._mandar_a(cid, "El enlace del tablero no está configurado "
                                    "(UBIDOTS_TABLERO_URL en el gateway).")
        elif cmd in ("/aprobar", "/rechazar", "/quitar", "/usuarios"):
            if not es_admin:
                self._mandar_a(cid, "🔒 Ese comando es solo para el administrador.")
                return
            self._mandar_a(self.admin, self._comando_admin(cmd, arg))

    def _atender_boton(self, cq):
        """Botones Aprobar / Rechazar del mensaje de solicitud."""
        quien = (cq.get("from") or {}).get("id")
        msg = cq.get("message") or {}
        accion, _, arg = (cq.get("data") or "").partition(":")
        if self.admin is None or quien != self.admin:
            self._api("answerCallbackQuery", callback_query_id=cq["id"],
                      text="Solo el administrador puede hacer esto")
            return
        resultado = self._comando_admin("/" + accion, arg)
        self._api("answerCallbackQuery", callback_query_id=cq["id"], text=resultado[:190])
        if msg:   # el mensaje queda con la decision y sin botones
            self._api("editMessageText", chat_id=msg["chat"]["id"],
                      message_id=msg["message_id"],
                      text=f"{msg.get('text', '')}\n\n→ {resultado}")

    def _pedir_acceso(self, cid, nombre, arg, es_admin):
        if self.clave and not es_admin:
            fallos, t = self.intentos.get(cid, (0, 0))
            if fallos >= MAX_INTENTOS_CLAVE and time.time() - t < BLOQUEO_CLAVE_S:
                return                        # bloqueado: ni siquiera se responde
            if arg != self.clave:
                self.intentos[cid] = (fallos + 1, time.time())
                self._mandar_a(cid, "🔒 Este bot es solo para personal autorizado. "
                                    "Escriba /start seguido de la clave de registro.")
                log.warning("Telegram: clave incorrecta desde %s (%s)", nombre, cid)
                return
            self.intentos.pop(cid, None)
        if es_admin or self.admin is None:
            # Administrador, o bot sin administrador (solo con clave, o abierto)
            self.db.solicitar(cid, nombre, aprobado=True)
            log.info("Telegram: suscriptor aprobado %s (%s)", nombre, cid)
            self._mandar_a(cid, BIENVENIDA + ("\n\nEres el administrador: /usuarios para "
                                              "ver solicitudes." if es_admin else ""))
            return
        if cid in self.db.suscriptores():
            self._mandar_a(cid, "Ya tienes acceso. /estado para consultar.")
            return
        self.db.solicitar(cid, nombre, aprobado=False)
        log.info("Telegram: solicitud de acceso de %s (%s)", nombre, cid)
        self._mandar_a(cid, "📝 Solicitud enviada. El administrador del sistema debe "
                            "aprobarla; te aviso cuando tengas acceso.")
        self._mandar_a(self.admin, f"🔐 Solicitud de acceso a las alertas WREWS:\n{nombre} "
                                   f"(id {cid})",
                       botones=[[("✅ Aprobar", f"aprobar:{cid}"),
                                 ("❌ Rechazar", f"rechazar:{cid}")]])

    def _comando_admin(self, cmd, arg):
        """Ejecuta un comando del administrador y devuelve el texto del resultado."""
        if cmd == "/usuarios":
            filas = self.db.lista_suscriptores()
            if not filas:
                return "No hay usuarios ni solicitudes."
            lineas = []
            for f in filas:
                c = f["chat_id"]
                if c == self.admin:       # sin comandos: no se puede quitar a si mismo
                    lineas.insert(0, f"👑 {f['nombre']}  (administrador)")
                elif f["aprobado"]:
                    lineas.append(f"✅ {f['nombre']}  {self._cmd('quitar', c)}")
                else:
                    lineas.append(f"⏳ {f['nombre']}  {self._cmd('aprobar', c)}  "
                                  f"{self._cmd('rechazar', c)}")
            return ("Usuarios (👑 administrador, ✅ aprobado, ⏳ pendiente). Toque el "
                    "comando junto a cada uno:\n\n" + "\n".join(lineas))
        if not arg.lstrip("-").isdigit():
            return f"Uso: {cmd}_ID (toque el comando que sale en /usuarios)"
        objetivo = int(arg)
        if objetivo == self.admin:
            return "El administrador no se puede aprobar ni quitar a sí mismo."
        nombre = next((f["nombre"] for f in self.db.lista_suscriptores()
                       if f["chat_id"] == objetivo), str(objetivo))
        if cmd == "/aprobar":
            if not self.db.aprobar(objetivo):
                return f"No hay solicitud de {nombre}."
            self._mandar_a(objetivo, BIENVENIDA)
            log.info("Telegram: el administrador aprobo a %s (%s)", nombre, objetivo)
            return f"✅ {nombre} aprobado: ya recibe las alertas."
        self.db.desuscribir(objetivo)   # /rechazar o /quitar
        self._mandar_a(objetivo, "🔒 Tu acceso a las alertas WREWS fue rechazado o "
                                 "retirado por el administrador.")
        log.info("Telegram: el administrador quito a %s (%s)", nombre, objetivo)
        return f"❌ {nombre} ya no tiene acceso."


def _main():
    from .almacen import Almacen
    from .config import Config
    cfg = Config.desde_entorno()
    if not cfg.telegram_token:
        print("Falta TELEGRAM_TOKEN en gateway.env")
        return 1
    r = requests.get(API.format(token=cfg.telegram_token, metodo="getMe"), timeout=10).json()
    if not r.get("ok"):
        print("El token no sirve:", r.get("description"))
        return 1
    print(f"Bot: @{r['result']['username']}")
    t = Telegram(cfg.telegram_token, cfg.telegram_chat_id)
    t.db = Almacen(cfg.db_path)
    dest = t.destinatarios()
    print("Suscriptores:", dest or "ninguno (escribale /start al bot con el gateway corriendo)")
    ok = all(t._mandar_a(c, texto_estado(1, 48, 37, "mensaje de prueba del gateway WREWS"))
             for c in dest)
    print("Enviado" if dest and ok else "No se envio")
    return 0 if dest and ok else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(_main())
