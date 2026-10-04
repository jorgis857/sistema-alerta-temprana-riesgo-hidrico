// ============================================================================
//  WREWS - Water Risk Early Warning System
//  Firmware del prototipo funcional  ·  v7
//  Challenge #2 - Internet de las Cosas - Universidad de La Sabana - 2026-2
//  v7: tablero de control web en la WLAN (servidor embebido, sesiones,
//      historial y eventos) y medicion en su propia tarea de FreeRTOS.
//  v6: el indice evaporativo pasa a ser evaporacion potencial diaria con
//      Priestley-Taylor (1972) y parametros FAO-56 (Allen et al., 1998).
// ----------------------------------------------------------------------------
//  Monitorea el nivel de un reservorio junto con las variables meteorologicas
//  que gobiernan la evaporacion, fusiona las tres senales en un indice de
//  riesgo hidrico y emite alerta LOCAL (LCD + LEDs + buzzer) que no depende
//  de la red. Ademas publica un tablero de control web dentro de la WLAN de
//  la zona (valor actual, historico, eventos y silencio de la alarma).
//
//  ARCHIVOS: wrews.ino (este), tablero.h (paginas web), secrets.h (red y
//  clave del tablero; no se sube, ver secrets.example.h).
//
//  PARAMETROS DEL BANCO DE PRUEBAS
//  Las constantes de tiempo y las escalas de tasa corresponden a la maqueta
//  de laboratorio, donde el nivel se mueve a mano en segundos. Los valores
//  equivalentes para un reservorio real y su justificacion estan en la wiki;
//  no se incluyen aqui porque no fueron validados experimentalmente.
//
//  REFERENCIAS
//  Los corchetes citan dos hojas complementarias del equipo:
//    [Ev n] "WREWS: referencias del modelo de evaporacion
//            (Priestley-Taylor + FAO-56)". Reemplaza las secciones 2 y 6 de
//            la hoja de pesos.
//    [Pe n] "WREWS: de donde salen las formulas, los pesos y los umbrales".
//            Vigente para todo lo demas.
//  Las mas usadas:
//    [Ev 1] Priestley y Taylor, Mon. Weather Rev., 1972.
//    [Ev 2] = [Pe 1] Allen et al., FAO-56, 1998.
//    [Ev 5] = [Pe 2] Rhiat et al., panel como piranometro, 2023.
//    [Pe 5] Saaty, AHP, 1990.   [Pe 7][Pe 8] Planes Especiales de Sequia.
//  "Supuesto" marca los valores sin fuente directa, declarados en la wiki.
//
//  Librerias: Adafruit BME280 / Adafruit Unified Sensor / Adafruit INA219 /
//             LiquidCrystal I2C (Frank de Brabander)
// ============================================================================

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_INA219.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <stdarg.h>
#include "tablero.h"

// Red y usuario del tablero. secrets.h NO se sube al repositorio: se crea
// copiando secrets.example.h y llenando los datos del hotspot.
#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "Falta secrets.h: copie secrets.example.h como secrets.h junto a wrews.ino y complete la red y la clave"
#endif

// ===========================================================================
//  PINES Y POLARIDAD
// ===========================================================================
const uint8_t PIN_SDA      = 21;
const uint8_t PIN_SCL      = 22;
const uint8_t PIN_TRIG     = 5;
const uint8_t PIN_ECHO     = 18;
const uint8_t PIN_LED_V    = 25;
const uint8_t PIN_LED_A    = 26;
const uint8_t PIN_LED_R    = 27;
const uint8_t PIN_BUZZER   = 19;

#define LED_ON      LOW      // LEDs en anodo comun
#define LED_OFF     HIGH
const int BUZZER_HZ = 2500;  // buzzer PASIVO: necesita PWM, no continua

// ===========================================================================
//  CALIBRACION DEL RECIPIENTE
//  Por debajo de ~5 cm el HC-SR04 [Pe 17] es poco fiable: el transductor sigue
//  resonando por su propio pulso cuando ya vuelve el eco. D_LLENO = 3 cm
//  esta dentro de esa zona; queda documentado como limitacion conocida.
// ===========================================================================
float D_LLENO_CM = 3.0;
float D_VACIO_CM = 20.0;

// ===========================================================================
//  PIRANOMETRO  [Ev 5][Ev 6]
//  La corriente de cortocircuito de una celda es lineal con la irradiancia
//  [Ev 5]. El shunt de 0.1 ohm del INA219 [Ev 6] mantiene el panel
//  practicamente en corto, que es la condicion donde esa linealidad se cumple.
//  K_PANEL = 1000 W/m2 / I a pleno sol, con los 100 mA de la etiqueta.
//  TODO calibrar con sol (no con la lampara halogena, otro espectro) contra un
//  piranometro o estacion, regresion por el origen: la etiqueta suele dar Imp,
//  no Isc, y el K real quedaria cerca de 9-9.5 [Ev sec. 4].
// ===========================================================================
const float K_PANEL_WM2_POR_MA = 10.0;
float OFFSET_PANEL_MA  = 0.0;   // cero de oscuridad, medido al arrancar

// Una corriente de reposo mayor que esto no es error del INA219 sino luz
// sobre el panel al encender: tomarla como cero restaria esa luz de todas
// las lecturas. 1 mA = 10 W/m2, muy por encima del offset tipico del sensor.
const float OFFSET_MAX_MA = 1.0;

// ===========================================================================
//  EVAPORACION POTENCIAL: PRIESTLEY-TAYLOR + FAO-56  [Ev 1][Ev 2]
//  Supuestos (documentados tambien en la wiki):
//  - Superficie de agua libre sin efecto oasis [Ev 1]. El sitio objetivo es
//    un embalse; el banco de pruebas no cumple este supuesto y solo valida la
//    cadena de calculo, no el valor absoluto de evaporacion.
//  - G = 0 a escala diaria. Supuesto: [Ev 2] ec. 42 lo justifica para suelo;
//    en agua profunda [Ev 7][Ev 8] advierten lo contrario.
//  - Rnl con FAO-56 ec. 39 [Ev 2] (calibrada para tierra) sobre agua:
//    aproximacion habitual, declarada.
//  - Ra fijo para latitud ~4.9 N: error < 3 % en ET a lo largo del ano [Ev 2].
//  - En modo demo la ventana comprimida representa un dia; sus valores no son
//    comparables 1 a 1 con los de campo (en la demo no hay noche). Supuesto.
//  Pendiente: mover estas constantes al archivo de configuracion en LittleFS.
// ===========================================================================
const float ALPHA_PT      = 1.26;      // [Ev 1] agua libre sin adveccion; [Ev 10] da 1.11 en tropico de altura
const float ALBEDO_AGUA   = 0.06;      // [Ev 4]; [Ev 8] midio 0.041 y 0.079
const float LAMBDA_MJ_KG  = 2.45;      // [Ev 2] calor latente a ~20 C
const float SIGMA_MJ      = 4.903e-9;  // [Ev 2] ec. 39, MJ K^-4 m^-2 dia^-1
const float ALTITUD_M     = 2560.0;    // [Ev 2] ec. 37, SOLO para Rso: gamma usa la P medida
const float RA_FIJO_MJ    = 36.0;      // [Ev 2] ec. 21 y anexo 2, MJ/m2 dia

// ET de un dia despejado del sitio (Rs = Rso, T 16 C [22/8], HR 65 %,
// P 75 kPa) con este mismo modelo [Ev 1][Ev 2]: 7.48 mm/dia. Asi el indice
// es la fraccion de la demanda evaporativa maxima posible [Ev sec. 6].
const float ET_REF_MM_DIA = 7.5;

// Escala diaria: ventana movil de 24 h [Ev 1][Ev 2]
const bool     MODO_DEMO       = true;
const uint32_t VENTANA_CAMPO_S = 86400;  // 24 h
const uint32_t VENTANA_DEMO_S  = 120;    // TODO ajustar: "un dia" comprimido. Supuesto
const uint8_t  NUM_BUCKETS     = 24;
const float    COBERTURA_MIN   = 0.5;    // TODO: fraccion minima de ventana. Supuesto

// Fusion del indice evaporativo (opcion 2 de [Ev sec. 7]). El peso del VPD
// es el reparto aerodinamico de Penman gamma/(D+gamma) [Ev 2] a 16 C y
// 75 kPa (0.30); [Ev 7] respalda que ese termino importa a escala de dias.
// El VPD se lee como senal de variacion diaria, no como evaporacion que se
// suma: ALPHA_PT ya incluye en promedio la parte aerodinamica.
const float W_PT        = 0.7;
const float W_VPD       = 0.3;
const float VPD_REF_KPA = 2.0;    // Supuesto: pico realista en la Sabana, es(24C)=2.98

// ===========================================================================
//  PESOS DEL INDICE DE RIESGO  [Pe 5][Pe 6]
//  Vector de pesos del AHP de Saaty [Pe 5] con la matriz de [Pe sec. 3]
//  (nivel 2x evaporacion, 3x tasa; evaporacion 2x tasa): CR = 0.008 < 0.10.
//  Mismo metodo que el indice compuesto de sequia de [Pe 6].
// ===========================================================================
const float W_NIVEL = 0.54;   // disponibilidad actual: la variable de estado
const float W_EVAP  = 0.30;   // forzante externo dominante en El Nino
const float W_TASA  = 0.16;   // tendencia: la senal mas ruidosa de las tres

