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

### 5.7.1 Calibración contra referencia (*ground truth*)

| Sensor | Referencia | Procedimiento | Resultado |
|---|---|---|---|
| Nivel (HC-SR04 en el tubo) | Regla graduada junto al tubo | Distancias de lleno y vacío capturadas desde el tablero ("Usar como lleno/vacío"); luego 5 o más alturas de agua comparadas con el nivel del tablero | Lleno ≈ 40 cm, vacío = 19.2 (usando la botella por dentro, pero depende de lo que usemos para simularlo) cm |
| Panel + INA219 | No usamos ninguna referencia, solo verificamos prendiéndolo en diferentes momentos del día comparando las sensaciones con los valores que arrojaba | Con sol, irradiancia de referencia en el tablero y "Calcular K" | K = 10 (W/m²)/mA (etiqueta: 10) |
| Cero del panel (INA219) | Panel a oscuras | Promedio de 20 lecturas al arrancar | −0.105 y −0.115 mA (≈ 1 W/m²), restado de todas las lecturas |
| BME280 (T, HR) | Termohigrómetro digital (±1 °C, ±5 % HR según su ficha) | Sonda junto a las rejillas del BME280, 5 a 10 min de estabilización y una lectura por minuto durante 5 min | ΔT ≈ 0.8 °C; ΔHR ≈ 4.7 pp. Estas diferencias son consistenes porque están dentro del rango de incertidumbre de la ficha del higrómetro |
| Buzzer (actuador) | Barrido de frecuencias, de 500 a 4000 Hz | Tono de 0.6 s por frecuencia, anotando cuáles suenan | Suena hasta **2000 Hz**; no suena desde 2500 Hz. El tono de crítico se ajustó de 2500 a 2000 Hz |

> El termohigrómetro tiene una exactitud similar la del BME280 (±1 °C, igual en ambos, y ±5 % contra ±3 % HR según su datasheet [15]), así que la comparación es una **verificación de consistencia** contra un instrumento independiente, no una calibración formal. Sin embargo, nos ayuda a verificar que el módulo que usamos no presenta errores de medición.

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

Además se verificaron a mano lecturas reales del tablero (21.2 °C, HR 42.6 %, 75.1 kPa, sin luz): Δ/(Δ+γ) = 0.756 en el equipo frente a 0.754 calculado; ea = 1.08 kPa en ambos; índice evaporativo = 21.5 frente a 21.6; riesgo = 19.8 en ambos. Las diferencias son de redondeo.

### 5.7.3 Emulación acelerada de condiciones reales

| Condición emulada | Cómo | Observado |
|---|---|---|
| Descenso del nivel | Vaciado del tubo | Escalera NORMAL → PRECAUCIÓN → CRÍTICO en el LCD, los LEDs, el buzzer y el tablero, y vuelta a NORMAL al llenarlo |
| Sol fuerte y aire seco | Equipo al sol (irradiancia medida de 831 W/m², 27.5 °C, 24.8 % HR, VPD 2.76 kPa) | Con el modo demo inicial el índice se saturaba en 100 (ver abajo); tras la corrección queda en ≈ 90 (Priestley-Taylor 60 + VPD 30) |
| Calor sin luz | Secador sobre el BME280, panel a la sombra (44.7 °C, 16.1 % HR, VPD 6.65 kPa) | El índice se queda en 30: sin radiación, Priestley-Taylor da ET = 0 y solo aporta el componente de VPD, que ya está en su tope. Comportamiento esperado del método. Se hizo una prueba también, llegando a unos 70°C y llegándole un poquito de luz; el índice evaporativo subió a crítico y el del sistema solo hasta Precaución: tal y como queríamos |
| Sombra o nube | Tapar el panel | El índice baja a medida que la ventana se llena con la luz nueva (hasta 120 s en modo demo) |

**Corrección encontrada en esta prueba.** En el modo demo inicial, la ventana de 120 s se extrapolaba a un día de 24 h con la misma luz. Con sol real, 831 W/m² equivalían a 72 MJ/m² "por día", 2.5 veces el máximo físico del sitio (28.8 MJ/m²), y la parte de Priestley-Taylor se saturaba siempre. Se cambió el modo demo para tratar la luz de la ventana como el mediodía de un día con esa nubosidad (índice de claridad, Sección 3.2.3). Con la regla nueva, un cielo parcialmente nublado (400 W/m², 21 °C, 50 % HR) pasa de un índice de ≈ 89 a ≈ 52, y el índice vuelve a distinguir días soleados de nublados.

