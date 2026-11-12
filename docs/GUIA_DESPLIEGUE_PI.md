# WREWS · Guía de despliegue y pruebas (Challenge #3)

Paso a paso para dejar funcionando, en la universidad, la cadena completa:

```
ESP32 (firmware v8) ──MQTT──▶ Raspberry Pi: Mosquitto ─▶ gateway ─▶ SQLite
                                                 │          │
                                                 │     procesamiento local
                                                 │     + IA (regresión + Claude)
                                                 ▼          ▼
                     ESP32 ◀── silenciar ◀── Ubidots (tablero global, notificaciones)
```

Lo que está entre `CAMBIAR_...` o `192.168.X.X` se reemplaza con los datos reales. Tiempo estimado: 45 a 60 minutos la primera vez.

## Cómo funciona (para explicarlo en la sustentación)

- **ESP32.** Mide, calcula el riesgo y maneja la alarma local igual que en la v7. El hilo nuevo, `tareaMqtt` (núcleo 0, prioridad 1, por debajo de la medición), publica la telemetría cada 5 s, el estado cuando cambia (mensaje retenido), cada evento, y `online`/`offline` como última voluntad (LWT). Además recibe el comando `silenciar` y la recomendación de la IA. Solo toma `mtx_estado` para copiar datos, nunca mientras usa la red, y nunca toca el bus I2C ni los pines. Por eso, si se cae la red o el broker, la alarma local no se entera. Además, el ESP32 descarta las lecturas imposibles del BME280 (por ejemplo, 180 °C por un contacto flojo en SDA/SCL) para que no generen una PRECAUCIÓN falsa; si llegan 5 seguidas, pasa a FALLO del sensor.
- **Gateway en la Pi.** Cada mensaje se guarda primero en SQLite y solo después se procesa:
  - valida la muestra: descarta solo la variable que esté fuera de rango físico, y para el nivel usa además un z robusto con MAD;
  - agrega por ventanas de 60 s (media, mínimo, máximo y % de muestras recibidas);
  - vigila el enlace: si pasan 20 s sin datos o llega el LWT, reporta FALLO en nombre del ESP32.

  Lo que va a Ubidots pasa por la tabla `cola_nube`. Si no hay Internet, se acumula ahí y se envía después con su hora real.
- **IA.** Tiene dos partes:
  1. Una predicción propia: regresión lineal del nivel en los últimos 10 min, que da la pendiente, el R² y los minutos hasta el 15 %.
  2. Una recomendación en lenguaje natural para la alcaldía. **Automáticamente**, al cambiar el estado, se genera con una tabla de reglas (gratis). **Claude** (`claude-opus-5-5`) se llama **solo cuando una autoridad la pide** con `/recomendacion` en el bot de Telegram, con un máximo de una llamada por minuto. Así no se gastan créditos en recomendaciones que nadie lee. Claude no calcula nada, solo interpreta las cifras ya calculadas. Con `IA_LLM_AUTO=1` también se llama automáticamente.

  Si no hay Internet, clave o créditos, se usa una tabla de reglas. Todo queda en la tabla `ia` (incluido el prompt exacto), se sube a Ubidots y se muestra en el tablero local.
- **Seguridad.** Mosquitto no acepta clientes anónimos y cada usuario tiene permisos propios en la ACL (el ESP32 no puede publicar comandos). La conexión con Ubidots va cifrada con TLS en el puerto 8883. Las claves están en `/etc/wrews/gateway.env` y en `secrets.h`, y ninguno de los dos se sube al repositorio.

## 0. Antes de ir a la universidad

1. **Cuenta de Ubidots** (plan STEM, gratuito para estudiantes): crear la cuenta en https://ubidots.com/stem y copiar el **token** en *Perfil → API Credentials → Default token*.
2. **Clave de la API de Anthropic**: en https://console.anthropic.com → *API Keys → Create key*. Se copia una sola vez (empieza por `sk-ant-`). Verificar en *Billing* que la organización tenga créditos.
   - Costo aproximado con `claude-opus-5-5` y esfuerzo `low`: unos 2 centavos de dólar por recomendación (unos 700 tokens de entrada y 750 de salida). Solo se gasta cuando alguien pide `/recomendacion`. El consumo real queda en el log (`Claude: N tokens de entrada, M de salida`).
   - Para gastar aún menos: subir `IA_CADA_S` o usar `CLAUDE_MODELO=claude-haiku-5-5` en el paso 4.
