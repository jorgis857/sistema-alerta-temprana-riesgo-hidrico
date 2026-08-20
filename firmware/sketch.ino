/**
 * =====================================================================
 *  SISTEMA DE ALERTA TEMPRANA DE RIESGO HÍDRICO (SATRH)
 * =====================================================================
 *
 *  Internet de las Cosas - 2026-2 - Challenge #1
 *  Facultad de Ingeniería - Universidad de La Sabana
 *  Equipo 1: Mateo Ramírez Cabrera · Antonio Benítez Rueda ·
 *            Jorge Andrés Rodríguez Huertas
 *
 *  DESCRIPCIÓN GENERAL
 *  --------------------
 *  Firmware para ESP32 que monitorea de forma autónoma (sin redes de
 *  comunicación) el nivel de un reservorio de agua y las condiciones
 *  ambientales que favorecen su pérdida por evaporación, fusiona esas
 *  señales en un índice de "riesgo hídrico" y emite una alerta local
 *  in situ mediante pantalla OLED, LEDs semafóricos y buzzer.
 *
 *  SENSORES (todos simulados en Wokwi mediante custom chips en C,
 *  ver /hardware/wokwi/chips/):
 *    - BME280  (I2C 0x76): temperatura, humedad, presión atmosférica.
 *    - INA219  (I2C 0x40): corriente de un mini panel solar, usada
 *              para aproximar la radiación solar incidente (W/m2).
 *    - HC-SR04 (GPIO TRIG/ECHO): distancia al espejo de agua, usada
 *              para estimar el nivel (%) del reservorio.
 *
 *  ACTUADORES (alerta local, sin comunicaciones):
 *    - OLED SSD1306 128x64 (I2C 0x3C): visualización de variables.
 *    - LED verde / amarillo / rojo (lógica activa en bajo: LOW=ON).
 *    - Buzzer piezoeléctrico (tono fijo de 1000 Hz en estado crítico).
 *
 *  MODELO DE FUSIÓN DE DATOS (ver Wiki, sección 3.2, para el detalle
 *  matemático completo):
 *    1) Nivel (%)                a partir de la distancia medida.
 *    2) VPD (kPa)                a partir de temperatura y humedad.
 *    3) Índice evaporativo (%)   50% radiación + 50% VPD normalizados.
 *    4) Tasa / índice de descenso a partir de la variación de nivel
 *       en el tiempo (10 s simulados = 1 h real en esta demo Wokwi).
 *    5) Riesgo hídrico (%)       50% déficit de nivel + 30% índice
 *       evaporativo + 20% índice de descenso.
 *    6) Reglas de seguridad independientes que fuerzan el estado
 *       CRÍTICO ante cualquier variable individualmente extrema,
 *       para que ninguna condición peligrosa quede oculta por el
 *       promedio ponderado del punto 5.
 *
 *  Repositorio completo y Wiki técnica: ver README.md del proyecto.
 * =====================================================================
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

// =====================================================
// I2C
// =====================================================

#define BME280_ADDRESS 0x76
#define INA219_ADDRESS 0x40

// =====================================================
// HC-SR04 / OKY3261
// =====================================================

#define TRIG_PIN 5
#define ECHO_PIN 18

// Maqueta actual:
// 3 cm  -> 100% lleno
// 30 cm -> 0% lleno
//
// EN EL PROTOTIPO REAL ESTOS VALORES SE CALIBRAN
// SEGÚN LAS DIMENSIONES DEL RESERVORIO.

const float DISTANCIA_LLENO = 3.0;
const float DISTANCIA_VACIO = 30.0;

// =====================================================
// LEDS
// =====================================================

#define LED_VERDE 25
#define LED_AMARILLO 26
#define LED_ROJO 27

// En TU circuito actual de Wokwi:
//
// LOW  = encendido
// HIGH = apagado

// =====================================================
// BUZZER
// =====================================================

#define BUZZER_PIN 19

// =====================================================
// OLED
// =====================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_ADDRESS 0x3C

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  OLED_RESET
);

// =====================================================
// CONFIGURACIÓN DEL MODELO
// =====================================================

// ---------------- RADIACIÓN ----------------

// Para normalización del índice evaporativo.
// 1000 W/m² ya representa radiación solar muy intensa.
// Valores mayores siguen aumentando la medición,
// pero el factor se limita a 100%.

const float RADIACION_REFERENCIA = 1000.0;

// ---------------- VPD ----------------

// Usamos 3 kPa como punto donde nuestro índice
// considera máxima la demanda atmosférica.
//
// NO significa que 3 kPa sea una frontera universal.
// Es un parámetro configurable del modelo.

const float VPD_REFERENCIA = 3.0;

// ---------------- TASA DE DESCENSO ----------------
//
// Para Wokwi:
//
// 10 segundos representan 1 hora simulada.
//
// Esto permite demostrar la tendencia sin tener que
// esperar una hora real.
//
// En hardware real:
//
// INTERVALO_TASA_MS podría cambiarse a:
// 3600000UL = 1 hora real.

const unsigned long INTERVALO_TASA_MS = 10000;

// Descenso que genera PRECAUCIÓN:
// 2 puntos porcentuales/hora

const float TASA_PRECAUCION = 2.0;

// Descenso considerado CRÍTICO:
// 5 puntos porcentuales/hora

const float TASA_CRITICA = 5.0;

// =====================================================
// VARIABLES PARA TASA DE DESCENSO
// =====================================================

float nivelAnterior = -1;

float tasaDescenso = 0;

float indiceDescenso = 0;

unsigned long ultimoCalculoTasa = 0;

// =====================================================
// BME280 CUSTOM
// =====================================================

// ---------------- TEMPERATURA ----------------

/**
 * Lee el registro custom de temperatura del chip BME280 simulado
 * (registro 0xFA, 2 bytes, big-endian, con signo).
 * @return Temperatura cruda = temperatura_real (°C) * 100.
 */
