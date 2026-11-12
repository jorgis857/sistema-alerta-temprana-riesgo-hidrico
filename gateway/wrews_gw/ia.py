"""Modulo de IA del gateway.

Dos partes, a proposito separadas:

1. PREDICCION (propia, deterministica, sin Internet): regresion lineal por
   minimos cuadrados del nivel en la ventana reciente (IA_VENTANA_MIN). Da la
   pendiente en pp/min, el R2 y el tiempo estimado para llegar al umbral
   critico del 15 %. Corre en la Pi aunque no haya Internet.

2. RECOMENDACION (modelo de lenguaje: Claude de Anthropic; Gemini u OpenAI
   como alternativas): con la prediccion, el
   estado y los ultimos eventos, el LLM redacta en lenguaje natural que deben
   hacer las autoridades (racionamiento, priorizacion, comunicacion). El LLM
   NO calcula nada: recibe los numeros ya calculados y solo los interpreta,
   asi una alucinacion no puede cambiar la cifra que se reporta. Si no hay
   clave, no hay Internet o la API falla, se usa una recomendacion por reglas
   para que el sistema nunca se quede sin respuesta.

Probar la clave desde la Pi:  python -m wrews_gw.ia --probar
"""
import json
import logging
import re
import sys
import time

import requests

from .procesamiento import limpiar_contexto

log = logging.getLogger("ia")

NOMBRE_EST = {0: "NORMAL", 1: "PRECAUCION", 2: "CRITICO", 3: "FALLO"}
PENDIENTE_ESTABLE_PPM = 0.5   # |pendiente| menor que esto se considera estable
MAX_TEXTO = 380               # bytes que caben comodos en el ESP32 (ia_texto[400])
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"


def regresion(serie):
    """Minimos cuadrados de [(t_s, nivel)]. Devuelve (pendiente pp/min, intercepto, r2)."""
    n = len(serie)
    t0 = serie[0][0]
    xs = [(t - t0) / 60.0 for t, _ in serie]
    ys = [y for _, y in serie]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0, my, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    m = sxy / sxx
    b = my - m * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (m * x + b)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return m, b, r2


def predecir(serie, umbral_critico=15.0, min_puntos=8, min_span_s=40):
    """Prediccion del tiempo hasta el umbral critico.

    serie: [(t_s, nivel %)] en orden. Devuelve un dict, o None si no hay
    suficientes datos (menos de min_puntos o menos de min_span_s de historia).
    """
    if len(serie) < min_puntos or serie[-1][0] - serie[0][0] < min_span_s:
        return None
    m, b, r2 = regresion(serie)
    nivel = serie[-1][1]
    if nivel <= umbral_critico:
        tendencia, minutos = "bajo el umbral critico", 0.0
    elif m <= -PENDIENTE_ESTABLE_PPM:
        tendencia, minutos = "descenso", (nivel - umbral_critico) / -m
    elif m >= PENDIENTE_ESTABLE_PPM:
        tendencia, minutos = "ascenso", None
    else:
        tendencia, minutos = "estable", None
    return {
        "nivel_actual": round(nivel, 1),
        "pendiente_ppm": round(m, 2),
        "r2": round(r2, 3),
        "n_puntos": len(serie),
        "ventana_s": round(serie[-1][0] - serie[0][0]),
        "min_a_critico": None if minutos is None else round(minutos, 1),
        "tendencia": tendencia,
    }