// ===========================================================================
//  UMBRALES
//  Nivel: fases de los Planes Especiales de Sequia de Espana [Pe 7][Pe 8]
//  (prealerta 0.50, emergencia 0.15); caso Chingaza 2024 en 16.5 % [Pe 9].
//  Riesgo: derivado de los de nivel [Pe sec. 5], estilo CDI europeo [Pe 11]:
//    PREC = W_NIVEL*(100-50) + W_EVAP*20 + W_TASA*20 = 36.2
//    CRIT = W_NIVEL*(100-15) + W_EVAP*60 + W_TASA*33 = 69.2
//  Evaporacion: el 100 % tiene base fisica (ET_REF); 60 / 85 son Supuesto.
//    TODO cerrarlos con percentiles 80 / 95 de una estacion IDEAM, metodo
//    del US Drought Monitor [Pe 10].
//  Tasa: calibracion experimental. Dos maniobras controladas de descenso
//  continuo dieron 46.9 pp/min (lenta) y 98.2 pp/min (rapida).
//  PRECAUCION = 70% de la lenta;  CRITICO = media geometrica de ambas, que
//  reparte el margen relativo por igual entre las dos maniobras.
// ===========================================================================
const float U_CRIT_NIVEL  = 15.0,  U_PREC_NIVEL  = 50.0;   // %
const float U_CRIT_RIESGO = 69.2,  U_PREC_RIESGO = 36.2;   // 0-100
const float U_CRIT_EVAP   = 85.0,  U_PREC_EVAP   = 60.0;   // 0-100
const float U_CRIT_TASA   = 68.0,  U_PREC_TASA   = 33.0;   // pp/min
const float TASA_REF      = 100.0;                          // pp/min

// ===========================================================================
//  TEMPORIZACION Y VENTANA
// ===========================================================================
const unsigned long T_MUESTREO_MS = 1000;
const unsigned long T_PAGINA_MS   = 2500;
const uint8_t VENTANA_N    = 20;   // 20 s de historia para la pendiente
const uint8_t MIN_MUESTRAS = 6;
// Confirmacion asimetrica: retardos de alarma de ANSI/ISA-18.2 [Pe 3]
const uint8_t CONF_SUBIR   = 2;    // ciclos para escalar de estado
const uint8_t CONF_BAJAR   = 3;    // ciclos para desescalar

// Cambio de nivel en una sola muestra que se interpreta como discontinuidad.
// 8 pp sobre este recorrido equivalen a 1.4 cm/s: por encima de eso el
// movimiento se clasifica como reposicionamiento, no como descenso.
const float SALTO_DISCONTINUIDAD_PP = 8.0;

// Banda muerta de la tasa [Pe 3][Pe 4]: se calcula sola al arrancar a partir del ruido
// medido. BANDA_MANUAL es el respaldo si la caracterizacion sale contaminada.
const bool  BANDA_AUTO   = true;
const float BANDA_MANUAL = 5.0;   // pp/min
float BANDA_MUERTA       = 5.0;

// ===========================================================================
//  OBJETOS Y ESTADO
// ===========================================================================
Adafruit_BME280    bme;
Adafruit_INA219    ina(0x40);
LiquidCrystal_I2C *lcd = NULL;

bool hay_lcd = false, hay_bme = false, hay_ina = false;
uint8_t addr_lcd = 0, addr_bme = 0, addr_ina = 0;

float distancia_cm = NAN, nivel_pct = NAN, nivel_anterior = NAN;
float temp_c = NAN, hum_pct = NAN, pres_hpa = NAN, vpd_kpa = NAN;
float corriente_ma = NAN, irradiancia = 0;
float idx_evap = 0, tasa_ppm = 0, riesgo = 0, tasa_max = 0;
float ruido_dist_cm = 0, ruido_nivel_pp = 0;
bool  ultra_ok = false;

uint8_t s_nivel = 0, s_evap = 0, s_tasa = 0, s_riesgo = 0;  // severidades 0/1/2

// ---- Ventana movil de la evaporacion ------------------------------------
// 24 h a 1 Hz serian 86 400 muestras: no caben junto al servidor web. Cada
// bucket resume VENTANA/NUM_BUCKETS segundos y el arreglo es circular.
struct Bucket {
  float energia_rs_mj;           // suma de Rs*dt / 1e6
  float suma_t, suma_hr, suma_p; // P en kPa
  float t_max, t_min;
  float duracion_s;              // tiempo efectivamente cubierto
  uint16_t n_muestras;
};

struct Ventana {
  uint32_t duracion_s;
  Bucket   b[NUM_BUCKETS];
  uint8_t  i;                    // bucket que se esta llenando
};

struct ResultadoPT {
  float rs_dia_mj, rn_mj, delta, gamma, frac_pt, ea_kpa, et_mm_dia;
};

const uint8_t EVAP_CALCULANDO = 0, EVAP_OK = 1;
const char *NOMBRE_EVAP[2] = { "CALCULANDO", "OK" };

Ventana     ventana_evap;
ResultadoPT pt = { 0, 0, 0, 0, 0, 0, 0 };
uint8_t     estado_evap = EVAP_CALCULANDO;
float       cobertura_ventana = 0;
unsigned long t_evap_prev = 0;

float    buf_nivel[VENTANA_N];
uint32_t buf_t[VENTANA_N];
uint8_t  buf_n = 0, buf_i = 0;

const uint8_t EST_NORMAL = 0, EST_PRECAUCION = 1, EST_CRITICO = 2, EST_FALLO = 3;
const char *NOMBRE_EST[4] = { "NORMAL", "PRECAUCION", "CRITICO", "FALLO" };

uint8_t estado = EST_NORMAL, estado_silenciado = EST_NORMAL;
uint8_t conf_contador = 0;
bool    silenciado = false;
unsigned long t_silencio = 0;
const unsigned long SILENCIO_MS = 15UL * 60UL * 1000UL;

//                     LED per,  on, BUZ per,  on
const uint16_t PAT[4][4] = {
  { 1000, 1000,    0,   0 },   // NORMAL      verde fijo, silencio
  { 1000, 1000, 4000, 150 },   // PRECAUCION  amarillo fijo, toque grave
  {  400,  200, 1200, 250 },   // CRITICO     rojo parpadea, pitido insistente
  {  600,  300, 3000, 120 }    // FALLO       los tres juntos, tono muy grave
};
//                       NORMAL  PREC  CRIT  FALLO
const int BUZ_HZ[4]  = {      0, 1000, 2500,  600 };

unsigned long t_pagina = 0;
uint8_t pagina = 0;
const uint8_t N_PAGINAS = 7;
unsigned long t_ultima_muestra = 0;    // millis() de la ultima muestra

// ---- Historial reciente (tablero) --------------------------------------
// Un punto cada HIST_CADA muestras: 300 puntos x 2 s = 10 min de historia,
// suficiente para ver una maniobra completa del banco de pruebas.
struct PuntoHist {
  uint32_t t_s;
  float nivel, riesgo, evap, tasa, temp, hum, irr;
  uint8_t estado;
};
const uint16_t N_HIST    = 300;
const uint8_t  HIST_CADA = 2;
PuntoHist hist[N_HIST];
uint16_t  hist_n = 0, hist_i = 0;
uint8_t   hist_cont = 0;

// ---- Eventos (notificaciones del tablero) ------------------------------
// gravedad: 0 informacion, 1 precaucion, 2 critico / fallo
struct Evento {
  uint32_t id, t_ms;
  uint8_t  gravedad;
  char     texto[64];
};
const uint8_t N_EVENTOS = 24;
Evento   eventos[N_EVENTOS];
uint8_t  ev_i = 0;
uint32_t ev_sig = 1;                   // id del proximo evento (0 = ninguno)
void registrarEvento(uint8_t gravedad, const char *fmt, ...);

// ---- Red y tablero ------------------------------------------------------
// Modo estacion (STA): el equipo se une a la WLAN de la Alcaldia (en la
// demo, el hotspot de un celular) y sirve el tablero dentro de ella.
const char *NOMBRE_HOST = "wrews";     // http://wrews.local en PC
const unsigned long WIFI_ESPERA_MS     = 15000;  // espera inicial en setup
const unsigned long WIFI_REINTENTO_MS  = 10000;  // reintento si se cae
WebServer servidor(80);
bool      wifi_ok = false;             // solo se usan desde loop()
char      ip_txt[16] = "0.0.0.0";
unsigned long t_reintento_wifi = 0;
uint16_t  reconexiones_wifi = 0;
bool      mdns_ok = false;

// Sesiones del tablero: token aleatorio en una cookie HttpOnly.
struct Sesion { char token[33]; unsigned long t_ms; bool activa; };
const uint8_t N_SESIONES = 4;
const unsigned long SESION_MS = 12UL * 3600UL * 1000UL;   // 12 h
Sesion sesiones[N_SESIONES];
uint8_t fallos_login = 0;
unsigned long t_bloqueo_login = 0;
const uint8_t MAX_FALLOS_LOGIN = 5;
const unsigned long BLOQUEO_LOGIN_MS = 30000;

// ---- Concurrencia -------------------------------------------------------
// Tres hilos (requisito del Challenge 2: medir fuera del hilo principal):
//   tareaMedicion  nucleo 0  sensores, modelo, estado, historial
//   tareaAlarmas   nucleo 1  LEDs y buzzer cada 10 ms
//   loop()         nucleo 1  servidor web, Wi-Fi y LCD
// Las alarmas van aparte del servidor a proposito: un cliente lento o una
// caida de la WLAN no pueden congelar la alarma fisica.
//   mtx_estado protege TODAS las variables de estado de arriba (menos las
//              de red y sesiones, que solo toca loop()).
//   mtx_i2c    protege el bus I2C (LCD, BME280 e INA219 lo comparten).
// Orden fijo para no bloquearse: nunca tomar mtx_i2c teniendo mtx_estado.
// Ninguna ISR: el I2C y la coma flotante no deben ir dentro de una ISR.
SemaphoreHandle_t mtx_estado = NULL, mtx_i2c = NULL;
TaskHandle_t      tarea_medicion = NULL, tarea_alarmas = NULL;
const uint32_t    PILA_MEDICION  = 8192;   // printf con floats usa varios kB
const uint32_t    PILA_ALARMAS   = 4096;
const UBaseType_t PRIO_MEDICION  = 2;      // por encima de loop() (1)
const UBaseType_t PRIO_ALARMAS   = 2;
const BaseType_t  NUCLEO_MEDICION = 0, NUCLEO_ALARMAS = 1;

void bloquear(SemaphoreHandle_t m) { xSemaphoreTake(m, portMAX_DELAY); }
void liberar(SemaphoreHandle_t m)  { xSemaphoreGive(m); }