int16_t readTemperatureRaw() {

  Wire.beginTransmission(BME280_ADDRESS);

  Wire.write(0xFA);

  Wire.endTransmission();

  Wire.requestFrom(BME280_ADDRESS, 2);

  int16_t value = 0;

  if (Wire.available() >= 2) {

    uint8_t msb = Wire.read();
    uint8_t lsb = Wire.read();

    value =
      (int16_t)(
        ((uint16_t)msb << 8) | lsb
      );
  }

  return value;
}

// ---------------- HUMEDAD ----------------

/**
 * Lee el registro custom de humedad del chip BME280 simulado
 * (registro 0xFD, 2 bytes, big-endian).
 * @return Humedad cruda = humedad_relativa_real (%) * 100.
 */
uint16_t readHumidityRaw() {

  Wire.beginTransmission(BME280_ADDRESS);

  Wire.write(0xFD);

  Wire.endTransmission();

  Wire.requestFrom(BME280_ADDRESS, 2);

  uint16_t value = 0;

  if (Wire.available() >= 2) {

    uint8_t msb = Wire.read();
    uint8_t lsb = Wire.read();

    value =
      ((uint16_t)msb << 8) | lsb;
  }

  return value;
}

// ---------------- PRESIÓN ----------------

/**
 * Lee el registro custom de presión del chip BME280 simulado
 * (registro 0xF7, 3 bytes, big-endian). No participa en el
 * cálculo del riesgo hídrico (ver Wiki, sección 3.2); solo se
 * mide y se muestra al usuario como contexto ambiental adicional.
 * @return Presión cruda = presión_real (hPa) * 100.
 */
uint32_t readPressureRaw() {

  Wire.beginTransmission(BME280_ADDRESS);

  Wire.write(0xF7);

  Wire.endTransmission();

  Wire.requestFrom(BME280_ADDRESS, 3);

  uint32_t value = 0;

  if (Wire.available() >= 3) {

    uint8_t b1 = Wire.read();
    uint8_t b2 = Wire.read();
    uint8_t b3 = Wire.read();

    value =
      ((uint32_t)b1 << 16) |
      ((uint32_t)b2 << 8) |
      b3;
  }

  return value;
}