def armar_prompt(pred, estado, ultima, eventos, cfg):
    """Prompt en espanol. Se guarda completo en SQLite (declaracion de uso de IA)."""
    if pred and pred["min_a_critico"] is not None:
        tiempo = f"{pred['min_a_critico']:.1f} minutos de la maqueta"
    else:
        tiempo = "no aplica (el nivel no esta bajando)"
    ev = "; ".join(e["texto"] for e in eventos) or "ninguno"
    datos = [
        f"Estado del sistema: {NOMBRE_EST.get(estado, estado)}",
        f"Nivel actual: {pred['nivel_actual'] if pred else ultima.get('nivel')} %",
        f"Tendencia (regresion lineal, {pred['ventana_s'] if pred else 0} s): "
        f"{pred['tendencia'] if pred else 'sin datos suficientes'}, "
        f"pendiente {pred['pendiente_ppm'] if pred else 'n/d'} puntos porcentuales/min, "
        f"R2 {pred['r2'] if pred else 'n/d'}",
        f"Tiempo estimado hasta el umbral critico de {cfg.ia_umbral_critico:.0f} %: {tiempo}",
        f"Indice de riesgo hidrico (0-100): {ultima.get('riesgo')}",
        f"Indice evaporativo (% de la demanda maxima): {ultima.get('idx_evap')}",
        f"Temperatura {ultima.get('temp')} C, humedad {ultima.get('hum')} %",
        f"Ultimos eventos: {ev}",
    ]
    return (
        "Eres asesor de gestion del riesgo hidrico de una alcaldia en la Sabana de Bogota "
        "(Colombia) durante un periodo seco tipo El Nino. Un sistema de alerta temprana "
        "midio lo siguiente en el reservorio que abastece al municipio:\n- "
        + "\n- ".join(datos)
        + f"\n\nUmbrales: precaucion con nivel <= {cfg.ia_umbral_precaucion:.0f} %, critico "
        f"con nivel <= {cfg.ia_umbral_critico:.0f} % (fases de los Planes Especiales de "
        "Sequia). Es un banco de pruebas: los minutos de la maqueta representan horas o "
        "dias de un embalse real.\n\n"
        "Escribe UNA recomendacion para las autoridades, en espanol, de maximo 55 palabras, "
        "en texto plano sin vinetas ni markdown: que hacer ahora (por ejemplo racionamiento "
        "por sectores, priorizar hospitales y colegios, comunicar a la poblacion, revisar "
        "fugas o fuentes alternas) y cuando revisar de nuevo. Usa solo los datos dados, no "
        "inventes cifras, y si R2 es menor que 0.5 di que la tendencia es incierta. Si el "
        "estado es FALLO, la prioridad es recuperar la medicion."
    )


def recomendacion_reglas(pred, estado, cfg):
    """Respaldo sin LLM: tabla de decisiones a partir del estado y la prediccion."""
    t = pred["min_a_critico"] if pred else None
    if estado == 3:
        return ("Falla del equipo de medicion o del enlace: verificar el sensor y la "
                "conexion en sitio y mientras tanto operar con lecturas manuales del reservorio.")
    if estado == 2 or (pred and pred["nivel_actual"] <= cfg.ia_umbral_critico):
        return ("Nivel critico: activar racionamiento por sectores, priorizar hospitales, "
                "colegios y acueductos veredales, y comunicar el plan a la poblacion ya.")
    if t is not None and t < 30:
        return (f"Descenso sostenido: a este ritmo se llega al {cfg.ia_umbral_critico:.0f} % "
                f"en unos {t:.0f} min de la maqueta. Preparar el plan de racionamiento y "
                "avisar a los usuarios para reducir el consumo.")
    if estado == 1:
        return ("Precaucion: pedir a la poblacion ahorro voluntario, revisar fugas en la red "
                "y vigilar la tendencia en la proxima hora.")
    return "Operacion normal: mantener el monitoreo; no se requieren medidas."


def _recortar(texto):
    texto = " ".join(texto.replace("*", "").replace("#", "").split())
    b = texto.encode("utf-8")
    if len(b) <= MAX_TEXTO:
        return texto
    return b[:MAX_TEXTO - 3].decode("utf-8", "ignore").rstrip() + "..."


# ---- Proveedores de LLM -----------------------------------------------------
# Claude (Anthropic) es el principal; Gemini y OpenAI quedan como alternativas
# por si se cambia IA_PROVEEDOR. Cualquier falla cae al respaldo por reglas.

