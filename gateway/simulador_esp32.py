#!/usr/bin/env python3
"""ESP32 simulado: publica lo mismo que el firmware v8, con los mismos topicos.

Sirve para probar el gateway, SQLite, Ubidots y la IA sin la maqueta, o para
descartar si una falla es del ESP32 o del resto. El nivel baja de 90 % a 5 %
y vuelve a subir, pasando por PRECAUCION y CRITICO. Responde al comando
silenciar igual que el equipo real.

    python3 simulador_esp32.py --host localhost --user esp32 --password CLAVE
    python3 simulador_esp32.py ... --descenso 3 --pico   # mas rapido + un dato malo
"""
import argparse
import json
import random
import time

import paho.mqtt.client as mqtt

NOMBRE = ["NORMAL", "PRECAUCION", "CRITICO", "FALLO"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--user", default="esp32")
    ap.add_argument("--password", default="")
    ap.add_argument("--dispositivo", default="wrews-01")
    ap.add_argument("--periodo", type=float, default=5.0, help="s entre telemetrias")
    ap.add_argument("--descenso", type=float, default=2.0, help="pp de nivel por telemetria")
    ap.add_argument("--pico", action="store_true", help="mete un dato anomalo a los 60 s")
    a = ap.parse_args()

    base = f"wrews/{a.dispositivo}"
    boot = random.randint(1, 2**31 - 1)
    st = {"estado": 0, "silenciado": 0, "ev": 0}

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{a.dispositivo}-sim")
    c.username_pw_set(a.user, a.password)
    c.will_set(f"{base}/disponibilidad", "offline", qos=1, retain=True)

    def evento(grav, texto):
        st["ev"] += 1
        c.publish(f"{base}/eventos", json.dumps(
            {"id": st["ev"], "boot": boot, "gravedad": grav, "hace_ms": 0, "texto": texto}))
        print("evento:", texto)

    def publicar_estado():
        c.publish(f"{base}/estado", json.dumps(
            {"estado": st["estado"], "estado_txt": NOMBRE[st["estado"]],
             "silenciado": st["silenciado"], "boot": boot}), retain=True)

    def al_conectar(cl, ud, flags, rc, props):
        if rc.is_failure:
            print("Conexion rechazada:", rc)
            return
        print("Conectado al broker")
        cl.publish(f"{base}/disponibilidad", "online", retain=True)
        cl.subscribe(f"{base}/cmd", 1)
        cl.subscribe(f"{base}/ia/texto", 0)
        publicar_estado()

    def al_recibir(cl, ud, m):
        if m.topic.endswith("/ia/texto"):
            print("IA ->", m.payload.decode())
            return
        try:
            cmd = json.loads(m.payload)
        except ValueError:
            cmd = {"accion": m.payload.decode(), "origen": "MQTT"}
        if cmd.get("accion") == "silenciar":
            ok = st["estado"] > 0 and not st["silenciado"]
            if ok:
                st["silenciado"] = 1
                evento(0, f"Buzzer silenciado 15 min desde {cmd.get('origen', 'MQTT')} (MQTT)")
                publicar_estado()
            resp = {"accion": "silenciar", "ok": int(ok), "estado": NOMBRE[st["estado"]]}
        else:
            resp = {"accion": cmd.get("accion"), "ok": 1}
        cl.publish(f"{base}/cmd/resp", json.dumps(resp))
        print("comando", cmd, "->", resp)

    c.on_connect = al_conectar
    c.on_message = al_recibir
    c.connect(a.host, a.port, keepalive=15)
    c.loop_start()

    nivel, sentido, seq, t0 = 90.0, -1, 0, time.time()
    try:
        while True:
            seq += 1
            nivel += sentido * a.descenso + random.gauss(0, 0.3)
            if nivel <= 5:
                sentido = 1
            if nivel >= 90:
                sentido = -1
            tasa = max(0.0, -sentido * a.descenso * 60 / a.periodo)
            riesgo = max(0.0, min(100.0, 0.54 * (100 - nivel) + 0.30 * 40 + 0.16 * min(tasa, 100)))
            nuevo = 2 if nivel <= 15 else 1 if nivel <= 50 else 0
            if nuevo != st["estado"]:
                if nuevo > st["estado"]:
                    st["silenciado"] = 0
                st["estado"] = nuevo
                evento(nuevo, f"Estado {NOMBRE[nuevo]} (simulado)")
                publicar_estado()
            n_pub = nivel
            if a.pico and 60 <= time.time() - t0 < 60 + a.periodo:
                n_pub = nivel + 45     # dato malo: el gateway debe descartarlo
            tel = {"seq": seq, "boot": boot, "uptime_s": int(time.time() - t0),
                   "estado": st["estado"], "estado_txt": NOMBRE[st["estado"]],
                   "silenciado": st["silenciado"], "nivel": round(n_pub, 1),
                   "distancia": round(20 - 17 * nivel / 100, 1), "tasa": round(tasa, 1),
                   "tasa_lista": 1, "riesgo": round(riesgo, 1), "idx_evap": 40.0, "et": 3.0,
                   "temp": 18.5, "hum": 62.0, "pres": 752.0, "vpd": 0.8, "irr": 350,
                   "sev_nivel": nuevo, "sev_evap": 0, "sev_tasa": 0, "sev_riesgo": nuevo,
                   "modo": "DEMO", "rssi": -55}
            c.publish(f"{base}/telemetria", json.dumps(tel))
            print(f"tel #{seq}: nivel {n_pub:5.1f} %  estado {NOMBRE[st['estado']]}"
                  f"{' [MUTE]' if st['silenciado'] else ''}")
            time.sleep(a.periodo)
    except KeyboardInterrupt:
        pass
    finally:
        c.loop_stop()
        c.disconnect()   # desconexion limpia: el broker NO manda el LWT


if __name__ == "__main__":
    main()