// =====================================================
// INA219 CUSTOM
// =====================================================

/**
 * Lee el registro custom de corriente del chip INA219 simulado
 * (registro 0x04, 2 bytes, big-endian). Esa corriente es generada
 * por el mini panel solar en función de la irradiancia configurada
 * en el simulador, y se usa como proxy de la radiación solar (ver
 * loop(), sección "RADIACIÓN SOLAR").
 * @return Corriente cruda = corriente_real (mA) * 100.
 */
uint16_t readINA219CurrentRaw() {

  Wire.beginTransmission(INA219_ADDRESS);

  Wire.write(0x04);

  Wire.endTransmission();

  Wire.requestFrom(INA219_ADDRESS, 2);

  uint16_t value = 0;

  if (Wire.available() >= 2) {

    uint8_t msb = Wire.read();
    uint8_t lsb = Wire.read();

    value =
      ((uint16_t)msb << 8) | lsb;
  }

  return value;
}

// =====================================================
// HC-SR04
// =====================================================

/**
 * Dispara un pulso ultrasónico por TRIG y mide el tiempo de vuelo
 * del eco en ECHO para estimar la distancia al espejo de agua.
 * Timeout de pulseIn() = 30000 us (~5 m de alcance máximo).
 * @return Distancia estimada en centímetros.
 */
float medirDistancia() {

  digitalWrite(TRIG_PIN, LOW);

  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);

  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duracion =
    pulseIn(ECHO_PIN, HIGH, 30000);

  float distancia =
    duracion * 0.0343 / 2.0;

  return distancia;
}

// =====================================================
// NIVEL DEL AGUA
// =====================================================

/**
 * Convierte la distancia medida por el HC-SR04 en un porcentaje de
 * nivel del reservorio, calibrado por los dos puntos DISTANCIA_LLENO
 * (100%) y DISTANCIA_VACIO (0%). El resultado se satura en [0, 100].
 * @param distancia Distancia medida en cm.
 * @return Nivel del reservorio en porcentaje (0-100%).
 */
float calcularNivel(float distancia) {

  float nivel =
    (
      DISTANCIA_VACIO - distancia
    )
    /
    (
      DISTANCIA_VACIO -
      DISTANCIA_LLENO
    )
    * 100.0;

  if (nivel > 100) {
    nivel = 100;
  }

  if (nivel < 0) {
    nivel = 0;
  }

  return nivel;
}

// =====================================================
// LIMITADOR 0 - 1
// =====================================================

/**
 * Satura un valor real al rango normalizado [0, 1].
 * Utilidad usada por calcularIndiceEvaporativo() para normalizar
 * radiación y VPD antes de combinarlos.
 * @param valor Valor de entrada sin normalizar.
 * @return Valor saturado entre 0.0 y 1.0.
 */
float limitar01(float valor) {

  if (valor < 0) {
    return 0;
  }

  if (valor > 1) {
    return 1;
  }

  return valor;
}

// =====================================================
// VPD
// =====================================================
//
// Temperatura + humedad permiten estimar el
// déficit de presión de vapor.
//
// Un VPD mayor representa aire con mayor
// capacidad de aceptar vapor de agua.
//
// Unidad: kPa
// =====================================================

/**
 * Calcula el déficit de presión de vapor (VPD) a partir de
 * temperatura y humedad relativa, usando la ecuación de
 * Tetens/FAO-56 para la presión de vapor de saturación.
 * Un VPD mayor indica un aire con mayor capacidad de "aceptar"
 * vapor de agua adicional (condiciones más favorables a la
 * evaporación).
 * @param temperatura Temperatura del aire en °C.
 * @param humedad Humedad relativa en % (0-100).
 * @return VPD en kPa (saturado a un mínimo de 0).
 */