### 5.7.4 Validación de la fusión y de los umbrales

| Caso | Condición | Estado esperado | Estado obtenido |
|---|---|---|---|
| F1 | Tubo lleno, sombra | NORMAL | NORMAL |
| F2 | Tubo lleno, sol fuerte y seco (índice ≥ 85) | **PRECAUCIÓN** (la evaporación sola no lleva a crítico) | PRECAUCIÓN |
| F3 | Nivel ≈ 40 %, sombra | PRECAUCIÓN | PRECAUCIÓN - CRÍTICO por cambios en la posición de la mano al sostener el tubo |
| F4 | Nivel ≈ 40 %, sol fuerte | CRÍTICO por riesgo combinado (≥ 69.2) | CRÍTICO |
| F5 | Nivel ≤ 15 % | CRÍTICO | CRÍTICO |
| F6 | Descenso rápido sostenido (≥ 68 pp/min) | CRÍTICO por tasa | No lo pudimos medir porque manualmente causa discontinuidad |
| F7 | Reposicionamiento brusco (> 8 pp en 1 s) | Sin alarma por tasa (discontinuidad) | Sin alarma |
| F8 | Sensor de nivel desconectado | FALLO | FALLO ("SIN ECHO") |

Falsos positivos observados: 1 (técnicamente medio). Falsos negativos observados: 1.

> El caso F2 motivó una regla nueva: antes del cambio, el equipo quedaba en CRÍTICO al sol con el tubo lleno (nivel 94 %, riesgo 33). Era un falso positivo, y desde entonces la evaporación sola llega como máximo a PRECAUCIÓN (Sección 3.2.6).

### 5.7.5 Pruebas de la notificación

| Prueba | Criterio | Resultado |
|---|---|---|
| Latencia de la alerta | Tiempo entre el cambio físico y el aviso en el tablero. Esperado ≤ ~5 s: confirmación del estado (2 ciclos de 1 s) + consulta del tablero (cada 2 s) | ~4s |
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
| Acceso con clave incorrecta | 5 intentos | Bloqueo de 30 s |
| Acceso desde fuera de la WLAN | Celular con datos móviles | No se puede acceder al tablero |
| Valores fuera de rango | Distancia mayor que "vacío" o menor que "lleno" | El nivel se limita a 0 % o 100 % (`constrain` en `distanciaANivel`) |
| Sensor de nivel o BME280 ausente | Desconectar | Lecturas arrojadas muy incorrectas (Ej. T° > 150 °C) |
| Calibración inválida | Guardar "vacío" menor que "lleno" + 2 cm | El equipo la rechaza con el motivo en rojo y no cambia nada |
| Persistencia de la calibración | Apagar y encender | Queda guardado siempre |

---

## 5.8 Validación del Challenge #3

### Configuración experimental

| Etapa | Gateway | Red | Fecha |
|---|---|---|---|
| **1. Simulación** | Gateway real + Mosquitto con ACL + un segundo Mosquitto haciendo de Ubidots + simulador del ESP32 (`gateway/simulador_esp32.py`) | Local (un computador) | 12/11/2026 |
| **2. Prototipo real, gateway en un PC** | Un computador portátil hace de Raspberry Pi (mismo software: Mosquitto con usuarios y ACL, gateway, SQLite) | Wi-Fi de la casa | 12/11/2026 |
| **3. Prototipo real, gateway en la Raspberry Pi** | Raspberry Pi 5 prestada por la universidad, con Raspberry Pi OS Lite de 64 bits (Debian 13) en la microSD del equipo, instalada con `instalar.sh` | Hotspot de un iPhone (2.4 GHz, WPA2) | 13/11/2026, de 9:44 a 13:41 |