// Agrega un evento al registro circular que lee el tablero y lo repite por
// el monitor serial. Se llama con mtx_estado tomado.
void registrarEvento(uint8_t gravedad, const char *fmt, ...) {
  Evento &e = eventos[ev_i];
  e.id = ev_sig++;
  e.t_ms = millis();
  e.gravedad = gravedad;
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(e.texto, sizeof(e.texto), fmt, ap);
  va_end(ap);
  ev_i = (ev_i + 1) % N_EVENTOS;
  Serial.printf(">>> [%lu] %s\n", (unsigned long)e.id, e.texto);
}

// Un punto de historia cada HIST_CADA muestras. Se llama con mtx_estado tomado.
void guardarHistorial() {
  if (++hist_cont < HIST_CADA) return;
  hist_cont = 0;
  PuntoHist &h = hist[hist_i];
  h.t_s    = millis() / 1000;
  h.nivel  = nivel_pct;
  h.riesgo = riesgo;
  h.evap   = idx_evap;
  h.tasa   = tasa_ppm;
  h.temp   = temp_c;
  h.hum    = hum_pct;
  h.irr    = irradiancia;
  h.estado = estado;
  hist_i = (hist_i + 1) % N_HIST;
  if (hist_n < N_HIST) hist_n++;
}

// ===========================================================================
//  SENSORES
// ===========================================================================

// Mediana de 5. El HC-SR04 no falla con desviaciones pequenas alrededor del
// valor bueno: falla con lecturas absurdas (ecos falsos, pulsos perdidos).
// El promedio se contamina con ellas; la mediana las descarta.
float leerDistancia() {
  const uint8_t N = 5;
  float v[N];
  for (uint8_t i = 0; i < N; i++) {
    digitalWrite(PIN_TRIG, LOW);  delayMicroseconds(4);
    digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);
    unsigned long us = pulseIn(PIN_ECHO, HIGH, 30000UL);
    v[i] = (us == 0) ? -1.0 : (us * 0.0343 / 2.0);
    delay(12);
  }
  for (uint8_t i = 1; i < N; i++) {
    float k = v[i]; int8_t j = i - 1;
    while (j >= 0 && v[j] > k) { v[j+1] = v[j]; j--; }
    v[j+1] = k;
  }
  return v[N/2];
}

float distanciaANivel(float d) {
  return constrain(100.0 * (D_VACIO_CM - d) / (D_VACIO_CM - D_LLENO_CM),
                   0.0, 100.0);
}

// FAO-56 [Pe 1] = [Ev 2]: ec. 11 (Tetens), 17, 8 y 13
float esSat(float t)             { return 0.6108 * exp((17.27*t)/(t+237.3)); }
float calcVPD(float t, float hr) { return esSat(t) * (1.0 - hr/100.0); }
float gammaPsi(float p_kpa)      { return 0.665e-3 * p_kpa; }
float deltaSat(float t)          { return 4098.0 * esSat(t) / sq(t + 237.3); }

// ===========================================================================
//  EVAPORACION POTENCIAL
// ===========================================================================
void ventanaReiniciar(Ventana &v, uint32_t duracion_s) {
  v.duracion_s = duracion_s;
  v.i = 0;
  memset(v.b, 0, sizeof(v.b));
}

// Corre en el ciclo de medicion, nunca en una ISR: hay coma flotante.
void ventanaAcumular(Ventana &v, float rs_wm2, float t, float hr,
                     float p_kpa, float dt_s) {
  Bucket &b = v.b[v.i];
  if (b.n_muestras == 0) { b.t_max = t; b.t_min = t; }
  b.energia_rs_mj += rs_wm2 * dt_s / 1e6;
  b.suma_t  += t;
  b.suma_hr += hr;
  b.suma_p  += p_kpa;
  if (t > b.t_max) b.t_max = t;
  if (t < b.t_min) b.t_min = t;
  b.duracion_s += dt_s;
  b.n_muestras++;

  // Bucket lleno: avanzar y reiniciar el siguiente, que es el mas antiguo
  if (b.duracion_s >= (float)v.duracion_s / NUM_BUCKETS) {
    v.i = (v.i + 1) % NUM_BUCKETS;
    memset(&v.b[v.i], 0, sizeof(Bucket));
  }
}

// ---------------------------------------------------------------------------
//  Priestley-Taylor con parametros FAO-56, a escala diaria.
//  Ra va como argumento para poder probar con los vectores de referencia.
//  Presion en kPa, temperaturas en C, HR en %.
// ---------------------------------------------------------------------------
ResultadoPT priestleyTaylor(float rs_dia, float t, float t_max, float t_min,
                            float hr, float p_kpa, float ra) {
  ResultadoPT r;
  r.rs_dia_mj = rs_dia;
  r.delta     = deltaSat(t);                                    // kPa/C, [Ev 2] ec. 13
  r.gamma     = gammaPsi(p_kpa);                                // kPa/C, [Ev 2] ec. 8
  r.frac_pt   = r.delta / (r.delta + r.gamma);
  r.ea_kpa    = (hr / 100.0) * (esSat(t_max) + esSat(t_min)) / 2.0;  // [Ev 2] ec. 19

  float rso = (0.75 + 2e-5 * ALTITUD_M) * ra;                   // cielo despejado, [Ev 2] ec. 37
  // Maximo 1.0 por [Ev 2]. El minimo de 0.3 es Supuesto propio: evita un
  // termino de nubes negativo sin luz (lampara apagada en la demo).
  float rel = constrain(rs_dia / rso, 0.3, 1.0);
  float rns = (1.0 - ALBEDO_AGUA) * rs_dia;                     // [Ev 2] ec. 38

  float tk_max = t_max + 273.15, tk_min = t_min + 273.15;
  float rnl = SIGMA_MJ * ((sq(sq(tk_max)) + sq(sq(tk_min))) / 2.0)   // [Ev 2] ec. 39
            * (0.34 - 0.14 * sqrt(r.ea_kpa)) * (1.35 * rel - 0.35);

  r.rn_mj = max(rns - rnl, 0.0f);
  const float G = 0.0;                     // escala diaria, [Ev 2] ec. 42. Supuesto en agua
  float lambda_et = ALPHA_PT * r.frac_pt * (r.rn_mj - G);       // MJ/m2 dia, [Ev 1]
  r.et_mm_dia = lambda_et / LAMBDA_MJ_KG;
  return r;
}

// ---------------------------------------------------------------------------
//  Agrega la ventana y calcula ET. Devuelve la cobertura (0-1); con poca
//  cobertura no hay estimacion y el resultado queda en cero.
//  El equivalente diario Rs_dia = E * 86400 / t_cubierto permite usar
//  ventanas cortas (demo) e incompletas (recien encendido).
// ---------------------------------------------------------------------------
float evaluarVentana(const Ventana &v, ResultadoPT &r) {
  float energia = 0, st = 0, shr = 0, sp = 0, cubierto = 0;
  float t_max = -1e9, t_min = 1e9;
  uint32_t n = 0;
  for (uint8_t k = 0; k < NUM_BUCKETS; k++) {
    const Bucket &b = v.b[k];
    if (b.n_muestras == 0) continue;
    energia  += b.energia_rs_mj;
    st += b.suma_t;  shr += b.suma_hr;  sp += b.suma_p;
    n        += b.n_muestras;
    cubierto += b.duracion_s;
    if (b.t_max > t_max) t_max = b.t_max;
    if (b.t_min < t_min) t_min = b.t_min;
  }
  float cob = min(cubierto / v.duracion_s, 1.0f);
  if (n == 0 || cob < COBERTURA_MIN) {
    r = ResultadoPT{ 0, 0, 0, 0, 0, 0, 0 };
    return cob;
  }
  float rs_dia = energia * 86400.0 / cubierto;
  r = priestleyTaylor(rs_dia, st / n, t_max, t_min, shr / n, sp / n, RA_FIJO_MJ);
  return cob;
}

// Fusion PT + VPD en el indice 0-100 que consume el riesgo.
float indiceEvaporativo(float et_mm_dia, float vpd) {
  float norm_pt  = constrain(et_mm_dia / ET_REF_MM_DIA, 0.0, 1.0);
  float norm_vpd = isnan(vpd) ? 0.0 : constrain(vpd / VPD_REF_KPA, 0.0, 1.0);
  return 100.0 * (W_PT * norm_pt + W_VPD * norm_vpd) / (W_PT + W_VPD);
}

// ---------------------------------------------------------------------------
//  Pendiente por minimos cuadrados sobre la ventana, en pp/MINUTO.
//  Tiempo RELATIVO a la muestra mas vieja y acumuladores en double: con
//  millis() absoluto en float, n*Sxx y (Sx)^2 valen casi lo mismo y su
//  diferencia se pierde por cancelacion a los pocos minutos de encendido.
//  Restar dos lecturas consecutivas seria el peor estimador posible: el error
//  de ambas entra completo. La regresion promedia el ruido de toda la ventana.
// ---------------------------------------------------------------------------
float calcularTasa() {
  if (buf_n < MIN_MUESTRAS) return 0.0;

  uint32_t t0 = buf_t[0];
  for (uint8_t k = 1; k < buf_n; k++) if (buf_t[k] < t0) t0 = buf_t[k];

  double sx = 0, sy = 0, sxy = 0, sxx = 0;
  for (uint8_t k = 0; k < buf_n; k++) {
    double x = (buf_t[k] - t0) / 60000.0;      // ms -> minutos
    double y = buf_nivel[k];
    sx += x; sy += y; sxy += x*y; sxx += x*x;
  }
  double den = (double)buf_n * sxx - sx * sx;
  if (den < 1e-9) return 0.0;

  // Signo invertido: pendiente negativa del nivel = descenso = tasa positiva
  float m = -(float)(((double)buf_n * sxy - sx * sy) / den);

  if (m < 0) return 0.0;                       // subir nunca es riesgo hidrico
  return (m < BANDA_MUERTA) ? 0.0 : m;
}