float calcularVPD(
  float temperatura,
  float humedad
) {

  // Presión de vapor de saturación

  float es =
    0.6108 *
    exp(
      (17.27 * temperatura)
      /
      (temperatura + 237.3)
    );

  // Presión de vapor real

  float ea =
    es * (humedad / 100.0);

  // Déficit de presión de vapor

  float vpd =
    es - ea;

  if (vpd < 0) {
    vpd = 0;
  }

  return vpd;
}

// =====================================================
// ÍNDICE DE PRESIÓN EVAPORATIVA
// =====================================================
//
// Combinamos:
//
// 50% radiación solar
// 50% VPD
//
// Resultado: 0 - 100%
//
// OJO:
//
// 80% NO significa que se evapora el 80% del agua.
//
// Significa que las condiciones ambientales están
// al 80% de nuestra escala de intensidad evaporativa.
// =====================================================

/**
 * Combina radiación solar y VPD normalizados (50%/50%) en un único
 * índice evaporativo. IMPORTANTE: el resultado NO representa el
 * porcentaje de agua que se evaporará, sino qué tan intensas son,
 * en una escala relativa 0-100%, las condiciones ambientales para
 * la pérdida de agua por evaporación.
 * @param radiacion Radiación solar aproximada en W/m2.
 * @param vpd Déficit de presión de vapor en kPa.
 * @return Índice evaporativo en porcentaje (0-100%).
 */
float calcularIndiceEvaporativo(
  float radiacion,
  float vpd
) {

  float factorRadiacion =
    radiacion /
    RADIACION_REFERENCIA;

  factorRadiacion =
    limitar01(factorRadiacion);


  float factorVPD =
    vpd /
    VPD_REFERENCIA;

  factorVPD =
    limitar01(factorVPD);


  float indice =
    (
      0.50 * factorRadiacion +
      0.50 * factorVPD
    )
    * 100.0;

  return indice;
}

// =====================================================
// TASA DE DESCENSO
// =====================================================
//
// En Wokwi cada 10 segundos representa una hora.
//
// Ejemplo:
//
// Nivel anterior = 70%
// Nivel actual   = 66%
//
// Tasa = 4 puntos porcentuales/hora simulada
// =====================================================

/**
 * Actualiza la tasa e índice de descenso del nivel del reservorio,
 * comparando el nivel actual contra el nivel medido en el intervalo
 * anterior (cada INTERVALO_TASA_MS: 10 s = 1 h simulada en Wokwi;
 * en hardware real usar 3 600 000 ms = 1 h real). Actualiza las
 * variables globales tasaDescenso e indiceDescenso.
 * @param nivelActual Nivel del reservorio en el ciclo actual (%).
 */
void actualizarTasaDescenso(float nivelActual) {

  unsigned long ahora = millis();

  // Primera medición

  if (nivelAnterior < 0) {

    nivelAnterior = nivelActual;

    ultimoCalculoTasa = ahora;

    tasaDescenso = 0;

    indiceDescenso = 0;

    return;
  }

  // Solo recalculamos cada intervalo

  if (
    ahora - ultimoCalculoTasa
    >= INTERVALO_TASA_MS
  ) {

    float diferencia =
      nivelAnterior - nivelActual;

    // Si el nivel aumentó,
    // NO existe descenso.

    if (diferencia < 0) {
      diferencia = 0;
    }

    // Como cada intervalo representa
    // una hora simulada:

    tasaDescenso = diferencia;

    // Convertir tasa a índice 0-100%

    indiceDescenso =
      (
        tasaDescenso /
        TASA_CRITICA
      )
      * 100.0;

    if (indiceDescenso > 100) {
      indiceDescenso = 100;
    }

    if (indiceDescenso < 0) {
      indiceDescenso = 0;
    }

    // Guardar nueva referencia

    nivelAnterior = nivelActual;

    ultimoCalculoTasa = ahora;
  }
}

