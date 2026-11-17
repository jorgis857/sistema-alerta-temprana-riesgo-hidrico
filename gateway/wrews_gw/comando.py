"""Manda un comando al ESP32 desde la Pi (prueba local, sin Ubidots).

    python -m wrews_gw.comando silenciar
    python -m wrews_gw.comando ping
"""
import json
import sys
import time

import paho.mqtt.client as mqtt

from .config import Config


def main():
    accion = sys.argv[1] if len(sys.argv) > 1 else "ping"
    cfg = Config.desde_entorno()
    base = f"wrews/{cfg.dispositivo}"
    respuesta = []

    def al_conectar(c, ud, flags, rc, props):
        if rc.is_failure:
            print("El broker rechazo la conexion:", rc)
            return
        c.subscribe(f"{base}/cmd/resp", qos=1)
        c.publish(f"{base}/cmd", json.dumps({"accion": accion, "origen": "consola de la Pi"}),
                  qos=1)

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"wrews-cli-{int(time.time())}")
    c.username_pw_set(cfg.mqtt_user, cfg.mqtt_pass)
    c.on_connect = al_conectar
    c.on_message = lambda c, ud, m: respuesta.append(m.payload.decode())
    c.connect(cfg.mqtt_host, cfg.mqtt_port)
    c.loop_start()
    for _ in range(50):
        if respuesta:
            break
        time.sleep(0.1)
    c.loop_stop()
    print(respuesta[0] if respuesta else "Sin respuesta del ESP32 en 5 s (esta conectado?)")
    sys.exit(0 if respuesta else 1)


if __name__ == "__main__":
    main()