Además, el gateway tiene **22 pruebas automáticas** (`pytest`) que cubren la validación, las ventanas, la regresión, el respaldo de la IA, la cola hacia la nube, el filtro del switch de Ubidots y el control de acceso del bot. Todas pasan. El firmware v8 compila sin advertencias con el core esp32 3.3.12 (90 % de la flash, 24 % de la RAM).

> Los resultados de la etapa 3 salen de la base de datos SQLite y del registro (`journalctl`) que se copiaron de la Pi al terminar las pruebas: 1477 mediciones, 114 cambios de estado, 228 eventos, 2 comandos, 63 recomendaciones de la IA y 423 envíos a Ubidots. Las horas son las de la Pi.

### Resultados de las pruebas de extremo a extremo

| # | Prueba | Criterio de aceptación | Resultado (etapa 2, 12/11/2026) | Resultado en la Pi (etapa 3) |
|---|---|---|---|---|
| 1 | Datos llegan a SQLite | Una medición cada 5 s | ✅ Cada 5 s; ~720 por hora | ✅ Mediana de **12 mediciones por minuto** (una cada 5 s). 1477 mediciones de 9:47 a 13:41; los huecos corresponden a las pruebas de desconexión. 38 muestras se marcaron como anomalía: saltos de nivel al mover el cartón a mano, aceptados al repetirse |
| 2 | Se guarda antes de reenviar | Todo lo que llega a Ubidots está antes en `cola_nube` | ✅ Cola en 0 con Internet; 155 envíos sin pendientes | ✅ 423 mensajes pasaron por `cola_nube`; al final, **0 pendientes** |
| 3 | Escalada PRECAUCIÓN → CRÍTICO | Alarma local, tableros y aviso al celular | ✅ Alarma local, tablero local, Ubidots, aviso por Telegram | ✅ Por ejemplo, 12:47:19 PRECAUCIÓN y 12:47:21 CRÍTICO: LEDs y buzzer, tablero local, Ubidots y aviso por Telegram a los suscriptores aprobados (ver prueba 10) |
| 4 | Silenciar desde Ubidots | El buzzer calla; el switch vuelve a 0 | ✅ 13:36:10: orden de Ubidots → respuesta del ESP32 `ok: 1` en **60 ms** desde el gateway; switch de vuelta en 0 en el mismo segundo | ✅ 11:36:16 y 11:46:10, en CRÍTICO: `ok: 1` en **56 ms** y **15 ms**; el buzzer calló y los LEDs siguieron |
| 5 | Silenciar desde la Pi | Respuesta del ESP32 | No se ejecutó | ⏳ No se alcanzó a ejecutar; queda para la sustentación (`python -m wrews_gw.comando silenciar`). La misma orden sí se probó desde Ubidots (prueba 4) |
| 6 | Recomendación de la IA | Respuesta en el tablero local, en Ubidots y en SQLite | ✅ Claude respondió en 2 a 10 s (típico 8 s); se guardó con su prompt | ✅ 7 consultas a Claude (`claude-opus-5-5`) con `/recomendacion`: de **6,9 a 11,5 s**, cada una guardada con su prompt. Otras 56 recomendaciones salieron de la tabla de reglas: las automáticas y las de los cortes de Internet |
| 7 | Caída de Internet | La alarma local sigue; los datos se envían al volver con su hora | ✅ parcial: corte corto; el aviso de Telegram retenido salió al volver (15:08:56 → 15:09:11) y Ubidots se reconectó en 3 s con la cola en 0. En simulación: cola de 5 mensajes vaciada al volver | ✅ Dos cortes. **12:18–12:26 (8 min):** se cayó la red del hotspot; la Pi guardó 10 mensajes en `cola_nube` y los subió en 5 s al volver (12:26:12–12:26:17), con su hora original. **13:26–13:28:** sin Internet en la Pi; Telegram reintentó cada 15 s, los avisos salieron al volver (13:28:05) y la cola quedó en 0. La alarma local no se afectó |
| 8 | ESP32 apagado | FALLO en ≤ 25 s | ✅ Detectado a los **20 s** (14:29:28); FALLO con `origen: gateway` en Ubidots; volvió a NORMAL al reconectar | ✅ Cuatro desconexiones (13:19, 13:23, 13:26 y 13:28): detectadas a los **20,5 a 21,0 s** de la última medición, con aviso por Telegram. Al reconectar, el estado volvió al real |
| 9 | Broker caído 1 min | La alarma local sigue; reconexión automática | ✅ 14:10:46–14:11:47: alarma local sin cambios; ESP32 y gateway reconectados solos en ~30 s (después se bajó el reintento del gateway a ≤ 5 s) | ✅ 13:37: con el broker detenido, el prototipo siguió alarmando; el gateway registró la última voluntad del ESP32 (`LWT`) a los 3 s. Al arrancar el broker, todo se reconectó solo (comprobado a las 13:39:30) |
| 10 | Latencia ESP32 → Ubidots | Estado: pocos segundos; variables: ≤ 60 s | Estado: se envía al instante (la cola se revisa cada 1 s) | ✅ Medido con las marcas de tiempo de la Pi: del gateway a Ubidots, **mediana 0,8 s** y 90 % en menos de 1,5 s (405 envíos, contando hasta la confirmación de Ubidots). Del cambio de estado al aviso de Telegram, **unos 2 s**. Las variables medidas se promedian en ventanas de 60 s, a propósito |
| 11 | Acceso restringido | Sin clave no hay acceso al broker, a Ubidots ni al bot | ✅ Broker: anónimo y clave errada rechazados (*not authorised*); el usuario `esp32` no puede publicar comandos. Bot: sin clave no hay solicitud; sin aprobación no hay alertas ni comandos | ✅ 13:36:12: publicar en el broker de la Pi sin usuario → `not authorised`. Bot: un usuario nuevo pidió acceso con la clave y quedó pendiente hasta que el administrador lo aprobó (13:21:28 → 13:21:35). Tablero de Ubidots abierto sin sesión (16/11, 21:51): redirige a la página de inicio de sesión |