// =====================================================
// RIESGO HÍDRICO
// =====================================================
//
// 50% -> déficit actual de agua
// 30% -> presión evaporativa
// 20% -> velocidad de descenso
//
// Resultado 0 - 100%
// =====================================================

/**
 * Fusiona las tres señales de riesgo (déficit de nivel 50%, índice
 * evaporativo 30%, índice de descenso 20%) en un único porcentaje
 * de riesgo hídrico. Este valor se complementa en loop() con reglas
 * de seguridad independientes que evitan que una variable
 * individualmente crítica quede oculta por el promedio.
 * @param nivel Nivel actual del reservorio (%).
 * @param indiceEvaporativo Índice evaporativo actual (%).
 * @param indiceDescenso Índice de descenso actual (%).
 * @return Riesgo hídrico combinado (0-100%).
 */
float calcularRiesgoHidrico(
  float nivel,
  float indiceEvaporativo,
  float indiceDescenso
) {

  // Si el reservorio está al 100%:
  // déficit = 0
  //
  // Si está vacío:
  // déficit = 100

  float deficitNivel =
    100.0 - nivel;


  float riesgo =
    0.50 * deficitNivel +
    0.30 * indiceEvaporativo +
    0.20 * indiceDescenso;


  if (riesgo > 100) {
    riesgo = 100;
  }

  if (riesgo < 0) {
    riesgo = 0;
  }


  return riesgo;
}

// =====================================================
// LEDS Y BUZZER
// =====================================================
// Nota: en este circuito los LEDs usan lógica activa en bajo
// (LOW = encendido, HIGH = apagado).
// =====================================================

/** Actúa el estado NORMAL: LED verde encendido, resto apagado, sin sonido. */
void estadoNormal() {

  digitalWrite(
    LED_VERDE,
    LOW
  );

  digitalWrite(
    LED_AMARILLO,
    HIGH
  );

  digitalWrite(
    LED_ROJO,
    HIGH
  );

  noTone(BUZZER_PIN);
}

/** Actúa el estado PRECAUCIÓN: LED amarillo encendido, resto apagado, sin sonido. */
void estadoPrecaucion() {

  digitalWrite(
    LED_VERDE,
    HIGH
  );

  digitalWrite(
    LED_AMARILLO,
    LOW
  );

  digitalWrite(
    LED_ROJO,
    HIGH
  );

  noTone(BUZZER_PIN);
}

/** Actúa el estado CRÍTICO: LED rojo encendido y buzzer sonando a 1000 Hz. */
void estadoCritico() {

  digitalWrite(
    LED_VERDE,
    HIGH
  );

  digitalWrite(
    LED_AMARILLO,
    HIGH
  );

  digitalWrite(
    LED_ROJO,
    LOW
  );

  tone(
    BUZZER_PIN,
    1000
  );
}

// =====================================================
// SETUP
// =====================================================

/**
 * Inicializa comunicación serial, bus I2C (SDA=21, SCL=22), pines de
 * HC-SR04, LEDs y buzzer (todo apagado al inicio), y la pantalla
 * OLED, mostrando una pantalla de bienvenida durante 1.5 s.
 */
void setup() {

  Serial.begin(115200);

  // ---------------- I2C ----------------

  Wire.begin(21, 22);

  // ---------------- HC-SR04 ----------------

  pinMode(
    TRIG_PIN,
    OUTPUT
  );

  pinMode(
    ECHO_PIN,
    INPUT
  );

  // ---------------- LEDs ----------------

  pinMode(
    LED_VERDE,
    OUTPUT
  );

  pinMode(
    LED_AMARILLO,
    OUTPUT
  );

  pinMode(
    LED_ROJO,
    OUTPUT
  );

  // Inicialmente apagados

  digitalWrite(
    LED_VERDE,
    HIGH
  );

  digitalWrite(
    LED_AMARILLO,
    HIGH
  );

  digitalWrite(
    LED_ROJO,
    HIGH
  );

  // ---------------- Buzzer ----------------

  pinMode(
    BUZZER_PIN,
    OUTPUT
  );

  noTone(BUZZER_PIN);

  // ---------------- OLED ----------------

  if (
    !display.begin(
      SSD1306_SWITCHCAPVCC,
      OLED_ADDRESS
    )
  ) {

    Serial.println(
      "ERROR OLED"
    );

    while (true) {
      delay(100);
    }
  }

  display.clearDisplay();

  display.setTextColor(
    SSD1306_WHITE
  );

  display.setTextSize(1);

  display.setCursor(20, 25);

  display.println(
    "Sistema IoT"
  );

  display.setCursor(15, 38);

  display.println(
    "Monitor hidrico"
  );

  display.display();

  delay(1500);
}