# Modelos de Claude que aceptan "fallbacks": si el modelo rechaza la consulta
# por sus filtros de seguridad, la API la reintenta sola con otro modelo.
_CLAUDE_CON_FALLBACK = ("claude-opus-5-5", "claude-opus-5", "claude-fable-5-1",
                        "claude-sonnet-5-5")


def _claude(prompt, cfg):
    """Devuelve (texto, modelo). Usa el SDK oficial (pip install anthropic)."""
    import anthropic
    # max_retries=1: si falla dos veces se usa el respaldo; no vale la pena
    # esperar mas, la recomendacion se vuelve a pedir en IA_CADA_S segundos.
    cliente = anthropic.Anthropic(api_key=cfg.claude_api_key, timeout=cfg.ia_timeout_s,
                                  max_retries=1)
    args = dict(model=cfg.claude_modelo, max_tokens=16000,
                # Esfuerzo bajo: es un texto corto a partir de numeros ya
                # calculados; responde rapido y gasta menos creditos.
                output_config={"effort": cfg.claude_esfuerzo},
                messages=[{"role": "user", "content": prompt}])
    if cfg.claude_modelo in _CLAUDE_CON_FALLBACK:
        r = cliente.beta.messages.create(betas=["server-side-fallback-2026-07-01"],
                                         fallbacks="default", **args)
    else:
        r = cliente.messages.create(**args)
    if r.stop_reason == "refusal":
        raise RuntimeError("Claude rechazo la consulta (stop_reason refusal)")
    texto = "".join(b.text for b in r.content if b.type == "text")
    # Consumo real de la llamada (va al log): sirve para estimar el costo en la wiki
    log.info("Claude: %d tokens de entrada, %d de salida",
             r.usage.input_tokens, r.usage.output_tokens)
    return texto, r.model


def texto_gemini(respuesta):
    """Texto de una respuesta de generateContent (sin las partes de 'pensamiento')."""
    cands = respuesta.get("candidates") or []
    if not cands:
        motivo = (respuesta.get("promptFeedback") or {}).get("blockReason", "sin candidatos")
        raise RuntimeError(f"Gemini no respondio texto ({motivo})")
    partes = (cands[0].get("content") or {}).get("parts") or []
    texto = "".join(p.get("text", "") for p in partes if not p.get("thought"))
    if not texto.strip():
        raise RuntimeError(f"Gemini sin texto (finishReason {cands[0].get('finishReason')})")
    return texto


def _gemini(prompt, cfg):
    # Sin maxOutputTokens: en los modelos actuales ese tope incluye los tokens
    # de "pensamiento" y, si es corto, la respuesta llega vacia.
    r = requests.post(f"{GEMINI_URL}/models/{cfg.gemini_modelo}:generateContent",
                      headers={"x-goog-api-key": cfg.gemini_api_key},
                      json={"contents": [{"parts": [{"text": prompt}]}]},
                      timeout=cfg.ia_timeout_s)
    r.raise_for_status()
    return texto_gemini(r.json()), cfg.gemini_modelo


def _openai(prompt, cfg):
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {cfg.openai_api_key}"},
                      json={"model": cfg.openai_modelo,
                            "messages": [{"role": "user", "content": prompt}]},
                      timeout=cfg.ia_timeout_s)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], cfg.openai_modelo


def _detalle_error(e):
    """Mensaje corto y util para el log y la tabla ia (sin claves)."""
    nombre = type(e).__name__
    pistas = {"AuthenticationError": "clave invalida (revise ANTHROPIC_API_KEY)",
              "PermissionDeniedError": "la clave no tiene permiso para ese modelo",
              "NotFoundError": "modelo inexistente (revise CLAUDE_MODELO)",
              "RateLimitError": "limite de uso alcanzado; se reintenta en el proximo ciclo",
              "APIConnectionError": "sin Internet o sin DNS",
              "APITimeoutError": "la API no respondio a tiempo",
              "ConnectionError": "sin Internet o sin DNS"}
    txt = f"{nombre}: {pistas.get(nombre, '')}"
    msg = getattr(e, "message", None) or str(e)
    resp = getattr(e, "response", None)
    if resp is not None and not getattr(e, "message", None):
        try:                                    # requests: el error viene en el JSON
            msg = resp.json().get("error", {}).get("message", msg)
        except (ValueError, AttributeError):
            pass
    txt += f" | {msg}"
    return re.sub(r"(key=|sk-ant-)[^&\s]+", r"\1***", txt)[:300]


