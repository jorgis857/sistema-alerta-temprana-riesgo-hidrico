[⬅ Volver al índice](00-Home.md)

# 3. Desarrollo teórico modular

## 3.1 Criterios de diseño establecidos

| Criterio | Decisión de diseño | Justificación |
|---|---|---|
| **Independencia de red** | Toda la lógica de decisión corre en el ESP32; no hay llamadas a servicios externos. El tablero del Challenge #2 solo publica lo que el equipo ya decidió | La alarma *in situ* funciona aunque la WLAN no esté disponible |
| **Medición en hilo propio (Ch. #2)** | Tres hilos de FreeRTOS: medición (núcleo 0), alarmas (núcleo 1) y servidor/LCD (`loop()`, núcleo 1) | Cumple la restricción del enunciado y evita que un navegador lento o una caída de la red congelen la alarma física |
| **Acceso restringido (Ch. #2)** | Misma subred que el equipo + sesión con usuario y contraseña | Solo dispositivos autorizados y conectados a la WLAN de la zona ven los datos o actúan sobre la alarma |
| **Producto cerrado (Ch. #2)** | Calibración desde el tablero, guardada en la flash del ESP32 | La carcasa no se abre para ajustar el equipo en el sitio |
| **Trazabilidad de los parámetros (Ch. #2)** | Cada constante del modelo cita su fuente en el código y en la Sección 7.5; las que no tienen fuente se declaran como supuesto | Responde a la observación del Challenge #1 de que los valores no se anclaban a literatura ni normativa |
| **Modularidad funcional** | El firmware se organiza por responsabilidades: lectura de sensores, cálculo de nivel, VPD, índice evaporativo, tasa de descenso, riesgo y actuación | Facilita mantenimiento, depuración y reemplazo de sensores |
| **Múltiples señales, una decisión** | El riesgo hídrico depende de la fusión de nivel, condiciones evaporativas y tendencia | Responde a la necesidad de combinar múltiples señales para una alerta más completa |
| **Ninguna variable crítica queda oculta por el promedio** | Se incorporan reglas de seguridad independientes al promedio ponderado | Reduce el riesgo de falsos negativos ante condiciones individuales extremas |
| **Calibración simple** | El nivel se ajusta mediante parámetros de distancia correspondientes a lleno y vacío (en el Challenge #2, desde el tablero) | Permite adaptar el sistema a distintas geometrías |
| **Simulación antes del montaje físico** | Se validó inicialmente la arquitectura y lógica en Wokwi | Redujo errores antes de integrar sensores reales |
| **Validación física posterior** | El sistema fue implementado sobre una maqueta funcional | Permite verificar sensores, actuadores y comportamiento real del sistema |
| **Legibilidad para usuarios no técnicos** | LCD 16×2 I²C + LEDs semafóricos + buzzer | Facilita la interpretación local del estado |
| **Enfoque en la problemática hídrica** | El nivel y su tendencia son las variables principales; la presión se mantiene como contexto | Mantiene la lógica alineada con el riesgo de disponibilidad y desabastecimiento |

---

## 3.2 Modelo matemático de fusión de datos

### 3.2.1 Nivel del reservorio

El porcentaje de nivel se calcula a partir de la distancia medida por el sensor ultrasónico:

```text
Nivel (%) =
100 × (D_vacío - D_medida)
      ----------------------
      (D_vacío - D_lleno)
```

El resultado se limita al rango:

```text
0 % ≤ Nivel ≤ 100 %
```

En la implementación física, `D_lleno` y `D_vacío` corresponden a la calibración real de la maqueta.

---

### 3.2.2 Déficit de presión de vapor — VPD

La temperatura y la humedad relativa permiten calcular el déficit de presión de vapor.

De forma general:

```text
e_s = presión de vapor de saturación
e_a = presión de vapor actual

VPD = e_s - e_a
```

El VPD representa la capacidad del aire para aceptar vapor de agua adicional.

Un valor mayor indica condiciones más favorables para la evaporación.

---

### 3.2.3 Índice evaporativo

> **Challenge #2:** el índice del Challenge #1 (50 % irradiancia normalizada + 50 % VPD normalizado, con un factor de altitud sobre la irradiancia) se reemplazó por la **evaporación potencial diaria de Priestley-Taylor** [5] con los parámetros de **FAO-56** [6]. El reparto 50/50 no tenía respaldo en la literatura; el modelo nuevo sí, y además usa la presión medida en vez de un factor fijo.

#### Ecuación de Priestley-Taylor

```text
λ·ET = α · Δ/(Δ+γ) · (Rn − G)        [MJ/m²·día]
ET   = λ·ET / λ                       [mm/día]
```

Es una simplificación de Penman que conserva el término radiativo y reemplaza el aerodinámico por el coeficiente α. Rosenberry et al. [7] compararon 15 métodos en un lago de montaña contra el balance de energía, y Priestley-Taylor quedó entre los tres mejores (error medio de 0.19 mm/día).

#### Cálculo, en el orden del firmware

Con los promedios de una ventana móvil de mediciones (T media, Tmax, Tmin, HR media, P media):

| # | Magnitud | Fórmula | Fuente |
|---|---|---|---|
| 1 | Presión de vapor de saturación | `es(T) = 0.6108 · exp(17.27·T / (T + 237.3))` | [6] ec. 11 |
| 2 | Pendiente de la curva de saturación | `Δ = 4098 · es(T) / (T + 237.3)²` | [6] ec. 13 |
| 3 | Constante psicrométrica, con la **presión medida** | `γ = 0.000665 · P` | [6] ec. 8 |
| 4 | Presión de vapor real | `ea = (HR/100) · (es(Tmax) + es(Tmin)) / 2` | [6] ec. 19 |
| 5 | Radiación de cielo despejado | `Rso = (0.75 + 2·10⁻⁵ · z) · Ra` | [6] ec. 37 |
| 6 | Relación de nubosidad | `r = Rs / Rso`, limitada entre 0.3 y 1.0 | [6] (máximo); el mínimo es supuesto propio |
| 7 | Onda corta neta | `Rns = (1 − a) · Rs` | [6] ec. 38 |
| 8 | Onda larga neta | `Rnl = σ · (Tmax,K⁴ + Tmin,K⁴)/2 · (0.34 − 0.14·√ea) · (1.35·r − 0.35)` | [6] ec. 39 |
| 9 | Radiación neta | `Rn = max(Rns − Rnl, 0)` | [6] |
| 10 | Flujo de calor almacenado | `G = 0` a escala diaria | [6] ec. 42 (supuesto en agua) |
| 11 | Evaporación potencial | `ET = α · Δ/(Δ+γ) · Rn / λ` | [5] |

#### Constantes

| Constante | Valor | Fuente / estado |
|---|---|---|
| α (Priestley-Taylor) | 1.26 | [5], superficie de agua libre sin advección. Seleshi [14] encontró 1.11 en trópico de altura; se deja configurable y su calibración en el embalse es trabajo futuro |
| Albedo del agua `a` | 0.06 | [8]; Xiao et al. [12] midieron 0.041 y 0.079 |
| Calor latente λ | 2.45 MJ/kg | [6] |
| σ (Stefan-Boltzmann) | 4.903·10⁻⁹ MJ·K⁻⁴·m⁻²·día⁻¹ | [6] ec. 39 |
| Altitud `z` | 2560 m | Sitio; **solo** se usa en Rso. γ usa la presión medida |
| Radiación extraterrestre Ra | 36 MJ/m²·día, fija | [6] ec. 21 y anexo 2. A ~5° N varía entre ~33.5 y ~37.5: error < 3 % en ET sin necesidad de fecha ni reloj |
| Constante del panel K | 10 (W/m²)/mA | Etiqueta del panel (100 mA a 1000 W/m²) [9], [10]. **Pendiente de calibrar con sol** |

#### Ventana móvil y modos

El modelo es válido a escala diaria [5], [6]. La energía de radiación y los promedios de T, HR y P se acumulan en una ventana móvil de 24 *buckets* (no se guarda cada muestra: 24 h a 1 Hz serían 86 400 muestras).

- **Modo campo:** ventana de 24 h reales. `Rs_día = energía acumulada · 86 400 / tiempo cubierto`.
- **Modo demo:** ventana corta (120 s por defecto) cuyo promedio de luz se toma como **el mediodía de un día con esa nubosidad**, mediante el índice de claridad: `Rs_día = min(G / G_pico, 1) · Rso`, con `G_pico = π · Rso / (2 · 12 h) ≈ 1049 W/m²`, la irradiancia de un mediodía despejado del sitio para un día senoidal de 12 h. Una primera versión extrapolaba la ventana corta a 24 h iguales; con sol real (831 W/m²) eso daba 72 MJ/m² "por día", 2.5 veces el máximo físico, y el índice se saturaba siempre (ver [Sección 7.2](07-Conclusiones-Trabajo-Futuro.md)).
- Mientras la ventana esté cubierta en menos del 50 %, el estado de la evaporación es `CALCULANDO`: el índice vale 0 y no dispara reglas. En el tablero se muestra como "estimación en curso".

#### Índice evaporativo (0–100)

```text
Índice_evap = 70 · min(ET / ET_REF, 1) + 30 · min(VPD / VPD_REF, 1)
ET_REF  = 7.5 mm/día   (ET de un día despejado del sitio con este mismo modelo)
VPD_REF = 2.0 kPa      (supuesto: tarde seca del percentil alto de la Sabana)
VPD     = (es(Tmax) + es(Tmin))/2 − ea   ([6] ec. 12), promedio de la ventana
```

- **ET_REF** sale del propio modelo con Rs = Rso, T = 16 °C (22/8 °C), HR = 65 %, P = 75 kPa: Rn = 20.8 MJ/m²·día, Δ/(Δ+γ) = 0.699, ET = 7.48 mm/día. Así el 100 % de la parte de Priestley-Taylor es la demanda evaporativa máxima posible del sitio, sin traer un número de afuera.
- **El componente de VPD (30 %)** se justifica con Jansen et al. [11]: en un embalse grande, a escala de horas y días la evaporación sigue sobre todo al gradiente de vapor y al viento, que Priestley-Taylor no ve. El peso de 0.3 es el reparto aerodinámico de Penman γ/(Δ+γ) [6] a 16 °C y 75 kPa. Como α ya incluye en promedio la parte aerodinámica, el VPD se lee como señal de variación diaria, no como una evaporación que se suma. WREWS no mide viento ni temperatura del agua, así que el VPD del aire es una aproximación.
- **El VPD es el de la ventana**, no el de un instante: así queda en la misma escala de tiempo que ET y no salta con cada pico de mediodía.

Este índice:

> **No representa el porcentaje de agua que se evapora.**

Representa, en una escala relativa, qué tan favorables son las condiciones ambientales para la evaporación, normalizado contra un día despejado del propio sitio.

**Papel de la presión atmosférica.** La presión no se emplea como indicador de riesgo: en una estación fija de la región tropical su variación es de apenas un par de hectopascales sobre una presión de fondo de ~745 hPa, y no cambia cuando hay desabastecimiento. Sí participa como **parámetro del modelo de evaporación**, a través de la constante psicrométrica `γ = 0.665·10⁻³·P`, que determina el reparto entre el término radiativo y el aerodinámico. En el Challenge #2 entra directamente en Δ/(Δ+γ) con la presión medida por el BME280; el factor de altitud fijo del Challenge #1 se eliminó.

**Papel de la humedad en Priestley-Taylor.** La humedad solo entra al término radiativo a través de `ea` en Rnl, con un efecto pequeño (≈ 3 % al bajar la HR de 75 a 50 %). Sin luz, Rn = 0 y la parte de Priestley-Taylor vale 0 por mucho calor que haga: en esas condiciones el índice solo puede llegar a 30 por el componente de VPD. Esto se observó en las pruebas con secador sin luz sobre el panel (Sección 5.7).

**Supuestos declarados:**

1. Superficie de agua libre sin efecto oasis [5]: se cumple en un embalse; el banco de pruebas no lo cumple y solo valida la cadena de cálculo, no el valor absoluto de evaporación.
2. G ≈ 0 a escala diaria: [6] lo justifica para suelo; para agua profunda, Jansen et al. [11] y Xiao et al. [12] advierten que el calor almacenado no es despreciable.
3. Rnl de FAO-56, calibrada para tierra, aplicada sobre agua: aproximación habitual.
4. Ra fijo: error < 3 % en ET.
5. Modo demo: supone una forma de día típica de 12 h; no reemplaza la ventana de 24 h de campo.

---

### 3.2.4 Tasa e índice de descenso

La primera versión del sistema estimaba la tendencia restando dos mediciones consecutivas de nivel. Ese método resultó inviable ya que con el ruido del sensor la tasa superaba por mucho el umbral crítico, incluso con la plataforma quieta.

La versión final estima la pendiente por **regresión lineal por mínimos cuadrados** sobre una ventana de las últimas 20 mediciones. La regresión promedia el ruido de todas las muestras en vez de depender de dos.

```text
Tasa (pp/min) = − pendiente de la recta ajustada a los pares (tiempo, nivel) de la ventana
```

Cuando el nivel sube, la pendiente se trunca a cero: una recarga no constituye riesgo hídrico.

**Banda muerta.** Por debajo de un umbral derivado del ruido medido del propio sensor, la pendiente se fuerza a cero. Ese umbral se calcula automáticamente en cada arranque (ver Sección 5).

**Discontinuidades.** Un reservorio real no cambia de nivel de forma instantánea. Variaciones superiores a 8 puntos porcentuales entre mediciones consecutivas se interpretan como recarga del reservorio —o, en la maqueta, como reposicionamiento manual de la plataforma— y descartan el historial acumulado de tendencia. Sin este tratamiento, la regresión ajustada sobre un escalón produce una pendiente que crece por sí sola mientras el escalón avanza por la ventana.

**Precauciones numéricas.** El eje temporal se expresa relativo a la muestra más antigua de la ventana. Usando el tiempo absoluto del sistema en punto flotante, los términos del denominador de la regresión se aproximan entre sí y su diferencia se pierde por cancelación a los pocos minutos de encendido.

### 3.2.5 Riesgo hídrico

El riesgo general se calcula mediante:

```text
Riesgo =
0.54 × Déficit de nivel
+
0.30 × Índice evaporativo
+
0.16 × Índice de descenso
```

La mayor ponderación corresponde al nivel porque representa directamente la disponibilidad actual de agua.

**Origen de los pesos (Challenge #2).** No existe una fuente que fije "el nivel pesa 50 %"; lo que sí existe es un método citado para derivar pesos de criterio experto: el **Proceso Analítico Jerárquico (AHP)** de Saaty [18], el más usado para construir índices compuestos de sequía [19]. Se compararon las tres señales por pares en la escala 1–9 de Saaty:

| | Nivel | Evaporación | Tasa |
|---|---|---|---|
| **Nivel** | 1 | 2 | 3 |
| **Evaporación** | 1/2 | 1 | 2 |
| **Tasa** | 1/3 | 1/2 | 1 |

El nivel es "levemente más importante" que la evaporación y "moderadamente más importante" que la tasa, y la evaporación es levemente más importante que la tasa: el nivel es la variable de estado, la evaporación es el forzante dominante en El Niño y la tasa es la señal más ruidosa de las tres. El vector de pesos resultante es **54 / 30 / 16 %**, con una razón de consistencia **CR = 0.008** (< 0.10, el límite de Saaty). Los 50/30/20 del Challenge #1 eran prácticamente ese mismo vector redondeado.

---

### 3.2.6 Reglas de clasificación de estado

La lógica de clasificación incorpora el índice ponderado y reglas de seguridad.

| Estado | Condición general |
|---|---|
| 🔴 **CRÍTICO** | Riesgo elevado o alguna variable individual alcanza un umbral crítico (excepto la evaporación, ver abajo) |
| 🟡 **PRECAUCIÓN** | Riesgo intermedio o alguna variable supera su umbral de advertencia |
| 🟢 **NORMAL** | Ninguna condición de precaución o crítica está activa |

La implementación utiliza umbrales definidos en el firmware para:

- nivel;
- índice evaporativo;
- tasa de descenso;
- riesgo combinado.

Estos valores corresponden a parámetros iniciales de diseño y pueden recalibrarse para una instalación real.

**La evaporación sola lleva como máximo a PRECAUCIÓN (Challenge #2).** El estado es la peor severidad de nivel, tasa y riesgo, y de la evaporación limitada a precaución. La evaporación es un forzante, no la disponibilidad de agua: con el embalse lleno, un mediodía seco y soleado no es una emergencia, y dejar que disparara CRÍTICO producía falsos positivos (se observó en las pruebas al sol, Sección 5.7). Su severidad completa se sigue reportando en el tablero ("demanda extrema") y entra al riesgo con su peso del 30 %: con el nivel bajo, el riesgo combinado sí lleva a CRÍTICO.

---

### 3.2.7 Umbrales aplicados

| Variable | PRECAUCIÓN | CRÍTICO | Origen del valor |
|---|---|---|---|
| Nivel del reservorio | ≤ 50 % | ≤ 15 % | Fases de los Planes Especiales de Sequía de España [20], [21] (prealerta 0.50, emergencia 0.15); caso Chingaza 2024, racionamiento con el sistema en 16.5 % [22] |
| Índice evaporativo | ≥ 60 | ≥ 85 (solo como severidad; el estado llega como máximo a PRECAUCIÓN) | **Supuesto.** El 100 % tiene base física (ET_REF); 60 y 85 deben cerrarse con los percentiles 80 y 95 de una estación del IDEAM, método del US Drought Monitor [23] |
| Tasa de descenso | ≥ 33 pp/min | ≥ 68 pp/min | **Calibración experimental** (Sección 5); editables desde el tablero |
| Riesgo ponderado | ≥ 36.2 | ≥ 69.2 | Derivados de los de nivel, al estilo de los indicadores por fases como el CDI europeo [24] |

**Derivación de los umbrales de riesgo.** No hay literatura para el número exacto porque el índice es propio; se derivan de los umbrales de nivel, que sí están citados:

```text
PRECAUCIÓN = 0.54·(100 − 50) + 0.30·20 + 0.16·20 = 36.2   (nivel en precaución, el resto en reposo)
CRÍTICO    = 0.54·(100 − 15) + 0.30·60 + 0.16·33 = 69.2   (nivel en crítico, el resto en su precaución)
```

**Mapeo de las fases de los PES a los estados de WREWS:**

| Fase en los PES | Índice | Estado WREWS |
|---|---|---|
| Normalidad | > 0.50 | NORMAL |
| Prealerta y alerta | 0.50 a 0.15 | PRECAUCIÓN |
| Emergencia | ≤ 0.15 | CRÍTICO |

Limitación declarada: el índice de los PES es el volumen normalizado contra la historia del propio embalse, no exactamente el porcentaje de llenado; para el prototipo es una aproximación razonable.

Referencias de normalización del índice evaporativo: ET_REF = 7.5 mm/día y VPD_REF = 2.0 kPa (Sección 3.2.3). La de VPD se fijó a partir del clima local: a 24 °C la presión de vapor de saturación es 2.98 kPa, de modo que 2.0 kPa representa una tarde seca del percentil alto de la región. Una referencia mayor dejaría el índice permanentemente por debajo de sus umbrales.

Los umbrales de tasa corresponden al banco de pruebas, donde la plataforma se desplaza manualmente en segundos. No deben interpretarse como límites hidrológicos de un reservorio real: en campo, con una escala temporal de horas, los valores equivalentes serían del orden de 0.03 y 0.08 pp/min.

### 3.2.8 Escalera de estados y confirmación temporal

Las transiciones se producen de un nivel a la vez, incluso cuando las condiciones instantáneas corresponden a un estado dos escalones por encima. Así PRECAUCIÓN es siempre observable, lo que permite anticipar la escalada y deja el historial completo en el registro.

La confirmación es **asimétrica**: dos ciclos consecutivos para escalar y tres para desescalar. Los costos de los dos errores posibles no son equivalentes: alertar tarde en un evento de desabastecimiento puede impedir la respuesta, mientras que sostener una alerta unos segundos de más no tiene costo operativo. La banda muerta, los retardos de confirmación y la escalera de estados son prácticas de gestión de alarmas industriales: la norma ANSI/ISA-18.2 exige que el sistema soporte banda muerta y retardos [16], y EEMUA 191 da valores de referencia para la banda muerta [17].

El estado **FALLO** no participa de la escalera. No es un nivel de riesgo sino una condición del equipo —ausencia de eco del ultrasónico, o del BME280 en el bus I²C— y se entra y se sale de forma directa. Su señalización, los tres LEDs parpadeando a la vez, no se confunde con ningún estado operativo: un sistema de alerta que enmudece cuando pierde un sensor es la peor falla posible.

## 3.3 Diagramas UML

Diagramas actualizados al firmware v7 del Challenge #2 (`firmware/wrews/wrews.ino` y `tablero.h`).

### 3.3.1 Diagrama de estados

```mermaid
stateDiagram-v2
    [*] --> NORMAL

    NORMAL --> PRECAUCION: condición de advertencia\n(confirmada 2 ciclos)
    PRECAUCION --> CRITICO: condición crítica\n(confirmada 2 ciclos)
    CRITICO --> PRECAUCION: riesgo disminuye\n(confirmado 3 ciclos)
    PRECAUCION --> NORMAL: condiciones mejoran\n(confirmado 3 ciclos)

    NORMAL --> FALLO: sin eco o sin BME280
    PRECAUCION --> FALLO: sin eco o sin BME280
    CRITICO --> FALLO: sin eco o sin BME280
    FALLO --> NORMAL: sensores de vuelta

    state NORMAL {
        [*] --> LED_Verde
        LED_Verde: LED verde fijo
        LED_Verde: buzzer apagado
    }

    state PRECAUCION {
        [*] --> LED_Amarillo
        LED_Amarillo: LED amarillo fijo
        LED_Amarillo: buzzer 1000 Hz, 150 ms cada 4 s
    }

    state CRITICO {
        [*] --> LED_Rojo
        LED_Rojo: LED rojo parpadeando
        LED_Rojo: buzzer 2000 Hz, 250 ms cada 1.2 s
    }

    state FALLO {
        [*] --> Tres_LEDs
        Tres_LEDs: los tres LEDs parpadeando
        Tres_LEDs: buzzer 600 Hz, 120 ms cada 3 s
    }
```

Se sube y se baja de a un peldaño: de NORMAL nunca se salta directo a CRÍTICO, así PRECAUCIÓN siempre es observable. En cualquier estado, el silencio desde el tablero calla solo el buzzer durante 15 min; si el estado empeora, el silencio se cancela.

---

### 3.3.2 Diagrama de secuencia — ciclo de medición

```mermaid
sequenceDiagram
    participant TM as tareaMedicion (núcleo 0)
    participant ULTRA as HC-SR04
    participant I2C as Bus I²C (mtx_i2c)
    participant EST as Estado compartido (mtx_estado)
    participant TA as tareaAlarmas (núcleo 1)
    participant ACT as LEDs / Buzzer

    loop cada 1 s (vTaskDelayUntil)
        TM->>ULTRA: 5 pulsos TRIG, mediana de 5 ecos
        ULTRA-->>TM: distancia
        TM->>I2C: tomar bus
        TM->>I2C: leer BME280 (T, HR, P) e INA219 (corriente)
        TM->>I2C: liberar bus
        TM->>EST: tomar candado
        TM->>TM: nivel, tasa (regresión), ventana de evaporación,<br/>Priestley-Taylor, índice, riesgo
        TM->>TM: clasificar y aplicar escalera de estados
        TM->>TM: registrar eventos e historial
        TM->>EST: liberar candado
    end

    loop cada 10 ms
        TA->>EST: copiar estado y silencio
        TA->>ACT: patrón de LEDs y buzzer
    end
```

La lectura del HC-SR04 (~100 ms) se hace **antes** de tomar el candado del estado, para no frenar las alarmas. El orden de los candados es fijo (nunca se toma el del bus teniendo el del estado), lo que evita bloqueos mutuos.

---

### 3.3.3 Diagrama de secuencia — tablero de control

```mermaid
sequenceDiagram
    actor U as Autoridad (navegador en la WLAN)
    participant SRV as loop(): servidor web
    participant EST as Estado compartido
    participant TA as tareaAlarmas

    U->>SRV: GET /
    SRV-->>U: redirige a /login (sin sesión)
    U->>SRV: POST /login (usuario, clave)
    SRV->>SRV: ¿misma subred? ¿credenciales? (bloqueo tras 5 fallos)
    SRV-->>U: cookie con token de sesión, redirige a /
    U->>SRV: GET / (tablero)

    loop cada 2 s
        U->>SRV: GET /api/actual
        SRV->>EST: copiar estado (candado)
        SRV-->>U: JSON con valores actuales
        opt cambió el último evento
            U->>SRV: GET /api/eventos?desde=N
            SRV-->>U: eventos nuevos → aviso en pantalla
        end
    end

    loop cada 5 s
        U->>SRV: GET /api/historial
        SRV-->>U: últimos 10 min (1 punto cada 2 s)
    end

    U->>SRV: POST /api/silenciar
    SRV->>EST: silenciarAlarma() (candado)
    TA->>EST: lee "silenciado"
    TA->>TA: buzzer apagado 15 min, LEDs igual
    SRV-->>U: confirmación + evento
```

---

### 3.3.4 Diagrama de componentes de software

```mermaid
classDiagram

    class TareaMedicion {
        +tomarMuestra()
        +actualizarModelo()
        +guardarHistorial()
    }

    class SensorUltrasonico {
        +leerDistancia()
    }

    class SensoresI2C {
        +leerBME280()
        +leerINA219()
    }

    class ModuloNivel {
        +distanciaANivel()
        +calcularTasa()
    }

    class ModuloEvaporacion {
        +ventanaAcumular()
        +evaluarVentana()
        +priestleyTaylor()
        +indiceEvaporativo()
    }

    class ModuloRiesgo {
        +severidad()
        +calcularObjetivo()
        +aplicarEstado()
    }

    class TareaAlarmas {
        +actualizarAlarmas()
        +buzzer()
        +silenciarAlarma()
    }

    class LoopPrincipal {
        +servidor.handleClient()
        +vigilarWiFi()
        +mostrarPagina()
    }

    class ServidorWeb {
        +procesarLogin()
        +apiActual()
        +apiHistorial()
        +apiEventos()
        +apiSilenciar()
        +apiParametros()
    }

    class Parametros {
        +cargarParametros()
        +guardarParametros()
        +validarParametros()
    }

    class RegistroEventos {
        +registrarEvento()
    }

    TareaMedicion --> SensorUltrasonico
    TareaMedicion --> SensoresI2C
    TareaMedicion --> ModuloNivel
    TareaMedicion --> ModuloEvaporacion
    TareaMedicion --> ModuloRiesgo
    ModuloRiesgo --> RegistroEventos
    TareaAlarmas --> ModuloRiesgo : lee estado
    LoopPrincipal --> ServidorWeb
    ServidorWeb --> RegistroEventos
    ServidorWeb --> TareaAlarmas : silenciar
    ServidorWeb --> Parametros
    Parametros --> ModuloNivel : distancias, tasa
    Parametros --> ModuloEvaporacion : K, ET_REF, modo
```

---

## 3.4 Arquitectura física

La versión final presentada utiliza los siguientes componentes:

```text
                 ┌───────────────┐
                 │     ESP32     │
                 │ procesamiento │
                 └───────┬───────┘
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
Sensor ultrasónico     BME280        Panel + INA219
Nivel                  T / HR / P     Irradiancia aprox.

                         │
                         ▼
                 Procesamiento local
                         │
                         ▼
              NORMAL / PRECAUCIÓN /
                     CRÍTICO
                         │
          ┌──────────────┼──────────────┬──────────────────┐
          ▼              ▼              ▼                  ▼
      LCD 16×2         LEDs           Buzzer     Wi-Fi → tablero web
                                                 (WLAN de la zona)
```

La simulación original de Wokwi se conserva en la carpeta `/hardware/wokwi` como evidencia del proceso de diseño previo. Corresponde al firmware del Challenge #1; el firmware v7 (tareas de FreeRTOS, Wi-Fi y servidor web) se validó directamente sobre el hardware.

El hardware físico final utiliza una LCD 16×2 I²C como interfaz local.

---

## 3.5 Comunicación I²C

El sistema aprovecha el bus I²C para conectar varios módulos al ESP32.

Los dispositivos principales son:

| Dispositivo | Interfaz | Dirección |
|---|---|---|
| BME280 | I²C | `0x76` |
| INA219 | I²C | `0x40` |
| LCD 16×2 | I²C | `0x27` |

El firmware escanea el bus al arrancar e identifica cada dispositivo por su dirección; si falta el BME280 el equipo pasa a FALLO, y si falta el INA219 la irradiancia se toma como 0.

El bus utiliza las líneas:

```text
SDA
SCL
```

compartidas entre los dispositivos.

Cada módulo utiliza una dirección propia, permitiendo que el ESP32 pueda comunicarse con varios periféricos sobre el mismo bus.

En el Challenge #2 el bus lo usan dos hilos distintos: la tarea de medición (BME280 e INA219) y `loop()` (LCD). Un mutex (`mtx_i2c`) garantiza que nunca haya dos transacciones I²C a la vez.

---

## 3.6 Sensor ultrasónico

El sensor ultrasónico utiliza dos señales digitales:

```text
TRIG
ECHO
```

El ESP32 genera un pulso sobre `TRIG`.

El sensor responde mediante `ECHO`, cuya duración permite estimar la distancia.

De manera simplificada:

```text
ESP32
  │
  ├── TRIG ──→ Sensor
  │
  └── ECHO ←── Sensor
```

Esta distancia se transforma posteriormente en porcentaje de nivel.

---

## 3.7 Pantalla LCD 16×2 I²C

La interfaz física final utiliza una pantalla LCD 16×2 con adaptador I²C.

La pantalla cumple dos funciones principales:

1. presentar información relevante del sistema;
2. mostrar al usuario el estado de riesgo.

Debido a la limitación de 16 caracteres por 2 filas, la interfaz prioriza la información esencial y organiza las variables en diferentes vistas o ciclos de actualización.

El procesamiento de todas las variables continúa realizándose internamente en el ESP32 aunque no todas se muestren simultáneamente.

En el firmware v7 la LCD rota entre siete páginas cada 2.5 s; la séptima muestra el estado del Wi-Fi y la **IP del tablero**, que es como el usuario sabe a qué dirección entrar (el detalle de las páginas está en la [Sección 2.14](02-Solucion-Propuesta.md)).

---

## 3.8 LEDs y buzzer

Los LEDs utilizan una codificación semafórica:

```text
Verde     → NORMAL
Amarillo  → PRECAUCIÓN
Rojo      → CRÍTICO
```

El buzzer actúa como alarma sonora adicional en el estado crítico.

En el firmware v7 cada estado tiene su patrón, para que se reconozca sin mirar el equipo:

| Estado | LEDs | Buzzer |
|---|---|---|
| NORMAL | Verde fijo | Apagado |
| PRECAUCIÓN | Amarillo fijo | 1000 Hz, 150 ms cada 4 s |
| CRÍTICO | Rojo parpadeando (200 ms cada 400 ms) | 2000 Hz, 250 ms cada 1.2 s |
| FALLO | Los tres parpadeando | 600 Hz, 120 ms cada 3 s |

Los LEDs son de ánodo común (se encienden en `LOW`). El buzzer es **pasivo** y se maneja con PWM (LEDC). La frecuencia del PWM se cambia solo cuando cambia el estado, y cada pitido se enciende y apaga con el ciclo útil (50 % / 0 %), que no reinicia la onda. El tono de crítico es de **2000 Hz** porque un barrido de 500 a 4000 Hz mostró que el buzzer del prototipo no suena desde 2500 Hz (Sección 5.7).

El silencio desde el tablero apaga **solo el buzzer** durante 15 minutos: los LEDs siguen mostrando el estado, porque la condición de riesgo no desaparece porque alguien la reconozca.

Esto proporciona dos mecanismos de notificación:

```text
VISUAL
LCD + LEDs

SONORO
Buzzer
```

---

## 3.9 Diseño de la maqueta

Para validar el sensor de nivel se construyó una maqueta con una plataforma móvil.

La plataforma representa la superficie del agua.

```text
Plataforma arriba
       ↓
Distancia pequeña
       ↓
Nivel alto

Plataforma abajo
       ↓
Distancia grande
       ↓
Nivel bajo
```

Esta solución permitió:

- controlar la distancia;
- repetir escenarios;
- observar las transiciones de estado;
- evitar contacto entre agua y electrónica;
- acelerar las pruebas durante la validación.

---

## 3.10 Estrategia de simulación

Antes del montaje físico se desarrolló una versión funcional en Wokwi.

La simulación permitió:

- validar el sensor ultrasónico;
- comprobar el bus I²C;
- simular temperatura, humedad y presión;
- simular el panel y el INA219;
- probar la lógica matemática;
- modificar las variables mediante controles;
- verificar NORMAL, PRECAUCIÓN y CRÍTICO.

En Wokwi se utilizaron *custom chips* para representar componentes que requerían comportamiento configurable.

La simulación original utiliza una pantalla OLED como componente virtual. Posteriormente, durante la implementación física, esta interfaz fue reemplazada por una **LCD 16×2 I²C** disponible para el equipo.

Este cambio no modifica la arquitectura lógica del sistema: ambos dispositivos cumplen la función de visualización local mediante I²C.

---

## 3.11 Estrategia de implementación física

Después de validar la lógica en simulación se integró el prototipo físico.

El proceso general fue:

```text
Prueba del ESP32
      ↓
Sensor ultrasónico
      ↓
LCD + buzzer
      ↓
BME280
      ↓
Panel + INA219
      ↓
LEDs
      ↓
Integración completa
      ↓
Calibración
      ↓
Pruebas de estados
```

Durante esta etapa se realizaron ajustes propios del hardware real, especialmente relacionados con:

- calibración de distancia;
- estabilidad de las lecturas;
- bus I²C;
- actuación de LEDs;
- comportamiento del buzzer;
- organización de la información en la LCD.

---

## 3.12 Estándares y buenas prácticas de ingeniería

| Estándar / práctica | Aplicación |
|---|---|
| **I²C** | Comunicación entre ESP32, BME280, INA219 y LCD |
| **UML** | Modelado de estados, secuencia y componentes |
| **Codificación semafórica** | Verde = normal, amarillo = precaución, rojo = crítico |
| **Diseño modular** | Separación de lectura, procesamiento, fusión y actuación |
| **Validación progresiva** | Simulación antes de implementación física |
| **Reglas de seguridad** | Condiciones críticas individuales pueden prevalecer sobre el promedio |
| **Procesamiento local** | El sistema no depende de servicios externos para generar alertas |
| **Calibración** | Los parámetros del nivel se ajustan a la geometría del sistema evaluado |
| **FAO-56 (Allen et al.) [6] y Priestley-Taylor [5]** | Ecuaciones de radiación neta, Δ, γ y evaporación potencial (Ch. #2) |
| **AHP de Saaty [18]** | Derivación de los pesos 54/30/16 del riesgo (Ch. #2) |
| **Planes Especiales de Sequía — Orden TEC/1399/2018 [20], [21]** | Umbrales de nivel de 50 % y 15 % (Ch. #2) |
| **ANSI/ISA-18.2 [16] y EEMUA 191 [17]** | Gestión de alarmas: banda muerta, retardos de confirmación, escalera de estados y silencio sin ocultar el estado |
| **IEEE 802.11 (Wi-Fi) [29]** | Enlace del ESP32 a la WLAN de la zona, banda de 2.4 GHz (Ch. #2) |
| **HTTP/1.1 — RFC 9110 [30]** | Servidor web embebido y API JSON del tablero (Ch. #2) |
| **FreeRTOS / ESP-IDF [31]** | Tareas por núcleo, `vTaskDelayUntil` y mutex para el estado compartido (Ch. #2) |

---

## 3.13 Flujo completo del sistema

```text
SENSOR ULTRASÓNICO
        ↓
      NIVEL
        │
        │
        ├───────────────────────────┐
        │                           │
        ▼                           │
 DÉFICIT DE NIVEL                   │
      54 %                          │
                                    │
BME280                              │
T + HR + P                          │
  ↓                                 │
 VPD · Δ/(Δ+γ) ─┐                   │
                ├→ PRIESTLEY-TAYLOR │
PANEL           │  + VPD            │
  ↓             │  ÍNDICE EVAP. ───┤
INA219          │       30 %        │
  ↓             │                   │
IRRADIANCIA ────┘                   │
                                    ├→ RIESGO
NIVEL EN EL TIEMPO                  │
        ↓                           │
TASA DE DESCENSO ───────────────────┘
       16 %
        ↓
REGLAS DE SEGURIDAD
        ↓
NORMAL / PRECAUCIÓN / CRÍTICO
        ↓
LCD + LEDs + Buzzer   ·   tablero web en la WLAN
```

---

## 3.14 Concurrencia: medición en un hilo propio (Challenge #2)

El enunciado exige que la medición se ejecute desde una ISR o desde un hilo distinto al principal. El firmware v7 usa tres hilos de FreeRTOS [31]:

| Hilo | Núcleo | Prioridad | Periodo | Responsabilidad |
|---|---|---|---|---|
| `tareaMedicion` | 0 | 2 | 1 s (`vTaskDelayUntil`) | Lee los sensores, actualiza el modelo (nivel, tasa, evaporación, riesgo), decide el estado y guarda historial y eventos |
| `tareaAlarmas` | 1 | 2 | 10 ms | LEDs y buzzer |
| `loop()` | 1 | 1 | continuo | Servidor web, vigilancia del Wi-Fi y páginas del LCD |

- **Por qué las alarmas van aparte del servidor:** un navegador lento o una caída de la WLAN pueden bloquear `loop()` unos segundos; con las alarmas en su propia tarea, la alarma física no se congela nunca.
- **Estado compartido:** un mutex (`mtx_estado`) protege todas las variables que leen o escriben varios hilos. Las lecturas lentas de los sensores se hacen **fuera** del candado, que solo se toma para actualizar el estado.
- **Bus I²C:** un segundo mutex (`mtx_i2c`) evita que la tarea de medición y el LCD usen el bus al mismo tiempo.
- **Orden fijo de los candados** (nunca se toma el del bus teniendo el del estado), para que no haya bloqueos mutuos.
- **No se usan ISR:** las lecturas I²C y los cálculos en coma flotante no deben ejecutarse dentro de una rutina de interrupción.

---

## 3.15 Conectividad: Wi-Fi en modo estación (Challenge #2)

- **Modo estación (STA):** el ESP32 se une a la WLAN que las autoridades ofrecen en la zona; en la demostración, el hotspot de un celular. No crea su propia red, de acuerdo con el enunciado.
- **Banda de 2.4 GHz** (IEEE 802.11 b/g/n [29]); el ESP32 no se conecta a redes de 5 GHz.
- **Una o dos redes configuradas.** El equipo se une a la que encuentre con mejor señal y, si una se cae, prueba con la otra. Los nombres y las claves van en `secrets.h`, que no se sube al repositorio (plantilla en `secrets.example.h`).
- **Sin ahorro de energía en el radio** (`WiFi.setSleep(false)`): con el ahorro activo, el ESP32 deja de escuchar entre paquetes y con hotspots de celular el tablero a veces no respondía. Aumenta el consumo (ver Sección 6.3).
- **Reconexión.** Si la red se cae, el ESP32 intenta reconectarse solo; si en 30 s no lo logra, el firmware reintenta. Al volver la red se reinician el servidor web y el anuncio mDNS, para que recargar la página o abrirla desde otro dispositivo funcione aunque el hotspot se haya reiniciado.
- **Dirección del tablero.** La IP la asigna la WLAN y se muestra en la página 7 del LCD. En un PC también funciona `http://wrews.local` (mDNS); en Android no. Si al reconectar la IP cambia, queda un evento en el tablero.
- **Eventos de red:** conexión (con el nombre de la red y la dirección del tablero), pérdida de la red y número de reconexiones, visibles en el tablero.

---

## 3.16 Tablero de control (Challenge #2)

El tablero es una página web servida por el propio ESP32 (`firmware/wrews/tablero.h`). No usa librerías externas ni CDN, porque la WLAN de la zona puede no tener salida a Internet: las gráficas se dibujan con `<canvas>`.

### Contenido

- **Estado general** (NORMAL, PRECAUCIÓN, CRÍTICO o FALLO) con su color, la severidad de cada variable y el botón **"Silenciar alarma 15 min"**.
- **Tarjetas con el valor actual:** nivel y distancia, tasa de descenso, índice evaporativo, riesgo hídrico, evaporación (mm/día) y radiación neta, irradiancia, temperatura, humedad, presión y VPD (instantáneo y de la ventana). El borde de cada tarjeta toma el color de su severidad.
- **Histórico reciente:** últimos 10 minutos (un punto cada 2 s) de nivel, riesgo, índice evaporativo, tasa, temperatura e irradiancia, con los umbrales de precaución y crítico punteados.
- **Eventos:** cambios de estado, silencios, pérdida y vuelta del Wi-Fi, inicios de sesión, claves incorrectas y cambios de configuración, con su antigüedad. Cada evento nuevo muestra un **aviso** en la parte superior, suena y vibra (después del primer toque en la página).
- **Encabezado y pie:** red, señal (dBm), antigüedad del último dato, tiempo encendido, reconexiones y modo.
- **Configuración y calibración** (Sección 3.17).

### API

| Método y ruta | Uso |
|---|---|
| `GET /` · `GET /login` · `POST /login` · `POST /logout` | Páginas del tablero y sesión |
| `GET /api/actual` | Valor actual de todas las variables (cada 2 s) |
| `GET /api/historial` | Últimos 300 puntos (cada 5 s) |
| `GET /api/eventos?desde=N` | Eventos nuevos (cuando cambia el último evento) |
| `GET /api/config` | Umbrales, pesos y modo, para dibujar las gráficas |
| `POST /api/silenciar` | Silencia el buzzer 15 min |
| `GET` y `POST /api/parametros` · `POST /api/parametros/restaurar` | Calibración |

Cada petición del navegador se cancela si no responde en 4 s (8 s para el historial), y no se lanza una nueva hasta que termina la anterior. Así, cuando la WLAN vuelve después de una caída, el tablero se recupera solo en pocos segundos en lugar de quedar en fila detrás de peticiones colgadas.

### Acceso restringido

El enunciado exige que solo dispositivos **autorizados** y **conectados a la WLAN de la zona** accedan al tablero. Se exigen las dos condiciones:

1. **Misma subred:** el servidor rechaza clientes cuya dirección no esté en la subred del equipo (respuesta 403).
2. **Sesión iniciada:** usuario y contraseña en `/login`. Al validarse, el equipo genera un **token aleatorio de 128 bits** (`esp_random`) que viaja en una cookie `HttpOnly` y `SameSite=Strict`, válida 12 h. Hay hasta 4 sesiones simultáneas; tras **5 claves incorrectas** el inicio de sesión se bloquea 30 s, y cada intento fallido queda como evento.

**Limitación declarada:** el tablero va por HTTP, sin TLS. La clave viaja una sola vez (al iniciar sesión) y solo la protege el cifrado WPA2 de la WLAN. Las sesiones se pierden si el equipo se reinicia.

---

## 3.17 Calibración desde el tablero (Challenge #2)

Los parámetros que dependen del sitio se editan desde la sección "Configuración y calibración" del tablero, se validan en el equipo y se guardan en la flash del ESP32 (`Preferences`/NVS): se conservan aunque el equipo se apague o se reprograme. Se aplican en caliente, sin reiniciar, y cada cambio queda como evento.

| Parámetro | De fábrica | Validación | Ayuda en el tablero |
|---|---|---|---|
| Distancia con el tubo lleno / vacío | 3 / 20 cm | lleno entre 2 y 300 cm; vacío al menos 2 cm mayor que lleno y hasta 400 cm | Muestra la distancia medida en vivo, con botones "Usar como lleno" y "Usar como vacío" |
| K del panel | 10 (W/m²)/mA | 0.5 a 100 | Con una irradiancia de referencia, "Calcular K" la divide por la corriente medida en ese momento |
| Tasa de precaución / crítico | 33 / 68 pp/min | precaución 0.5 a 1000; crítico mayor que precaución | — |
| Salto de discontinuidad | 8 pp | 1 a 100 | — |
| Modo | Demo | Demo o campo | — |
| Ventana demo | 120 s | 30 a 86 400 s | — |
| ET de referencia | 7.5 mm/día | 1 a 20 | — |

Si cambian las distancias, la tendencia de la tasa se reinicia (la escala del nivel cambió); si cambian el modo o la ventana, la estimación de evaporación vuelve a llenarse. Un botón restaura los valores de fábrica. **Los pesos y los umbrales de nivel, riesgo y evaporación no son editables**: están justificados con referencias y solo se cambian en el código.

---

## 3.18 Autodiagnóstico al arrancar (Challenge #2)

Al encender, y antes de empezar a operar, el firmware:

1. Prueba las salidas: LEDs en orden y los dos tonos de alarma (1000 y 2000 Hz).
2. Escanea el bus I²C e identifica LCD, BME280 e INA219.
3. Mide la **corriente del panel en reposo** (promedio de 20 lecturas) y la toma como cero del piranómetro **solo si es menor de 1 mA**; si es mayor, asume que hay luz sobre el panel y deja el cero en 0.
4. Caracteriza el **ruido del sensor de nivel** y calcula la banda muerta de la tasa (Sección 5.5.1).
5. Ejecuta **7 pruebas del modelo de evaporación** contra valores de referencia (Sección 5.7).
6. Carga la calibración guardada en la flash.

Todo queda en el monitor serial como evidencia.

---

## 3.19 Producto terminado: carcasa, alimentación e instalación (Challenge #2)

### Carcasa

Diseñada en CadQuery e impresa en PETG, en seis piezas: prueba de ajuste del tubo, acople al tubo, tapa, caja, piso intermedio y techo del BME280. La caja mide 136 × 110 × 73 mm (interior 130 × 104 × 70 mm). El BME280 va bajo un techo con rejillas, a la sombra y ventilado, como pide la buena práctica meteorológica para medir temperatura y humedad del aire. Los STL y el script de CadQuery de la versión impresa están en [`/Carcasa_3D_/Carcasa_3D_v16`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/tree/main/Carcasa_3D_/Carcasa_3D_v16).

### Sensor de nivel en tubo

El HC-SR04 va dentro de un tubo de **PVC sanitario de 3"** (diámetro exterior ≈ 82.5 mm) de 40 a 50 cm, con corte recto, borde interior lijado y entradas de agua en la parte inferior. El tubo aísla la medición del oleaje y de reflexiones laterales. El agua no debe subir a menos de **5 cm** del sensor (zona ciega), por lo que la distancia de "lleno" se calibra a 5 cm o más.

### Alimentación

| Rama | Desde | Alimenta |
|---|---|---|
| Pilas | Portapilas 4×AA → interruptor | Pin `VIN` del ESP32 y fila de 5 V |
| 5 V | `VIN` | HC-SR04, buzzer, LEDs, LCD |
| 3.3 V | Pin `3V3` del ESP32 | BME280, INA219 |

Usamos un portapilas con 4 pilas AA recargables Duracell de 1.5V, junto con 2 diodos 1N4007 en serie para alimentar el prototipo sin necesidad de un cable de alimentación. Usamos los diodos para limitar el voltaje y que no fueran 6 V. Para programar por USB, el interruptor va en OFF.

### Mapa de pines (ESP32 DevKit de 38 pines)

| Pin ESP32 | Conectado a | Función |
|---|---|---|
| `GPIO 21 (SDA)` · `GPIO 22 (SCL)` | BME280, INA219, LCD | Bus I²C |
| `GPIO 5` | TRIG del HC-SR04 | Disparo del pulso ultrasónico |
| `GPIO 18` | ECHO del HC-SR04 | Recepción del eco. Falta verificar si lleva divisor resistivo: el HC-SR04 alimentado a 5 V entrega 5 V en el ECHO, y el ESP32 trabaja a 3.3 V |
| `GPIO 25` · `GPIO 26` · `GPIO 27` | LED verde · amarillo · rojo (ánodo común) | Estado |
| `GPIO 19` | Buzzer pasivo | Alarma sonora (PWM) |
| `VIN` · `3V3` · `GND` | Ver tabla de alimentación | Alimentación y tierra común |

En el Challenge #2 se retiró el botón físico de silencio del Challenge #1: el silencio se hace desde el tablero.

---

## 3.21 Firmware v8: comunicación MQTT en un hilo propio (Challenge #3)

El firmware v8 conserva toda la lógica del v7 y agrega un **cuarto hilo** de FreeRTOS para la comunicación con el gateway, con la librería PubSubClient [32]:

| Hilo | Núcleo | Prioridad | Periodo | Responsabilidad |
|---|---|---|---|---|
| `tareaMedicion` | 0 | 2 | 1 s | Sensores, modelo, estado, historial y eventos (igual que en v7) |
| `tareaMqtt` **(nuevo)** | 0 | 1 | 50 ms | Conexión al broker; publica telemetría (cada 5 s), estado (al cambiar) y eventos; recibe la orden de silenciar y la recomendación de la IA |
| `tareaAlarmas` | 1 | 2 | 10 ms | LEDs y buzzer |
| `loop()` | 1 | 1 | continuo | Servidor web, Wi-Fi, LCD y búsqueda del gateway por mDNS |

Reglas de concurrencia:

- **La librería MQTT solo se usa dentro de `tareaMqtt`**: PubSubClient no es segura entre hilos.
- `tareaMqtt` toma `mtx_estado` **solo para copiar** los datos, y lo suelta **antes** de usar la red. Conectarse o publicar puede tardar segundos, y en ese tiempo la medición y la alarma no esperan.
- `tareaMqtt` **nunca toma `mtx_i2c`** ni toca los pines. Se mantiene el orden fijo de los candados del v7.
- Corre con prioridad 1, por debajo de la medición (2): si el broker no responde, los reintentos no le quitan tiempo de CPU a la medición.

Otros mecanismos del v8:

- **Última voluntad (LWT):** al conectarse, el ESP32 le deja al broker el mensaje `offline` retenido en `wrews/<id>/disponibilidad`. Si se apaga o pierde la red, el broker lo publica por él; con *keepalive* de 15 s, el gateway se entera en ~22 s como máximo.
- **Eventos sin pérdida:** si el broker estuvo caído, al reconectar se publican los eventos que sigan en el registro circular (los 24 últimos). El gateway los guarda con su `id` y el identificador de arranque (`boot`) y descarta los repetidos.
- **Gateway por nombre:** `MQTT_HOST` puede ser una IP o un nombre `.local`. Con un nombre, `loop()` lo resuelve por mDNS y lo vuelve a buscar si la conexión falla, así el ESP32 sigue al gateway aunque el hotspot le cambie la IP. La búsqueda va en `loop()` porque es el hilo que reinicia el mDNS al volver el Wi-Fi.
- **Filtro de plausibilidad del BME280:** una lectura fuera de rango físico (temperatura fuera de −10 a 60 °C, humedad fuera de 0 a 100 %, presión fuera de 500 a 1100 hPa) se descarta y se conservan los últimos valores válidos; no entra a la ventana de evaporación. Cinco lecturas imposibles seguidas llevan a **FALLO** ("BME280 con lecturas imposibles"). Ver el incidente en [5.8](05-Configuracion-Experimental-Resultados.md).

## 3.22 Gateway: arquitectura del servicio (Challenge #3)

El gateway es un servicio en Python (`wrews-gateway`, systemd) que arranca solo con la Raspberry Pi. Sus hilos:

| Hilo | Qué hace |
|---|---|
| Red local (paho-mqtt [33]) | Recibe los mensajes del ESP32 y los pone en una cola en memoria |
| Trabajador | Saca cada mensaje, **lo guarda en SQLite** y luego lo procesa |
| Periódico (1 s) | Cierra las ventanas de agregación y vigila el enlace con el ESP32 |
| Nube | Vacía la cola de SQLite hacia Ubidots, del más viejo al más nuevo |
| IA | Predicción y recomendación (la consulta al LLM puede tardar: va aparte) |
| Red Ubidots (paho) | Conexión TLS con Ubidots; recibe el switch de silenciar |
| Telegram (3 hilos) | Envía avisos, atiende comandos y actualiza el dashboard en vivo |

El trabajador y el periódico comparten el estado del enlace y el agregador, y lo tocan siempre con un candado.

**Esquema de SQLite [34]** (comentado en `gateway/wrews_gw/almacen.py`):

| Tabla | Contenido |
|---|---|
| `mediciones` | Cada telemetría tal como llegó (JSON crudo) más sus columnas, la hora de llegada y la marca de anomalía |
| `estados` | Cada cambio de estado, con su origen (`esp32`, o `gateway` cuando el FALLO lo declara el gateway) |
| `eventos` | Eventos del ESP32 y del gateway; clave única (`dispositivo`, `boot`, `id`) para descartar reenvíos |
| `comandos` | Órdenes enviadas al ESP32 (origen, acción) y su respuesta |
| `agregados` | Resumen de cada ventana: media, mínimo, máximo y completitud |
| `ia` | Cada predicción y recomendación, **con el prompt exacto** enviado al modelo, el proveedor, la latencia y el error si lo hubo |
| `suscriptores` | Autoridades del bot de Telegram y si el administrador las aprobó |
| `cola_nube` | Lo que debe subir a Ubidots; `enviado_ms` en vacío significa pendiente |

## 3.23 Procesamiento local en el gateway (Challenge #3)

1. **Validación por variable.** Cada variable se compara con su rango físico. Una variable imposible se descarta **sola**: la muestra sigue valiendo para las demás, sobre todo para el nivel.
2. **Anomalías del nivel con z robusto.** Se mira la *diferencia* con la muestra válida anterior, no el valor, para que un descenso sostenido no se confunda con un pico. Con las últimas 20 diferencias:

   ```text
   z = |d − mediana(d)| / máx(1.4826 × MAD, 1)
   ```

   donde MAD es la mediana de las desviaciones absolutas respecto a la mediana. La muestra es anómala si z > 4 **y** el salto supera 10 pp. Tres muestras seguidas en el nuevo valor se aceptan como un escalón real (recarga o reposicionamiento). La mediana y el MAD no se dejan arrastrar por los propios picos, como sí pasaría con la media y la desviación estándar.
3. **Agregación por ventanas de 60 s.** Media, mínimo y máximo de cada variable y **completitud** (muestras recibidas sobre las esperadas). Es lo que se sube a Ubidots: una muestra por minuto en vez de doce, dentro de los límites del plan gratuito.
4. **Vigilancia del enlace.** Si pasan más de 20 s sin telemetría, o el broker publica la última voluntad del ESP32, el gateway declara **FALLO con origen `gateway`** y lo sube a Ubidots, porque el ESP32 ya no puede avisar por sí mismo.

## 3.24 Puente con Ubidots (Challenge #3)

- **Conexión:** MQTT sobre TLS al puerto 8883 de `industrial.api.ubidots.com` [35]. El certificado (Let's Encrypt) se valida con el almacén del sistema. El token de Ubidots es el usuario MQTT y nunca viaja en claro.
- **Formato:** `{"variable": {"value": x, "timestamp": ms, "context": {...}}}`. La marca de tiempo es la de la medición, así que lo que se envía tarde queda en su hora real.
- **Store and forward:** todo lo que va a la nube pasa por `cola_nube`. Sin Internet, se acumula; al volver, se envía en orden, a un ritmo máximo de 2 mensajes por segundo, esperando la confirmación de Ubidots (QoS 1) antes de marcarlo como enviado.
- **Bajada del switch `silenciar`:** el gateway está suscrito a la variable. Una orden con marca de tiempo **de menos de 2 minutos** y no ejecutada antes se reenvía al ESP32 por el broker local; luego el gateway devuelve el switch a 0. Así, una orden dada mientras la Pi estaba sin Internet se cumple al reconectar, y un 1 viejo guardado en Ubidots no silencia la alarma por error.

| Variable en Ubidots | Qué es |
|---|---|
| `nivel`, `riesgo`, `tasa`, `idx_evap`, `temp` | Media de la ventana de 60 s (mínimo y máximo en el *context*) |
| `estado` | 0 NORMAL, 1 PRECAUCIÓN, 2 CRÍTICO, 3 FALLO (*context*: origen y motivo) |
| `silenciado` | 1 si el buzzer está silenciado |
| `gw_calidad` | Completitud de la ventana (0 % si el ESP32 no envía) |
| `ia_min_critico` | Minutos estimados hasta el 15 % (−1 si no baja); la recomendación va en el *context* |
| `silenciar` | Switch del tablero para desactivar la alarma física |

## 3.25 Módulo de inteligencia artificial (Challenge #3)

El módulo tiene **dos partes, separadas a propósito**:

**1. Predicción propia (sin costo, sin Internet).** Regresión lineal por mínimos cuadrados del nivel en los últimos 10 minutos (mínimo 8 puntos y 40 s de historia):

```text
Nivel(t) ≈ m × t + b                          (mínimos cuadrados, t en minutos)
Minutos hasta el 15 % = (Nivel actual − 15) / (−m)     solo si m < −0.5 pp/min
```

Entrega la pendiente m (pp/min), el R² y los **minutos estimados hasta el umbral crítico del 15 %**. Si |m| < 0.5 pp/min la tendencia se considera estable. Corre en la Pi, se guarda en SQLite y se publica en Ubidots (`ia_min_critico`).

**2. Recomendación en lenguaje natural (Claude, a pedido).** Cuando una autoridad escribe `/recomendacion` en el bot, el gateway arma un prompt con el estado, la predicción, los índices y los últimos eventos, y lo envía a **Claude** (`claude-opus-5-5`, Anthropic [36]) por su API, con esfuerzo bajo. El modelo devuelve una recomendación de máximo 55 palabras para la alcaldía (racionamiento por sectores, priorización de hospitales y colegios, comunicación a la población, revisión de fugas).

Decisiones de diseño:

- **El modelo no calcula nada.** Recibe los números ya calculados y el prompt le prohíbe inventar cifras y le pide decir que la tendencia es incierta si R² < 0.5. Una alucinación no puede cambiar el valor que se reporta.
- **Respaldo por reglas.** Sin Internet, sin créditos o con la clave mala, responde una tabla de decisiones a partir del estado y la predicción. El sistema nunca se queda sin recomendación.
- **Solo a pedido.** Lo automático (al cambiar el estado) usa la tabla de reglas, que es gratis. El modelo se consulta cuando alguien lo pide, como máximo una vez por minuto: si varias autoridades lo piden a la vez, reciben la misma respuesta. Costo medido: ~700 tokens de entrada y ~750 de salida por consulta, unos USD 0,02.
- **Trazabilidad.** Cada recomendación queda en la tabla `ia` con el prompt exacto, el modelo, la latencia y el motivo del respaldo si lo hubo, y se publica en el tablero local, en Ubidots y en Telegram.

**¿Por qué un LLM y no solo reglas?** La predicción numérica resuelve el "cuándo"; el modelo de lenguaje traduce esos números a una acción concreta para personas que no son técnicas, teniendo en cuenta el conjunto (estado, tendencia, evaporación y eventos recientes), lo que una tabla de reglas fija no puede hacer.

## 3.26 Canal móvil por Telegram (Challenge #3)

Complementa al tablero global. El gateway atiende un bot de Telegram [37] (`@WREWS_Alertasbot`):

| Comando | Qué hace | Costo |
|---|---|---|
| (automático) | Aviso en cada cambio de estado, con el último dato y una recomendación por reglas | Gratis |
| `/dashboard` | Tablero completo en una imagen: tarjetas de estado y variables, gráficas de la última hora y la última recomendación. Lo dibuja el gateway con SQLite y matplotlib [38] | Gratis |
| `/envivo` | Fija ese dashboard arriba del chat y lo reemplaza cada 60 s y apenas cambia el estado | Gratis |
| `/grafica`, `/estado` | Gráfica rápida de nivel y riesgo, y resumen en texto | Gratis |
| `/tablero` | Enlace al tablero de Ubidots (pide iniciar sesión) | Gratis |
| `/recomendacion` | Análisis de Claude con los datos actuales | ~USD 0,02 |

**Acceso restringido en dos pasos:**
1. **Clave de registro:** solo quien escribe `/start CLAVE` (o abre el enlace con la clave) puede pedir acceso. Con 5 claves erradas, el chat queda bloqueado 10 minutos.
2. **Aprobación del administrador:** la solicitud le llega al administrador con los botones **Aprobar** y **Rechazar**. Solo los aprobados reciben alertas y pueden usar los comandos. El administrador ve la lista con `/usuarios` y puede retirar un acceso.

## 3.27 Seguridad por capas (Challenge #3)

| Capa | Mecanismo |
|---|---|
| Tablero local | Misma subred + usuario y clave + sesión con token aleatorio de 128 bits (Challenge #2) |
| Broker MQTT | Sin acceso anónimo; usuario y clave por equipo (`esp32`, `gateway`, `monitor`); ACL por usuario: el ESP32 solo publica sus datos y solo lee comandos y la recomendación; el usuario `monitor` solo lee |
| Gateway → Ubidots | TLS 1.2/1.3 con validación del certificado |
| Tablero global | Cuenta privada de Ubidots; no se usa el enlace público |
| Telegram | Clave de registro + aprobación del administrador |
| Secretos | Claves solo en `secrets.h` (ESP32) y `/etc/wrews/gateway.env` (permisos 640): ninguno se sube al repositorio |

**Limitación declarada:** el tramo ESP32 ↔ Mosquitto va por MQTT sin TLS dentro de la WLAN, protegido por el cifrado WPA2 de la red. Ver trabajo futuro en [7.3](07-Conclusiones-Trabajo-Futuro.md).

## 3.28 Diagramas UML del Challenge #3

### 3.28.1 Secuencia: desactivar la alarma física desde Ubidots

```mermaid
sequenceDiagram
    actor A as Autoridad
    participant U as Ubidots
    participant G as Gateway (Pi)
    participant M as Mosquitto
    participant E as ESP32 (tareaMqtt)
    participant L as tareaAlarmas
    A->>U: Activa el switch "silenciar"
    U-->>G: silenciar = 1 (con marca de tiempo)
    G->>G: ¿orden de menos de 2 min y no repetida?
    G->>M: publica wrews/wrews-01/cmd {"accion":"silenciar","origen":"Ubidots"}
    M->>E: entrega el comando
    E->>E: silenciarAlarma() con mtx_estado
    E->>M: cmd/resp {"ok":1,"estado":"PRECAUCION"}
    M->>G: respuesta
    G->>G: guarda orden y respuesta en SQLite (comandos)
    G->>U: silenciar = 0 (el switch vuelve solo)
    L->>L: siguiente ciclo (10 ms): buzzer apagado, LEDs siguen
```

### 3.28.2 Secuencia: del dato a la nube, con caída de Internet

```mermaid
sequenceDiagram
    participant E as ESP32
    participant G as Gateway
    participant D as SQLite
    participant U as Ubidots
    E->>G: telemetría (cada 5 s, MQTT)
    G->>D: guarda la medición (primero)
    G->>G: valida y agrega a la ventana
    Note over G: cada 60 s
    G->>D: guarda el agregado y lo encola en cola_nube
    alt hay Internet
        G->>U: publica (QoS 1, TLS)
        U-->>G: confirmación
        G->>D: marca como enviado
    else sin Internet
        Note over G,D: la cola crece; la alarma local sigue
        G->>U: al volver: envía en orden con su hora original
    end
```

### 3.28.3 Componentes del Challenge #3

```mermaid
flowchart TB
    subgraph ESP32["ESP32 · wrews.ino (v8)"]
        MED[tareaMedicion] --> EST[(estado compartido<br/>mtx_estado)]
        ALA[tareaAlarmas] --> EST
        MQT[tareaMqtt] --> EST
        WEB[loop: servidor web, Wi-Fi, LCD, mDNS] --> EST
    end
    subgraph GW["Gateway · wrews_gw"]
        GA[gateway.py] --> AL[almacen.py · SQLite]
        GA --> PR[procesamiento.py]
        GA --> NU[nube.py · Ubidots]
        GA --> IAM[ia.py · regresión + LLM]
        GA --> TE[telegram.py]
        TE --> GR[grafica.py]
    end
    MQT <-- MQTT --> GA
```


## 3.29 Estándares aplicados en el Challenge #3

| Estándar | Dónde se aplica |
|---|---|
| **MQTT 3.1.1** (OASIS, ISO/IEC 20922) [39] | Toda la comunicación dispositivo ↔ gateway ↔ Ubidots; QoS 1 hacia la nube; mensajes retenidos y última voluntad |
| **TLS 1.2/1.3** (IETF RFC 8446) | Gateway ↔ Ubidots, gateway ↔ APIs de Claude y Telegram |
| **ANSI/ISA-18.2** [16] | Gestión de alarmas: confirmación asimétrica, silencio que no apaga los LEDs, eventos con gravedad |
| **Ley 1581 de 2012** [41] | Minimización de datos personales en el bot |

## 3.30 Trazabilidad Wiki ↔ código (Challenge #3)

| Sección | Archivo |
|---|---|
| 3.21 Hilo MQTT, LWT, mDNS, filtro BME280 | `firmware/wrews/wrews.ino` (sección "MQTT HACIA EL GATEWAY", `lecturaBmeValida`) |
| 3.22 Servicio y SQLite | `gateway/wrews_gw/gateway.py`, `almacen.py` |
| 3.23 Validación y ventanas | `gateway/wrews_gw/procesamiento.py` |
| 3.24 Ubidots | `gateway/wrews_gw/nube.py` |
| 3.25 IA | `gateway/wrews_gw/ia.py` |
| 3.26 Telegram y dashboard | `gateway/wrews_gw/telegram.py`, `grafica.py` |
| 3.27 Broker y permisos | `gateway/mosquitto/wrews.conf`, `wrews.acl`, `gateway/instalar.sh` |
| Pruebas automáticas (22) | `gateway/tests/test_gateway.py` |

---

[⬅ Anterior: Solución propuesta](02-Solucion-Propuesta.md) · [⬆ Índice](00-Home.md) · [Siguiente: Modelo de negocio ➡](04-Modelo-de-Negocio.md)
