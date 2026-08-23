[⬅ Volver al índice](00-Home.md)

# 7. Conclusiones, retos y trabajo futuro

## 7.1 Conclusiones

El desarrollo de WREWS permitió cumplir el objetivo principal del Challenge #1: construir un prototipo capaz de **monitorear variables relacionadas con la disponibilidad de agua, procesar la información localmente y generar alertas tempranas ante diferentes escenarios de riesgo hídrico**.

A partir del proceso de diseño, simulación, implementación y validación se obtuvieron las siguientes conclusiones:

### 1. El prototipo funcional fue implementado y validado físicamente

WREWS pasó de una primera etapa de diseño y simulación en Wokwi a una **implementación física funcional basada en ESP32**.

El montaje final permitió comprobar la adquisición de las variables, el procesamiento local, la visualización mediante LCD y la actuación mediante LEDs y buzzer.

De esta manera, la validación no se limitó al entorno simulado, sino que se comprobó el funcionamiento integrado del sistema utilizando sensores y actuadores reales.

### 2. El nivel por sí solo no representa completamente el riesgo

Una de las principales decisiones de diseño fue evitar que el sistema dependiera únicamente del nivel instantáneo del reservorio.

WREWS integra tres dimensiones:

```text
DISPONIBILIDAD ACTUAL
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
```

Esto permite considerar no solamente **cuánta agua queda**, sino también las condiciones que favorecen la evaporación y **qué tan rápido está disminuyendo el nivel**.

### 3. La tasa de descenso aporta información sobre la evolución del sistema

Dos reservorios pueden presentar el mismo porcentaje de nivel y, sin embargo, encontrarse en situaciones diferentes si uno permanece estable y el otro está disminuyendo rápidamente.

Por esta razón, incorporar la tasa de descenso permite que WREWS analice la **tendencia** y no únicamente una medición instantánea.

### 4. Las variables ambientales complementan la evaluación del riesgo

La temperatura y la humedad obtenidas mediante el BME280 permiten calcular el **déficit de presión de vapor (VPD)**.

Este indicador se combina con la irradiancia estimada mediante el panel fotovoltaico y el INA219 para representar qué tan favorables son las condiciones ambientales para la evaporación.

La presión atmosférica se mantiene como una variable ambiental de contexto. Debido a su baja variación esperada en un punto fijo de instalación, no se utiliza directamente como disparador principal de las alertas.

### 5. La fusión de información permite una clasificación más completa

La combinación ponderada de déficit de nivel, condiciones evaporativas y tasa de descenso permite obtener un índice general de riesgo.

Además, las reglas de seguridad implementadas permiten que una condición individual extrema pueda elevar el estado del sistema aunque el promedio ponderado todavía no alcance por sí solo el umbral crítico.

De esta forma se obtienen tres estados fácilmente interpretables:

- 🟢 **NORMAL**
- 🟡 **PRECAUCIÓN**
- 🔴 **CRÍTICO**

### 6. Las alertas funcionan de manera completamente local

El ESP32 realiza localmente:

- adquisición de sensores;
- procesamiento de variables;
- cálculo de indicadores;
- fusión de información;
- clasificación del riesgo;
- control de los actuadores.

Por tanto, el prototipo puede generar una alerta sin depender de Wi-Fi, Internet o servicios externos.

La información se comunica mediante la **LCD 16×2 I²C**, los LEDs de estado y el buzzer.

### 7. La simulación fue una etapa útil antes de la implementación física

Wokwi permitió comprobar la arquitectura, las comunicaciones I²C, la lógica de procesamiento y diferentes escenarios antes de integrar el hardware real.

Posteriormente, la implementación física permitió ajustar el sistema a las características reales de los componentes y de la maqueta.

El proceso seguido puede resumirse como:

```text
DISEÑO
   ↓
SIMULACIÓN
   ↓
DEPURACIÓN
   ↓
IMPLEMENTACIÓN FÍSICA
   ↓
CALIBRACIÓN
   ↓
VALIDACIÓN
```

Esta metodología permitió reducir errores durante la integración final.

---

## 7.2 Retos encontrados durante el desarrollo

### Integración del sensor ultrasónico

Uno de los principales retos fue obtener mediciones estables y coherentes con las dimensiones de la maqueta.

La respuesta del sensor físico requirió pruebas y ajustes de calibración para transformar correctamente la distancia medida en un porcentaje representativo del nivel.