// ===========================================================================
//  CARACTERIZACION DEL RUIDO
//  Con el objetivo quieto, mide la dispersion real del montaje y de ahi
//  deriva la banda muerta. El error tipico de una pendiente por minimos
//  cuadrados sobre n puntos en un lapso T es  SE = sigma*sqrt(12)/(T*sqrt(n)).
//  La banda se fija en 3*SE: probabilidad de falso positivo bajo el 1%.
// ===========================================================================
void caracterizarRuido() {
  const uint8_t N = 20;
  float m[N];
  Serial.println(F("\n--- Caracterizacion de ruido (objetivo QUIETO) ---"));

  if (hay_lcd) {
    lcd->clear();
    lcd->setCursor(0,0); lcd->print("Midiendo ruido");
    lcd->setCursor(0,1); lcd->print("No mover...");
  }

  for (uint8_t i = 0; i < N; i++) { m[i] = leerDistancia(); delay(120); }

  float suma = 0, validas = 0;
  for (uint8_t i = 0; i < N; i++) if (m[i] > 0) { suma += m[i]; validas++; }
  if (validas < 5) {
    Serial.println(F("  Muy pocas lecturas validas; se usa la banda manual."));
    BANDA_MUERTA = BANDA_MANUAL;
    return;
  }

  float media = suma / validas, acc = 0;
  for (uint8_t i = 0; i < N; i++) if (m[i] > 0) acc += sq(m[i] - media);
  ruido_dist_cm  = sqrt(acc / (validas - 1));
  ruido_nivel_pp = 100.0 * ruido_dist_cm / (D_VACIO_CM - D_LLENO_CM);

  float T_min = (VENTANA_N * T_MUESTREO_MS) / 60000.0;
  float se    = ruido_nivel_pp * 3.4641 / (T_min * sqrt((float)VENTANA_N));
  float banda = 3.0 * se;
  if (banda < 0.3) banda = 0.3;

  Serial.printf("  distancia media   : %.2f cm\n", media);
  Serial.printf("  sigma distancia   : %.3f cm\n", ruido_dist_cm);
  Serial.printf("  sigma nivel       : %.2f pp\n", ruido_nivel_pp);
  Serial.printf("  ventana           : %.2f min, %u muestras\n", T_min, VENTANA_N);
  Serial.printf("  error de pendiente: %.2f pp/min\n", se);
  Serial.printf("  banda calculada   : %.2f pp/min\n", banda);

  BANDA_MUERTA = BANDA_AUTO ? banda : BANDA_MANUAL;

  // Tope de cordura: si alguien movio el objetivo durante la medicion, una
  // banda absurda desactivaria la deteccion de descenso sin avisar.
  if (BANDA_MUERTA > U_PREC_TASA * 0.5) {
    Serial.printf("  Banda excesiva frente al umbral PREC (%.1f): se usa %.1f\n",
                  U_PREC_TASA, BANDA_MANUAL);
    BANDA_MUERTA = BANDA_MANUAL;
  }
  Serial.printf("  BANDA MUERTA APLICADA: %.2f pp/min\n", BANDA_MUERTA);

  if (ruido_dist_cm > 0.8)
    Serial.println(F("  AVISO: sigma alto. Por debajo de 5 cm el HC-SR04\n"
                     "         entra en su zona ciega. Sube el sensor."));
  Serial.println();
}

// ===========================================================================
//  MUESTREO Y MODELO
// ===========================================================================
// Corre en la tarea de medicion. Las lecturas, que son lentas (el HC-SR04
// tarda ~100 ms), se hacen SIN el candado del estado para no frenar las
// alarmas; el candado se toma solo para actualizar las variables compartidas.
void tomarMuestra() {
  float d = leerDistancia();

  float t = NAN, h = NAN, p = NAN, i_ma = NAN;
  if (hay_bme || hay_ina) {
    bloquear(mtx_i2c);
    if (hay_bme) {
      t = bme.readTemperature();
      h = bme.readHumidity();
      p = bme.readPressure() / 100.0;
    }
    if (hay_ina) i_ma = ina.getCurrent_mA();
    liberar(mtx_i2c);
  }

  bloquear(mtx_estado);
  actualizarModelo(d, t, h, p, i_ma);
  aplicarEstado(calcularObjetivo());
  imprimirSerial();
  guardarHistorial();
  liberar(mtx_estado);
}

// Todo lo que sigue escribe estado compartido: se llama con mtx_estado tomado.
void actualizarModelo(float d, float t, float h, float p, float i_ma) {
  t_ultima_muestra = millis();
  distancia_cm = d;
  ultra_ok = (distancia_cm > 0 && distancia_cm < 400);

  if (ultra_ok) {
    nivel_pct = distanciaANivel(distancia_cm);

    // DISCONTINUIDAD en cualquiera de las dos direcciones. Un reservorio real
    // no salta: si el nivel cambia de golpe es una recarga, o en la maqueta
    // el reposicionamiento manual de la plataforma. En ambos casos la
    // tendencia previa deja de describir el sistema, y una regresion ajustada
    // sobre un escalon produce una pendiente que crece sola mientras el
    // escalon avanza por la ventana.
    if (!isnan(nivel_anterior) &&
        fabs(nivel_pct - nivel_anterior) > SALTO_DISCONTINUIDAD_PP) {
      buf_n = 0; buf_i = 0; tasa_ppm = 0;
      Serial.printf(">>> Discontinuidad de %+.1f pp: tendencia reiniciada\n",
                    nivel_pct - nivel_anterior);
    }
    nivel_anterior = nivel_pct;

    buf_nivel[buf_i] = nivel_pct;
    buf_t[buf_i]     = millis();
    buf_i = (buf_i + 1) % VENTANA_N;
    if (buf_n < VENTANA_N) buf_n++;
  } else nivel_pct = NAN;

  tasa_ppm = calcularTasa();
  if (tasa_ppm > tasa_max) tasa_max = tasa_ppm;

  if (hay_bme) {
    temp_c   = t;
    hum_pct  = h;
    pres_hpa = p;
    vpd_kpa  = calcVPD(temp_c, hum_pct);
  } else temp_c = hum_pct = pres_hpa = vpd_kpa = NAN;

  if (hay_ina) {
    corriente_ma = i_ma - OFFSET_PANEL_MA;
    irradiancia  = K_PANEL_WM2_POR_MA * corriente_ma;
    if (irradiancia < 0) irradiancia = 0;
  } else { corriente_ma = NAN; irradiancia = 0; }

  // ---- Indice evaporativo (Priestley-Taylor sobre la ventana movil) -----
  // dt real entre muestras; un hueco largo (setup, bloqueo) cuenta como un
  // periodo normal para no inflar la energia con una sola lectura.
  unsigned long ahora = millis();
  float dt_s = T_MUESTREO_MS / 1000.0;
  if (t_evap_prev != 0 && ahora - t_evap_prev < 10 * T_MUESTREO_MS)
    dt_s = (ahora - t_evap_prev) / 1000.0;
  t_evap_prev = ahora;

  if (hay_bme && !isnan(temp_c) && !isnan(hum_pct) && !isnan(pres_hpa))
    ventanaAcumular(ventana_evap, irradiancia, temp_c, hum_pct,
                    pres_hpa / 10.0, dt_s);

  cobertura_ventana = evaluarVentana(ventana_evap, pt);
  if (cobertura_ventana < COBERTURA_MIN) {
    estado_evap = EVAP_CALCULANDO;
    idx_evap = 0;
  } else {
    estado_evap = EVAP_OK;
    idx_evap = indiceEvaporativo(pt.et_mm_dia, vpd_kpa);
  }

  // ---- Riesgo hidrico ponderado ----------------------------------------
  float def_nivel = isnan(nivel_pct) ? 100.0 : (100.0 - nivel_pct);
  float idx_tasa  = 100.0 * constrain(tasa_ppm / TASA_REF, 0.0, 1.0);
  riesgo = W_NIVEL*def_nivel + W_EVAP*idx_evap + W_TASA*idx_tasa;
}

// Severidad de una variable: 0 normal, 1 precaucion, 2 critico.
// invertido = true para el nivel de agua, donde MENOR es peor.
uint8_t severidad(float v, float u_prec, float u_crit, bool invertido) {
  if (invertido) { if (v <= u_crit) return 2;  if (v <= u_prec) return 1; }
  else           { if (v >= u_crit) return 2;  if (v >= u_prec) return 1; }
  return 0;
}

// Reglas independientes sobre el indice ponderado: una condicion extrema
// dispara por si sola aunque el promedio no llegue, y el promedio dispara
// cuando ninguna variable esta mal por separado pero todas juntas si.
uint8_t calcularObjetivo() {
  if (!ultra_ok || !hay_bme) return EST_FALLO;

  s_nivel  = severidad(nivel_pct, U_PREC_NIVEL,  U_CRIT_NIVEL,  true);
  // Sin estimacion valida el indice evaporativo no dispara reglas
  s_evap   = (estado_evap == EVAP_OK)
           ? severidad(idx_evap, U_PREC_EVAP, U_CRIT_EVAP, false) : 0;
  s_tasa   = severidad(tasa_ppm,  U_PREC_TASA,   U_CRIT_TASA,   false);
  s_riesgo = severidad(riesgo,    U_PREC_RIESGO, U_CRIT_RIESGO, false);

  uint8_t peor = max(max(s_nivel, s_evap), max(s_tasa, s_riesgo));
  if (peor == 2) return EST_CRITICO;
  return (peor == 1) ? EST_PRECAUCION : EST_NORMAL;
}

