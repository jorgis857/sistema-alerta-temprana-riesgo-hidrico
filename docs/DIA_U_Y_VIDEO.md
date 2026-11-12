# WREWS · Plan del día en la U, guion del video y sustentación

Todo lo de la casa ya está probado con el prototipo real (12/11/2026, con el Mac haciendo de gateway):
- ESP32 → MQTT → gateway → SQLite → Ubidots;
- alertas al celular (los SMS de Ubidots funcionaron hasta agotar el cupo del plan; ahora van por Telegram desde el gateway);
- silenciar la alarma desde Ubidots (`ok: 1`);
- recomendación de Claude;
- broker caído y reconexión;
- filtro de lecturas imposibles del BME280.

En la U solo falta **cambiar el Mac por la Raspberry Pi** y **grabar**.

---

## 1. Qué llevar

- [ ] Raspberry Pi con su fuente y la microSD con **Raspberry Pi OS** (SSH activado y usuario creado en Raspberry Pi Imager).
- [ ] El prototipo WREWS y su **cable USB de datos**.
- [ ] El Mac con el repo (tiene arduino-cli, el core del ESP32 y las librerías ya instaladas).
- [ ] Un celular para el **hotspot** (2.4 GHz y con datos) y otro para **grabar**.
- [ ] Anotado: token de Ubidots, clave de Anthropic (están en `gateway/gateway.env` del Mac) y la cuenta de Ubidots abierta en el navegador.
- [ ] Un cartón o la mano para mover el nivel frente al ultrasónico (lleno = 30 cm, vacío = 40,3 cm).

## 2. Montaje en la U (unos 45 min)

### 2.1 Red
1. Prender el hotspot.
   - **iPhone:** *Compartir Internet* → activar **Maximizar compatibilidad** (eso lo deja en 2.4 GHz).
   - **Android:** banda **2.4 GHz**.
2. Conectar a ese hotspot **el Mac, la Pi y luego el ESP32**.

### 2.2 Raspberry Pi
Desde el Mac, conectado al hotspot:
```bash
ssh USUARIO@raspberrypi.local          # o con la IP que muestre el hotspot
hostname -I                            # ANOTAR la IP de la Pi: ________________
# Nombre UNICO para la Pi: en la U puede haber varias "raspberrypi" en la red
sudo hostnamectl set-hostname wrews-gw && sudo reboot
# a partir de aqui la Pi es wrews-gw.local:  ssh USUARIO@wrews-gw.local
timedatectl                            # debe decir "System clock synchronized: yes"
exit
```
Copiar el código. El repo no está publicado todavía, así que se copia directo desde el Mac:
```bash
cd ~/sistema-alerta-temprana-riesgo-hidrico
scp -r gateway docs USUARIO@wrews-gw.local:~/wrews/
ssh USUARIO@wrews-gw.local
cd ~/wrews/gateway && rm -f gateway.env *.db && chmod +x instalar.sh
sudo ./instalar.sh
```
`instalar.sh` pide tres claves MQTT. **Anótenlas:**
- `esp32` = ____________
- `gateway` = ____________
- `monitor` = ____________

Configurar el gateway:
```bash
sudo nano /etc/wrews/gateway.env
#   MQTT_PASS=<la clave de "gateway" que pidio instalar.sh>  (NO la del Mac)
#   Y copiar TAL CUAL del gateway/gateway.env del Mac estas lineas:
#     UBIDOTS_TOKEN, UBIDOTS_TABLERO_URL, ANTHROPIC_API_KEY,
#     TELEGRAM_TOKEN, TELEGRAM_ADMIN, TELEGRAM_CLAVE
sudo bash -c 'set -a; . /etc/wrews/gateway.env; cd /opt/wrews/gateway; /opt/wrews/venv/bin/python -m wrews_gw.ia --probar'
sudo systemctl restart wrews-gateway
journalctl -u wrews-gateway -f     # "Broker local: conectado" y "Ubidots: conectado"
```

### 2.3 ESP32
Desde el Mac, con el ESP32 conectado por USB:
```bash
cd ~/sistema-alerta-temprana-riesgo-hidrico
open -e firmware/wrews/secrets.h
#   WIFI_SSID / WIFI_PASS -> los del hotspot
#   MQTT_HOST -> "wrews-gw.local" (el nombre unico que se le puso a la Pi);
#                si el hotspot no deja resolver nombres, usar la IP de la Pi
#   MQTT_PASS -> la clave de esp32 que pidió instalar.sh
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/wrews
arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/cu.usbserial-0001 firmware/wrews
arduino-cli monitor -p /dev/cu.usbserial-0001 -c baudrate=115200   # salir con Ctrl+C
```
En el monitor debe aparecer `Wi-Fi: conectado`, la **IP del tablero** (anotarla: ____________) y `MQTT: conectado`.

