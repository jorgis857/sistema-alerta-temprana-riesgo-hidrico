[⬅ Volver al índice](00-Home.md)

# 5. Configuración experimental, resultados y análisis

## 5.1 Estrategia de validación

La validación de WREWS se desarrolló en **dos etapas complementarias**. Primero se utilizó **Wokwi** para comprobar la arquitectura, la adquisición de variables y la lógica de fusión en un entorno controlado. Posteriormente, el sistema fue ensamblado como un **prototipo físico funcional**, verificando el comportamiento real de los sensores, el procesamiento local en el ESP32 y la activación de las alertas.

### Etapa 1 — Simulación en Wokwi

El proyecto de simulación está disponible en:

<https://wokwi.com/projects/472250559337371649>

Se utilizaron *custom chips* para representar el BME280, el panel fotovoltaico y el INA219, además del sensor ultrasónico disponible en Wokwi.

Esta etapa permitió:

- modificar las variables de entrada de forma controlada;
- comprobar los cálculos intermedios;
- verificar la adquisición mediante I²C;
- probar la lógica de fusión;
- comprobar los estados NORMAL, PRECAUCIÓN y CRÍTICO;
- depurar el firmware antes de realizar el montaje físico.

### Etapa 2 — Prototipo físico

La implementación final integra:

- **ESP32** como unidad central de adquisición y procesamiento.
- **Sensor ultrasónico OKY3261/HC-SR04** para estimar el nivel.
- **BME280** para temperatura, humedad relativa y presión atmosférica.
- **Mini panel fotovoltaico + INA219** para obtener una estimación de la irradiancia solar.
- **LCD 16×2 I²C** para visualización local.
- **LED verde, amarillo y rojo** para representar los estados del sistema.
- **Buzzer** para la alarma sonora.

Para probar el nivel de manera controlada, la maqueta utiliza una **plataforma móvil que representa la superficie del agua**.

Al subir o bajar esta plataforma cambia la distancia detectada por el sensor ultrasónico y, por tanto, el porcentaje de nivel calculado.

Esto permite reproducir diferentes condiciones de almacenamiento sin exponer directamente la electrónica al agua.

Todo el procesamiento y la generación de alertas se realizan **localmente en el ESP32**, sin depender de una red de comunicaciones.

---

## 5.2 Procesamiento de la información

WREWS no determina el riesgo utilizando una sola variable.

El procesamiento integra tres componentes principales:

### 1. Disponibilidad actual

El sensor ultrasónico mide la distancia entre el sensor y la superficie que representa el agua.

A partir de la calibración del reservorio se transforma esta distancia en un **porcentaje de nivel**.

Un nivel elevado representa mayor disponibilidad de agua, mientras que un nivel bajo aumenta el riesgo de desabastecimiento.

### 2. Condiciones ambientales

El BME280 obtiene:

- temperatura;
- humedad relativa;
- presión atmosférica.

La temperatura y la humedad se utilizan para calcular el **déficit de presión de vapor (VPD)**.

El VPD se combina con la irradiancia estimada mediante el panel fotovoltaico y el INA219 para generar un **índice de condiciones favorables a la evaporación**.

Este índice no representa directamente la cantidad de agua evaporada. Su función es indicar qué tan favorables son las condiciones ambientales para que ocurra evaporación.

La presión atmosférica se conserva como una variable ambiental de contexto y no actúa directamente como disparador del riesgo.

### 3. Tendencia del nivel

El sistema compara varias mediciones del nivel a lo largo del tiempo.

Esto permite calcular una **tasa de descenso**, utilizada para identificar si el nivel está disminuyendo de manera acelerada.

Por tanto, WREWS puede diferenciar entre un nivel determinado que permanece relativamente estable y un nivel que está disminuyendo rápidamente.

---

## 5.3 Fusión del riesgo

El índice general de riesgo utiliza tres componentes:

```text
Déficit de nivel                 50 %
Condiciones evaporativas        30 %
Tasa de descenso                20 %
```

De forma conceptual:

```text
RIESGO =
0.50 × Déficit de nivel
+
0.30 × Índice evaporativo
+
0.20 × Tendencia
```

Además del resultado ponderado, el firmware utiliza **reglas de seguridad**.

Estas reglas permiten escalar el estado cuando una variable individual alcanza una condición crítica, evitando que un riesgo importante quede oculto por el promedio de las demás variables.

Finalmente, WREWS clasifica la situación en:

- 🟢 **NORMAL**
- 🟡 **PRECAUCIÓN**
- 🔴 **CRÍTICO**

---

## 5.4 Resultados de simulación

Durante la etapa de diseño se definieron diferentes escenarios en Wokwi para comprobar las rutas de clasificación del algoritmo.

