
# 🎬 Guion de video — WREWS

## Water Risk Early Warning System

**Proyecto:** WREWS — Water Risk Early Warning System  
**Curso:** Internet de las Cosas — Challenge #1 — 2026-2  
**Universidad de La Sabana**

▶️ **Video final:** https://youtu.be/zUS3DWeHSsw

---

# 1. Objetivo del video

El video presenta de forma resumida:

- la problemática abordada;
- la solución propuesta;
- los sensores y componentes utilizados;
- el procesamiento de las variables;
- la lógica de fusión de información;
- el funcionamiento de la maqueta;
- los estados NORMAL, PRECAUCIÓN y CRÍTICO;
- la validación del prototipo físico.

Duración aproximada:

**4:30 – 4:45 minutos**

---

# 2. Nombre del proyecto

## WREWS

**Water Risk Early Warning System**

Pronunciación utilizada:

**WREWS → “rúus”**

La primera vez se presenta como:

> WREWS, por *Water Risk Early Warning System*.

Después se utiliza simplemente **WREWS** como nombre del sistema.

---

# 3. Estructura del video

| Tiempo | Sección |
|---|---|
| 0:00–0:07 | Portada |
| 0:07–0:40 | Introducción y problemática |
| 0:40–1:20 | Componentes y hardware |
| 1:20–2:00 | Procesamiento y cálculo del riesgo |
| 2:00–2:15 | Explicación de la maqueta |
| 2:15–2:45 | Estado NORMAL |
| 2:45–3:15 | Estado PRECAUCIÓN |
| 3:15–3:45 | Estado CRÍTICO |
| 3:45–4:10 | Variables ambientales y tasa |
| 4:10–4:28 | Validación |
| 4:28–4:45 | Conclusión |

---

# 4. Portada

## Qué se muestra

Toma general del prototipo físico funcionando.

Texto utilizado:

```text
WREWS
Water Risk Early Warning System

Sistema de Alerta Temprana
de Riesgo Hídrico

Challenge #1 — Internet de las Cosas
Universidad de La Sabana
```

---

# 5. Introducción y problemática

## Guion

> La disponibilidad de agua representa un desafío importante para la región de Sabana Centro, especialmente ante condiciones ambientales que pueden acelerar la disminución de los niveles de almacenamiento.
>
> Por esta razón desarrollamos WREWS, por *Water Risk Early Warning System*.
>
> WREWS es un prototipo IoT de bajo costo diseñado para monitorear un punto de almacenamiento de agua y generar alertas tempranas cuando identifica condiciones asociadas a un posible riesgo de desabastecimiento.
>
> Nuestro objetivo no es solamente conocer cuánto agua queda, sino analizar también las condiciones ambientales y la velocidad con la que disminuye el nivel.

---

# 6. Componentes y funcionamiento físico

## Guion

> El sistema utiliza un ESP32 como unidad central de procesamiento.
>
> Para determinar el nivel utilizamos un sensor ultrasónico, que mide la distancia entre la parte superior del reservorio y la superficie que representa el agua.
>
> El BME280 obtiene temperatura, humedad relativa y presión atmosférica.
>
> También utilizamos un mini panel fotovoltaico junto con un INA219, con el que obtenemos una estimación de la irradiancia solar.
>
> La información procesada se presenta mediante una pantalla LCD y LEDs de estado, mientras que un buzzer permite generar una alarma sonora.
>
> Todo el procesamiento y la generación de alertas se realizan localmente, sin depender de una red de comunicaciones.

## Componentes mostrados

```text
ESP32
↓
Sensor ultrasónico
↓
BME280
↓
Panel fotovoltaico
↓
INA219
↓
LCD 16×2 I²C
↓
LEDs
↓
Buzzer
```

---

# 7. Procesamiento y cálculo del riesgo

## Guion

> Una característica importante de WREWS es que no toma decisiones utilizando una sola variable.
>
> Primero, el nivel representa la disponibilidad actual de agua.
>
> Segundo, utilizamos la temperatura y la humedad para calcular el déficit de presión de vapor, o VPD.
>
> Este indicador se combina con la irradiancia solar estimada para obtener un índice de condiciones favorables a la evaporación.
>
> Finalmente, analizamos la tasa de descenso, para determinar qué tan rápido está disminuyendo el nivel.
>
> El índice de riesgo combina un cincuenta por ciento de déficit de nivel, treinta por ciento de condiciones evaporativas y veinte por ciento de tendencia.
>
> Con esta información, WREWS clasifica la situación en tres estados: Normal, Precaución o Crítico.

## Lógica de fusión

```text
DISPONIBILIDAD
Déficit de nivel
      50 %
        │
        │
CONDICIONES AMBIENTALES
VPD + irradiancia
      30 %
        │
        ▼
   RIESGO HÍDRICO
        ▲
        │
TENDENCIA DEL NIVEL
Tasa de descenso
      20 %
        │
        ▼
NORMAL / PRECAUCIÓN / CRÍTICO
```

---

# 8. Explicación de la maqueta

## Guion

> Para realizar las pruebas de forma controlada y segura, en nuestra maqueta representamos la superficie del agua mediante una plataforma móvil.
>
> Al subirla o bajarla modificamos la distancia detectada por el sensor ultrasónico, simulando diferentes niveles de almacenamiento sin exponer la electrónica al agua.

## Funcionamiento

```text
Plataforma arriba
        ↓
Distancia pequeña
        ↓
Nivel alto
```

