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

// Usuario y clave del tablero de control
#define WEB_USER  "alcaldia"
#define WEB_PASS  "cambie-esta-clave"