// ---------------------------------------------------------------------------
//  ESCALERA DE ESTADOS
//  Se sube y se baja de a UN peldano, aunque el objetivo este dos escalones
//  mas arriba: PRECAUCION siempre es observable, para que el operario vea
//  venir la escalada y para que el historial quede completo en el log.
//  La confirmacion es asimetrica: escalar es rapido, desescalar es lento,
//  porque alertar tarde en una emergencia hidrica cuesta mas que sostener
//  una alerta algo mas de lo necesario.
//  FALLO no participa de la escalera: no es un nivel de riesgo sino una
//  condicion del equipo, y se entra y se sale de forma directa.
// ---------------------------------------------------------------------------
void aplicarEstado(uint8_t objetivo) {
  if (objetivo == estado) { conf_contador = 0; return; }

  bool involucraFallo = (objetivo == EST_FALLO || estado == EST_FALLO);

  conf_contador++;
  uint8_t necesarios = involucraFallo ? CONF_SUBIR
                     : (objetivo > estado ? CONF_SUBIR : CONF_BAJAR);
  if (conf_contador < necesarios) return;

  estado = involucraFallo ? objetivo
         : (objetivo > estado ? estado + 1 : estado - 1);
  conf_contador = 0;

  registrarEvento(estado == EST_NORMAL ? 0 : (estado == EST_PRECAUCION ? 1 : 2),
                  "Estado %s (nivel %u, evap %u, tasa %u, riesgo %u)",
                  NOMBRE_EST[estado], s_nivel, s_evap, s_tasa, s_riesgo);
  if (silenciado && estado > estado_silenciado) {
    silenciado = false;
    registrarEvento(1, "Silencio cancelado: el estado empeoro");
  }
}

// ===========================================================================
//  ALARMAS  (no bloqueante: ni un solo delay())
// ===========================================================================
bool enFase(unsigned long t, uint16_t per, uint16_t on) {
  if (per == 0 || on == 0) return false;
  return (t % per) < on;
}

void buzzerOn(uint8_t est) { ledcWriteTone(PIN_BUZZER, BUZ_HZ[est]); }
void buzzerOff()           { ledcWrite(PIN_BUZZER, 0); }

void apagarLeds() {
  digitalWrite(PIN_LED_V, LED_OFF);
  digitalWrite(PIN_LED_A, LED_OFF);
  digitalWrite(PIN_LED_R, LED_OFF);
}

// El silencio afecta SOLO al buzzer: los LEDs siguen igual, porque la
// condicion peligrosa no desaparecio porque alguien la reconociera.
// No hay boton fisico: lo dispara el tablero web. Se llama con mtx_estado tomado.
// Devuelve false si no habia nada que silenciar.
bool silenciarAlarma(const char *origen) {
  if (silenciado || estado == EST_NORMAL) return false;
  silenciado = true; estado_silenciado = estado; t_silencio = millis();
  registrarEvento(0, "Buzzer silenciado 15 min desde %s", origen);
  return true;
}

// Corre en tareaAlarmas (nucleo 1): toma una copia del estado bajo el
// candado y maneja los pines sin el.
void actualizarAlarmas() {
  unsigned long ahora = millis();

  bloquear(mtx_estado);
  if (silenciado && ahora - t_silencio > SILENCIO_MS) {
    silenciado = false;
    registrarEvento(0, "Fin del silencio de 15 min");
  }
  uint8_t est  = estado;
  bool    mute = silenciado;
  liberar(mtx_estado);

  bool led_on = enFase(ahora, PAT[est][0], PAT[est][1]);
  apagarLeds();
  if      (est == EST_NORMAL)     digitalWrite(PIN_LED_V, LED_ON);
  else if (est == EST_PRECAUCION) digitalWrite(PIN_LED_A, LED_ON);
  else if (est == EST_CRITICO)  { if (led_on) digitalWrite(PIN_LED_R, LED_ON); }
  else if (led_on) {                                  // FALLO: los tres
    digitalWrite(PIN_LED_V, LED_ON);
    digitalWrite(PIN_LED_A, LED_ON);
    digitalWrite(PIN_LED_R, LED_ON);
  }

  bool sonar = !mute && enFase(ahora, PAT[est][2], PAT[est][3]);
  if (sonar) buzzerOn(est); else buzzerOff();
}

// ===========================================================================
//  SALIDA
// ===========================================================================
// El texto se arma con el candado del estado y se escribe con el del bus
// I2C: el LCD comparte bus con el BME280 y el INA219, que lee la otra tarea.
void mostrarPagina(uint8_t p) {
  if (!hay_lcd) return;
  char l1[17], l2[17];

  bloquear(mtx_estado);
  armarPagina(p, l1, l2);
  liberar(mtx_estado);

  bloquear(mtx_i2c);
  lcd->clear();
  lcd->setCursor(0,0); lcd->print(l1);
  lcd->setCursor(0,1); lcd->print(l2);
  liberar(mtx_i2c);
}

void armarPagina(uint8_t p, char *l1, char *l2) {

  switch (p) {
    case 0:
      if (ultra_ok) snprintf(l1, 17, "Nivel: %5.1f%%", nivel_pct);
      else          snprintf(l1, 17, "Nivel: SIN ECO");
      snprintf(l2, 17, "%-11s%s", NOMBRE_EST[estado], silenciado ? "MUTE" : "");
      break;
    case 1:
      if (hay_bme) { snprintf(l1, 17, "Temp: %5.1f C", temp_c);
                     snprintf(l2, 17, "HR:   %5.1f %%", hum_pct); }
      else         { snprintf(l1, 17, "BME280 ausente");
                     snprintf(l2, 17, "Rev. bus I2C"); }
      break;
    case 2:
      if (hay_bme) { snprintf(l1, 17, "P: %6.1f hPa", pres_hpa);
                     snprintf(l2, 17, "VPD: %5.2f kPa", vpd_kpa); }
      else         { snprintf(l1, 17, "P:      ---");
                     snprintf(l2, 17, "VPD:    ---"); }
      break;
    case 3:
      if (!hay_ina)             snprintf(l1, 17, "Sol: sin sensor");
      else if (irradiancia < 5) snprintf(l1, 17, "Sol: NOCHE");
      else                      snprintf(l1, 17, "Sol:%6.0f W/m2", irradiancia);
      if (estado_evap == EVAP_OK) snprintf(l2, 17, "Evap: %5.1f %%", idx_evap);
      else snprintf(l2, 17, "Evap: calc %3.0f%%", 100.0 * cobertura_ventana);
      break;
    case 5:
      // Detalle de Priestley-Taylor: ET diaria, radiacion neta y modo
      if (estado_evap == EVAP_OK) snprintf(l1, 17, "ET: %5.2f mm/d", pt.et_mm_dia);
      else                        snprintf(l1, 17, "ET: estimando");
      snprintf(l2, 17, "Rn:%5.1fMJ %s", pt.rn_mj, MODO_DEMO ? "DEMO" : "CAMPO");
      break;
    case 4:
      // Severidad por variable: se ve de un vistazo QUE disparo la alarma
      snprintf(l1, 17, "N%u E%u T%u  R:%3.0f", s_nivel, s_evap, s_tasa, riesgo);
      if (buf_n < MIN_MUESTRAS) snprintf(l2, 17, "Tasa: midiendo");
      else                      snprintf(l2, 17, "Tasa:%6.1f pp/m", tasa_ppm);
      break;
    case 6:
      // Direccion del tablero: Android no resuelve wrews.local, la IP si
      snprintf(l1, 17, "WiFi: %s", wifi_ok ? "conectado" : "sin red");
      snprintf(l2, 17, "%s", wifi_ok ? ip_txt : WIFI_SSID);
      break;
  }
}

void imprimirSerial() {
  Serial.printf("d=%5.1f N=%5.1f%% | T=%4.1fC HR=%4.1f%% P=%6.1f VPD=%4.2f "
                "| G=%4.0f Rs=%5.2f Rn=%5.2f f=%4.3f ea=%4.2f ET=%4.2f "
                "Evap=%4.1f cob=%3.0f%% %s %s "
                "| tasa=%6.1f (max %5.1f) R=%5.1f "
                "| N%u E%u T%u R%u | %s%s\n",
                distancia_cm, nivel_pct, temp_c, hum_pct, pres_hpa, vpd_kpa,
                irradiancia, pt.rs_dia_mj, pt.rn_mj, pt.frac_pt, pt.ea_kpa,
                pt.et_mm_dia, idx_evap, 100.0 * cobertura_ventana,
                NOMBRE_EVAP[estado_evap], MODO_DEMO ? "DEMO" : "CAMPO",
                tasa_ppm, tasa_max, riesgo,
                s_nivel, s_evap, s_tasa, s_riesgo,
                NOMBRE_EST[estado], silenciado ? " [MUTE]" : "");
}

// ===========================================================================
//  RED: WI-FI EN MODO ESTACION
//  El equipo se une a la WLAN de la Alcaldia (hotspot del celular en la
//  demo). Si la red se cae, la medicion y la alarma fisica siguen igual:
//  corren en sus propias tareas y no dependen de la red.
// ===========================================================================

// Corre en la tarea de eventos del Wi-Fi, no en una ISR: puede tomar el candado.
void eventoWiFi(WiFiEvent_t ev, WiFiEventInfo_t info) {
  static bool estaba_conectado = false;
  if (ev == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
    IPAddress ip(info.got_ip.ip_info.ip.addr);
    bloquear(mtx_estado);
    registrarEvento(0, "Wi-Fi conectado, tablero en http://%s",
                    ip.toString().c_str());
    liberar(mtx_estado);
    estaba_conectado = true;
  } else if (ev == ARDUINO_EVENT_WIFI_STA_DISCONNECTED && estaba_conectado) {
    // Solo la primera desconexion: los reintentos fallidos no son eventos nuevos
    bloquear(mtx_estado);
    registrarEvento(1, "Wi-Fi perdido (motivo %u); la alarma local sigue activa",
                    info.wifi_sta_disconnected.reason);
    liberar(mtx_estado);
    estaba_conectado = false;
  }
}

void iniciarWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(NOMBRE_HOST);
  WiFi.setAutoReconnect(true);
  WiFi.onEvent(eventoWiFi);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.printf("Wi-Fi: conectando a \"%s\"", WIFI_SSID);

  // Espera acotada: sin red el equipo arranca igual y reintenta desde loop()
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_ESPERA_MS) {
    delay(500);
    Serial.print('.');
  }
  Serial.println();
  t_reintento_wifi = millis();
  vigilarWiFi();
  if (!wifi_ok)
    Serial.println(F("Wi-Fi: sin conexion; se sigue intentando cada 10 s"));
}

