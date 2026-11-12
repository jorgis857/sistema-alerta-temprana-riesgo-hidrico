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

## 1. Qué llevar (todo quedó preparado la noche anterior)

- [ ] **La microSD ya grabada** (la prepara Jorge con `GUIA_MICROSD_JORGE`): hostname `wrews-gw`, usuario `equipo2`, Wi-Fi `WREWS-Hotspot` y SSH activado. **La Raspberry Pi la presta la universidad**: confirmar que venga con su fuente (Pi 4: USB-C de 3 A).
- [ ] **El prototipo WREWS** y su **cable USB de datos**. El ESP32 ya tiene el firmware para la U: busca `WREWS-Hotspot` y `wrews-gw.local`.
- [ ] **El Mac de Mateo** con la carpeta **`~/Downloads/WREWS-kit-U`**. Trae el `gateway.env` de la Pi ya lleno con todas las claves, el script `instalar_en_pi.sh` y las guías de la microSD. También tiene Raspberry Pi Imager y arduino-cli, por si hay que regrabar algo.
- [ ] **Un celular para el hotspot**, con datos, y **otro para grabar**.
- [ ] La cuenta de Ubidots abierta en el navegador y Telegram en el celular del administrador.
- [ ] Un cartón o la mano para mover el nivel frente al ultrasónico (lleno = 30 cm, vacío = 40,3 cm).

## 2. Montaje en la U (unos 20 min)

### 2.1 Hotspot
Quien preste el celular le pone al hotspot **el nombre `WREWS-Hotspot` y la clave acordada** (está en la guía de la microSD). En **iPhone**, el nombre del hotspot es el nombre del teléfono (*Ajustes → General → Información → Nombre*) y hay que activar **Maximizar compatibilidad**; en **Android**, la banda va en **2.4 GHz**. Conectar el Mac a ese hotspot.

### 2.2 Raspberry Pi: un solo comando
1. Meter la microSD en la Pi de la U y conectarla a la corriente. Esperar **2 a 3 minutos**: en el celular debe aparecer `wrews-gw` como conectado.
2. Desde el Mac:
   ```bash
   scp -r ~/Downloads/WREWS-kit-U equipo2@wrews-gw.local:~/
   ssh -t equipo2@wrews-gw.local 'bash ~/WREWS-kit-U/instalar_en_pi.sh'
   ```
   Pide la clave del usuario `equipo2` dos o tres veces: es la de la guía de la microSD. El script:
   - baja el código de GitHub (rama `challenge3-sistema`);
   - copia el `gateway.env` ya lleno;
   - instala Mosquitto con los usuarios y permisos, sin preguntar las claves;
   - arranca el servicio y hace las comprobaciones.

   Tarda **5 a 10 min**.
3. Al final debe mostrar:
   - `not authorised` (el broker rechaza a quien no tiene clave);
   - `Proveedor: claude` (la IA funciona);
   - `Broker local: conectado` y `Ubidots: conectado`.

**Si algo falla:**
- **`wrews-gw` no aparece en el hotspot:** revisar que el nombre y la clave del hotspot sean exactos y que esté en 2.4 GHz.
- **La Pi de la U es un modelo viejo** (Pi 2 o anterior) y no arranca: regrabar la microSD en el Mac con *Raspberry Pi Imager* (ya instalado), con los mismos ajustes de la guía, eligiendo **Raspberry Pi OS Lite (32-bit)**.
- **`Could not resolve hostname`:** usar la IP de la Pi que muestra el celular, en vez de `wrews-gw.local`.

### 2.3 ESP32: ya está listo
Solo conectarlo a la corriente o al USB. En unos 30 s se une a `WREWS-Hotspot` y encuentra `wrews-gw.local` solo. Para ver que se conectó: en la Pi, `journalctl -u wrews-gateway -f` muestra `Evento ESP32: Gateway MQTT conectado`. La IP del tablero local aparece en el LCD (anotarla: ____________).

Si hubiera que regrabar el ESP32, desde el Mac:
```bash
cd ~/sistema-alerta-temprana-riesgo-hidrico
arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/cu.usbserial-0001 firmware/wrews
```
El puerto puede cambiar; se averigua con `arduino-cli board list`.

### 2.3.1 Telegram
- El administrador (Mateo) le escribe `/start` al bot, porque la base de datos de la Pi empieza vacía.
- Jorge y Antonio abren el enlace con la clave de registro y Mateo los aprueba con el botón **✅ Aprobar**.
- **El gateway del Mac debe estar apagado** (cerrar la sesión de Claude Code): Telegram deja un solo lector por bot.

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