```text
Plataforma abajo
        ↓
Distancia grande
        ↓
Nivel bajo
```

---

# 9. Escenario NORMAL 🟢

## Guion

> En el primer escenario simulamos un reservorio con una disponibilidad adecuada de agua.
>
> La superficie se encuentra cerca del sensor, por lo que la distancia medida es pequeña y el porcentaje de nivel calculado es alto.
>
> Como ninguno de los indicadores supera los umbrales establecidos, WREWS permanece en estado NORMAL.

## Respuesta del sistema

```text
NORMAL

LED verde → activo
Buzzer → apagado
LCD → estado e información
```

---

# 10. Escenario PRECAUCIÓN 🟡

## Guion

> Ahora simulamos una disminución del nivel del reservorio.
>
> Al aumentar la distancia medida por el sensor, disminuye el porcentaje de almacenamiento disponible.
>
> Cuando una de las variables supera su umbral de advertencia, WREWS cambia al estado PRECAUCIÓN.
>
> El firmware utiliza varias mediciones consecutivas antes de confirmar el cambio de estado, reduciendo la posibilidad de generar alertas por una lectura aislada.

## Respuesta

```text
PRECAUCIÓN

LED amarillo → activo
LCD → estado e información
```

---

# 11. Escenario CRÍTICO 🔴

## Guion

> Finalmente simulamos una reducción severa en la disponibilidad de agua.
>
> Cuando el nivel alcanza un valor críticamente bajo, WREWS activa una regla de seguridad independientemente del resultado del índice ponderado.
>
> El sistema cambia al estado CRÍTICO, activa el indicador rojo y genera una alarma sonora para advertir localmente sobre la situación.

## Respuesta

```text
CRÍTICO

LED rojo → activo
Buzzer → activo
LCD → estado e información
```

---

# 12. Variables ambientales

## Guion

> Además del nivel, WREWS monitorea continuamente las condiciones ambientales.
>
> La temperatura y humedad permiten calcular el VPD, mientras que el panel fotovoltaico proporciona una estimación de la irradiancia.
>
> La combinación de estas variables genera un índice que representa qué tan favorables son las condiciones ambientales para la evaporación.

## Flujo mostrado

```text
TEMPERATURA ──┐
              ├──→ VPD
HUMEDAD ──────┘


PANEL SOLAR
     ↓
   INA219
     ↓
IRRADIANCIA ESTIMADA
```

Posteriormente:

```text
VPD ───────────────┐
                   ├──→ ÍNDICE EVAPORATIVO
IRRADIANCIA ───────┘
```

> El índice evaporativo no representa el porcentaje de agua que se evapora. Representa qué tan favorables son las condiciones ambientales para que ocurra evaporación.

---

# 13. Tasa de descenso

## Guion

> El sistema también analiza múltiples mediciones del nivel a lo largo del tiempo para estimar su tasa de descenso y detectar reducciones aceleradas.

## Concepto mostrado

```text
Nivel
100 % │ ●
      │   ●
 80 % │      ●
      │          ●
 60 % │              ●
      │                  ●
 40 % │                      ●
      └──────────────────────── Tiempo

                  ↘
            Tasa de descenso
```

Conceptualmente:

```text
Nivel anterior
      +
Nivel actual
      +
Tiempo transcurrido
      ↓
Tasa de descenso
      ↓
¿El nivel está disminuyendo rápidamente?
```

---

# 14. Validación

## Guion

> La solución fue desarrollada inicialmente mediante simulación en Wokwi y posteriormente implementada sobre el prototipo físico.
>
> Durante la validación realizamos pruebas individuales de sensores y actuadores, calibración del nivel y pruebas integradas de los diferentes estados.
>
> De esta manera verificamos el proceso completo desde la adquisición de las variables hasta la generación de la alerta.

## Elementos validados

```text
✓ Nivel
✓ Temperatura
✓ Humedad
✓ Presión
✓ Irradiancia estimada
✓ VPD
✓ Índice evaporativo
✓ Tasa de descenso
✓ Riesgo
✓ NORMAL
✓ PRECAUCIÓN
✓ CRÍTICO
✓ LCD
✓ LEDs
✓ Buzzer
```

---

# 15. Conclusión

La conclusión final es presentada por un solo integrante.

## Guion

> En conclusión, con WREWS logramos desarrollar un prototipo funcional capaz de monitorear la disponibilidad de agua, analizar las condiciones ambientales y detectar cambios en el comportamiento del nivel.
>
> Al integrar estas variables, el sistema puede identificar diferentes escenarios de riesgo y generar alertas tempranas de manera local, permitiendo anticipar posibles situaciones de desabastecimiento.

---

# 16. Pantalla final

```text
WREWS

Water Risk Early Warning System
```

---

# 17. Flujo general presentado

```text
SENSORES
   ↓
ADQUISICIÓN
   ↓
PROCESAMIENTO EN ESP32
   ↓
NIVEL + AMBIENTE + TENDENCIA
   ↓
FUSIÓN DE INFORMACIÓN
   ↓
ÍNDICE DE RIESGO
   ↓
NORMAL / PRECAUCIÓN / CRÍTICO
   ↓
LCD + LEDs + BUZZER
```

---

# 18. Video final

▶️ **[Ver demostración final de WREWS](https://youtu.be/zUS3DWeHSsw)**

El video demuestra el funcionamiento del prototipo físico y complementa la documentación técnica disponible en la Wiki.