def recomendar(pred, estado, ultima, eventos, cfg, usar_llm=True):
    """Devuelve el registro completo (se guarda en SQLite y se publica).

    usar_llm=False: se responde con la tabla de reglas sin llamar a la API
    (p. ej. con el ESP32 desconectado no hay datos nuevos que interpretar).
    """
    prompt = armar_prompt(pred, estado, ultima or {}, eventos, cfg)
    reg = dict(pred or {})
    reg.update({"estado": estado, "prompt": prompt, "error": None})
    t0 = time.time()
    proveedor = cfg.ia_proveedor
    if not usar_llm:
        reg.update({"proveedor": "reglas", "modelo": "tabla de decisiones",
                    "texto": _recortar(recomendacion_reglas(pred, estado, cfg)),
                    "latencia_ms": 0})
        return reg
    try:
        if proveedor == "claude" and cfg.claude_api_key:
            texto, modelo = _claude(prompt, cfg)
        elif proveedor == "gemini" and cfg.gemini_api_key:
            texto, modelo = _gemini(prompt, cfg)
        elif proveedor == "openai" and cfg.openai_api_key:
            texto, modelo = _openai(prompt, cfg)
        else:
            raise RuntimeError(f"proveedor '{proveedor}' sin clave configurada")
        if not texto.strip():
            raise RuntimeError("respuesta vacia")
        reg.update({"proveedor": proveedor, "modelo": modelo, "texto": _recortar(texto)})
    except Exception as e:  # sin Internet, sin cuota, clave mala...: respaldo por reglas
        reg.update({"proveedor": "reglas", "modelo": "tabla de decisiones",
                    "texto": _recortar(recomendacion_reglas(pred, estado, cfg)),
                    "error": _detalle_error(e)})
    reg["latencia_ms"] = int((time.time() - t0) * 1000)
    return reg


def payload_ubidots(reg, ts_ms):
    """Variable ia_min_critico. -1 significa 'el nivel no esta bajando'."""
    v = reg.get("min_a_critico")
    return {"ia_min_critico": {
        "value": -1 if v is None else v,
        "timestamp": ts_ms,
        "context": limpiar_contexto({
            "tendencia": reg.get("tendencia", "sin datos"),
            "pendiente_ppm": reg.get("pendiente_ppm"),
            "r2": reg.get("r2"),
            "fuente": reg.get("proveedor"),
            "recomendacion": (reg.get("texto") or "")[:250]})}}


def mensaje_local(reg):
    """JSON completo para wrews/<id>/ia (lo pueden leer otros clientes locales)."""
    claves = ("nivel_actual", "pendiente_ppm", "r2", "min_a_critico", "tendencia",
              "proveedor", "modelo", "texto", "estado")
    return json.dumps({k: reg.get(k) for k in claves}, ensure_ascii=False)


def _probar():
    """Una llamada real con la configuracion del entorno, para revisar la clave."""
    from .config import Config
    cfg = Config.desde_entorno()
    serie = [(t * 5.0, 60 - 0.4 * t) for t in range(24)]
    pred = predecir(serie, cfg.ia_umbral_critico)
    print("Prediccion de prueba:", pred)
    reg = recomendar(pred, 1, {"nivel": pred["nivel_actual"], "riesgo": 40}, [], cfg)
    print(f"Proveedor: {reg['proveedor']} ({reg['modelo']}), {reg['latencia_ms']} ms")
    print("Texto:", reg["texto"])
    if reg["error"]:
        print("ERROR (se uso el respaldo por reglas):", reg["error"])
        return 1
    return 0


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(_probar())
    print(__doc__)