| Caso | Distancia | Temp. | Humedad | Irradiancia | Nivel | VPD | Índice evap. | Tasa descenso | Riesgo | Estado esperado |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 — Escenario favorable | 4.0 cm | 18.0 °C | 70 % | 300 W/m² | 96.3 % | 0.62 kPa | 25.3 % | 0.0 pp/h | 9.4 % | 🟢 **NORMAL** |
| C2 — Riesgo combinado | 15.0 cm | 22.0 °C | 55 % | 600 W/m² | 55.6 % | 1.19 kPa | 49.8 % | 1.0 pp/h | 41.2 % | 🟡 **PRECAUCIÓN** |
| C3 — Nivel bajo | 20.0 cm | 24.0 °C | 45 % | 500 W/m² | 37.0 % | 1.64 kPa | 52.4 % | 1.5 pp/h | 53.2 % | 🟡 **PRECAUCIÓN** |
| C4 — Evaporación alta | 5.0 cm | 25.0 °C | 15 % | 650 W/m² | 92.6 % | 2.69 kPa | 77.4 % | 0.5 pp/h | 28.9 % | 🟡 **PRECAUCIÓN** |
| C5 — Nivel muy bajo | 27.0 cm | 20.0 °C | 60 % | 400 W/m² | 11.1 % | 0.94 kPa | 35.6 % | 0.5 pp/h | 57.1 % | 🔴 **CRÍTICO** |
| C6 — Evaporación extrema | 12.0 cm | 33.0 °C | 15 % | 1150 W/m² | 66.7 % | 4.28 kPa | 100.0 % | 1.0 pp/h | 50.7 % | 🔴 **CRÍTICO** |
| C7 — Tasa de descenso alta | 14.0 cm | 21.0 °C | 60 % | 350 W/m² | 59.3 % | 0.99 kPa | 34.1 % | 6.0 pp/h | 50.6 % | 🔴 **CRÍTICO** |
| C8 — Riesgo combinado ≥ 70 % | 24.0 cm | 29.0 °C | 25 % | 900 W/m² | 22.2 % | 3.00 kPa | 95.0 % | 3.0 pp/h | 79.4 % | 🔴 **CRÍTICO** |

> Estos valores corresponden a la etapa de simulación y fueron utilizados para validar la lógica del algoritmo. La implementación física utiliza la calibración correspondiente a las dimensiones reales de la maqueta.

---

## 5.5 Resultados del prototipo físico

Una vez integrados los componentes se realizaron pruebas funcionales sobre el montaje completo.

El objetivo fue comprobar la cadena:

```text
SENSADO
   ↓
ADQUISICIÓN
   ↓
PROCESAMIENTO
   ↓
FUSIÓN DE INFORMACIÓN
   ↓
CLASIFICACIÓN
   ↓
ACTUACIÓN
```

Los resultados obtenidos fueron:

| Prueba | Elemento evaluado | Comportamiento esperado | Resultado |
|---|---|---|---|
| P1 | Sensor ultrasónico y nivel | La altura de la plataforma modifica coherentemente el nivel calculado | ✅ Correcto |
| P2 | BME280 | Lectura de temperatura, humedad y presión mediante I²C | ✅ Correcto |
| P3 | Panel fotovoltaico + INA219 | La señal cambia según la iluminación y permite estimar irradiancia | ✅ Correcto |
| P4 | Estado NORMAL | Condiciones favorables → LED verde y sin alarma crítica | ✅ Correcto |
| P5 | Estado PRECAUCIÓN | Condición intermedia → LED amarillo | ✅ Correcto |
| P6 | Estado CRÍTICO | Condición crítica → LED rojo y alarma sonora | ✅ Correcto |
| P7 | LCD 16×2 I²C | Visualización local de información y estado | ✅ Correcto |
| P8 | Procesamiento local | Clasificación y actuación sin conexión de red | ✅ Correcto |
| P9 | Tasa de descenso | Comparación de mediciones sucesivas para detectar disminuciones aceleradas | ✅ Correcto |

Las pruebas permitieron comprobar el **funcionamiento completo del prototipo** y la correspondencia entre la lógica previamente validada en Wokwi y el comportamiento del montaje físico.

---

## 5.6 Análisis de resultados

### Validación progresiva

La simulación permitió depurar la lógica y comprobar el comportamiento esperado antes del montaje.

Posteriormente, la implementación física permitió confirmar que la arquitectura podía funcionar utilizando sensores y actuadores reales.

### Fusión de múltiples variables

El sistema no depende únicamente del porcentaje de nivel.

WREWS integra:

```text
Disponibilidad actual
        +
Condiciones ambientales
        +
Tendencia del nivel
        ↓
Riesgo hídrico
```

Esto permite obtener una evaluación más completa que la obtenida utilizando únicamente una medición instantánea del nivel.

### Respuesta de las alertas

Durante las pruebas físicas se verificaron los tres estados:

```text
NORMAL       → LED verde
PRECAUCIÓN   → LED amarillo
CRÍTICO      → LED rojo + buzzer
```

La pantalla LCD permite consultar localmente la información procesada por el sistema.

### Irradiancia estimada

El mini panel fotovoltaico y el INA219 proporcionan una señal relacionada con la radiación recibida.

En esta etapa del proyecto se utiliza como una **estimación experimental de irradiancia**.

Una medición metrológica precisa en W/m² requeriría una calibración frente a un instrumento de referencia.

### Presión atmosférica

Aunque el BME280 registra presión atmosférica, esta variable se utiliza principalmente como información de contexto.

Debido a que se espera una variación relativamente pequeña en un punto fijo de instalación, la presión no participa directamente en la lógica principal de generación de alertas.

### Alcance de la validación

La plataforma móvil permite reproducir cambios de nivel de manera controlada, repetible y segura.

Por tanto, las pruebas realizadas permiten validar el funcionamiento del prototipo a escala de laboratorio.

Una implementación en un reservorio real requeriría posteriormente calibración específica para su geometría y condiciones ambientales.

---

[⬅ Anterior: Modelo de negocio](04-Modelo-de-Negocio.md) · [⬆ Índice](00-Home.md) · [Siguiente: Autoevaluación del protocolo de pruebas ➡](06-Autoevaluacion-Pruebas.md)