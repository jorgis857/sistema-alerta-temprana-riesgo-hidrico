// ============================================================================
//  WREWS - Plantilla de credenciales
//  Copie este archivo como secrets.h, en la misma carpeta que wrews.ino, y
//  complete los datos. secrets.h esta en .gitignore: nunca se sube al repo.
// ============================================================================
#pragma once

// WLAN de la zona (en la demo, el hotspot del celular). Solo 2.4 GHz: el
// ESP32 no se conecta a redes de 5 GHz.
#define WIFI_SSID "nombre-de-la-red"
#define WIFI_PASS "clave-de-la-red"

// Segunda red, OPCIONAL (por ejemplo, el hotspot de otro integrante). El
// equipo se une a la que encuentre con mejor senal y, si una se cae, prueba
// con la otra. Para usar una sola red, borre o comente estas dos lineas.
#define WIFI_SSID_2 "nombre-de-la-otra-red"
#define WIFI_PASS_2 "clave-de-la-otra-red"

// Usuario y clave del tablero de control
#define WEB_USER  "alcaldia"
#define WEB_PASS  "cambie-esta-clave"

// ---- MQTT hacia el gateway (Challenge 3) ---------------------------------
// Gateway dentro de la MISMA red Wi-Fi. Puede ser su nombre en la red
// ("wrews-gw.local": conviene un nombre unico, ver docs/DIA_U_Y_VIDEO.md):
// asi el ESP32 lo encuentra aunque el hotspot le cambie la IP. Tambien sirve
// la IP fija (en la Pi: hostname -I), si el hotspot bloquea el mDNS.
// Usuario y clave son los que se crearon con mosquitto_passwd para el ESP32
// (ver docs/GUIA_DESPLIEGUE_PI.md, paso 3). Si borra MQTT_HOST, el equipo
// funciona como la v7, sin MQTT.
#define MQTT_HOST "wrews-gw.local"
#define MQTT_PORT 1883
#define MQTT_USER "esp32"
#define MQTT_PASS "clave-del-esp32-en-mosquitto"
// Identificador del equipo: va en los topicos (wrews/<DEVICE_ID>/...)
#define DEVICE_ID "wrews-01"