> El puerto (`/dev/cu.usbserial-0001`) puede cambiar en otro Mac o en otro puerto USB. Se averigua con `arduino-cli board list`.

### 2.4 Comprobar antes de grabar (5 min)
- [ ] Tablero local (`http://IP-del-ESP32`, usuario `alcaldia`, clave `wrews-2026`): datos en vivo, «Gateway MQTT: conectado» y la tarjeta de IA con texto.
- [ ] Ubidots: los valores se actualizan. El dispositivo es el mismo `wrews-01`, así que el tablero y los eventos **no se tocan**.
- [ ] Telegram: con el gateway de la Pi corriendo (y el del Mac **apagado**: Telegram solo deja un lector por bot). Luego el administrador escribe `/start` en el bot, los compañeros abren `t.me/WREWS_Alertasbot?start=CLAVE` y el administrador los aprueba con el botón **✅ Aprobar**. Los suscriptores no pasan del Mac a la Pi: hay que repetir el `/start`.
- [ ] En la Pi, en una segunda terminal: `mosquitto_sub -h localhost -u monitor -P CLAVE_MONITOR -t 'wrews/#' -v` muestra la telemetría cada 5 s.

---

## 3. Pruebas para la wiki (anotar la hora y sacar captura de cada una)

Los comandos SQL van en `sudo sqlite3 /var/lib/wrews/wrews.db`.

| # | Prueba | Cómo | Resultado esperado | Hora / resultado |
|---|---|---|---|---|
| 1 | Datos en SQLite | `SELECT COUNT(*) FROM mediciones;` dos veces, con 1 min de diferencia | Sube ~12 por minuto | |
| 2 | Guardar antes de reenviar | `SELECT COUNT(*) FROM cola_nube WHERE enviado_ms IS NULL;` | 0 o pocos | |
| 3 | PRECAUCIÓN → CRÍTICO | Alejar el cartón a >35 cm y luego a >39 cm | LEDs, buzzer, tablero local, Ubidots, Telegram | |
| 4 | Silenciar desde Ubidots | Switch con la alarma sonando | El buzzer calla y `SELECT * FROM comandos;` muestra `ok: 1` | ✅ en casa (13:36:10) |
| 5 | Silenciar desde la Pi | `python -m wrews_gw.comando silenciar` (ver la guía, prueba 5) | Respuesta del ESP32 | |
| 6 | IA | `/recomendacion` en el bot | Responde Claude en unos 10 s, y aparece también en el tablero local, en Ubidots y en `SELECT proveedor, texto FROM ia ORDER BY id DESC LIMIT 1;` | ✅ en casa |
| 7 | Sin Internet | Quitar los datos móviles del hotspot 3 min | Alarma y tablero local siguen. La IA pasa a `reglas` y la cola crece; al volver, se vacía | |
| 8 | ESP32 apagado | Desconectar el USB | ~20 s: FALLO en Ubidots + Telegram | ✅ en casa (detectado a los 20 s) |
| 9 | Broker caído | `sudo systemctl stop mosquitto`, 1 min, `start` | La alarma local sigue y todo se reconecta solo | ✅ en casa |
| 10 | Latencia | Cronometrar desde el cambio en el LCD hasta Ubidots y hasta Telegram | Estado: pocos segundos | |
| 11 | Acceso restringido | `mosquitto_pub -h localhost -t wrews/x -m hola` sin clave y el tablero de Ubidots en una ventana privada | Rechazado en los dos casos | |

---

## 4. Guion del video (máximo 5:00, los tres en cámara)

**Requisitos del enunciado:** que demuestre y explique **la validación** del prototipo, que **los tres aporten y aparezcan con la cámara encendida**, y que se pueda reproducir en Teams.

**Consejos de grabación:**
- Graben **escena por escena** y luego unan los clips.
- Para la pantalla: grabación de pantalla del Mac (**Cmd+Shift+5**) más un celular grabando el prototipo y a quien habla.
- Dejen el tablero local y el de Ubidots abiertos en pestañas, y la terminal SSH de la Pi lista.
- Hagan **un ensayo completo** antes de grabar: el estado necesita unos 3 s por escalón y el promedio de Ubidots 1 min.
- Si la rúbrica de comunicación lo pide, la intro y el cierre pueden ir en inglés (abajo hay una versión).

