"""Grafica de la ultima hora para el bot de Telegram (comando /grafica).

Dibuja con matplotlib (sin pantalla: backend Agg) el nivel y el riesgo con
los umbrales, y devuelve el PNG en memoria junto con un pie de foto.
"""
import io
import time
from datetime import datetime

NOMBRE = {0: "NORMAL", 1: "PRECAUCIÓN", 2: "CRÍTICO", 3: "FALLO"}
COLOR = {0: "#2e7d32", 1: "#f9a825", 2: "#c62828", 3: "#616161"}


def grafica_png(filas, estado, u_prec=50.0, u_crit=15.0, minutos=60):
    """filas: [{"ts_ms", "nivel", "riesgo", "estado"}] en orden. Devuelve (png, pie)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    t = [datetime.fromtimestamp(f["ts_ms"] / 1000) for f in filas]
    nivel = [f["nivel"] for f in filas]
    riesgo = [f["riesgo"] for f in filas]

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=110)
    color = COLOR.get(estado, "#616161")
    ax.set_title(f"WREWS · estado {NOMBRE.get(estado, estado)} · última {minutos} min",
                 color=color, fontsize=13, fontweight="bold", loc="left")
    ax.axhspan(0, u_crit, color="#c62828", alpha=0.08)
    ax.axhspan(u_crit, u_prec, color="#f9a825", alpha=0.08)
    ax.axhline(u_prec, color="#f9a825", ls="--", lw=1)
    ax.axhline(u_crit, color="#c62828", ls="--", lw=1)
    if filas:
        ax.plot(t, nivel, color="#1565c0", lw=2, label="Nivel (%)")
        ax.plot(t, riesgo, color="#ef6c00", lw=1.6, label="Riesgo (0-100)")
        ax.legend(loc="center right", fontsize=9, framealpha=0.9)
    else:
        ax.text(0.5, 0.5, "Sin datos en este periodo", transform=ax.transAxes,
                ha="center", va="center", color="#616161")
    ax.set_ylim(0, 105)
    ax.set_ylabel("%")
    ax.grid(alpha=0.25)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)

    ultimo = next((f for f in reversed(filas) if f["nivel"] is not None), None)
    pie = f"Estado {NOMBRE.get(estado, estado)}"
    if ultimo:
        pie += f" · nivel {ultimo['nivel']:.0f} % · riesgo {ultimo['riesgo']:.0f}/100"
    pie += f" · {time.strftime('%H:%M:%S')}"
    return buf.getvalue(), pie


def _tarjeta(ax, titulo, valor, unidad="", color="#1b2733", nota=""):
    ax.set_axis_off()
    ax.add_patch(matplotlib_patches().FancyBboxPatch(
        (0.02, 0.04), 0.96, 0.92, boxstyle="round,pad=0.01,rounding_size=0.06",
        transform=ax.transAxes, facecolor="white", edgecolor="#d5dde5", lw=1))
    ax.add_patch(matplotlib_patches().Rectangle(
        (0.02, 0.90), 0.96, 0.06, transform=ax.transAxes, facecolor=color, lw=0))
    ax.text(0.08, 0.72, titulo.upper(), transform=ax.transAxes, fontsize=8, color="#5c6b7a")
    ax.text(0.08, 0.30, valor, transform=ax.transAxes, fontsize=19, fontweight="bold",
            color=color)
    if unidad:
        ax.text(0.92, 0.32, unidad, transform=ax.transAxes, fontsize=9, color="#5c6b7a",
                ha="right")
    if nota:
        ax.text(0.08, 0.10, nota, transform=ax.transAxes, fontsize=7.5, color="#5c6b7a")


def matplotlib_patches():
    import matplotlib.patches as patches
    return patches


def _fmt(v, dec=1):
    return "—" if v is None else f"{v:.{dec}f}"


def dashboard_png(filas, ultima, estado, ia_reg=None, completitud=None,
                  u_prec=50.0, u_crit=15.0, minutos=60):
    """Tablero completo en una imagen (comando /dashboard). Devuelve (png, pie).

    filas: [{"ts_ms","nivel","riesgo","temp","hum"}] de la ultima hora (validas).
    ultima: ultima medicion valida (dict) o None. ia_reg: ultima fila de la tabla ia.
    """
    import textwrap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.ticker  # noqa: F401  (FormatStrFormatter)

    u = ultima or {}
    color_est = COLOR.get(estado, "#616161")
    fig = plt.figure(figsize=(9, 8.8), dpi=100, facecolor="#f4f6f8")
    g = fig.add_gridspec(5, 4, height_ratios=[0.3, 1, 1, 2.1, 1.1], hspace=0.4,
                         wspace=0.25, left=0.06, right=0.94, top=0.97, bottom=0.03)

    cab = fig.add_subplot(g[0, :])
    cab.set_axis_off()
    cab.text(0, 0.5, "WREWS · Tablero de control", fontsize=15, fontweight="bold",
             color="#1b2733", va="center")
    cab.text(1, 0.5, time.strftime("%Y-%m-%d %H:%M:%S"), fontsize=9, color="#5c6b7a",
             va="center", ha="right")

    nivel = u.get("nivel")
    sev_nivel = 2 if nivel is not None and nivel <= u_crit else 1 if (
        nivel is not None and nivel <= u_prec) else 0
    min_crit = (ia_reg or {}).get("min_a_critico")
    tarjetas = [
        ("Estado", NOMBRE.get(estado, str(estado)), "", color_est,
         "buzzer silenciado" if u.get("silenciado") else ""),
        ("Nivel", _fmt(nivel), "%", COLOR[sev_nivel], f"umbrales {u_prec:.0f} / {u_crit:.0f} %"),
        ("Riesgo hídrico", _fmt(u.get("riesgo")), "/100", "#1b2733", "pesos AHP 54/30/16"),
        ("Minutos hasta 15 %", "—" if min_crit is None else f"{min_crit:.0f}", "min",
         "#1b2733", f"IA: {(ia_reg or {}).get('tendencia') or 'sin datos'}"),
        ("Temperatura", _fmt(u.get("temp")), "°C", "#1b2733", ""),
        ("Humedad", _fmt(u.get("hum")), "%", "#1b2733", ""),
        ("Presión", _fmt(u.get("pres")), "hPa", "#1b2733", ""),
        ("Índice evaporativo", _fmt(u.get("idx_evap")), "%", "#1b2733",
         "" if completitud is None else f"enlace: {completitud:.0f} % de muestras"),
    ]
    for k, (tit, val, uni, col, nota) in enumerate(tarjetas):
        _tarjeta(fig.add_subplot(g[1 + k // 4, k % 4]), tit, val, uni, col, nota)

    t = [datetime.fromtimestamp(f["ts_ms"] / 1000) for f in filas]
    ax1 = fig.add_subplot(g[3, :2])
    ax2 = fig.add_subplot(g[3, 2:])
    ax1.axhspan(0, u_crit, color="#c62828", alpha=0.08)
    ax1.axhspan(u_crit, u_prec, color="#f9a825", alpha=0.08)
    ax1.plot(t, [f["nivel"] for f in filas], color="#1565c0", lw=2, label="Nivel %")
    ax1.plot(t, [f["riesgo"] for f in filas], color="#ef6c00", lw=1.5, label="Riesgo")
    ax1.set_ylim(0, 105)
    ax1.set_title(f"Nivel y riesgo · {minutos} min", fontsize=10, loc="left")
    ax2.plot(t, [f["temp"] for f in filas], color="#c62828", lw=1.6, label="Temp °C")
    ax2b = ax2.twinx()
    ax2b.plot(t, [f["hum"] for f in filas], color="#00838f", lw=1.6, label="Humedad %")
    ax2.set_title("Temperatura y humedad", fontsize=10, loc="left")
    ax2.legend([ax2.lines[0], ax2b.lines[0]], ["Temp °C (izq.)", "Humedad % (der.)"],
               fontsize=7.5, loc="upper left", framealpha=0.9)
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f"))
    ax2b.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f"))
    for ax in (ax1, ax2):
        ax.set_facecolor("white")
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2b.tick_params(labelsize=8)
    ax1.legend(fontsize=7.5, loc="center right", framealpha=0.9)
    if not filas:
        for ax in (ax1, ax2):
            ax.text(0.5, 0.5, "Sin datos", transform=ax.transAxes, ha="center",
                    color="#616161")

    pie_ax = fig.add_subplot(g[4, :])
    pie_ax.set_axis_off()
    if ia_reg and ia_reg.get("texto"):
        fuente = "Claude" if ia_reg.get("proveedor") == "claude" else "tabla de reglas"
        texto = "\n".join(textwrap.wrap(ia_reg["texto"], 110)[:5])
        pie_ax.text(0, 0.95, f"Última recomendación ({fuente})", fontsize=9.5,
                    fontweight="bold", color="#1b2733", va="top")
        pie_ax.text(0, 0.72, texto, fontsize=8.5, color="#1b2733", va="top")
    pie_ax.text(0, 0.0, "Para el análisis de la IA con los datos actuales: /recomendacion",
                fontsize=8, color="#5c6b7a")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    pie = f"WREWS · {NOMBRE.get(estado, estado)} · nivel {_fmt(nivel, 0)} %"
    return buf.getvalue(), pie