3. **Arduino IDE**: core **esp32 de Espressif 3.x** (se compiló con 3.3.12) y la librería **PubSubClient** (Nick O'Leary) desde el gestor de librerías. Las demás ya estaban desde el Challenge #2: Adafruit BME280, Adafruit Unified Sensor, Adafruit INA219 y LiquidCrystal I2C.
4. **Una red Wi-Fi común** para el ESP32 y la Pi. El hotspot de un celular sirve y evita los bloqueos de la red de la universidad. Debe ser de 2.4 GHz y tener Internet (para Ubidots y Claude).

## 1. Preparar la Raspberry Pi

1. Raspberry Pi OS (Bookworm, 64 bits, la versión Lite basta) con SSH activado. Conectarla a la misma red del paso 0.4.
2. Desde un PC en la misma red: `ssh USUARIO@raspberrypi.local`, o con la IP. `USUARIO` es el que se creó en Raspberry Pi Imager; ya no existe por defecto el usuario `pi`.
3. Averiguar la IP de la Pi y anotarla, porque va en el ESP32:
   ```bash
   hostname -I
   ```
   > Si la Pi cambia de IP cada vez que se conecta, el ESP32 pierde el broker. En el hotspot del celular suele mantenerse; si no, fijarla con `sudo nmcli con mod "<nombre de la red>" ipv4.method manual ipv4.addresses 192.168.X.X/24 ipv4.gateway 192.168.X.1 ipv4.dns 8.8.8.8` y reconectar.
4. **Hora:** `timedatectl` debe decir `System clock synchronized: yes`. La Pi no tiene reloj propio y toma la hora de Internet; con la hora mal, los datos en Ubidots quedan en otra fecha y la orden de silenciar se descarta por vieja.

## 2. Bajar el código

**Opción A: el código ya está en GitHub**
```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico.git
cd sistema-alerta-temprana-riesgo-hidrico/gateway
```

**Opción B: todavía no se ha publicado.** Se copia desde el PC que tiene el repositorio, por la misma red:
```bash
# en el PC, dentro de la carpeta del repo:
scp -r gateway docs USUARIO@raspberrypi.local:~/wrews/
# en la Pi:
cd ~/wrews/gateway && rm -f gateway.env *.db && chmod +x instalar.sh
```
(`gateway.env` y `*.db` son los de las pruebas en el PC: no se usan en la Pi.)

## 3. Instalar (Mosquitto con usuario y clave, Python, servicio)

```bash
sudo ./instalar.sh
```

El script pide **tres claves** para los usuarios MQTT (cada una dos veces, y no se ven al escribirlas). Anótenlas:

| Usuario | Para qué | Dónde va la clave |
|---|---|---|
| `esp32` | El ESP32 publica sus datos y recibe comandos | `MQTT_PASS` en `secrets.h` |
| `gateway` | El servicio del gateway (lee todo) | `MQTT_PASS` en `/etc/wrews/gateway.env` |
| `monitor` | Solo lectura, para depurar con `mosquitto_sub` | (solo para ustedes) |

Qué deja instalado:
- Mosquitto en el puerto 1883, **sin acceso anónimo** y con lista de permisos por usuario (`/etc/mosquitto/wrews.acl`).
- El gateway en `/opt/wrews`, con su entorno de Python (paho-mqtt, requests y anthropic).
- La base de datos en `/var/lib/wrews/wrews.db`.
- El servicio `wrews-gateway`, que arranca solo al encender la Pi.

**Verificación 3.1 (acceso restringido):** esto debe fallar con *not authorised*:
```bash
mosquitto_pub -h localhost -t wrews/prueba -m hola
```
y esto debe funcionar (dejarlo abierto en una segunda terminal SSH, sirve en todas las pruebas):
```bash
mosquitto_sub -h localhost -u monitor -P CLAVE_MONITOR -t 'wrews/#' -v
```

## 4. Configurar el gateway (aquí va la clave de Claude)

```bash
sudo nano /etc/wrews/gateway.env
```

Llenar estas tres líneas; lo demás puede quedar igual:

```
MQTT_PASS=la-clave-del-usuario-gateway
UBIDOTS_TOKEN=el-token-de-ubidots
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Guardar con Ctrl+O, Enter, Ctrl+X. **Probar la clave de Claude** antes de arrancar:

```bash
sudo bash -c 'set -a; . /etc/wrews/gateway.env; cd /opt/wrews/gateway; /opt/wrews/venv/bin/python -m wrews_gw.ia --probar'
```

Debe imprimir `Proveedor: claude (claude-opus-5-5)` y una recomendación. Si dice `reglas`, la línea `ERROR` explica la causa: `clave invalida`, `credit balance is too low` (faltan créditos) o `sin Internet`. Luego:

```bash
sudo systemctl restart wrews-gateway
journalctl -u wrews-gateway -f
```

Debe verse `Broker local: conectado` y `Ubidots: conectado`.
- Si sale `Ubidots rechazo la conexion`, el token está mal.
- Si Ubidots nunca conecta, la red puede estar bloqueando el puerto 8883: poner `UBIDOTS_TLS=0` en el `gateway.env` y reiniciar el servicio.

## 5. Primera prueba sin el ESP32 (simulador)

Antes de tocar el hardware conviene comprobar que todo lo demás funciona. En otra terminal SSH:

```bash
cd ~/sistema-alerta-temprana-riesgo-hidrico/gateway   # o ~/wrews/gateway si se copió con scp
/opt/wrews/venv/bin/python simulador_esp32.py --host localhost --user esp32 --password CLAVE_ESP32 --descenso 3 --pico
```

El simulador baja el nivel de 90 % a 5 % y vuelve a subir, publicando en los mismos tópicos que el ESP32. Con `--pico` mete un dato malo al minuto. En el log del gateway deben aparecer:

- `Ventana: N muestras ...` cada minuto: el agregado se guardó y se encoló para Ubidots.
- `Evento gateway: Muestra descartada por el gateway: salto de nivel ...`: la detección de anomalías.
- `Estado NORMAL -> PRECAUCION` y luego `CRITICO`.
- `IA (claude, ... ms): {...} | <recomendación>`. Si dice `IA (reglas ...` con un aviso, Claude no respondió; el sistema sigue con el respaldo y el aviso dice por qué.

Detenerlo con Ctrl+C. **Después de esta prueba borren los datos simulados** para que no se mezclen con los reales (paso 9.5).

## 6. Ubidots: tablero global y notificaciones

Con el simulador o el ESP32 corriendo, Ubidots crea solo el dispositivo `wrews-01` y sus variables al llegar el primer dato (*Devices → Devices*).

### 6.1 Variables

| Variable | Qué es | Cada cuánto |
|---|---|---|
| `nivel`, `riesgo`, `tasa`, `idx_evap`, `temp` | Media de la ventana de 60 s (min y max en el *context*) | 1 por minuto |
| `estado` | 0 NORMAL, 1 PRECAUCIÓN, 2 CRÍTICO, 3 FALLO | Al cambiar |
| `silenciado` | 1 si el buzzer está silenciado | Al cambiar |
| `gw_calidad` | % de muestras recibidas en la ventana (0 si el ESP32 no envía) | 1 por minuto |
| `ia_min_critico` | Minutos estimados hasta el 15 % (−1 = no está bajando); la recomendación va en el *context* | Al cambiar el estado; además cada 5 min en alerta y cada 30 min en NORMAL |
| `silenciar` | **Se crea a mano** (siguiente paso): el interruptor de la nube | — |

Crear `silenciar`: entrar al dispositivo → *Add variable → Raw* → nombre y etiqueta `silenciar`. Se usan los valores 0 y 1.

> Son 10 variables. Revisen en la cuenta los límites del plan STEM (variables por dispositivo y puntos por día). Con la configuración por defecto se suben unos 7 a 8 puntos por minuto, unos 450 por hora. Si se pasan, quiten variables de `UBIDOTS_VARIABLES` o suban `VENTANA_S` en el `gateway.env`.

### 6.2 Tablero

*Data → Dashboards → New dashboard* «WREWS · Tablero global». Widgets sugeridos:

1. **Indicator** o **Metric** de `estado` con colores por rango: 0 verde, 1 amarillo, 2 rojo, 3 gris.
2. **Gauge** de `nivel` con rangos 0–15 rojo, 15–50 amarillo y 50–100 verde.
3. **Line chart** de `nivel` y `riesgo` (histórico).
4. **Metric** de `ia_min_critico` y una **Values table** de la misma variable mostrando el *context* (ahí se lee la recomendación de Claude).
5. **Switch** sobre la variable `silenciar`: es el botón para **desactivar la alarma física desde la nube**.
6. **Metric** de `gw_calidad` (salud del enlace).

### 6.3 Acceso restringido

El tablero es privado por defecto (exige iniciar sesión). Para que lo vea el profesor o las «autoridades» sin darles la cuenta del equipo: *Users → Add user* (o *Share → con usuario*), con permiso solo de lectura. **No** usen el enlace público. Si el plan STEM no permite usuarios adicionales, muéstrenlo desde la cuenta del equipo y documéntenlo como limitación en la wiki.

### 6.4 Eventos de notificación

*Data → Events → Create event*, sobre la variable `estado` con la condición **igual a** (no «mayor o igual», para que cada nivel dispare su propio aviso):

| Evento | Condición | Acción |
|---|---|---|
| WREWS precaución | `estado` = 1 | Email (y/o Telegram) a los integrantes |
| WREWS crítico | `estado` = 2 | Email + Telegram |
| WREWS fallo | `estado` = 3 | Email: «revisar el equipo o el enlace» |
| WREWS recuperado | `estado` = 0 | Email (opcional) |

En el mensaje se puede usar el valor y el *context* de la variable, por ejemplo `{{last_value}}` o `{{context.origen}}`; el editor de Ubidots muestra la lista exacta de marcadores. Cuando el FALLO lo sube el gateway porque perdió al ESP32, el *context* trae `origen: gateway` y el `motivo`.

### 6.5 Avisos al celular por Telegram (recomendado)

Los SMS de Ubidots consumen un cupo pequeño del plan STEM. Cuando se acaba, aparece *«You've reached your account limit»* y Ubidots pide comprar saldo. Por eso el gateway también avisa por **Telegram**, que es gratis y sin límite. Manda un mensaje en cada cambio de estado y, enseguida, la recomendación de Claude, **solo a los usuarios aprobados**.

**Acceso solo para personal autorizado.** Quien le escribe `/start` al bot queda como *solicitud pendiente* y no recibe nada. El **administrador** (por ejemplo, el responsable de la alcaldía) recibe la solicitud con dos botones, **✅ Aprobar** y **❌ Rechazar**. Solo los aprobados reciben alertas y pueden consultar `/estado`. El administrador ve la lista con `/usuarios`, donde cada persona trae su comando tocable (`/quitar_ID`, `/aprobar_ID`). Además se puede exigir una clave de registro (`TELEGRAM_CLAVE`): se escribe `/start CLAVE` (también vale pegada o con `_`), o se comparte el enlace `https://t.me/WREWS_Alertasbot?start=CLAVE`. La clave distingue mayúsculas, y después de 5 intentos fallidos ese chat queda bloqueado 10 min.

1. En Telegram, abrir **@BotFather** → `/newbot` → darle un nombre y un usuario que termine en `bot`. Copiar el **token** que entrega.
2. En `/etc/wrews/gateway.env` poner `TELEGRAM_TOKEN=...` y `TELEGRAM_ADMIN=<chat id del administrador>`. El chat id es el número que aparece en el log (`journalctl -u wrews-gateway`) cuando esa persona le escribe `/start` al bot. Reiniciar el servicio.
3. El administrador escribe `/start` y queda aprobado de una vez. Los demás escriben `/start` y el administrador los aprueba desde su chat.
4. Probar con `/estado`, o cambiando el estado en la maqueta.

Comandos para los usuarios aprobados (aparecen en el menú al escribir `/`):
- `/estado`: estado actual, último dato y última recomendación.
- `/recomendacion`: **pide el análisis de la IA (Claude)** con los datos actuales. También se publica en el tablero local y en Ubidots y queda en SQLite.
- `/dashboard`: **el tablero completo en una imagen**: tarjetas de estado, nivel, riesgo, minutos hasta el 15 %, temperatura, humedad, presión e índice evaporativo; gráficas de la última hora y la última recomendación. Lo dibuja el gateway con los datos de SQLite, así que no gasta créditos ni datos de Ubidots.
- `/envivo`: **fija el dashboard arriba del chat** y el gateway lo actualiza solo cada 60 s, y de inmediato cuando cambia el estado. Así queda siempre a la vista al abrir el chat. `/detener` lo quita.
- `/grafica`: versión rápida, solo nivel y riesgo de la última hora.
- `/tablero`: enlace al tablero de Ubidots, que pide iniciar sesión, así que sigue siendo privado. Hay que pegar el enlace en `UBIDOTS_TABLERO_URL` del `gateway.env`.
- `/stop`: dejar de recibir alertas.

> Telegram deja que **un solo programa** lea los mensajes de un bot: si el gateway corre en dos equipos con el mismo token, uno de los dos falla (error 409).

Recomendación: en Ubidots, dejar los eventos con **Email**, que no tiene ese cupo, y usar Telegram para el celular.

## 7. Flashear el ESP32

1. En `firmware/wrews/`, copiar `secrets.example.h` como `secrets.h`. Si ya lo tenían del Challenge #2, solo agreguen el bloque MQTT del final.
2. Llenar `MQTT_HOST` con el **nombre de la Pi en la red**, por ejemplo `"wrews-gw.local"`. Conviene darle a la Pi un nombre único, porque en la universidad puede haber varias «raspberrypi»: `sudo hostnamectl set-hostname wrews-gw && sudo reboot`. Así el ESP32 la encuentra aunque el hotspot le cambie la IP. Si el hotspot bloquea los nombres `.local`, usar la IP (paso 1.3). Además: `MQTT_USER "esp32"` y `MQTT_PASS` con la clave del paso 3. La clave de Claude **no** va aquí.
3. Compilar y subir. Se probó con `arduino-cli` y el core esp32 3.3.12: ocupa el 89 % de la flash con el esquema de particiones por defecto.
4. En el monitor serial (115200) deben verse `Tarea MQTT en el nucleo 0 -> 192.168.X.X:1883` y `MQTT: conectado`.
   - `fallo (estado 5)`: el usuario o la clave están mal.
   - `estado -2`: el ESP32 no llega a la IP (otra red, IP equivocada o broker apagado).
5. En la terminal con `mosquitto_sub` aparecen `wrews/wrews-01/telemetria` cada 5 s, además de `estado` y `eventos`.
6. El tablero local (`http://IP-del-ESP32`) ahora tiene la tarjeta **«Recomendación del módulo de IA»** y el estado del enlace con el gateway. Pulsen **«Activar avisos»** al abrirlo para que el navegador permita el sonido. En CRÍTICO y FALLO el aviso se repite hasta pulsar «Entendido».

## 8. Pruebas de extremo a extremo (para la wiki y el video)

Anoten la hora y saquen captura de cada una. Los comandos SQL van dentro de `sudo sqlite3 /var/lib/wrews/wrews.db` (salir con `.quit`).

| # | Prueba | Cómo | Resultado esperado |
|---|---|---|---|
| 1 | Datos llegan a SQLite | Dejar correr 2 min | `SELECT COUNT(*), MAX(datetime(ts_ms/1000,'unixepoch','localtime')) FROM mediciones;` crece cada 5 s |
| 2 | Se guarda antes de reenviar | `SELECT COUNT(*) FROM cola_nube WHERE enviado_ms IS NULL;` | 0 o pocos con Internet; todo lo que llegó a Ubidots pasó antes por SQLite |
| 3 | Escalada a PRECAUCIÓN y CRÍTICO | Bajar el nivel en la maqueta | Alarma local, cambio en el tablero local y en Ubidots, correo del evento |
| 4 | Silenciar desde Ubidots | Con la alarma sonando, activar el switch `silenciar` | El buzzer calla (los LEDs siguen) y el switch vuelve solo a 0. El tablero local muestra el evento «Buzzer silenciado 15 min desde Ubidots (MQTT)». `SELECT * FROM comandos;` muestra la orden y la respuesta |
| 5 | Silenciar desde la Pi | `sudo bash -c 'set -a; . /etc/wrews/gateway.env; cd /opt/wrews/gateway; /opt/wrews/venv/bin/python -m wrews_gw.comando silenciar'` | Imprime la respuesta del ESP32 (`ok: 0` si no había nada que silenciar) |
| 6 | Recomendación de la IA | Escribir `/recomendacion` en el bot | Aparece en el tablero local, en el *context* de `ia_min_critico` en Ubidots y en `SELECT datetime(ts_ms/1000,'unixepoch','localtime'), proveedor, min_a_critico, texto FROM ia ORDER BY id DESC LIMIT 3;` |
| 7 | Se cae Internet | Quitar los datos móviles del hotspot 3 min (la WLAN sigue) y luego devolverlos | La alarma local y el tablero local siguen. El log dice `Ubidots: desconectado` y la IA pasa a `reglas`. La cola crece (prueba 2) y, en menos de 15 s después de volver, se vacía. En Ubidots el hueco se llena con la hora real |
| 8 | Se apaga el ESP32 | Desconectarlo | En ~20 s: evento «Sin datos del ESP32», `estado` = 3 en Ubidots con `origen: gateway`, `gw_calidad` = 0 y el correo de FALLO |
| 9 | Se cae el broker | `sudo systemctl stop mosquitto` 1 min, luego `sudo systemctl start mosquitto` | El ESP32 sigue alarmando local y el tablero local muestra «Gateway MQTT: desconectado». Ubidots pasa a FALLO (`origen: gateway`), porque la nube deja de ver al equipo. Al volver, el ESP32 (en ≤ 30 s) y el gateway (en ≤ 5 s) se reconectan solos, el ESP32 publica los eventos pendientes y el estado vuelve al real |
| 10 | Latencia ESP32 → Ubidots | Cambiar el estado y medir con cronómetro hasta que cambia en Ubidots | Estado: 1 a 3 s (se envía al instante). Variables medidas: hasta 60 s, por la ventana de agregación (es a propósito) |
| 11 | Acceso restringido | Probar `mosquitto_pub` sin clave (paso 3.1) y abrir el tablero de Ubidots en una ventana privada | Rechazado en los dos casos |

## 9. Si algo falla

1. **Log del gateway:** `journalctl -u wrews-gateway -n 100 --no-pager`
2. **Log de Mosquitto:** `sudo tail -n 50 /var/log/mosquitto/mosquitto.log`
3. **¿El ESP32 llega a la Pi?** Desde la Pi: `ping IP_DEL_ESP32`. Si no responde, no están en la misma red o el hotspot aísla a los clientes (algunos celulares lo hacen: probar con otro).
4. **Ver lo que pasa por el broker:** la terminal con `mosquitto_sub` del paso 3.1.
5. **Empezar de cero la base de datos** (por ejemplo, después del simulador): `sudo systemctl stop wrews-gateway && sudo rm /var/lib/wrews/wrews.db* && sudo systemctl start wrews-gateway`.
6. **Actualizar el código** después de un cambio en el repo: `cd ~/sistema-alerta-temprana-riesgo-hidrico && git pull && cd gateway && sudo ./instalar.sh && sudo systemctl restart wrews-gateway`. No borra claves ni datos.
7. **La IA siempre dice `reglas`:** correr el `--probar` del paso 4 y leer la línea `ERROR`.

## Referencia rápida de tópicos MQTT

| Tópico | Sentido | Contenido |
|---|---|---|
| `wrews/wrews-01/telemetria` | ESP32 → gateway | JSON cada 5 s: nivel, tasa, riesgo, idx_evap, et, temp, hum, pres, vpd, irr, estado, severidades, rssi |
| `wrews/wrews-01/estado` | ESP32 → gateway | JSON al cambiar (retenido) |
| `wrews/wrews-01/eventos` | ESP32 → gateway | JSON por evento (id, boot, gravedad, texto) |
| `wrews/wrews-01/disponibilidad` | ESP32 / broker | `online` / `offline` (última voluntad, retenido) |
| `wrews/wrews-01/cmd` | gateway → ESP32 | `{"accion":"silenciar","origen":"Ubidots"}` (también `ping`) |
| `wrews/wrews-01/cmd/resp` | ESP32 → gateway | `{"accion":"silenciar","ok":1,...}` |
| `wrews/wrews-01/ia` | gateway | JSON completo de la predicción y la recomendación (retenido) |
| `wrews/wrews-01/ia/texto` | gateway → ESP32 | Recomendación en texto plano (retenido) |
| `wrews/wrews-01/gateway` | gateway | `online` / `offline` |
| `/v1.6/devices/wrews-01` | gateway → Ubidots | Variables con marca de tiempo |
| `/v1.6/devices/wrews-01/silenciar` | Ubidots → gateway | Valor del switch con su marca de tiempo (solo se ejecutan órdenes de menos de 2 min) |

Tablas de SQLite: `mediciones`, `estados`, `eventos`, `comandos`, `agregados`, `ia` y `cola_nube`. La tabla `ia` guarda el prompt exacto enviado a Claude, útil para la declaración de uso de IA. El esquema comentado está en `gateway/wrews_gw/almacen.py`.
