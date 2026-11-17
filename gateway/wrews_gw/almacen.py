"""Persistencia local en SQLite.

Regla del gateway: TODO lo que llega del ESP32 se guarda aqui ANTES de
procesarlo o reenviarlo. Lo que va a la nube pasa por la tabla cola_nube
(patron "store and forward"): si se cae Internet, los datos se acumulan y se
mandan con su marca de tiempo original cuando vuelve la conexion.
"""
import json
import os
import sqlite3
import threading
import time

ESQUEMA = """
CREATE TABLE IF NOT EXISTS mediciones (
    id          INTEGER PRIMARY KEY,
    ts_ms       INTEGER NOT NULL,      -- hora de llegada al gateway (epoch ms)
    dispositivo TEXT    NOT NULL,
    boot        INTEGER,               -- id aleatorio de cada arranque del ESP32
    seq         INTEGER,
    estado      INTEGER,
    silenciado  INTEGER,
    nivel       REAL,                  -- %
    distancia   REAL,                  -- cm
    tasa        REAL,                  -- pp/min
    riesgo      REAL,                  -- 0-100
    idx_evap    REAL,                  -- %
    et          REAL,                  -- mm/dia
    temp        REAL,                  -- C
    hum         REAL,                  -- %
    pres        REAL,                  -- hPa
    vpd         REAL,                  -- kPa
    irr         REAL,                  -- W/m2
    rssi        INTEGER,               -- dBm
    anomalia    TEXT,                  -- NULL si la muestra es valida
    crudo       TEXT    NOT NULL       -- JSON tal como llego
);
CREATE INDEX IF NOT EXISTS ix_med_ts ON mediciones(dispositivo, ts_ms);

CREATE TABLE IF NOT EXISTS estados (
    id          INTEGER PRIMARY KEY,
    ts_ms       INTEGER NOT NULL,
    dispositivo TEXT    NOT NULL,
    estado      INTEGER NOT NULL,      -- 0 NORMAL, 1 PRECAUCION, 2 CRITICO, 3 FALLO
    estado_txt  TEXT,
    silenciado  INTEGER,
    origen      TEXT,                  -- esp32 | gateway (FALLO por perdida del enlace)
    crudo       TEXT
);

CREATE TABLE IF NOT EXISTS eventos (
    id          INTEGER PRIMARY KEY,
    ts_ms       INTEGER NOT NULL,
    dispositivo TEXT    NOT NULL,
    origen      TEXT    NOT NULL,      -- esp32 | gateway
    boot        INTEGER,
    ev_id       INTEGER,               -- id del evento en el ESP32
    gravedad    INTEGER,               -- 0 info, 1 precaucion, 2 critico/fallo
    texto       TEXT    NOT NULL,
    UNIQUE (dispositivo, boot, ev_id)
);

CREATE TABLE IF NOT EXISTS comandos (
    id          INTEGER PRIMARY KEY,
    ts_ms       INTEGER NOT NULL,
    dispositivo TEXT    NOT NULL,
    origen      TEXT    NOT NULL,      -- Ubidots | consola de la Pi | ...
    accion      TEXT    NOT NULL,
    respuesta   TEXT,                  -- JSON de wrews/<id>/cmd/resp
    ts_resp_ms  INTEGER
);

CREATE TABLE IF NOT EXISTS agregados (
    id           INTEGER PRIMARY KEY,
    ts_inicio_ms INTEGER NOT NULL,
    ts_fin_ms    INTEGER NOT NULL,
    dispositivo  TEXT    NOT NULL,
    n            INTEGER NOT NULL,     -- muestras validas
    n_esperadas  INTEGER NOT NULL,
    anomalias    INTEGER NOT NULL,
    completitud  REAL    NOT NULL,     -- % de muestras recibidas
    resumen      TEXT    NOT NULL      -- JSON: media/min/max por variable
);

CREATE TABLE IF NOT EXISTS ia (
    id            INTEGER PRIMARY KEY,
    ts_ms         INTEGER NOT NULL,
    dispositivo   TEXT    NOT NULL,
    nivel_actual  REAL,
    pendiente_ppm REAL,                -- pp/min de la regresion
    r2            REAL,
    n_puntos      INTEGER,
    min_a_critico REAL,                -- NULL si no desciende
    tendencia     TEXT,
    estado        INTEGER,
    proveedor     TEXT,                -- gemini | openai | reglas
    modelo        TEXT,
    prompt        TEXT,                -- prompt exacto enviado al LLM
    texto         TEXT,
    latencia_ms   INTEGER,
    error         TEXT                 -- por que se uso el respaldo, si aplica
);

CREATE TABLE IF NOT EXISTS suscriptores (
    chat_id     INTEGER PRIMARY KEY,   -- chat de Telegram que escribio /start
    nombre      TEXT,
    ts_ms       INTEGER NOT NULL,      -- hora de la solicitud
    aprobado    INTEGER NOT NULL DEFAULT 0,  -- 1 = el administrador lo autorizo
    msg_vivo    INTEGER                      -- mensaje del dashboard en vivo fijado
);

CREATE TABLE IF NOT EXISTS cola_nube (
    id          INTEGER PRIMARY KEY,
    ts_ms       INTEGER NOT NULL,
    payload     TEXT    NOT NULL,      -- JSON en formato Ubidots
    enviado_ms  INTEGER,               -- NULL = pendiente
    intentos    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_cola_pend ON cola_nube(enviado_ms, id);
"""