### Incidentes encontrados en las pruebas y cómo se resolvieron

**1. Lecturas imposibles del BME280.** Durante la etapa 2, la temperatura saltó de 22 °C a **179,7 °C** y la presión llegó a valores negativos (−153 hPa). El gateway marcó como anomalía las 59 muestras afectadas y no las subió a Ubidots. Sin embargo, en el ESP32 esas lecturas entraron a la ventana de evaporación y produjeron una **PRECAUCIÓN falsa**: con T_max = 180 °C, el déficit de vapor de la ventana llegó a 45 kPa y el modelo calculó radiación neta positiva sin luz. Diagnóstico: un contacto intermitente en el bus I²C (SDA/SCL), que corrompe bytes que la compensación de Bosch convierte en valores absurdos. Después de reasentar el cableado, 2 de 319 lecturas siguieron siendo malas. Acciones:
- se agregó al firmware el **filtro de plausibilidad** (sección 3.21);
- el gateway pasó a descartar **solo la variable** fuera de rango y no la muestra completa, para no perder el nivel.

**2. Cupo de SMS agotado.** Los eventos de Ubidots con SMS funcionaron, pero cada reinicio del ESP32 en las pruebas generó un FALLO y un "normal otra vez", y el plan gratuito pidió saldo. Las alertas al celular se pasaron a **Telegram** desde el gateway.

**3. Cambio de IP del gateway.** Al reconectar la Wi-Fi, el computador que hacía de gateway cambió de IP y el ESP32 dejó de conectarse. Se cambió el firmware para buscar el gateway **por nombre** (mDNS), y después del cambio el ESP32 lo encontró solo.

### Costo de la IA medido

| Medida | Valor (12/11/2026) |
|---|---|
| Consultas a Claude | 31 (con la configuración automática del inicio de las pruebas) |
| Tokens de entrada / salida | 21 978 / 23 690 (≈ 700 / 750 por consulta) |
| Costo total aproximado | **USD 0,56** (≈ USD 0,02 por consulta) |
| Latencia | 2 a 10 s, típico 8 s |

A partir de esta medición, el modelo pasó a consultarse **solo a pedido**: en operación normal el costo es cero.

---

[⬅ Anterior: Modelo de negocio](04-Modelo-de-Negocio.md) · [⬆ Índice](00-Home.md) · [Siguiente: Autoevaluación del protocolo de pruebas ➡](06-Autoevaluacion-Pruebas.md)