// Corre en loop(). Mantiene wifi_ok / ip_txt y reintenta si la red se cayo.
void vigilarWiFi() {
  bool ahora_ok = (WiFi.status() == WL_CONNECTED);

  if (ahora_ok && !wifi_ok) {
    snprintf(ip_txt, sizeof(ip_txt), "%s", WiFi.localIP().toString().c_str());
    Serial.printf("Wi-Fi: conectado, IP %s, RSSI %d dBm\n", ip_txt, WiFi.RSSI());
    if (!mdns_ok && MDNS.begin(NOMBRE_HOST)) {
      MDNS.addService("http", "tcp", 80);
      mdns_ok = true;
    }
  }
  if (!ahora_ok && wifi_ok) reconexiones_wifi++;
  wifi_ok = ahora_ok;

  // El reconectado automatico del ESP32 a veces se rinde: reintento propio
  if (!wifi_ok && millis() - t_reintento_wifi > WIFI_REINTENTO_MS) {
    t_reintento_wifi = millis();
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASS);
  }
}

// ===========================================================================
//  TABLERO: ACCESO
//  Dos condiciones, las dos obligatorias:
//  1. El cliente esta en la MISMA subred que el equipo (la WLAN de la zona).
//  2. Tiene una sesion abierta con usuario y clave (cookie HttpOnly con un
//     token aleatorio de 128 bits, valido 12 h).
//  Limitacion declarada: el tablero va por HTTP, sin TLS. La clave viaja una
//  sola vez (al iniciar sesion) y protegida solo por el cifrado WPA2 de la WLAN.
// ===========================================================================
bool mismaSubred() {
  IPAddress c = servidor.client().remoteIP();
  IPAddress l = WiFi.localIP(), m = WiFi.subnetMask();
  for (uint8_t i = 0; i < 4; i++)
    if ((c[i] & m[i]) != (l[i] & m[i])) return false;
  return true;
}

// Token de la cookie "wrews", o "" si no viene
String tokenCookie() {
  String ck = servidor.header("Cookie");
  int i = ck.indexOf("wrews=");
  if (i < 0) return "";
  return ck.substring(i + 6, i + 6 + 32);
}

bool autorizado() {
  if (!mismaSubred()) return false;
  String tk = tokenCookie();
  if (tk.length() != 32) return false;
  for (uint8_t k = 0; k < N_SESIONES; k++) {
    Sesion &s = sesiones[k];
    if (!s.activa) continue;
    if (millis() - s.t_ms > SESION_MS) { s.activa = false; continue; }
    if (tk.equals(s.token)) return true;
  }
  return false;
}

// Abre una sesion nueva (reemplaza la mas vieja si estan todas ocupadas)
const char *abrirSesion() {
  uint8_t k_libre = 0;
  unsigned long mas_vieja = 0;
  for (uint8_t k = 0; k < N_SESIONES; k++) {
    if (!sesiones[k].activa) { k_libre = k; break; }
    unsigned long edad = millis() - sesiones[k].t_ms;
    if (edad >= mas_vieja) { mas_vieja = edad; k_libre = k; }
  }
  Sesion &s = sesiones[k_libre];
  for (uint8_t b = 0; b < 16; b++)
    snprintf(s.token + 2*b, 3, "%02x", (uint8_t)(esp_random() & 0xFF));
  s.t_ms = millis();
  s.activa = true;
  return s.token;
}

void cerrarSesion() {
  String tk = tokenCookie();
  for (uint8_t k = 0; k < N_SESIONES; k++)
    if (sesiones[k].activa && tk.equals(sesiones[k].token)) sesiones[k].activa = false;
}

void redirigir(const char *a) {
  servidor.sendHeader("Location", a);
  servidor.send(303, "text/plain", "");
}

void responderNoAutorizado() {
  if (!mismaSubred()) servidor.send(403, "application/json", "{\"error\":\"fuera de la WLAN\"}");
  else                servidor.send(401, "application/json", "{\"error\":\"sesion requerida\"}");
}

// ===========================================================================
//  TABLERO: JSON
//  Sin librerias externas. NaN e infinito salen como null (JSON valido).
// ===========================================================================
void jsonNum(String &s, const char *k, float v, uint8_t dec) {
  s += '"'; s += k; s += "\":";
  if (isnan(v) || isinf(v)) s += "null"; else s += String(v, (unsigned int)dec);
  s += ',';
}
void jsonEnt(String &s, const char *k, long v) {
  s += '"'; s += k; s += "\":"; s += v; s += ',';
}
void jsonTxt(String &s, const char *k, const char *v) {
  s += '"'; s += k; s += "\":\"";
  for (const char *c = v; *c; c++) { if (*c == '"' || *c == '\\') s += '\\'; s += *c; }
  s += "\",";
}
void jsonCerrar(String &s, char cierre) {
  if (s.endsWith(",")) s.setCharAt(s.length() - 1, cierre); else s += cierre;
}

// Escribe un float en buf como numero JSON o null
void numTxt(char *buf, size_t n, float v, uint8_t dec) {
  if (isnan(v) || isinf(v)) snprintf(buf, n, "null");
  else snprintf(buf, n, "%.*f", dec, v);
}

// GET /api/actual: valor actual de todo. El JSON se arma bajo el candado
// (es rapido) y se envia sin el.
void apiActual() {
  if (!autorizado()) { responderNoAutorizado(); return; }
  String s;
  s.reserve(1400);
  s = "{";
  unsigned long ahora = millis();
  bloquear(mtx_estado);
  jsonEnt(s, "t_ms", ahora);
  jsonEnt(s, "t_muestra_ms", t_ultima_muestra);
  jsonTxt(s, "estado", NOMBRE_EST[estado]);
  jsonEnt(s, "estado_n", estado);
  jsonEnt(s, "silenciado", silenciado ? 1 : 0);
  jsonEnt(s, "silencio_rest_s",
          silenciado ? (long)((SILENCIO_MS - (ahora - t_silencio)) / 1000) : 0);
  jsonEnt(s, "sev_nivel", s_nivel);
  jsonEnt(s, "sev_evap", s_evap);
  jsonEnt(s, "sev_tasa", s_tasa);
  jsonEnt(s, "sev_riesgo", s_riesgo);
  jsonNum(s, "nivel_pct", nivel_pct, 1);
  jsonNum(s, "distancia_cm", distancia_cm, 1);
  jsonEnt(s, "ultra_ok", ultra_ok ? 1 : 0);
  jsonNum(s, "tasa_ppm", tasa_ppm, 1);
  jsonNum(s, "tasa_max", tasa_max, 1);
  jsonEnt(s, "tasa_lista", buf_n >= MIN_MUESTRAS ? 1 : 0);
  jsonNum(s, "riesgo", riesgo, 1);
  jsonNum(s, "temp_c", temp_c, 1);
  jsonNum(s, "hum_pct", hum_pct, 1);
  jsonNum(s, "pres_hpa", pres_hpa, 1);
  jsonNum(s, "vpd_kpa", vpd_kpa, 2);
  jsonNum(s, "rs_wm2", irradiancia, 0);
  jsonNum(s, "rs_dia_mj", pt.rs_dia_mj, 2);
  jsonNum(s, "rn_mj", pt.rn_mj, 2);
  jsonNum(s, "delta", pt.delta, 4);
  jsonNum(s, "gamma", pt.gamma, 4);
  jsonNum(s, "frac_pt", pt.frac_pt, 3);
  jsonNum(s, "ea_kpa", pt.ea_kpa, 3);
  jsonNum(s, "et_mm_dia", pt.et_mm_dia, 2);
  jsonNum(s, "idx_evap", idx_evap, 1);
  jsonNum(s, "cobertura_ventana", cobertura_ventana, 2);
  jsonTxt(s, "estado_evap", NOMBRE_EVAP[estado_evap]);
  jsonTxt(s, "modo", MODO_DEMO ? "DEMO" : "CAMPO");
  jsonEnt(s, "ultimo_evento", ev_sig - 1);
  liberar(mtx_estado);
  jsonEnt(s, "rssi", WiFi.RSSI());
  jsonEnt(s, "reconexiones_wifi", reconexiones_wifi);
  jsonCerrar(s, '}');
  servidor.sendHeader("Cache-Control", "no-store");
  servidor.send(200, "application/json", s);
}

// GET /api/config: constantes del modelo, para dibujar umbrales y textos
void apiConfig() {
  if (!autorizado()) { responderNoAutorizado(); return; }
  String s = "{";
  jsonNum(s, "u_prec_nivel", U_PREC_NIVEL, 1);
  jsonNum(s, "u_crit_nivel", U_CRIT_NIVEL, 1);
  jsonNum(s, "u_prec_riesgo", U_PREC_RIESGO, 1);
  jsonNum(s, "u_crit_riesgo", U_CRIT_RIESGO, 1);
  jsonNum(s, "u_prec_evap", U_PREC_EVAP, 1);
  jsonNum(s, "u_crit_evap", U_CRIT_EVAP, 1);
  jsonNum(s, "u_prec_tasa", U_PREC_TASA, 1);
  jsonNum(s, "u_crit_tasa", U_CRIT_TASA, 1);
  jsonNum(s, "w_nivel", W_NIVEL, 2);
  jsonNum(s, "w_evap", W_EVAP, 2);
  jsonNum(s, "w_tasa", W_TASA, 2);
  jsonNum(s, "et_ref", ET_REF_MM_DIA, 1);
  jsonTxt(s, "modo", MODO_DEMO ? "DEMO" : "CAMPO");
  jsonEnt(s, "ventana_s", ventana_evap.duracion_s);
  jsonEnt(s, "hist_cada_s", HIST_CADA * T_MUESTREO_MS / 1000);
  jsonTxt(s, "red", WIFI_SSID);
  jsonCerrar(s, '}');
  servidor.send(200, "application/json", s);
}