CAMPOS_MEDICION = ("nivel", "distancia", "tasa", "riesgo", "idx_evap", "et",
                   "temp", "hum", "pres", "vpd", "irr")


def ahora_ms():
    return int(time.time() * 1000)


class Almacen:
    """Envoltorio de SQLite seguro entre hilos (un candado para todo)."""

    def __init__(self, ruta):
        if ruta != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        self._db = sqlite3.connect(ruta, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA synchronous=NORMAL")
            self._db.executescript(ESQUEMA)
            # Bases creadas antes de la aprobacion de suscriptores
            cols = [r[1] for r in self._db.execute("PRAGMA table_info(suscriptores)")]
            if "aprobado" not in cols:
                self._db.execute("ALTER TABLE suscriptores ADD COLUMN aprobado "
                                 "INTEGER NOT NULL DEFAULT 0")
            if "msg_vivo" not in cols:
                self._db.execute("ALTER TABLE suscriptores ADD COLUMN msg_vivo INTEGER")
            self._db.commit()

    def _ejecutar(self, sql, args=()):
        with self._lock:
            cur = self._db.execute(sql, args)
            self._db.commit()
            return cur.lastrowid

    def _consultar(self, sql, args=()):
        with self._lock:
            return [dict(r) for r in self._db.execute(sql, args).fetchall()]

    # ---- Entradas del ESP32 -------------------------------------------------
    def guardar_medicion(self, dispositivo, datos, ts_ms=None):
        ts_ms = ts_ms or ahora_ms()
        valores = [datos.get(c) for c in CAMPOS_MEDICION]
        return self._ejecutar(
            "INSERT INTO mediciones (ts_ms, dispositivo, boot, seq, estado, silenciado, "
            + ", ".join(CAMPOS_MEDICION) + ", rssi, crudo) VALUES ("
            + ", ".join("?" * (6 + len(CAMPOS_MEDICION) + 2)) + ")",
            [ts_ms, dispositivo, datos.get("boot"), datos.get("seq"),
             datos.get("estado"), datos.get("silenciado")] + valores
            + [datos.get("rssi"), json.dumps(datos, ensure_ascii=False)])

    def marcar_anomalia(self, id_medicion, motivo):
        self._ejecutar("UPDATE mediciones SET anomalia = ? WHERE id = ?", (motivo, id_medicion))

    def guardar_estado(self, dispositivo, datos, ts_ms=None, origen="esp32"):
        return self._ejecutar(
            "INSERT INTO estados (ts_ms, dispositivo, estado, estado_txt, silenciado, origen, "
            "crudo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts_ms or ahora_ms(), dispositivo, datos.get("estado"), datos.get("estado_txt"),
             datos.get("silenciado"), origen, json.dumps(datos, ensure_ascii=False)))

    def guardar_evento(self, dispositivo, origen, texto, gravedad=0, boot=None, ev_id=None,
                       ts_ms=None):
        """Devuelve el id nuevo, o None si el evento ya estaba (reenvio del ESP32)."""
        with self._lock:
            cur = self._db.execute(
                "INSERT OR IGNORE INTO eventos (ts_ms, dispositivo, origen, boot, ev_id, "
                "gravedad, texto) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts_ms or ahora_ms(), dispositivo, origen, boot, ev_id, gravedad, texto))
            self._db.commit()
            return cur.lastrowid if cur.rowcount else None

    def guardar_comando(self, dispositivo, origen, accion):
        return self._ejecutar(
            "INSERT INTO comandos (ts_ms, dispositivo, origen, accion) VALUES (?, ?, ?, ?)",
            (ahora_ms(), dispositivo, origen, accion))

    def guardar_respuesta_comando(self, dispositivo, respuesta):
        """Asocia la respuesta al ultimo comando sin respuesta de ese dispositivo."""
        with self._lock:
            fila = self._db.execute(
                "SELECT id FROM comandos WHERE dispositivo = ? AND respuesta IS NULL "
                "ORDER BY id DESC LIMIT 1", (dispositivo,)).fetchone()
            if fila:
                self._db.execute("UPDATE comandos SET respuesta = ?, ts_resp_ms = ? WHERE id = ?",
                                 (json.dumps(respuesta, ensure_ascii=False), ahora_ms(), fila[0]))
                self._db.commit()

    # ---- Procesamiento ------------------------------------------------------
    def guardar_agregado(self, dispositivo, ag):
        return self._ejecutar(
            "INSERT INTO agregados (ts_inicio_ms, ts_fin_ms, dispositivo, n, n_esperadas, "
            "anomalias, completitud, resumen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ag["ts_inicio_ms"], ag["ts_fin_ms"], dispositivo, ag["n"], ag["n_esperadas"],
             ag["anomalias"], ag["completitud"], json.dumps(ag["resumen"])))

    def serie_nivel(self, dispositivo, desde_ms):
        """[(t_s, nivel)] validos desde desde_ms, en orden."""
        filas = self._consultar(
            "SELECT ts_ms, nivel FROM mediciones WHERE dispositivo = ? AND ts_ms >= ? "
            "AND nivel IS NOT NULL AND anomalia IS NULL ORDER BY ts_ms", (dispositivo, desde_ms))
        return [(f["ts_ms"] / 1000.0, f["nivel"]) for f in filas]

    def ultima_medicion(self, dispositivo):
        filas = self._consultar(
            "SELECT * FROM mediciones WHERE dispositivo = ? AND anomalia IS NULL "
            "ORDER BY id DESC LIMIT 1", (dispositivo,))
        return filas[0] if filas else None

    def eventos_recientes(self, dispositivo, n=5):
        return self._consultar(
            "SELECT ts_ms, origen, gravedad, texto FROM eventos WHERE dispositivo = ? "
            "ORDER BY id DESC LIMIT ?", (dispositivo, n))

    def guardar_ia(self, dispositivo, r):
        return self._ejecutar(
            "INSERT INTO ia (ts_ms, dispositivo, nivel_actual, pendiente_ppm, r2, n_puntos, "
            "min_a_critico, tendencia, estado, proveedor, modelo, prompt, texto, latencia_ms, "
            "error) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ahora_ms(), dispositivo, r.get("nivel_actual"), r.get("pendiente_ppm"),
             r.get("r2"), r.get("n_puntos"), r.get("min_a_critico"), r.get("tendencia"),
             r.get("estado"), r.get("proveedor"), r.get("modelo"), r.get("prompt"),
             r.get("texto"), r.get("latencia_ms"), r.get("error")))

    # ---- Suscriptores de Telegram --------------------------------------------
    def solicitar(self, chat_id, nombre, aprobado=False):
        """Registra una solicitud (o la aprueba directo). No baja a un ya aprobado."""
        self._ejecutar(
            "INSERT INTO suscriptores (chat_id, nombre, ts_ms, aprobado) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET nombre = excluded.nombre, "
            "aprobado = MAX(aprobado, excluded.aprobado)",
            (chat_id, nombre, ahora_ms(), int(aprobado)))

    def aprobar(self, chat_id):
        """True si existia la solicitud."""
        with self._lock:
            cur = self._db.execute("UPDATE suscriptores SET aprobado = 1 WHERE chat_id = ?",
                                   (chat_id,))
            self._db.commit()
            return cur.rowcount > 0

    def desuscribir(self, chat_id):
        self._ejecutar("DELETE FROM suscriptores WHERE chat_id = ?", (chat_id,))

    def suscriptores(self):
        """Solo los aprobados: son los unicos que reciben alertas."""
        return [f["chat_id"] for f in self._consultar(
            "SELECT chat_id FROM suscriptores WHERE aprobado = 1")]

    def poner_vivo(self, chat_id, msg_id):
        """msg_id=None quita el dashboard en vivo de ese chat."""
        self._ejecutar("UPDATE suscriptores SET msg_vivo = ? WHERE chat_id = ?",
                       (msg_id, chat_id))

    def vivos(self):
        """[(chat_id, msg_id)] de los aprobados con dashboard en vivo."""
        return [(f["chat_id"], f["msg_vivo"]) for f in self._consultar(
            "SELECT chat_id, msg_vivo FROM suscriptores WHERE aprobado = 1 "
            "AND msg_vivo IS NOT NULL")]

    def lista_suscriptores(self):
        return self._consultar("SELECT chat_id, nombre, aprobado FROM suscriptores "
                               "ORDER BY aprobado DESC, ts_ms")

    # ---- Cola hacia la nube -------------------------------------------------
    def encolar_nube(self, payload, ts_ms=None):
        return self._ejecutar("INSERT INTO cola_nube (ts_ms, payload) VALUES (?, ?)",
                              (ts_ms or ahora_ms(), json.dumps(payload, ensure_ascii=False)))

    def pendientes_nube(self, limite=20):
        filas = self._consultar(
            "SELECT id, ts_ms, payload, intentos FROM cola_nube WHERE enviado_ms IS NULL "
            "ORDER BY id LIMIT ?", (limite,))
        for f in filas:
            f["payload"] = json.loads(f["payload"])
        return filas

    def marcar_enviado(self, id_cola):
        self._ejecutar("UPDATE cola_nube SET enviado_ms = ? WHERE id = ?", (ahora_ms(), id_cola))

    def sumar_intento(self, id_cola):
        self._ejecutar("UPDATE cola_nube SET intentos = intentos + 1 WHERE id = ?", (id_cola,))

    def contar_pendientes(self):
        return self._consultar("SELECT COUNT(*) AS n FROM cola_nube WHERE enviado_ms IS NULL")[0]["n"]

    def cerrar(self):
        with self._lock:
            self._db.close()