La implementación de una plataforma móvil permitió realizar estas pruebas de manera controlada y repetible.

### Integración de diferentes dispositivos I²C

El sistema utiliza varios componentes que comparten el bus I²C.

Fue necesario verificar las direcciones y el funcionamiento conjunto de los dispositivos para garantizar que el ESP32 pudiera adquirir correctamente la información.

### Estimación de irradiancia

El mini panel fotovoltaico no es un piranómetro calibrado.

Por esta razón, su señal junto con el INA219 se utiliza como una **estimación experimental de irradiancia**, suficiente para observar cambios relativos en las condiciones de iluminación dentro del alcance del prototipo.

Este punto fue importante para evitar presentar la medición como una lectura metrológica de precisión.

### Diferencias entre simulación y montaje físico

La simulación permitió trabajar con entradas ideales y fácilmente controlables.

En el montaje físico aparecieron aspectos adicionales como:

- variación en las lecturas;
- comportamiento real de los sensores;
- conexiones físicas;
- calibración;
- dimensiones reales de la maqueta;
- respuesta de los actuadores.

Esto hizo necesario ajustar algunos parámetros respecto a los utilizados inicialmente en Wokwi.

### Visualización en una LCD 16×2

El espacio disponible en la pantalla LCD es limitado frente a la cantidad de información procesada por WREWS.

Por ello, fue necesario priorizar y organizar la información mostrada para mantener una interfaz local comprensible sin afectar el procesamiento interno de todas las variables.

---

## 7.3 Trabajo futuro

Aunque el prototipo físico cumple los objetivos establecidos para esta etapa, existen oportunidades para continuar desarrollando WREWS.

### 1. Calibración en un reservorio real

La calibración actual corresponde a la maqueta construida para las pruebas.

Una implementación real requeriría medir las dimensiones y geometría del reservorio para convertir correctamente la distancia ultrasónica en nivel y, si se requiere, volumen de agua disponible.

### 2. Calibración de la irradiancia

El panel fotovoltaico permite obtener una señal relacionada con la radiación recibida.

Como trabajo futuro, esta señal podría compararse contra un piranómetro o instrumento de referencia para obtener una curva de calibración más precisa en W/m².

### 3. Ajuste de umbrales utilizando datos históricos

Los umbrales actuales permiten demostrar la lógica del sistema y validar el prototipo.

Una implementación en campo podría utilizar registros históricos de nivel y condiciones ambientales para ajustar los límites de NORMAL, PRECAUCIÓN y CRÍTICO según las características reales del lugar de instalación.

### 4. Pruebas prolongadas

Una siguiente etapa podría evaluar el sistema durante periodos de varios días o semanas para analizar:

- estabilidad de los sensores;
- comportamiento de la tasa de descenso;
- variaciones ambientales reales;
- falsas alarmas;
- funcionamiento continuo del sistema.

### 5. Protección para operación en exteriores

Para una implementación permanente sería necesario utilizar una carcasa adecuada para proteger el ESP32, conexiones y demás componentes frente a humedad, lluvia, polvo y exposición ambiental.

### 6. Validación de campo

El siguiente nivel de validación consistiría en instalar WREWS temporalmente sobre un punto real de almacenamiento de agua y comparar las estimaciones del sistema con mediciones de referencia.

---

## 7.4 Cierre

WREWS demuestra que un sistema IoT de bajo costo puede combinar **nivel, condiciones ambientales y tendencia** para construir una evaluación local del riesgo hídrico.

El resultado final es un prototipo físico capaz de adquirir información mediante múltiples sensores, procesarla en un ESP32 y transformar los datos en tres estados de fácil interpretación.

```text
NIVEL
   +
CONDICIONES AMBIENTALES
   +
TASA DE DESCENSO
   ↓
RIESGO HÍDRICO
   ↓
NORMAL / PRECAUCIÓN / CRÍTICO
```

El proyecto permite demostrar de forma funcional el concepto de **alerta temprana**, pasando de la adquisición de datos a una decisión local y una respuesta física mediante indicadores visuales y sonoros.

---

[⬅ Anterior: Autoevaluación del protocolo de pruebas](06-Autoevaluacion-Pruebas.md) · [⬆ Índice](00-Home.md) · [Siguiente: Uso de Inteligencia Artificial ➡](08-Uso-de-IA.md)