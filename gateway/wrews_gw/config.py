"""Configuracion del gateway, leida de variables de entorno.

En la Raspberry Pi las variables vienen de /etc/wrews/gateway.env (systemd
las carga con EnvironmentFile). Para correrlo a mano: `set -a; . gateway.env; set +a`.
Ver gateway.env.example para la lista completa con explicaciones.
"""
import os
from dataclasses import dataclass, field


def _txt(nombre, defecto=""):
    v = os.environ.get(nombre, defecto).strip()
    # Un marcador sin llenar de gateway.env.example cuenta como vacio
    return "" if v.startswith("CAMBIAR") else v


def _num(nombre, defecto):
    v = _txt(nombre)
    return type(defecto)(v) if v else defecto


def _bool(nombre, defecto):
    v = _txt(nombre).lower()
    if not v:
        return defecto
    return v in ("1", "si", "sí", "true", "yes", "on")


@dataclass
class Config:
    dispositivo: str = "wrews-01"

    # Broker local (Mosquitto en la misma Pi)
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_user: str = "gateway"
    mqtt_pass: str = ""

    # Base de datos
    db_path: str = "/var/lib/wrews/wrews.db"

    # Procesamiento local
    ventana_s: int = 60          # cada cuanto se agrega y se manda a la nube
    periodo_tel_s: float = 5.0   # periodo de la telemetria del ESP32
    sin_datos_s: int = 20        # sin telemetria por mas de esto -> alerta de enlace
    z_max: float = 4.0           # umbral del z robusto (MAD) para marcar anomalias

    # Ubidots
    ubidots_token: str = ""
    ubidots_dispositivo: str = "wrews-01"
    ubidots_host: str = "industrial.api.ubidots.com"
    ubidots_port: int = 8883
    ubidots_tls: bool = True
    ubidots_variables: list = field(default_factory=lambda: [
        "nivel", "riesgo", "tasa", "idx_evap", "temp"])
    ubidots_msg_por_s: float = 2.0       # ritmo maximo al vaciar la cola tras una caida
    ubidots_tablero_url: str = ""        # enlace del tablero (comando /tablero del bot)

    # Modulo de IA
    ia_proveedor: str = "claude"         # claude | gemini | openai | ninguno
    ia_llm_auto: bool = False            # False: el LLM solo a pedido (/recomendacion)
    ia_cada_s: int = 300                 # periodo del LLM en PRECAUCION / CRITICO
    ia_cada_s_normal: int = 1800         # periodo del LLM en NORMAL (casi no cambia)
    ia_min_entre_llamadas_s: int = 60    # aunque cambie el estado, no mas seguido que esto
    ia_ventana_min: float = 10.0         # minutos de historia para la regresion
    ia_umbral_critico: float = 15.0      # % de nivel (U_CRIT_NIVEL del firmware)
    ia_umbral_precaucion: float = 50.0   # % de nivel (U_PREC_NIVEL del firmware)
    ia_timeout_s: float = 40.0
    claude_api_key: str = ""
    claude_modelo: str = "claude-opus-5-5"
    claude_esfuerzo: str = "low"         # low | medium | high
    gemini_api_key: str = ""
    gemini_modelo: str = "gemini-3.6-flash"
    openai_api_key: str = ""
    openai_modelo: str = "gpt-4o-mini"

    # Avisos al celular por Telegram (opcional)
    telegram_token: str = ""
    telegram_chat_id: str = ""
    telegram_clave: str = ""             # si se define: /start CLAVE para suscribirse
    telegram_admin: str = ""             # chat id del administrador que aprueba

    @property
    def nube_activa(self):
        return bool(self.ubidots_token)

    @classmethod
    def desde_entorno(cls):
        c = cls()
        c.dispositivo = _txt("WREWS_DISPOSITIVO", c.dispositivo)
        c.mqtt_host = _txt("MQTT_HOST", c.mqtt_host)
        c.mqtt_port = _num("MQTT_PORT", c.mqtt_port)
        c.mqtt_user = _txt("MQTT_USER", c.mqtt_user)
        c.mqtt_pass = _txt("MQTT_PASS", c.mqtt_pass)
        c.db_path = _txt("DB_PATH", c.db_path)
        c.ventana_s = _num("VENTANA_S", c.ventana_s)
        c.sin_datos_s = _num("SIN_DATOS_S", c.sin_datos_s)
        c.z_max = _num("Z_MAX", c.z_max)
        c.ubidots_token = _txt("UBIDOTS_TOKEN")
        c.ubidots_dispositivo = _txt("UBIDOTS_DISPOSITIVO", c.dispositivo)
        c.ubidots_host = _txt("UBIDOTS_HOST", c.ubidots_host)
        c.ubidots_tls = _bool("UBIDOTS_TLS", c.ubidots_tls)
        c.ubidots_port = _num("UBIDOTS_PORT", 8883 if c.ubidots_tls else 1883)
        c.ubidots_msg_por_s = _num("UBIDOTS_MSG_POR_S", c.ubidots_msg_por_s)
        c.ubidots_tablero_url = _txt("UBIDOTS_TABLERO_URL")
        vars_txt = _txt("UBIDOTS_VARIABLES")
        if vars_txt:
            c.ubidots_variables = [v.strip() for v in vars_txt.split(",") if v.strip()]
        c.ia_proveedor = _txt("IA_PROVEEDOR", c.ia_proveedor).lower()
        c.ia_llm_auto = _bool("IA_LLM_AUTO", c.ia_llm_auto)
        c.ia_cada_s = _num("IA_CADA_S", c.ia_cada_s)
        c.ia_cada_s_normal = _num("IA_CADA_S_NORMAL", c.ia_cada_s_normal)
        c.ia_min_entre_llamadas_s = _num("IA_MIN_ENTRE_LLAMADAS_S", c.ia_min_entre_llamadas_s)
        c.ia_ventana_min = _num("IA_VENTANA_MIN", c.ia_ventana_min)
        c.ia_umbral_critico = _num("IA_UMBRAL_CRITICO", c.ia_umbral_critico)
        c.ia_umbral_precaucion = _num("IA_UMBRAL_PRECAUCION", c.ia_umbral_precaucion)
        c.ia_timeout_s = _num("IA_TIMEOUT_S", c.ia_timeout_s)
        c.claude_api_key = _txt("ANTHROPIC_API_KEY")
        c.claude_modelo = _txt("CLAUDE_MODELO", c.claude_modelo)
        c.claude_esfuerzo = _txt("CLAUDE_ESFUERZO", c.claude_esfuerzo)
        c.gemini_api_key = _txt("GEMINI_API_KEY")
        c.gemini_modelo = _txt("GEMINI_MODELO", c.gemini_modelo)
        c.openai_api_key = _txt("OPENAI_API_KEY")
        c.openai_modelo = _txt("OPENAI_MODELO", c.openai_modelo)
        c.telegram_token = _txt("TELEGRAM_TOKEN")
        c.telegram_chat_id = _txt("TELEGRAM_CHAT_ID")
        c.telegram_clave = _txt("TELEGRAM_CLAVE")
        c.telegram_admin = _txt("TELEGRAM_ADMIN")
        return c