// =====================================================
// LOOP
// =====================================================

/**
 * Ciclo principal (cada ~500 ms):
 *   1. Lee sensores ambientales (BME280) e hidráulicos (HC-SR04) y
 *      la señal del panel solar (INA219).
 *   2. Calcula nivel, VPD, radiación, índice evaporativo, tasa/
 *      índice de descenso y riesgo hídrico (lógica de fusión).
 *   3. Clasifica el estado del sistema (CRÍTICO > PRECAUCIÓN >
 *      NORMAL) aplicando primero las reglas de seguridad y luego
 *      el umbral de riesgo combinado.
 *   4. Reporta el estado por el Monitor Serial.
 *   5. Actualiza la pantalla OLED (alternando cada 3 s entre la
 *      vista de mediciones y la vista de análisis/riesgo) y activa
 *      LEDs/buzzer según el estado (alerta 100% local, in situ).
 */
void loop() {

  // ===================================================
  // 1. MEDICIONES AMBIENTALES
  // ===================================================

  float temperatura =
    readTemperatureRaw()
    / 100.0;

  float humedad =
    readHumidityRaw()
    / 100.0;

  float presion =
    readPressureRaw()
    / 100.0;


  // ===================================================
  // 2. RADIACIÓN SOLAR
  // ===================================================

  float corriente_mA =
    readINA219CurrentRaw()
    / 100.0;

  // Nuestro modelo simulado:
  //
  // 10 mA = 100 W/m²

  float radiacion =
    corriente_mA
    * 10.0;


  // ===================================================
  // 3. NIVEL DEL AGUA
  // ===================================================

  float distancia =
    medirDistancia();

  distancia =
    round(
      distancia * 10.0
    )
    / 10.0;

  float nivel =
    calcularNivel(
      distancia
    );


  // ===================================================
  // 4. VPD
  // ===================================================

  float vpd =
    calcularVPD(
      temperatura,
      humedad
    );


  // ===================================================
  // 5. PRESIÓN EVAPORATIVA
  // ===================================================

  float indiceEvaporativo =
    calcularIndiceEvaporativo(
      radiacion,
      vpd
    );


  // ===================================================
  // 6. TASA DE DESCENSO
  // ===================================================

  actualizarTasaDescenso(
    nivel
  );


  // ===================================================
  // 7. RIESGO HÍDRICO
  // ===================================================

  float riesgo =
    calcularRiesgoHidrico(
      nivel,
      indiceEvaporativo,
      indiceDescenso
    );


  // ===================================================
  // 8. CLASIFICACIÓN DEL ESTADO
  // ===================================================

  String estado;


  // ---------------- CRÍTICO ----------------
  //
  // Basta UNA condición crítica:

  if (

    riesgo >= 70

    ||

    nivel <= 15

    ||

    indiceEvaporativo >= 85

    ||

    tasaDescenso >= TASA_CRITICA

  ) {

    estado =
      "CRITICO";

    estadoCritico();
  }


  // ------------- PRECAUCIÓN ----------------

  else if (

    riesgo >= 35

    ||

    nivel <= 40

    ||

    indiceEvaporativo >= 60

    ||

    tasaDescenso >= TASA_PRECAUCION

  ) {

    estado =
      "PRECAUCION";

    estadoPrecaucion();
  }


  // ---------------- NORMAL ------------------

  else {

    estado =
      "NORMAL";

    estadoNormal();
  }


  // ===================================================
  // SERIAL MONITOR
  // ===================================================

  Serial.println(
    "================================"
  );

  Serial.print(
    "Temperatura: "
  );

  Serial.print(
    temperatura,
    1
  );

  Serial.println(
    " C"
  );


  Serial.print(
    "Humedad: "
  );

  Serial.print(
    humedad,
    1
  );

  Serial.println(
    " %"
  );


  Serial.print(
    "Presion: "
  );

  Serial.print(
    presion,
    1
  );

  Serial.println(
    " hPa"
  );


  Serial.print(
    "Radiacion: "
  );

  Serial.print(
    radiacion,
    0
  );

  Serial.println(
    " W/m2"
  );


  Serial.print(
    "Distancia: "
  );

  Serial.print(
    distancia,
    1
  );

  Serial.println(
    " cm"
  );


  Serial.print(
    "Nivel: "
  );

  Serial.print(
    nivel,
    1
  );

  Serial.println(
    " %"
  );


  Serial.print(
    "VPD: "
  );

  Serial.print(
    vpd,
    2
  );

  Serial.println(
    " kPa"
  );


  Serial.print(
    "Indice evaporativo: "
  );

  Serial.print(
    indiceEvaporativo,
    1
  );

  Serial.println(
    " %"
  );


  Serial.print(
    "Tasa descenso: "
  );

  Serial.print(
    tasaDescenso,
    1
  );

  Serial.println(
    " pp/h simulada"
  );


  Serial.print(
    "Indice descenso: "
  );

  Serial.print(
    indiceDescenso,
    1
  );

  Serial.println(
    " %"
  );


  Serial.print(
    "Riesgo hidrico: "
  );

  Serial.print(
    riesgo,
    1
  );

  Serial.println(
    " %"
  );


  Serial.print(
    "ESTADO: "
  );

  Serial.println(
    estado
  );


  // ===================================================
  // OLED
  // ===================================================
  //
  // Alternamos dos pantallas cada 3 segundos.
  //
  // Pantalla 1 = mediciones
  // Pantalla 2 = análisis/riesgo
  // ===================================================

  bool paginaDos =
    (
      millis() / 3000
    )
    % 2;


  display.clearDisplay();

  display.setTextSize(1);

  display.setTextColor(
    SSD1306_WHITE
  );


  // ===================================================
  // PÁGINA 1
  // ===================================================

  if (!paginaDos) {

    display.setCursor(0, 0);

    display.println(
      "MEDICIONES"
    );


    display.setCursor(0, 12);

    display.print("T:");
    display.print(
      temperatura,
      1
    );
    display.print("C ");

    display.print("H:");
    display.print(
      humedad,
      0
    );
    display.print("%");


    display.setCursor(0, 24);

    display.print("P:");
    display.print(
      presion,
      0
    );
    display.print(" hPa");


    display.setCursor(0, 36);

    display.print("Rad:");
    display.print(
      radiacion,
      0
    );
    display.print(" W/m2");


    display.setCursor(0, 48);

    display.print("Nivel:");
    display.print(
      nivel,
      0
    );
    display.print("%");
  }


  // ===================================================
  // PÁGINA 2
  // ===================================================

  else {

    display.setCursor(0, 0);

    display.println(
      "ANALISIS"
    );


    display.setCursor(0, 12);

    display.print("VPD:");
    display.print(
      vpd,
      2
    );
    display.print("kPa");


    display.setCursor(0, 24);

    display.print("Evap:");
    display.print(
      indiceEvaporativo,
      0
    );
    display.print("%");


    display.setCursor(0, 36);

    display.print("Desc:");
    display.print(
      tasaDescenso,
      1
    );
    display.print("pp/h");


    display.setCursor(0, 48);

    display.print("R:");
    display.print(
      riesgo,
      0
    );
    display.print("% ");

    display.print(
      estado
    );
  }


  display.display();

  delay(500);
}