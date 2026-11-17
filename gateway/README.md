# Gateway WREWS (Raspberry Pi)

Recibe por MQTT lo que publica el ESP32, lo **guarda en SQLite antes de cualquier otra cosa**, lo procesa localmente y lo reenvía a Ubidots. También corre el módulo de IA (predicción propia + recomendación con Claude) y baja a la maqueta la orden de silenciar la alarma que se da en Ubidots.

| Archivo | Qué hace |
|---|---|
| `wrews_gw/gateway.py` | Servicio principal (hilos: red local, trabajador, periódico, nube, IA) |
| `wrews_gw/almacen.py` | Esquema y acceso a SQLite, cola *store and forward* hacia la nube |
| `wrews_gw/procesamiento.py` | Validación (rango físico + z robusto con MAD), agregados por ventana, formato Ubidots |
| `wrews_gw/ia.py` | Predicción por regresión lineal (minutos hasta el 15 %) + recomendación con Claude (o Gemini/OpenAI), con respaldo por reglas. `python -m wrews_gw.ia --probar` revisa la clave |
| `wrews_gw/nube.py` | Puente MQTT con Ubidots (TLS), subida y bajada del switch `silenciar` |
| `wrews_gw/telegram.py` | Avisos al celular por Telegram cuando cambia el estado, con la recomendación de la IA (`--chat-id`, `--probar`) |
| `wrews_gw/comando.py` | Mandar `silenciar` o `ping` al ESP32 desde la consola de la Pi |
| `simulador_esp32.py` | ESP32 falso con los mismos tópicos, para probar sin la maqueta |
| `mosquitto/` | Configuración del broker: sin anónimos, usuarios y ACL |
| `instalar.sh`, `systemd/`, `gateway.env.example` | Instalación como servicio |

Instalación y pruebas paso a paso: [`docs/GUIA_DESPLIEGUE_PI.md`](../docs/GUIA_DESPLIEGUE_PI.md).

Pruebas unitarias (no necesitan broker ni Internet):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests
```
