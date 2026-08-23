# 💧 WREWS — Water Risk Early Warning System

**Internet de las Cosas — Challenge #1 — 2026-2**
Facultad de Ingeniería, Universidad de La Sabana

[![Plataforma](https://img.shields.io/badge/MCU-ESP32-blue)](https://www.espressif.com/en/products/socs/esp32)
[![Simulación](https://img.shields.io/badge/Simulación-Wokwi-green)](https://wokwi.com/projects/472250559337371649)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-lightgrey)](LICENSE)
[![Estado](https://img.shields.io/badge/Estado-Prototipo%20físico%20funcional-brightgreen)]()

> **WREWS (Water Risk Early Warning System)** es un prototipo IoT de bajo costo que monitorea la disponibilidad de agua y genera alertas tempranas ante condiciones asociadas a un posible riesgo de desabastecimiento. El sistema combina el nivel actual, las condiciones ambientales favorables a la evaporación y la velocidad de descenso del nivel para generar un **índice de riesgo hídrico** y comunicar localmente los estados 🟢 NORMAL, 🟡 PRECAUCIÓN y 🔴 CRÍTICO.

---

## 🎯 El reto

El Challenge #1 plantea el desarrollo de una solución IoT orientada al monitoreo de la disponibilidad de agua y a la generación de alertas tempranas locales.

WREWS aborda el problema mediante tres dimensiones principales:

```text
DISPONIBILIDAD ACTUAL
Nivel del reservorio
        50 %
          │
          │
CONDICIONES AMBIENTALES
VPD + irradiancia estimada
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

El procesamiento se realiza localmente en un **ESP32**, por lo que la generación de la alerta no depende de Wi-Fi, Internet, servicios en la nube ni otra infraestructura de comunicaciones.

📄 **Documentación técnica completa:** [`/wiki`](wiki/00-Home.md)

---

## ✅ Estado actual

WREWS fue desarrollado mediante dos etapas complementarias:

### 1. Simulación en Wokwi

Se desarrolló inicialmente una simulación para:

- validar la arquitectura;
- probar la adquisición de sensores;
- comprobar el bus I²C;
- desarrollar y probar *custom chips*;
- verificar los cálculos;
- reproducir diferentes escenarios;
- validar los estados NORMAL, PRECAUCIÓN y CRÍTICO;
- depurar el firmware antes de integrar el hardware.

### 2. Prototipo físico

Posteriormente se construyó un **prototipo físico funcional** que integra:

- ESP32;
- sensor ultrasónico OKY3261/HC-SR04;
- BME280;
- mini panel fotovoltaico;
- INA219;
- LCD 16×2 I²C;
- LEDs verde, amarillo y rojo;
- buzzer;
- maqueta con plataforma móvil para representar diferentes niveles de agua.

Las pruebas físicas permitieron verificar la cadena completa:

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
ALERTA LOCAL
```

---

## 🧭 Navegación rápida de la Wiki

| # | Sección | Contenido |
|---|---|---|
| 0 | [Home](wiki/00-Home.md) | Índice general de la Wiki |
| 1 | [Resumen, motivación y justificación](wiki/01-Resumen-Motivacion.md) | Contexto, problemática, objetivo y justificación |
| 2 | [Solución propuesta](wiki/02-Solucion-Propuesta.md) | Arquitectura, variables, procesamiento y lógica de riesgo |
| 3 | [Desarrollo modular](wiki/03-Desarrollo-Modular.md) | Modelo matemático, UML, hardware y estrategia de implementación |
| 4 | [Modelo de negocio](wiki/04-Modelo-de-Negocio.md) | Business Model Canvas |
| 5 | [Configuración experimental y resultados](wiki/05-Configuracion-Experimental-Resultados.md) | Simulación, pruebas físicas y análisis de resultados |
| 6 | [Autoevaluación del protocolo de pruebas](wiki/06-Autoevaluacion-Pruebas.md) | Cobertura, fortalezas y limitaciones |
| 7 | [Conclusiones, retos y trabajo futuro](wiki/07-Conclusiones-Trabajo-Futuro.md) | Resultados finales, retos y oportunidades de mejora |
| 8 | [Uso de Inteligencia Artificial](wiki/08-Uso-de-IA.md) | Declaración de uso de IA |
| 9 | [Equipo de trabajo](wiki/09-Equipo-Roles.md) | Roles, contribuciones, acta y autoevaluación |
| 10 | [Executive Summary (English)](wiki/10-English-Executive-Summary.md) | Resumen ejecutivo en inglés |

---

## 🗂️ Estructura del repositorio

```text
sistema-alerta-temprana-riesgo-hidrico/
├── README.md
├── LICENSE
│
├── wiki/
│   ├── 00-Home.md
│   ├── 01-Resumen-Motivacion.md
│   ├── 02-Solucion-Propuesta.md
│   ├── 03-Desarrollo-Modular.md
│   ├── 04-Modelo-de-Negocio.md
│   ├── 05-Configuracion-Experimental-Resultados.md
│   ├── 06-Autoevaluacion-Pruebas.md
│   ├── 07-Conclusiones-Trabajo-Futuro.md
│   ├── 08-Uso-de-IA.md
│   ├── 09-Equipo-Roles.md
│   └── 10-English-Executive-Summary.md
│
├── firmware/
│   ├── sketch.ino
│   └── libraries.txt
│
├── hardware/
│   ├── wokwi/
│   │   ├── diagram.json
│   │   ├── wokwi-project-link.txt
│   │   └── chips/
│   └── schematics/
│       └── diagrama_circuito_wokwi.png
│
└── video/
    └── GUION_VIDEO.md
```

---

## ⚙️ Simulación en Wokwi

La simulación utilizada durante el desarrollo está disponible en:

**https://wokwi.com/projects/472250559337371649**

Para probarla:

1. Abrir el proyecto en Wokwi.
2. Iniciar la simulación.
3. Modificar los controles asociados a temperatura, humedad, presión e irradiancia.
4. Modificar la distancia del sensor ultrasónico.
5. Observar las variables calculadas y los cambios de estado.

La simulación permite reproducir:

```text
🟢 NORMAL
     ↓
🟡 PRECAUCIÓN
     ↓
🔴 CRÍTICO
```

> **Nota:** la simulación original utiliza una pantalla OLED SSD1306 como interfaz virtual. Durante la implementación física esta fue sustituida por una **LCD 16×2 I²C**. El firmware y los archivos almacenados en `hardware/wokwi/` corresponden a esta etapa de simulación y se conservan como evidencia del proceso de desarrollo.

---

## 🧩 Componentes del prototipo físico

| Función | Sensor / Actuador | Interfaz |
|---|---|---|
| Temperatura, humedad y presión | BME280 | I²C |
| Estimación de irradiancia | Mini panel fotovoltaico + INA219 | I²C |
| Nivel | OKY3261 / HC-SR04 | GPIO TRIG/ECHO |
| Visualización local | LCD 16×2 I²C | I²C |
| Alerta visual | LED verde / amarillo / rojo | GPIO digital |
| Alerta sonora | Buzzer | GPIO digital |
| Procesamiento | ESP32 | — |

---

## 🧠 Procesamiento del riesgo

WREWS utiliza tres componentes principales.

### 💧 Disponibilidad de agua

El sensor ultrasónico mide la distancia hasta la superficie que representa el agua.

Esta distancia se convierte en un porcentaje de nivel mediante la calibración correspondiente a las dimensiones de la maqueta.

### 🌡️ Condiciones ambientales

El BME280 obtiene temperatura y humedad relativa para calcular el **Vapor Pressure Deficit (VPD)**.

La señal obtenida mediante el panel fotovoltaico y el INA219 permite realizar una estimación experimental de irradiancia.

Ambas variables se combinan para obtener un **índice de condiciones favorables a la evaporación**.

### 📉 Tendencia

WREWS analiza diferentes mediciones del nivel a lo largo del tiempo para estimar su **tasa de descenso**.

Esto permite detectar reducciones aceleradas incluso antes de que el nivel alcance una condición extremadamente baja.

---

## 🚦 Sistema de alertas

La información procesada se transforma en tres estados:

| Estado | Indicador | Interpretación |
|---|---|---|
| 🟢 **NORMAL** | LED verde | Condiciones dentro del rango esperado |
| 🟡 **PRECAUCIÓN** | LED amarillo | Existen condiciones que requieren atención |
| 🔴 **CRÍTICO** | LED rojo + buzzer | Se detectó una condición de riesgo elevado |

La **LCD 16×2 I²C** proporciona información local adicional sobre el sistema.

---

## 🧪 Validación

La validación se realizó en dos niveles:

```text
WOKWI
Simulación controlada
      ↓
PROTOTIPO FÍSICO
Sensores + ESP32 + actuadores
      ↓
VALIDACIÓN FUNCIONAL
```

En el prototipo físico se verificó:

- respuesta del sensor ultrasónico;
- adquisición del BME280;
- adquisición del INA219 y panel;
- cálculo y procesamiento local;
- tasa de descenso;
- estados NORMAL, PRECAUCIÓN y CRÍTICO;
- LCD;
- LEDs;
- buzzer.

Para representar el nivel del agua se utilizó una **plataforma móvil** cuya altura puede modificarse frente al sensor ultrasónico.

Esto permite realizar pruebas repetibles sin exponer la electrónica directamente al agua.

Los resultados y el análisis completo se encuentran en:

[`wiki/05-Configuracion-Experimental-Resultados.md`](wiki/05-Configuracion-Experimental-Resultados.md)

---

## 🎥 Video de demostración

El video final presenta:

- problemática abordada;
- funcionamiento de WREWS;
- sensores utilizados;
- procesamiento de las variables;
- VPD e índice evaporativo;
- tasa de descenso;
- clasificación del riesgo;
- demostración del prototipo físico;
- estados NORMAL, PRECAUCIÓN y CRÍTICO.

El guion utilizado durante la producción se encuentra en:

[`video/GUION_VIDEO.md`](video/GUION_VIDEO.md)

> 🎬 **Video final de demostración:** [WREWS — Water Risk Early Warning System](https://youtu.be/zUS3DWeHSsw)

---

## 👥 Equipo — Challenge #1, Equipo 1

| Integrante | Rol principal |
|---|---|
| **Mateo Ramírez Cabrera** | Hardware e integración de sensores |
| **Antonio Benítez Rueda** | Firmware y lógica de fusión de datos |
| **Jorge Andrés Rodríguez Huertas** | Documentación, pruebas y gestión del proyecto |

El detalle de las contribuciones, compromisos y autoevaluación se encuentra en:

[`wiki/09-Equipo-Roles.md`](wiki/09-Equipo-Roles.md)

---

## 🤖 Uso de Inteligencia Artificial

El proyecto utilizó herramientas de Inteligencia Artificial como apoyo durante diferentes etapas del desarrollo.

La declaración y descripción correspondiente se mantiene documentada en:

[`wiki/08-Uso-de-IA.md`](wiki/08-Uso-de-IA.md)

---

## 📌 Resultado

WREWS evolucionó desde una arquitectura simulada hasta un **prototipo físico funcional**.

El sistema integra:

```text
NIVEL
   +
CONDICIONES AMBIENTALES
   +
TASA DE DESCENSO
   ↓
ÍNDICE DE RIESGO HÍDRICO
   ↓
NORMAL / PRECAUCIÓN / CRÍTICO
   ↓
LCD + LEDs + Buzzer
```

El prototipo demuestra la posibilidad de generar una **alerta temprana local de riesgo hídrico** mediante sensores de bajo costo y procesamiento embebido en un ESP32.