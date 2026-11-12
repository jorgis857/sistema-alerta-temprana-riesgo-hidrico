"""Pruebas unitarias del gateway (sin broker ni Internet):  python -m pytest tests"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrews_gw import ia  # noqa: E402
from wrews_gw.almacen import Almacen  # noqa: E402
from wrews_gw.config import Config  # noqa: E402
from wrews_gw.nube import FiltroOrdenes, leer_switch  # noqa: E402
from wrews_gw.procesamiento import Agregador, Validador, payload_ubidots  # noqa: E402


def test_validador_acepta_rampa_y_rechaza_pico():
    v = Validador()
    for i in range(20):                       # descenso sostenido de 4 pp por muestra
        assert v.revisar({"nivel": 95 - 4 * i}) is None
    v = Validador()
    for _ in range(10):
        assert v.revisar({"nivel": 70.0}) is None
    assert v.revisar({"nivel": 20.0}) is not None   # pico aislado
    assert v.revisar({"nivel": 70.2}) is None       # vuelve: se acepta


def test_validador_acepta_escalon_real_tras_tres_muestras():
    v = Validador()
    for _ in range(10):
        v.revisar({"nivel": 80.0})
    assert v.revisar({"nivel": 30.0}) is not None
    assert v.revisar({"nivel": 30.0}) is not None
    assert v.revisar({"nivel": 30.0}) is None        # recarga o reposicionamiento


def test_validador_rango_fisico_y_sin_eco():
    # Una temperatura imposible se descarta sola: el nivel sigue valiendo
    limpios, fuera = Validador.limpiar({"nivel": 50, "temp": 179.6, "pres": -153.0})
    assert fuera == {"temp": 179.6, "pres": -153.0}
    assert limpios["temp"] is None and limpios["nivel"] == 50
    assert Validador().revisar(limpios) is None
    assert "fuera de rango" in Validador().revisar({"nivel": 140})
    assert Validador().revisar({"nivel": None, "temp": 18}) is None


def test_agregador_completitud_y_anomalias():
    a = Agregador(ventana_s=60, periodo_s=5)
    for k in range(10):
        a.agregar({"nivel": 50 + k, "temp": 18}, 1000 + k * 5000)
    a.agregar({"nivel": 999}, 51000, anomalia="pico")
    assert a.lista(61000)
    ag = a.cerrar(61000)
    assert ag["n"] == 10 and ag["anomalias"] == 1 and ag["n_esperadas"] == 12
    assert ag["resumen"]["nivel"]["media"] == 54.5
    p = payload_ubidots(ag, ["nivel", "riesgo"], 61000)
    assert p["nivel"]["value"] == 54.5 and "riesgo" not in p
    assert p["gw_calidad"]["value"] == round(100 * 11 / 12, 1)


def test_prediccion_descenso():
    serie = [(t * 5.0, 80 - 0.5 * t) for t in range(24)]   # 6 pp/min durante 2 min
    p = ia.predecir(serie, 15.0)
    assert p["tendencia"] == "descenso"
    assert abs(p["pendiente_ppm"] + 6.0) < 0.01 and p["r2"] > 0.99
    assert abs(p["min_a_critico"] - (serie[-1][1] - 15) / 6.0) < 0.1


def test_prediccion_estable_y_pocos_datos():
    assert ia.predecir([(0, 50), (5, 50)], 15) is None
    p = ia.predecir([(t * 5.0, 60.0) for t in range(20)], 15)
    assert p["tendencia"] == "estable" and p["min_a_critico"] is None


def test_recomendacion_sin_clave_usa_reglas():
    cfg = Config(ia_proveedor="claude", claude_api_key="")
    pred = ia.predecir([(t * 5.0, 30 - 0.5 * t) for t in range(20)], 15)
    r = ia.recomendar(pred, 1, {"nivel": 20.5, "riesgo": 50}, [], cfg)
    assert r["proveedor"] == "reglas" and r["texto"] and r["error"]
    assert len(r["texto"].encode()) <= ia.MAX_TEXTO
    assert "Nivel actual" in r["prompt"]


def test_recomendacion_con_claude_simulado(monkeypatch):
    cfg = Config(ia_proveedor="claude", claude_api_key="sk-ant-prueba")
    monkeypatch.setattr(ia, "_claude", lambda p, c: ("**Racionar** ya. " * 40, "claude-opus-5-5"))
    r = ia.recomendar(None, 2, {"nivel": 12}, [], cfg)
    assert r["proveedor"] == "claude" and r["error"] is None
    assert "*" not in r["texto"] and len(r["texto"].encode()) <= ia.MAX_TEXTO


def test_error_de_claude_cae_a_reglas_sin_filtrar_la_clave(monkeypatch):
    cfg = Config(ia_proveedor="claude", claude_api_key="sk-ant-api03-secreta")

    class AuthenticationError(Exception):
        message = "invalid x-api-key sk-ant-api03-secreta"

    def falla(p, c):
        raise AuthenticationError()
    monkeypatch.setattr(ia, "_claude", falla)
    r = ia.recomendar(None, 3, {}, [], cfg)
    assert r["proveedor"] == "reglas" and "clave invalida" in r["error"]
    assert "secreta" not in r["error"]
    assert "Falla del equipo" in r["texto"]


def test_payload_ia_sin_nulos():
    p = ia.payload_ubidots({"texto": "x", "proveedor": "reglas"}, 1000)["ia_min_critico"]
    assert p["value"] == -1 and None not in p["context"].values()


def test_texto_gemini_sin_partes_es_error():
    with pytest.raises(RuntimeError):
        ia.texto_gemini({"candidates": [{"finishReason": "MAX_TOKENS", "content": {}}]})
    ok = {"candidates": [{"content": {"parts": [{"text": "pienso", "thought": True},
                                                 {"text": "Racionar"}]}}]}
    assert ia.texto_gemini(ok) == "Racionar"


def test_switch_de_ubidots():
    assert leer_switch(b'{"value": 1.0, "timestamp": 1700000000000}') == (1.0, 1700000000000)
    assert leer_switch(b"1.0") == (1.0, None)
    assert leer_switch(b"hola") is None
    f = FiltroOrdenes()
    ahora = 1_700_000_100.0
    assert f.es_orden(1, 1_700_000_090_000, ahora)            # orden de hace 10 s
    assert not f.es_orden(1, 1_700_000_090_000, ahora + 1)    # la misma, repetida
    assert not f.es_orden(1, 1_699_999_000_000, ahora)        # vieja (guardada en Ubidots)
    assert not f.es_orden(0, 1_700_000_095_000, ahora)        # el switch volviendo a 0
    f.suscrito()
    assert not f.es_orden(1, None)                             # /lv justo al suscribirse


def test_almacen_cola_y_eventos_duplicados(tmp_path):
    db = Almacen(str(tmp_path / "t.db"))
    assert db.guardar_evento("d", "esp32", "x", 1, boot=7, ev_id=3)
    assert db.guardar_evento("d", "esp32", "x", 1, boot=7, ev_id=3) is None   # reenvio
    db.encolar_nube({"nivel": {"value": 1}})
    db.encolar_nube({"nivel": {"value": 2}})
    pend = db.pendientes_nube()
    assert [p["payload"]["nivel"]["value"] for p in pend] == [1, 2]
    db.marcar_enviado(pend[0]["id"])
    assert db.contar_pendientes() == 1
    i = db.guardar_medicion("d", {"nivel": 40.0, "estado": 1})
    db.marcar_anomalia(i, "pico")
    assert db.ultima_medicion("d") is None


def test_config_desde_entorno(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "CAMBIAR_clave")      # marcador sin llenar
    monkeypatch.setenv("UBIDOTS_TLS", "0")
    monkeypatch.setenv("UBIDOTS_VARIABLES", "nivel, riesgo")
    c = Config.desde_entorno()
    assert c.claude_api_key == "" and c.ia_proveedor == "claude"
    assert c.ubidots_port == 1883 and c.ubidots_variables == ["nivel", "riesgo"]


def test_telegram_avisa_solo_cambios(tmp_path):
    from wrews_gw.gateway import Gateway
    gw = Gateway(Config(db_path=str(tmp_path / "g.db")))
    enviados = []
    gw.telegram.enviar = enviados.append
    gw.ultimo_dato = {"nivel": 12.3, "riesgo": 71}
    for e in (0, 0, 2, 2, 3, 0):
        gw._encolar_estado(e, 0, 1000, "esp32")
    assert len(enviados) == 3                      # CRITICO, FALLO, NORMAL
    assert "CRÍTICO" in enviados[0] and "nivel 12 %" in enviados[0]
    gw.db.cerrar()


def test_telegram_solo_autorizados(tmp_path):
    from wrews_gw.telegram import Telegram
    db = Almacen(str(tmp_path / "t.db"))
    t = Telegram("", db=db, admin="1")               # sin token: no arranca hilos
    msgs = []
    botones, api = [], []

    def mandar(chat, txt, botones_msg=None):
        msgs.append((chat, txt))
        if botones_msg:
            botones.append(botones_msg)
        return True
    t._mandar_a = lambda chat, txt, botones=None: mandar(chat, txt, botones)
    t._api = lambda metodo, **k: api.append((metodo, k))
    t._atender({"text": "/start", "chat": {"id": 1, "first_name": "Admin"}})
    assert db.suscriptores() == [1]                  # el administrador entra directo
    t._atender({"text": "/start@WREWS_Alertasbot", "chat": {"id": 5, "first_name": "Ana"}})
    assert db.suscriptores() == [1]                  # Ana queda pendiente
    assert botones[-1] == [[("✅ Aprobar", "aprobar:5"), ("❌ Rechazar", "rechazar:5")]]
    t._atender({"text": "/estado", "chat": {"id": 5}})
    assert "autorizado" in msgs[-1][1]
    t._atender({"text": "/aprobar_1", "chat": {"id": 5}})   # Ana no es administradora
    assert "administrador" in msgs[-1][1]
    # Boton tocado por alguien que no es el administrador: no pasa nada
    t._atender_boton({"id": "q0", "from": {"id": 5}, "data": "aprobar:5"})
    assert db.suscriptores() == [1]
    # El administrador toca "Aprobar": se aprueba y el mensaje se edita
    t._atender_boton({"id": "q1", "from": {"id": 1}, "data": "aprobar:5",
                      "message": {"chat": {"id": 1}, "message_id": 9, "text": "Solicitud"}})
    assert sorted(db.suscriptores()) == [1, 5]
    assert api[-1][0] == "editMessageText" and "aprobado" in api[-1][1]["text"]
    t._atender({"text": "/usuarios", "chat": {"id": 1}})
    assert "/quitar_5" in msgs[-1][1]
    assert "/quitar_1" not in msgs[-1][1] and "👑" in msgs[-1][1]   # el admin no se quita
    t._atender({"text": "/stop", "chat": {"id": 1}})
    assert 1 in db.suscriptores()
    t._atender({"text": "/quitar_5", "chat": {"id": 1}})    # comando tocable, sin espacio
    assert db.suscriptores() == [1]


def test_telegram_clave_y_bloqueo(tmp_path):
    from wrews_gw.telegram import MAX_INTENTOS_CLAVE, Telegram
    db = Almacen(str(tmp_path / "t.db"))
    t = Telegram("", db=db, clave="sabana")
    msgs = []
    t._mandar_a = lambda chat, txt, botones=None: msgs.append((chat, txt)) or True
    for _ in range(MAX_INTENTOS_CLAVE):
        t._atender({"text": "/start mala", "chat": {"id": 7}})
    n = len(msgs)
    t._atender({"text": "/start sabana", "chat": {"id": 7}})   # bloqueado 10 min
    assert len(msgs) == n and db.suscriptores() == []
    t._atender({"text": "/start sabana", "chat": {"id": 8}})
    assert db.suscriptores() == [8]
    # La clave tambien vale pegada o con guion bajo, y respeta mayusculas
    t.clave = "Sabana-26"
    t._atender({"text": "/startSabana-26", "chat": {"id": 9}})
    t._atender({"text": "/start_Sabana-26", "chat": {"id": 10}})
    t._atender({"text": "/start sabana-26", "chat": {"id": 11}})    # minusculas: no
    assert sorted(db.suscriptores()) == [8, 9, 10]


def test_grafica_y_comandos_restringidos(tmp_path):
    from wrews_gw.grafica import grafica_png
    from wrews_gw.telegram import Telegram
    filas = [{"ts_ms": 1_700_000_000_000 + k * 5000, "nivel": 80 - k, "riesgo": 20 + k,
              "estado": 0} for k in range(40)]
    png, pie = grafica_png(filas, 1)
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and "PRECAUCIÓN" in pie and "nivel 41 %" in pie
    assert grafica_png([], 3)[0][:4] == b"\x89PNG"          # sin datos tambien dibuja
    db = Almacen(str(tmp_path / "t.db"))
    t = Telegram("", db=db, admin="1", grafica=lambda: (png, pie))
    msgs, fotos = [], []
    t._mandar_a = lambda chat, txt, botones=None: msgs.append((chat, txt)) or True
    t._mandar_grafica = lambda chat: fotos.append(chat)
    t._atender({"text": "/grafica", "chat": {"id": 5}})     # no autorizado
    assert fotos == [] and "autorizado" in msgs[-1][1]
    t._atender({"text": "/grafica", "chat": {"id": 1}})     # administrador
    assert fotos == [1]
    t._atender({"text": "/tablero", "chat": {"id": 1}})
    assert "UBIDOTS_TABLERO_URL" in msgs[-1][1]


def test_fallo_de_enlace_no_llama_al_llm(monkeypatch):
    cfg = Config(ia_proveedor="claude", claude_api_key="sk-ant-prueba")
    monkeypatch.setattr(ia, "_claude", lambda p, c: (_ for _ in ()).throw(AssertionError))
    r = ia.recomendar(None, 3, {}, [], cfg, usar_llm=False)
    assert r["proveedor"] == "reglas" and r["error"] is None and "Falla" in r["texto"]


def test_llm_solo_a_pedido(tmp_path, monkeypatch):
    from wrews_gw.gateway import Gateway
    gw = Gateway(Config(db_path=str(tmp_path / "g.db"), claude_api_key="sk-ant-x"))
    gw.local.publish = lambda *a, **k: None
    llamadas = []
    monkeypatch.setattr(ia, "_claude", lambda p, c: llamadas.append(1) or ("Racionar.", "m"))
    gw.db.guardar_medicion(gw.dev, {"nivel": 40.0, "estado": 1, "riesgo": 50})
    reg = gw.correr_ia(avisar=False, usar_llm=gw.cfg.ia_llm_auto)   # lo automatico
    assert reg["proveedor"] == "reglas" and llamadas == []
    assert "Claude" in gw.recomendacion_a_pedido() and len(llamadas) == 1
    assert "hace" in gw.recomendacion_a_pedido() and len(llamadas) == 1   # no repite
    gw.db.cerrar()


def test_dashboard_imagen():
    from wrews_gw.grafica import dashboard_png
    filas = [{"ts_ms": 1_700_000_000_000 + k * 5000, "nivel": 60 - k, "riesgo": 30 + k,
              "temp": 20 + k / 10, "hum": 50.0} for k in range(30)]
    png, pie = dashboard_png(filas, {"nivel": 31.0, "riesgo": 59.0, "temp": 22.9,
                                     "hum": 50.0, "pres": 749.0, "idx_evap": 30.0},
                             1, {"proveedor": "claude", "min_a_critico": 3.2,
                                 "tendencia": "descenso", "texto": "Racionar ya. " * 30}, 92.0)
    assert png[:4] == b"\x89PNG" and "PRECAUCIÓN" in pie and "31" in pie
    assert dashboard_png([], None, 3)[0][:4] == b"\x89PNG"   # sin datos no falla


def test_dashboard_en_vivo(tmp_path):
    from wrews_gw.telegram import Telegram

    class Resp:
        def __init__(self, codigo, texto=""):
            self.status_code, self.text = codigo, texto

    db = Almacen(str(tmp_path / "t.db"))
    t = Telegram("", db=db, admin="1", dashboard=lambda: (b"png", "pie"))
    api, editados = [], []
    t._mandar_a = lambda chat, txt, botones=None: True
    t._api = lambda metodo, **k: api.append(metodo)
    t._mandar_grafica = lambda chat, fuente=None: 77          # message_id de la foto
    t._atender({"text": "/start", "chat": {"id": 1}})
    t._atender({"text": "/envivo", "chat": {"id": 1}})
    assert db.vivos() == [(1, 77)] and "pinChatMessage" in api
    t._editar_foto = lambda chat, msg, png, pie: editados.append((chat, msg)) or Resp(200)
    t._actualizar_vivos(db.vivos(), b"png", "pie")
    assert editados == [(1, 77)]
    t._editar_foto = lambda chat, msg, png, pie: Resp(400, "message to edit not found")
    t._actualizar_vivos(db.vivos(), b"png", "pie")
    assert db.vivos() == []                                   # lo borro: se deja de editar
    t._atender({"text": "/envivo", "chat": {"id": 5}})        # no autorizado
    assert db.vivos() == []