| Tiempo | Quién | Qué se ve | Qué se dice |
|---|---|---|---|
| 0:00–0:20 | **Integrante A** en cámara, con el prototipo | Los tres en cuadro y luego el prototipo | «Somos [nombres]. WREWS es un sistema de alerta temprana de riesgo hídrico para la Sabana Centro ante El Niño: mide el nivel del reservorio y las variables que gobiernan la evaporación, y alerta en el sitio, en un tablero local y en la nube.» |
| 0:20–0:55 | **A** | Diagrama de arquitectura (wiki) y luego el hardware | «El ESP32 mide nivel, temperatura, humedad, presión y radiación, y calcula un índice de riesgo con pesos AHP. Mide y comunica en hilos de FreeRTOS separados. Por MQTT envía todo a una Raspberry Pi con Mosquitto, con usuario, clave y permisos por usuario. El gateway lo guarda en SQLite, lo valida, lo promedia y lo sube a Ubidots por MQTT con TLS. Un módulo de IA predice y recomienda.» |
| 0:55–1:35 | **Integrante B** | LCD + tablero local + Ubidots + terminal con `mosquitto_sub` + `SELECT COUNT(*)` | «En operación normal: el LCD y los LEDs en el sitio, el tablero local en la WLAN con usuario y clave, el mismo dato en Ubidots desde cualquier lugar, y cada mensaje pasando por el broker y quedando en SQLite antes de subir a la nube.» |
| 1:35–2:35 | **B** | Mover el cartón: LED amarillo y luego rojo, el buzzer, el banner del tablero local, el estado en Ubidots y **el aviso de Telegram llegando al celular** | «Simulamos el descenso del nivel. Al bajar del 50 % pasa a PRECAUCIÓN y al bajar del 15 % a CRÍTICO, con confirmación para evitar falsas alarmas. La alarma física suena, el tablero local avisa, Ubidots se actualiza en segundos y llega el aviso al celular de las autoridades, por Telegram, con la recomendación de la IA.» |
| 2:35–3:05 | **Integrante C** | El switch en Ubidots: el buzzer se calla y el evento aparece en el tablero local | «Desde la nube, una autoridad puede desactivar la alarma física: el switch de Ubidots baja por MQTT al gateway, el gateway lo manda al ESP32 y el buzzer se silencia 15 minutos. Los LEDs siguen encendidos, porque el riesgo no desapareció.» |
| 3:05–3:45 | **C** | En el celular: escribir `/dashboard` y `/recomendacion` al bot → la respuesta de Claude aparece también en la tarjeta del tablero local y en Ubidots → `SELECT proveedor, min_a_critico, texto FROM ia ...` | «El módulo de IA tiene dos partes. Una regresión lineal propia estima en cuántos minutos se llega al 15 %, y corre siempre, sin Internet. Cuando una autoridad pide /recomendacion, Claude, de Anthropic, redacta una recomendación a partir de esos números, sin calcular cifras por su cuenta. Así solo se consume la API cuando alguien la necesita. Si no hay Internet, responde una tabla de reglas. Todo queda en SQLite, incluido el prompt exacto.» |
| 3:45–4:35 | **A** | Desconectar el USB del ESP32 → FALLO en Ubidots + aviso en Telegram. Quitar los datos del hotspot → alarma local funcionando, cola en SQLite creciendo y vaciándose al volver | «Validamos las fallas. Si el ESP32 se apaga, el gateway lo detecta en unos 20 s por la última voluntad de MQTT y reporta FALLO. Si se cae Internet, la alarma local sigue, los datos se acumulan en SQLite y se suben con su hora real cuando vuelve. También filtramos lecturas imposibles del sensor, como un pico de 180 °C por un contacto flojo.» |
| 4:35–5:00 | **Los tres** en cámara | Tablero de Ubidots de fondo | «WREWS integra medición, procesamiento local, comunicación MQTT, visualización local y global, alertas e IA en un prototipo de bajo costo. Gracias.» |

**Intro y cierre en inglés (opcional):**
- *Intro:* «We are [names]. WREWS is a low-cost IoT early-warning system for water scarcity in Sabana Centro: it monitors reservoir level and evaporation drivers, and alerts on site, on a local dashboard and in the cloud.»
- *Cierre:* «WREWS integrates sensing, local processing at the gateway, MQTT, local and global dashboards, alerts and an AI module. Thank you.»

