"""Procesamiento local en el gateway (antes de subir a la nube).

1. Validacion de cada muestra:
   - Rango fisico por variable: una variable imposible (p. ej. 180 C por un
     contacto flojo del BME280) se descarta SOLA; el resto de la muestra,
     sobre todo el nivel, sigue valiendo.
   - Nivel: rango fisico y z robusto (mediana / MAD) del cambio de nivel
     frente a los ultimos cambios. Si el nivel es anomalo se descarta la
     muestra entera: se guarda en SQLite marcada, pero no entra a los
     promedios ni a la IA.
2. Agregacion por ventanas fijas (VENTANA_S, 60 s por defecto): media, minimo
   y maximo de cada variable y completitud (muestras recibidas / esperadas).
   Reduce lo que se sube a Ubidots de una muestra cada 5 s a una por minuto.
3. Vigilancia del enlace: si el ESP32 deja de publicar, el gateway lo detecta
   (ver Gateway._periodico) aunque el equipo no haya alcanzado a avisar.
"""
import statistics
from collections import deque

# Rangos fisicamente posibles. Fuera de ellos la muestra es error del sensor o
# del enlace, no un dato. El nivel admite un margen por la calibracion.
RANGO_NIVEL = (-5.0, 105.0)
RANGOS = {
    "riesgo": (0.0, 100.0),
    "idx_evap": (0.0, 150.0),
    "temp": (-10.0, 50.0),
    "hum": (0.0, 100.0),
    "pres": (500.0, 1100.0),
    "irr": (0.0, 1500.0),
}

VARIABLES_AGREGADAS = ("nivel", "riesgo", "tasa", "idx_evap", "et", "temp", "hum",
                       "pres", "vpd", "irr")

# Diferencias de nivel por debajo de esto no se consideran anomalia aunque el
# MAD sea casi cero (nivel quieto): evita falsas alarmas por la cuantizacion.
SALTO_MIN_PP = 10.0


class Validador:
    """Marca muestras anomalas del nivel.

    Se mira la DIFERENCIA con la muestra valida anterior, no el valor: asi un
    descenso sostenido (una rampa, que es justo lo que hay que alertar) no se
    confunde con un pico. Se compara cada diferencia con la mediana de las
    ultimas N usando un z robusto (MAD), que no se deja arrastrar por los
    propios picos como lo haria la desviacion estandar.
    """

    def __init__(self, n=20, z_max=4.0):
        self.difs = deque(maxlen=n)
        self.anterior = None
        self.rechazos = 0
        self.z_max = z_max

    @staticmethod
    def limpiar(datos):
        """Copia de la muestra sin las variables fuera de rango fisico.

        Devuelve (datos_limpios, {variable: valor descartado}).
        """
        limpios, fuera = dict(datos), {}
        for var, (lo, hi) in RANGOS.items():
            v = datos.get(var)
            if v is not None and not (lo <= v <= hi):
                fuera[var] = v
                limpios[var] = None
        return limpios, fuera

    def revisar(self, datos):
        """Valida el nivel. None si la muestra es valida, o el motivo."""
        nivel = datos.get("nivel")
        if nivel is None:
            return None            # sin eco: el ESP32 ya lo reporta como FALLO
        lo, hi = RANGO_NIVEL
        if not (lo <= nivel <= hi):
            return f"nivel={nivel} fuera de rango [{lo}, {hi}]"
        if self.anterior is not None and len(self.difs) >= 5:
            d = nivel - self.anterior
            med = statistics.median(self.difs)
            mad = statistics.median(abs(x - med) for x in self.difs)
            # 1.4826 * MAD estima la desviacion estandar si el ruido es normal
            escala = max(1.4826 * mad, 1.0)
            z = abs(d - med) / escala
            if abs(d - med) > SALTO_MIN_PP and z > self.z_max:
                self.rechazos += 1
                if self.rechazos < 3:
                    return f"salto de nivel {d:+.1f} pp (z={z:.1f})"
                # Tres seguidas en el nuevo valor: es un escalon real (recarga
                # o reposicionamiento de la maqueta). Se acepta y se reinicia.
                self.difs.clear()
                self.anterior = nivel
                self.rechazos = 0
                return None
        if self.anterior is not None:
            self.difs.append(nivel - self.anterior)
        self.anterior = nivel
        self.rechazos = 0
        return None


class Agregador:
    """Acumula muestras validas y cierra una ventana cada `ventana_s` segundos."""

    def __init__(self, ventana_s=60, periodo_s=5.0):
        self.ventana_s = ventana_s
        self.periodo_s = periodo_s
        self._reiniciar(None)

    def _reiniciar(self, inicio_ms):
        self.inicio_ms = inicio_ms
        self.valores = {v: [] for v in VARIABLES_AGREGADAS}
        self.n = 0
        self.anomalias = 0

    def agregar(self, datos, ts_ms, anomalia=None):
        if self.inicio_ms is None:
            self.inicio_ms = ts_ms
        if anomalia:
            self.anomalias += 1
            return
        self.n += 1
        for v in VARIABLES_AGREGADAS:
            x = datos.get(v)
            if x is not None:
                self.valores[v].append(float(x))

    def lista(self, ahora_ms):
        return self.inicio_ms is not None and ahora_ms - self.inicio_ms >= self.ventana_s * 1000

    def cerrar(self, ahora_ms):
        """Devuelve el resumen de la ventana y empieza otra. None si no hubo nada."""
        if self.inicio_ms is None:
            return None
        dur_s = max((ahora_ms - self.inicio_ms) / 1000.0, self.periodo_s)
        esperadas = max(int(round(dur_s / self.periodo_s)), 1)
        resumen = {}
        for v, xs in self.valores.items():
            if xs:
                resumen[v] = {"media": round(statistics.fmean(xs), 3),
                              "min": round(min(xs), 3), "max": round(max(xs), 3)}
        ag = {
            "ts_inicio_ms": self.inicio_ms,
            "ts_fin_ms": ahora_ms,
            "n": self.n,
            "n_esperadas": esperadas,
            "anomalias": self.anomalias,
            "completitud": round(min(100.0, 100.0 * (self.n + self.anomalias) / esperadas), 1),
            "resumen": resumen,
        }
        self._reiniciar(ahora_ms)
        return ag


def limpiar_contexto(ctx):
    """Ubidots no necesita (y puede rechazar) valores nulos en el context."""
    return {k: v for k, v in ctx.items() if v is not None}


def payload_ubidots(ag, variables, ts_ms):
    """Convierte un agregado al JSON que recibe Ubidots por MQTT.

    Formato: {"var": {"value": x, "timestamp": ms, "context": {...}}}. El
    timestamp es el del cierre de la ventana, asi los datos que se envian
    tarde (despues de una caida de Internet) quedan en su hora real.
    """
    p = {}
    for v in variables:
        r = ag["resumen"].get(v)
        if r is None:
            continue
        p[v] = {"value": r["media"], "timestamp": ts_ms,
                "context": {"min": r["min"], "max": r["max"]}}
    p["gw_calidad"] = {"value": ag["completitud"], "timestamp": ts_ms,
                       "context": {"anomalias": ag["anomalias"], "n": ag["n"],
                                   "esperadas": ag["n_esperadas"]}}
    return p