// GET /api/historial: [[t_s, nivel, riesgo, evap, tasa, temp, hum, irr, estado], ...]
// Se copia bajo el candado y se envia por partes sin el: un cliente lento no
// debe frenar la medicion.
void apiHistorial() {
  if (!autorizado()) { responderNoAutorizado(); return; }
  static PuntoHist copia[N_HIST];      // static: 10 kB fuera de la pila
  bloquear(mtx_estado);
  uint16_t n = hist_n;
  uint16_t inicio = (hist_i + N_HIST - n) % N_HIST;
  for (uint16_t k = 0; k < n; k++) copia[k] = hist[(inicio + k) % N_HIST];
  liberar(mtx_estado);

  servidor.sendHeader("Cache-Control", "no-store");
  servidor.setContentLength(CONTENT_LENGTH_UNKNOWN);
  servidor.send(200, "application/json", "");
  String bloque;
  bloque.reserve(1600);
  bloque = "[";
  char a[12], b[12], c[12], d[12], e[12], f[12], g[12];
  for (uint16_t k = 0; k < n; k++) {
    const PuntoHist &h = copia[k];
    numTxt(a, sizeof(a), h.nivel, 1);  numTxt(b, sizeof(b), h.riesgo, 1);
    numTxt(c, sizeof(c), h.evap, 1);   numTxt(d, sizeof(d), h.tasa, 1);
    numTxt(e, sizeof(e), h.temp, 1);   numTxt(f, sizeof(f), h.hum, 1);
    numTxt(g, sizeof(g), h.irr, 0);
    char linea[110];
    snprintf(linea, sizeof(linea), "%s[%lu,%s,%s,%s,%s,%s,%s,%s,%u]",
             k ? "," : "", (unsigned long)h.t_s, a, b, c, d, e, f, g, h.estado);
    bloque += linea;
    if (bloque.length() > 1400) { servidor.sendContent(bloque); bloque = ""; }
  }
  bloque += "]";
  servidor.sendContent(bloque);
  servidor.sendContent("");
}

// GET /api/eventos?desde=N: eventos con id > N, del mas viejo al mas nuevo
void apiEventos() {
  if (!autorizado()) { responderNoAutorizado(); return; }
  uint32_t desde = servidor.hasArg("desde") ? servidor.arg("desde").toInt() : 0;
  String s;
  s.reserve(2400);
  s = "{";
  bloquear(mtx_estado);
  jsonEnt(s, "t_ms", millis());
  s += "\"eventos\":[";
  for (uint8_t k = 0; k < N_EVENTOS; k++) {
    const Evento &e = eventos[(ev_i + k) % N_EVENTOS];   // del mas viejo
    if (e.id == 0 || e.id <= desde) continue;
    s += '{';
    jsonEnt(s, "id", e.id);
    jsonEnt(s, "t_ms", e.t_ms);
    jsonEnt(s, "gravedad", e.gravedad);
    jsonTxt(s, "texto", e.texto);
    jsonCerrar(s, '}');
    s += ',';
  }
  liberar(mtx_estado);
  jsonCerrar(s, ']');
  s += '}';
  servidor.sendHeader("Cache-Control", "no-store");
  servidor.send(200, "application/json", s);
}

// POST /api/silenciar: lo mismo que haria un boton de silencio en el equipo
void apiSilenciar() {
  if (!autorizado()) { responderNoAutorizado(); return; }
  char origen[40];
  snprintf(origen, sizeof(origen), "el tablero (%s)",
           servidor.client().remoteIP().toString().c_str());
  bloquear(mtx_estado);
  bool hecho = silenciarAlarma(origen);
  liberar(mtx_estado);
  servidor.send(200, "application/json",
                hecho ? "{\"ok\":1}" : "{\"ok\":0,\"motivo\":\"nada que silenciar\"}");
}

// ===========================================================================
//  TABLERO: PAGINAS Y RUTAS
// ===========================================================================
void paginaTablero() {
  if (!mismaSubred()) { responderNoAutorizado(); return; }
  if (!autorizado())  { redirigir("/login"); return; }
  servidor.sendHeader("Cache-Control", "no-store");
  servidor.send_P(200, "text/html; charset=utf-8", TABLERO_HTML);
}

void paginaLogin() {
  if (!mismaSubred()) { responderNoAutorizado(); return; }
  servidor.send_P(200, "text/html; charset=utf-8", LOGIN_HTML);
}

// Tras MAX_FALLOS_LOGIN claves malas seguidas, el login se bloquea 30 s
void procesarLogin() {
  if (!mismaSubred()) { responderNoAutorizado(); return; }
  if (fallos_login >= MAX_FALLOS_LOGIN) {
    if (millis() - t_bloqueo_login < BLOQUEO_LOGIN_MS) { redirigir("/login?b=1"); return; }
    fallos_login = 0;
  }
  String ip = servidor.client().remoteIP().toString();
  if (servidor.arg("u") == WEB_USER && servidor.arg("p") == WEB_PASS) {
    fallos_login = 0;
    String ck = String("wrews=") + abrirSesion() + "; Path=/; HttpOnly; SameSite=Strict";
    servidor.sendHeader("Set-Cookie", ck);
    bloquear(mtx_estado);
    registrarEvento(0, "Sesion iniciada desde %s", ip.c_str());
    liberar(mtx_estado);
    redirigir("/");
  } else {
    if (++fallos_login >= MAX_FALLOS_LOGIN) t_bloqueo_login = millis();
    bloquear(mtx_estado);
    registrarEvento(1, "Clave incorrecta desde %s (%u/%u)",
                    ip.c_str(), fallos_login, MAX_FALLOS_LOGIN);
    liberar(mtx_estado);
    redirigir(fallos_login >= MAX_FALLOS_LOGIN ? "/login?b=1" : "/login?e=1");
  }
}

void procesarLogout() {
  cerrarSesion();
  servidor.sendHeader("Set-Cookie", "wrews=; Path=/; Max-Age=0");
  redirigir("/login");
}

void iniciarServidor() {
  const char *cabeceras[] = { "Cookie" };
  servidor.collectHeaders(cabeceras, 1);

  servidor.on("/",              HTTP_GET,  paginaTablero);
  servidor.on("/login",         HTTP_GET,  paginaLogin);
  servidor.on("/login",         HTTP_POST, procesarLogin);
  servidor.on("/logout",        HTTP_POST, procesarLogout);
  servidor.on("/api/actual",    HTTP_GET,  apiActual);
  servidor.on("/api/config",    HTTP_GET,  apiConfig);
  servidor.on("/api/historial", HTTP_GET,  apiHistorial);
  servidor.on("/api/eventos",   HTTP_GET,  apiEventos);
  servidor.on("/api/silenciar", HTTP_POST, apiSilenciar);
  servidor.onNotFound([]() { servidor.send(404, "text/plain", "No existe"); });
  servidor.begin();
  Serial.println(F("Servidor web en el puerto 80"));
}

// ===========================================================================
//  SETUP
// ===========================================================================
void escanearI2C() {
  Serial.println(F("--- Escaneo del bus I2C ---"));
  uint8_t n = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      n++;
      Serial.printf("  0x%02X  ", a);
      if (a == 0x27 || a == 0x3F)      { addr_lcd = a; Serial.println(F("-> LCD")); }
      else if (a == 0x76 || a == 0x77) { addr_bme = a; Serial.println(F("-> BME280")); }
      else if (a >= 0x40 && a <= 0x4F) { addr_ina = a; Serial.println(F("-> INA219")); }
      else Serial.println(F("-> desconocido"));
    }
  }
  if (!n) Serial.println(F("  NADA. Revisa SDA/SCL, alimentacion y GND comun."));
  Serial.println();
}

void autotestSalidas() {
  Serial.println(F("--- Autotest de salidas ---"));
  digitalWrite(PIN_LED_V, LED_ON);  delay(300); digitalWrite(PIN_LED_V, LED_OFF);
  digitalWrite(PIN_LED_A, LED_ON);  delay(300); digitalWrite(PIN_LED_A, LED_OFF);
  digitalWrite(PIN_LED_R, LED_ON);  delay(300); digitalWrite(PIN_LED_R, LED_OFF);
  ledcWriteTone(PIN_BUZZER, 2500);  delay(500);
  ledcWrite(PIN_BUZZER, 0);
  Serial.println(F("  Verde, amarillo, rojo y un tono de medio segundo.\n"));
}

// ---------------------------------------------------------------------------
//  Vectores de referencia de Priestley-Taylor. Las ventanas de prueba son
//  static para no gastar ~1.5 kB de pila del loopTask.
// ---------------------------------------------------------------------------
bool chequeo(const char *nombre, bool ok) {
  Serial.printf("  [%s] %s\n", ok ? " OK " : "FALLA", nombre);
  return ok;
}

