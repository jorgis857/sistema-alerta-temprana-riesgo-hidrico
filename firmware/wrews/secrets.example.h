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
