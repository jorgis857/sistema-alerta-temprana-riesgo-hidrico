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
Déficit de nivel                 54 %   (50 % en el Challenge #1)
Condiciones evaporativas        30 %
Tasa de descenso                16 %   (20 % en el Challenge #1)
```

De forma conceptual:

```text
RIESGO =
0.54 × Déficit de nivel
+
0.30 × Índice evaporativo
+
0.16 × Tendencia
```

Los pesos del Challenge #2 son el vector del método AHP (Sección 3.2.5); las pruebas de simulación de la Sección 5.4 se hicieron con los pesos del Challenge #1.

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

En los ocho casos, el estado obtenido en la simulación coincidió con el estado esperado según el modelo.

> Estos valores corresponden a la etapa de simulación y fueron utilizados para validar la lógica del algoritmo. La implementación física utiliza la calibración correspondiente a las dimensiones reales de la maqueta.

> Las tasas de esta tabla se expresan en pp/h y corresponden a la formulación
> inicial de la tendencia (diferencia entre mediciones consecutivas), previa a
> la adopción de la regresión sobre ventana deslizante descrita en la Sección
> 3.2.4. Se conservan como evidencia del proceso de desarrollo.

> El caso C6 (33 °C, 15 % HR) constituye un escenario sintético fuera de la
> envolvente climática de la Sabana de Bogotá. Se incluyó para verificar la
> saturación del índice evaporativo, no como condición esperable en la región.

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
| P9 | Tasa de descenso | Estimación de la pendiente por regresión sobre ventana deslizante, con banda muerta derivada del ruido medido | ✅ Correcto |

### 5.5.1 Caracterización del sensor y calibración de umbrales

Antes de fijar los parámetros de detección de tendencia se caracterizó experimentalmente el ruido del sensor ultrasónico. Con la plataforma inmóvil se tomaron 20 mediciones y se calculó su desviación estándar.

| Magnitud | Valor medido |
|---|---|
| σ de distancia | 0.4 cm |
| σ de nivel (sobre recorrido de 17 cm) | 2.4 pp |
| Ventana de estimación | 20 muestras · 20 s |
| Error típico de la pendiente | 1.8 pp/min |
| Banda muerta aplicada | 5.5 pp/min |

El error típico de una pendiente ajustada por mínimos cuadrados sobre *n* puntos repartidos en un lapso *T* es `SE = σ·√12 / (T·√n)`. La banda muerta se fijó en tres veces ese valor, lo que sitúa la probabilidad de falso positivo por debajo del 1 %. El procedimiento se ejecuta **automáticamente en cada arranque**, de modo que la banda se adapta al montaje concreto en lugar de depender de un valor elegido a priori.

Los umbrales de tendencia se calibraron mediante dos maniobras controladas de descenso continuo, registrando la pendiente máxima estimada en cada una:

| Maniobra | Pendiente máxima | Umbral derivado |
|---|---|---|
| Descenso lento sostenido | **46.9 pp/min** | PRECAUCIÓN = 33 pp/min (70 % de la lenta) |
| Descenso rápido | **98.2 pp/min** | CRÍTICO = 68 pp/min (media geométrica) |

Se eligió la media geométrica sobre la aritmética porque ambas maniobras se comparan por proporción —la rápida es 2.1 veces la lenta— y la geométrica deja el mismo margen relativo a cada lado: un factor de 1.45 en ambos casos.

El detector de discontinuidad impone además un techo: 8 pp entre mediciones consecutivas equivalen a 1.4 cm/s sobre este recorrido, por encima de lo cual el movimiento se clasifica como reposicionamiento y no como descenso.

**Cero del piranómetro.** Se caracterizó promediando 20 lecturas del INA219 con el panel sin iluminación, obteniendo −0.11 mA (−0.105 y −0.115 mA en dos arranques del 4 de octubre de 2026, equivalentes a ≈ 1 W/m²). Ese valor corresponde al offset del amplificador del INA219 más la corriente de fuga del panel, y se resta de todas las lecturas posteriores. Desde el firmware v7 solo se toma como cero si su magnitud es menor de 1 mA (10 W/m²): un valor mayor indica que había luz sobre el panel al encender, y tomarlo como cero restaría esa luz de todas las lecturas. La pendiente de la escala se deriva de la corriente de cortocircuito declarada por el fabricante (100 mA a 1000 W/m²), valor **pendiente de verificación experimental**: las etiquetas de paneles pequeños suelen declarar la corriente en el punto de máxima potencia, típicamente entre 5 y 10 % menor que la de cortocircuito.

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

## 5.7 Validación del Challenge #2

El banco de pruebas del Challenge #2 se organizó según los bloques mínimos del enunciado. Las pruebas se hicieron sobre el equipo integrado (carcasa, tubo de PVC, alimentación por pilas) con el firmware v7, al sol, y con el tablero abierto desde celulares y PC conectados al hotspot que hace de WLAN de la zona.

> Las celdas marcadas con ⟨completar⟩ corresponden a mediciones que el equipo debe registrar con sus propios datos.

### Criterios de aceptación

Fijados en la hoja de trabajo del equipo antes de las pruebas:

| Prueba | Criterio de aceptación | Resultado |
|---|---|---|
| Nivel contra referencia | Error ≤ ±1 cm tras calibración | ⟨completar⟩ |
| Temperatura y humedad contra referencia | T ≤ ±1 °C; HR ≤ ±5 % | ⟨completar⟩ |
| Fusión y umbrales | ≥ 12 escenarios × 3 repeticiones; 0 falsos negativos en escenarios críticos; ≤ 1 falso positivo; sin oscilación al bajar de estado | ⟨completar⟩ |
| Latencia | Alarma física ≤ 2 s y tablero ≤ 5 s tras el evento (desde que se cumple la condición; la escalera de estados agrega la confirmación) | ⟨completar⟩ |
| Acceso restringido | Un dispositivo no autorizado no accede a los datos | ⟨completar⟩ |
| Caída de la WLAN | La alerta in situ continúa; reconexión automática < 60 s | ✅ alerta in situ continúa; tiempo de reconexión ⟨completar⟩ |
| Repetibilidad | Desviación estándar del nivel ≤ 0.5 cm; *jitter* del periodo de muestreo < 5 % con el tablero en uso | ⟨completar⟩ |
| Consumo | Consumo medio reportado; autonomía objetivo ≥ 24 h | ⟨completar⟩ |
| Larga duración | 12–24 h encendido sin reinicios | ⟨completar⟩ |

> Sobre el criterio de acceso: en la implementación final, un dispositivo fuera de la subred de la WLAN recibe **403**, y uno dentro de la WLAN pero sin sesión es enviado al inicio de sesión (**401** en la API). La lista blanca de IP planeada se reemplazó por la sesión con usuario y contraseña (ver [Sección 12.4](12-Mejoras-Challenge-1.md)).

### 5.7.1 Calibración contra referencia (*ground truth*)

| Sensor | Referencia | Procedimiento | Resultado |
|---|---|---|---|
| Nivel (HC-SR04 en el tubo) | Regla graduada junto al tubo | Distancias de lleno y vacío capturadas desde el tablero ("Usar como lleno/vacío"); luego 5 o más alturas de agua comparadas con el nivel del tablero | Lleno = ⟨completar⟩ cm, vacío = ⟨completar⟩ cm; error medio = ⟨completar⟩ pp; error máximo = ⟨completar⟩ pp |
| Panel + INA219 | ⟨completar: piranómetro o estación de referencia⟩ | Con sol, irradiancia de referencia en el tablero y "Calcular K" (regresión por el origen si hay varias medidas) | K = ⟨completar⟩ (W/m²)/mA (etiqueta: 10); R² = ⟨completar⟩ |
| Cero del panel (INA219) | Panel a oscuras | Promedio de 20 lecturas al arrancar | −0.105 y −0.115 mA (≈ 1 W/m²), restado de todas las lecturas |
| BME280 (T, HR) | Termohigrómetro digital (±1 °C, ±5 % HR según su ficha) | Sonda junto a las rejillas del BME280, 5 a 10 min de estabilización y una lectura por minuto durante 5 min | ΔT = ⟨completar⟩ °C; ΔHR = ⟨completar⟩ pp. Consistentes si caen dentro de la exactitud de la referencia |
| Buzzer (actuador) | Barrido de frecuencias, de 500 a 4000 Hz | Tono de 0.6 s por frecuencia, anotando cuáles suenan | Suena hasta **2000 Hz**; no suena desde 2500 Hz. El tono de crítico se ajustó de 2500 a 2000 Hz |

> El termohigrómetro tiene una exactitud del mismo orden que la del BME280 (±1 °C y ±3 % HR según su datasheet [15]), así que la comparación es una **verificación de consistencia** contra un instrumento independiente, no una calibración formal.

### 5.7.2 Verificación del modelo de evaporación

En cada arranque, el firmware ejecuta pruebas de Priestley-Taylor contra valores de referencia calculados de forma independiente (en Python, con las mismas ecuaciones). Resultados en el ESP32 real:

| Prueba | Esperado | Obtenido en el ESP32 | Resultado |
|---|---|---|---|
| Rs = 17 MJ/m², T = 14 °C (20/7), HR = 75 %, P = 75 kPa, Ra = 37.5 | Δ = 0.1038, γ = 0.0499, Δ/(Δ+γ) = 0.675, ea = 1.253, ET = 4.67 ± 0.05 mm/día | Δ = 0.1037, γ = 0.0499, f = 0.675, ea = 1.253, Rn = 13.46, ET = 4.675 | ✅ |
| Mismo caso con Ra = 36 | ET = 4.61 ± 0.05 | Rn = 13.27, ET = 4.608 | ✅ |
| Día despejado de referencia (Rs = Rso) | ET = ET_REF = 7.5 ± 0.05 | Rn = 20.80, ET = 7.483 | ✅ |
| Oscuridad (Rs = 0) | Rn = 0, ET = 0, sin valores negativos | Rn = 0, ET = 0 | ✅ |
| Ventana cubierta al 8 % | Sin estimación (CALCULANDO) | Sin estimación | ✅ |
| Modo campo: ventana de 120 s y de 24 h con la misma luz | Mismo Rs equivalente (43.2 MJ/m²) | 43.20 y 43.20 | ✅ |
| Modo demo: luz de mediodía despejado (G_pico = 1048.8 W/m²) y luz constante de 500 W/m² | Rs = Rso = 28.84 MJ/m²; con 500 W/m², Rs = 500/G_pico · Rso = 13.75 MJ/m² (± 0.1) | 28.84 y 13.75 MJ/m² (*) | ✅ (*) |

(*) Esta prueba se agregó en el firmware v7 y su salida no quedó registrada del monitor serial del ESP32. El valor reportado se obtuvo ejecutando en un PC la misma lógica del firmware (llenado de los 24 *buckets* con 120 muestras de 1 s y cálculo del modo demo) en precisión `float` de 32 bits, como la del ESP32: 28.8432 y 13.7510 MJ/m², frente a 28.8432 y 13.7510 esperados. Al arrancar, el equipo ejecuta esta misma prueba e imprime el resultado en el monitor serial.

Además se verificaron a mano lecturas reales del tablero (21.2 °C, HR 42.6 %, 75.1 kPa, sin luz): Δ/(Δ+γ) = 0.756 en el equipo frente a 0.754 calculado; ea = 1.08 kPa en ambos; índice evaporativo = 21.5 frente a 21.6; riesgo = 19.8 en ambos. Las diferencias son de redondeo.

### 5.7.3 Emulación acelerada de condiciones reales

| Condición emulada | Cómo | Observado |
|---|---|---|
| Descenso del nivel | Vaciado del tubo | Escalera NORMAL → PRECAUCIÓN → CRÍTICO en el LCD, los LEDs, el buzzer y el tablero, y vuelta a NORMAL al llenarlo |
| Sol fuerte y aire seco | Equipo al sol (irradiancia medida de 831 W/m², 27.5 °C, 24.8 % HR, VPD 2.76 kPa) | Con el modo demo inicial el índice se saturaba en 100 (ver abajo); tras la corrección queda en ≈ 90 (Priestley-Taylor 60 + VPD 30) |
| Calor sin luz | Secador sobre el BME280, panel a la sombra (44.7 °C, 16.1 % HR, VPD 6.65 kPa) | El índice se queda en 30: sin radiación, Priestley-Taylor da ET = 0 y solo aporta el componente de VPD, que ya está en su tope. Comportamiento esperado del método |
| Sombra o nube | Tapar el panel | El índice baja a medida que la ventana se llena con la luz nueva (hasta 120 s en modo demo) |

**Corrección encontrada en esta prueba.** En el modo demo inicial, la ventana de 120 s se extrapolaba a un día de 24 h con la misma luz. Con sol real, 831 W/m² equivalían a 72 MJ/m² "por día", 2.5 veces el máximo físico del sitio (28.8 MJ/m²), y la parte de Priestley-Taylor se saturaba siempre. Se cambió el modo demo para tratar la luz de la ventana como el mediodía de un día con esa nubosidad (índice de claridad, Sección 3.2.3). Con la regla nueva, un cielo parcialmente nublado (400 W/m², 21 °C, 50 % HR) pasa de un índice de ≈ 89 a ≈ 52, y el índice vuelve a distinguir días soleados de nublados.

### 5.7.4 Validación de la fusión y de los umbrales

| Caso | Condición | Estado esperado | Estado obtenido |
|---|---|---|---|
| F1 | Tubo lleno, sombra | NORMAL | ⟨completar⟩ |
| F2 | Tubo lleno, sol fuerte y seco (índice ≥ 85) | **PRECAUCIÓN** (la evaporación sola no lleva a crítico) | ⟨completar⟩ |
| F3 | Nivel ≈ 40 %, sombra | PRECAUCIÓN | ⟨completar⟩ |
| F4 | Nivel ≈ 40 %, sol fuerte | CRÍTICO por riesgo combinado (≥ 69.2) | ⟨completar⟩ |
| F5 | Nivel ≤ 15 % | CRÍTICO | ⟨completar⟩ |
| F6 | Descenso rápido sostenido (≥ 68 pp/min) | CRÍTICO por tasa | ⟨completar⟩ |
| F7 | Reposicionamiento brusco (> 8 pp en 1 s) | Sin alarma por tasa (discontinuidad) | ⟨completar⟩ |
| F8 | Sensor de nivel desconectado | FALLO | ⟨completar⟩ |
| F9 | Nivel justo en 50 % (borde de precaución) | PRECAUCIÓN (la regla es ≤ 50 %) | ⟨completar⟩ |
| F10 | Nivel justo en 15 % (borde de crítico) | CRÍTICO (la regla es ≤ 15 %) | ⟨completar⟩ |
| F11 | Recuperación: llenar el tubo desde CRÍTICO | CRÍTICO → PRECAUCIÓN → NORMAL, sin oscilar (3 ciclos de confirmación para bajar) | ⟨completar⟩ |
| F12 | Alarma silenciada desde el tablero y el estado empeora | El silencio se cancela y el buzzer vuelve a sonar | ⟨completar⟩ |

Falsos positivos observados: ⟨completar⟩. Falsos negativos observados: ⟨completar⟩.

> El caso F2 motivó una regla nueva: antes del cambio, el equipo quedaba en CRÍTICO al sol con el tubo lleno (nivel 94 %, riesgo 33). Era un falso positivo, y desde entonces la evaporación sola llega como máximo a PRECAUCIÓN (Sección 3.2.6).

### 5.7.5 Pruebas de la notificación

| Prueba | Criterio | Resultado |
|---|---|---|
| Latencia de la alerta | Tiempo entre el cambio físico y el aviso en el tablero. Esperado ≤ ~5 s: confirmación del estado (2 ciclos de 1 s) + consulta del tablero (cada 2 s) | ⟨completar con cronómetro o con la antigüedad del evento⟩ |
| Actualización del valor actual | El tablero muestra "dato de hace X s" | Valores observados de 0.1 a 0.4 s |
| Actualización del histórico | Las gráficas se actualizan cada 5 s con un punto cada 2 s | ✅ observado |
| Avisos | Cada cambio de estado muestra un aviso, suena y vibra | ✅ observado |
| Desactivación de la alarma desde el tablero | El buzzer se calla 15 min, los LEDs siguen, queda un evento | ✅ observado |
| Alarma física por estado | Tonos distintos en precaución (1000 Hz) y crítico (2000 Hz) | ✅ tras el ajuste a 2000 Hz |

### 5.7.6 Robustez y casos límite

| Prueba | Procedimiento | Resultado |
|---|---|---|
| Pérdida y reconexión de la WLAN | Apagar y volver a prender los datos o el hotspot con el tablero abierto | **Primera versión:** el tablero se quedaba en "Sin conexión" y, al recargar, la página no cargaba. **Tras la corrección** (cancelación de peticiones a los 4 s, reconexión sin cortar intentos en curso, Wi-Fi sin ahorro de energía y reinicio del servidor al volver la red), la alarma local siguió funcionando durante la caída y el tablero se recuperó solo al volver la red. En la prueba del tablero con red simulada, la recuperación tomó 1.2 s |
| Recarga y apertura desde otro dispositivo tras la caída | Recargar, abrir desde un segundo celular o PC | ✅ tras la corrección |
| Acceso con clave incorrecta | 5 intentos | ⟨completar⟩ (esperado: bloqueo de 30 s y evento por intento) |
| Acceso desde fuera de la WLAN | Celular con datos móviles | ⟨completar⟩ (esperado: no llega al equipo) |
| Valores fuera de rango | Distancia mayor que "vacío" o menor que "lleno" | El nivel se limita a 0 % o 100 % ⟨confirmar⟩ |
| Sensor de nivel o BME280 ausente | Desconectar | ⟨completar⟩ (esperado: FALLO con los tres LEDs) |
| Calibración inválida | Guardar "vacío" menor que "lleno" + 2 cm | El equipo la rechaza con el motivo en rojo y no cambia nada |
| Persistencia de la calibración | Apagar y encender | ⟨completar⟩ (esperado: "Cargados de la flash" en el arranque) |

### 5.7.7 Repetibilidad, precisión y desempeño

| Prueba | Resultado |
|---|---|
| Repetición de la maniobra de vaciado (3 a 5 veces) | Tasa máxima: ⟨completar media ± desviación⟩; tiempo hasta CRÍTICO: ⟨completar⟩ |
| Ruido del nivel en reposo (caracterización automática) | ⟨completar con el σ del tubo⟩ |
| Consumo | Corriente de las pilas en NORMAL: ⟨completar⟩ mA; en CRÍTICO: ⟨completar⟩ mA |
| Autonomía estimada | ⟨completar⟩ h con 4×AA (≈ ⟨completar⟩ mAh) |

---

[⬅ Anterior: Modelo de negocio](04-Modelo-de-Negocio.md) · [⬆ Índice](00-Home.md) · [Siguiente: Autoevaluación del protocolo de pruebas ➡](06-Autoevaluacion-Pruebas.md)