bool autotestPT() {
  Serial.println(F("--- Autotest Priestley-Taylor ---"));
  bool ok = true;
  ResultadoPT r;

  // Rs=17, T=14 (20/7), HR=75, P=75 kPa. Tolerancia +-0.05 mm/dia
  r = priestleyTaylor(17.0, 14.0, 20.0, 7.0, 75.0, 75.0, 37.5);
  Serial.printf("  Ra=37.5: D=%.4f g=%.4f f=%.3f ea=%.3f Rn=%.2f ET=%.3f\n",
                r.delta, r.gamma, r.frac_pt, r.ea_kpa, r.rn_mj, r.et_mm_dia);
  ok &= chequeo("Ra=37.5 -> ET 4.67", fabs(r.et_mm_dia - 4.67) <= 0.05);

  r = priestleyTaylor(17.0, 14.0, 20.0, 7.0, 75.0, 75.0, 36.0);
  Serial.printf("  Ra=36.0: Rn=%.2f ET=%.3f\n", r.rn_mj, r.et_mm_dia);
  ok &= chequeo("Ra=36.0 -> ET 4.61", fabs(r.et_mm_dia - 4.61) <= 0.05);

  // Dia despejado de referencia: debe reproducir ET_REF [Ev sec. 6]
  float rso_ref = (0.75 + 2e-5 * ALTITUD_M) * RA_FIJO_MJ;
  r = priestleyTaylor(rso_ref, 16.0, 22.0, 8.0, 65.0, 75.0, RA_FIJO_MJ);
  Serial.printf("  despejado: Rn=%.2f ET=%.3f\n", r.rn_mj, r.et_mm_dia);
  ok &= chequeo("dia despejado -> ET_REF", fabs(r.et_mm_dia - ET_REF_MM_DIA) <= 0.05);

  r = priestleyTaylor(0.0, 14.0, 20.0, 7.0, 75.0, 75.0, RA_FIJO_MJ);
  ok &= chequeo("oscuridad -> Rn=0, ET=0", r.rn_mj == 0 && r.et_mm_dia == 0);

  // Cobertura insuficiente: 10 s en una ventana de 120 s
  static Ventana v1, v2;
  ventanaReiniciar(v1, 120);
  for (uint8_t k = 0; k < 10; k++) ventanaAcumular(v1, 500, 14, 75, 75, 1.0);
  float cob = evaluarVentana(v1, r);
  ok &= chequeo("cobertura baja -> sin estimacion",
                cob < COBERTURA_MIN && r.et_mm_dia == 0);

  // Muestras constantes: el equivalente diario no depende de la ventana
  ResultadoPT r_demo, r_campo;
  ventanaReiniciar(v1, VENTANA_DEMO_S);
  ventanaReiniciar(v2, VENTANA_CAMPO_S);
  for (uint32_t k = 0; k < VENTANA_DEMO_S; k++)
    ventanaAcumular(v1, 500, 14, 75, 75, 1.0);
  for (uint32_t k = 0; k < VENTANA_CAMPO_S / 10; k++)
    ventanaAcumular(v2, 500, 14, 75, 75, 10.0);
  evaluarVentana(v1, r_demo);
  evaluarVentana(v2, r_campo);
  Serial.printf("  demo: Rs=%.2f ET=%.3f | campo: Rs=%.2f ET=%.3f\n",
                r_demo.rs_dia_mj, r_demo.et_mm_dia,
                r_campo.rs_dia_mj, r_campo.et_mm_dia);
  ok &= chequeo("demo == campo con muestras constantes",
                fabs(r_demo.et_mm_dia - r_campo.et_mm_dia) < 0.01 &&
                fabs(r_demo.rs_dia_mj - 43.2) < 0.1);

  Serial.println(ok ? F("  Todo OK\n") : F("  HAY FALLAS: revisar el modelo\n"));
  return ok;
}

void setup() {
  Serial.begin(115200);
  delay(400);
  Serial.println(F("\n\n===== WREWS v7 - prototipo funcional =====\n"));

  mtx_estado = xSemaphoreCreateMutex();
  mtx_i2c    = xSemaphoreCreateMutex();
  if (!mtx_estado || !mtx_i2c) {
    Serial.println(F("Sin memoria para los mutex: el equipo no puede arrancar."));
    while (true) delay(1000);
  }

  // Estado seguro inmediato: pinMode() deja el pin en LOW y con polaridad
  // invertida eso significaria "encendido".
  pinMode(PIN_LED_V, OUTPUT); pinMode(PIN_LED_A, OUTPUT); pinMode(PIN_LED_R, OUTPUT);
  ledcAttach(PIN_BUZZER, BUZZER_HZ, 8);
  ledcWrite(PIN_BUZZER, 0);
  apagarLeds();

  pinMode(PIN_TRIG, OUTPUT); pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);

  autotestSalidas();

  Wire.begin(PIN_SDA, PIN_SCL);
  escanearI2C();

  if (addr_lcd) {
    lcd = new LiquidCrystal_I2C(addr_lcd, 16, 2);
    lcd->init(); lcd->backlight();
    lcd->setCursor(0,0); lcd->print("WREWS v7");
    lcd->setCursor(0,1); lcd->print("Iniciando...");
    hay_lcd = true;
    Serial.printf("LCD  ..... OK en 0x%02X\n", addr_lcd);
  } else Serial.println(F("LCD  ..... AUSENTE (prueba 0x27 y 0x3F)"));

  if (addr_bme && bme.begin(addr_bme)) {        // [Ev 12] = [Pe 14]
    hay_bme = true;
    Serial.printf("BME280 ... OK en 0x%02X, sensorID=0x%02X %s\n",
      addr_bme, bme.sensorID(),
      bme.sensorID()==0x60 ? "(correcto)" : "(OJO: parece BMP280, sin humedad)");
    bme.setSampling(Adafruit_BME280::MODE_NORMAL,
                    Adafruit_BME280::SAMPLING_X2,  Adafruit_BME280::SAMPLING_X16,
                    Adafruit_BME280::SAMPLING_X1,  Adafruit_BME280::FILTER_X16,
                    Adafruit_BME280::STANDBY_MS_500);
  } else Serial.println(F("BME280 ... AUSENTE"));

  if (addr_ina && ina.begin()) {
    hay_ina = true;
    ina.setCalibration_16V_400mA();   // mejor resolucion que el rango de 2 A [Pe 15]
    Serial.printf("INA219 ... OK en 0x%02X\n", addr_ina);
    delay(200);
    float s = 0;
    for (uint8_t i = 0; i < 20; i++) { s += ina.getCurrent_mA(); delay(20); }
    float reposo = s / 20.0;
    Serial.printf("           corriente en reposo: %+.3f mA\n", reposo);
    if (fabs(reposo) <= OFFSET_MAX_MA) {
      OFFSET_PANEL_MA = reposo;
      Serial.println(F("           -> se toma como CERO del piranometro"));
    } else {
      Serial.printf("           -> mayor que %.1f mA: hay luz sobre el panel, "
                    "offset = 0\n", OFFSET_MAX_MA);
    }
  } else Serial.println(F("INA219 ... AUSENTE (irradiancia = 0)"));

  caracterizarRuido();

  autotestPT();
  ventanaReiniciar(ventana_evap, MODO_DEMO ? VENTANA_DEMO_S : VENTANA_CAMPO_S);
  Serial.printf("Evaporacion: modo %s, ventana %lu s en %u buckets, "
                "cobertura minima %.0f %%\n",
                MODO_DEMO ? "DEMO" : "CAMPO", (unsigned long)ventana_evap.duracion_s,
                NUM_BUCKETS, 100.0 * COBERTURA_MIN);

  Serial.printf("Umbrales de tasa : PRECAUCION %.1f, CRITICO %.1f pp/min\n",
                U_PREC_TASA, U_CRIT_TASA);
  Serial.printf("Umbrales de nivel: PRECAUCION <=%.0f%%, CRITICO <=%.0f%%\n",
                U_PREC_NIVEL, U_CRIT_NIVEL);
  Serial.printf("  -> en distancia : PRECAUCION desde %.1f cm, "
                "CRITICO desde %.1f cm\n\n",
                D_VACIO_CM - (U_PREC_NIVEL/100.0)*(D_VACIO_CM - D_LLENO_CM),
                D_VACIO_CM - (U_CRIT_NIVEL/100.0)*(D_VACIO_CM - D_LLENO_CM));
  Serial.println(F("--- Operacion normal ---"));

  tomarMuestra();
  mostrarPagina(0);
  t_pagina = millis();

  BaseType_t ok_m = xTaskCreatePinnedToCore(tareaMedicion, "medicion",
                                            PILA_MEDICION, NULL, PRIO_MEDICION,
                                            &tarea_medicion, NUCLEO_MEDICION);
  BaseType_t ok_a = xTaskCreatePinnedToCore(tareaAlarmas, "alarmas",
                                            PILA_ALARMAS, NULL, PRIO_ALARMAS,
                                            &tarea_alarmas, NUCLEO_ALARMAS);
  if (ok_m != pdPASS || ok_a != pdPASS) {
    Serial.println(F("No se pudieron crear las tareas: el equipo no puede operar."));
    while (true) delay(1000);
  }
  Serial.printf("Tarea de medicion en el nucleo %d, cada %lu ms\n",
                NUCLEO_MEDICION, T_MUESTREO_MS);
  Serial.printf("Tarea de alarmas en el nucleo %d\n", NUCLEO_ALARMAS);

  // La red va despues de las tareas: mientras se conecta, el equipo ya mide
  // y alarma. Sin red arranca igual.
  iniciarWiFi();
  iniciarServidor();
  if (wifi_ok)
    Serial.printf("Tablero: http://%s  (o http://%s.local desde un PC)\n\n",
                  ip_txt, NOMBRE_HOST);
}

// ---------------------------------------------------------------------------
//  TAREA DE MEDICION (nucleo 0)
//  vTaskDelayUntil mantiene el periodo fijo aunque una muestra tarde mas o
//  menos, y entre muestra y muestra la tarea duerme y libera el nucleo.
// ---------------------------------------------------------------------------
void tareaMedicion(void *param) {
  TickType_t ultimo = xTaskGetTickCount();
  const TickType_t periodo = pdMS_TO_TICKS(T_MUESTREO_MS);
  for (;;) {
    vTaskDelayUntil(&ultimo, periodo);
    tomarMuestra();
  }
}

// ---------------------------------------------------------------------------
//  TAREA DE ALARMAS (nucleo 1)
//  Cada 10 ms: suficiente para los patrones de parpadeo y pitido (el mas
//  corto dura 120 ms) y aislada del servidor web.
// ---------------------------------------------------------------------------
void tareaAlarmas(void *param) {
  for (;;) {
    actualizarAlarmas();
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// loop() corre en el nucleo 1: servidor web, Wi-Fi y LCD.
void loop() {
  servidor.handleClient();
  vigilarWiFi();

  unsigned long ahora = millis();
  if (ahora - t_pagina >= T_PAGINA_MS) {
    t_pagina = ahora;
    pagina = (pagina + 1) % N_PAGINAS;
    mostrarPagina(pagina);
  }
  delay(2);              // cede el nucleo a las demas tareas
}