---

## 5. Sustentación (19/11): pitch de 3 min y preguntas

**Pitch (3 min):**
1. Problema: El Niño y 20 municipios en riesgo extremo.
2. Solución: un dispositivo que fusiona nivel y evaporación, más un gateway y la nube.
3. Arquitectura en una diapositiva.
4. Demostración en vivo: bajar el nivel → alarma → aviso en Telegram → silenciar desde Ubidots.
5. IA.
6. Resultados de las pruebas.

**Preguntas probables y respuestas cortas:**

| Pregunta | Respuesta |
|---|---|
| ¿Por qué MQTT y no HTTP? | Es liviano, de publicación/suscripción y con QoS. Tiene última voluntad (LWT) para detectar la caída del equipo y deja comunicación en los dos sentidos (comando de silenciar) sin hacer *polling*. |
| ¿Qué hace el gateway además de reenviar? | Guarda todo en SQLite antes de reenviar, valida (rango físico por variable y z robusto con MAD para el nivel), promedia por ventanas de 60 s, mide la completitud, vigila el enlace y corre la IA. |
| ¿Qué pasa si se cae Internet? | La alarma local y el tablero local no dependen de Internet. El gateway encola en SQLite y envía después con su marca de tiempo original (*store and forward*). La IA usa el respaldo por reglas. |
| ¿Y si se cae el broker o la Pi? | El ESP32 sigue alarmando, porque MQTT va en su propio hilo, y se reconecta solo. Al volver, publica los eventos pendientes. |
| ¿Cómo se restringe el acceso? | Tablero local: misma subred + usuario y clave + sesión con token aleatorio. Mosquitto: sin anónimos, con usuario, clave y ACL por usuario. Ubidots: cuenta privada y TLS. Telegram: solo reciben alertas los usuarios que el administrador aprueba (`/aprobar`); los demás quedan pendientes y no pueden consultar nada. |
| ¿Por qué un LLM y no solo reglas? | La predicción numérica es propia (regresión). El LLM traduce esos números a una recomendación accionable en lenguaje natural para las autoridades. No inventa cifras: recibe los datos calculados y se le prohíbe crear números. Hay respaldo por reglas si falla. |
| ¿Cuánto cuesta la IA? | Unos 700 tokens de entrada y 750 de salida por recomendación, alrededor de 2 centavos de dólar. Solo se llama cuando una autoridad la pide (`/recomendacion`), máximo una vez por minuto; lo automático usa la predicción propia y reglas, que no cuestan. |
| ¿Cómo evitan falsas alarmas? | Confirmación asimétrica (ISA-18.2), banda muerta de la tasa calculada a partir del ruido, discontinuidades, y descarte de lecturas imposibles en el ESP32 y en el gateway. |
| ¿Qué tan rápido llega una alerta? | Estado: pocos segundos hasta Ubidots (se envía al instante; ver la prueba 10). Variables medidas: hasta 60 s, porque se promedian por minuto a propósito. |
| ¿Cómo validaron lo que les dio la IA que usaron para desarrollar? | Compilando, con pruebas unitarias, con pruebas de punta a punta con un simulador y con el prototipo real. Ver la sección de declaración de uso de IA en la wiki. |

---

## 6. Evidencias para la wiki (lista de capturas)

- [ ] Monitor serial: `MQTT: conectado` y el autotest OK.
- [ ] `mosquitto_pub` sin clave rechazado (*not authorised*).
- [ ] `mosquitto_sub` con la telemetría.
- [ ] Consultas SQL: `mediciones`, `cola_nube`, `comandos` (silenciar `ok: 1`), `ia` (con el prompt).
- [ ] Log del gateway: `Ubidots: conectado`, `IA (claude, … ms)`, `Claude: N tokens…`, `Sin datos del ESP32 (LWT)`.
- [ ] El tablero de Ubidots completo y la configuración de los eventos.
- [ ] El aviso de Telegram recibido (captura del celular) y, si alcanzó, un SMS de los que llegaron hoy.
- [ ] El tablero local en NORMAL, PRECAUCIÓN y CRÍTICO, con la tarjeta de IA.
- [ ] La prueba de Internet caído: el log con `Ubidots: desconectado`, la cola creciendo y la cola en 0 al volver.
