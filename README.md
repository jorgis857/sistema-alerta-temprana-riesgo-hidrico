# 💧 Sistema de Alerta Temprana de Riesgo Hídrico (SATRH)

**Internet de las Cosas — Challenge #1 — 2026-2**
Facultad de Ingeniería, Universidad de La Sabana

[![Plataforma](https://img.shields.io/badge/MCU-ESP32-blue)](https://www.espressif.com/en/products/socs/esp32)
[![Simulación](https://img.shields.io/badge/Simulado%20en-Wokwi-green)](https://wokwi.com/projects/472250559337371649)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-lightgrey)](LICENSE)
[![Estado](https://img.shields.io/badge/Estado-Prototipo%20funcional-yellow)]()

> Prototipo IoT de bajo costo que mide en tiempo real el nivel de un reservorio de agua, las condiciones ambientales que favorecen su evaporación y la velocidad con la que el nivel está descendiendo, para fusionar esas tres señales en un **índice de riesgo hídrico** y emitir una **alerta local (in situ)** — visual y sonora — sin depender de redes de comunicación, Wi-Fi o Internet.

---

## 🎯 El reto

Durante 2026 el Fenómeno de El Niño agudizó el riesgo de desabastecimiento hídrico en 20 municipios de la Sabana Centro (Cundinamarca). El reto pide diseñar un prototipo IoT que **mida y analice en tiempo real** el nivel de agua, la evaporación potencial y variables meteorológicas, **combinándolas mediante lógica de fusión** para emitir alertas tempranas **in situ**, sin usar redes de comunicación convencionales.

📄 Documentación completa (Wiki): **[`/wiki`](wiki/00-Home.md)**

---

## 🧭 Navegación rápida de la Wiki

| # | Sección | Contenido |
|---|---------|-----------|
| 0 | [Home](wiki/00-Home.md) | Índice general de la Wiki |
| 1 | [Resumen, motivación y justificación](wiki/01-Resumen-Motivacion.md) | Contexto del problema, alcance y estructura del documento |
| 2 | [Solución propuesta](wiki/02-Solucion-Propuesta.md) | Restricciones de diseño, arquitectura y diagrama de bloques (HW/SW) |
| 3 | [Desarrollo modular](wiki/03-Desarrollo-Modular.md) | Criterios de diseño, diagramas UML, esquemático, estándares de ingeniería |
| 4 | [Modelo de negocio](wiki/04-Modelo-de-Negocio.md) | Business Model Canvas |
| 5 | [Configuración experimental y resultados](wiki/05-Configuracion-Experimental-Resultados.md) | Casos de prueba en Wokwi y análisis de resultados |
| 6 | [Autoevaluación del protocolo de pruebas](wiki/06-Autoevaluacion-Pruebas.md) | Checklist de validación |
| 7 | [Conclusiones, retos y trabajo futuro](wiki/07-Conclusiones-Trabajo-Futuro.md) | Cierre, lecciones aprendidas y referencias IEEE |
| 8 | [Uso de Inteligencia Artificial](wiki/08-Uso-de-IA.md) | Declaración obligatoria de uso de IA |
| 9 | [Equipo de trabajo](wiki/09-Equipo-Roles.md) | Roles, contribuciones y acta de reunión |
| 10 | [Executive Summary (English)](wiki/10-English-Executive-Summary.md) | Resumen ejecutivo en inglés (segunda lengua) |


> 💡 Estos mismos archivos están pensados para copiarse tal cual dentro de la **Wiki de GitHub** del repositorio (pestaña *Wiki*), además de poder leerse directamente desde `/wiki` en el código fuente.

---

## 🗂️ Estructura del repositorio

```
sistema-alerta-temprana-riesgo-hidrico/
├── README.md                     # Este archivo
├── LICENSE
├── wiki/                         # Documentación técnica completa (formato Wiki)
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
│   ├── 10-English-Executive-Summary.md
│   └── 11-Checklist-Rubrica.md
├── firmware/
│   ├── sketch.ino                # Código fuente documentado (ESP32)
│   └── libraries.txt             # Librerías Arduino/Wokwi requeridas
├── hardware/
│   ├── wokwi/
│   │   ├── diagram.json          # Diagrama de conexiones Wokwi
│   │   ├── wokwi-project-link.txt
│   │   └── chips/                # Chips personalizados (C) simulando BME280, INA219 y panel solar
│   └── schematics/
│       └── diagrama_circuito_wokwi.png
├── video/
│   └── GUION_VIDEO.md            # Guion para el video de demostración (máx. 5 min)
└── .github/
    └── PULL_REQUEST_TEMPLATE.md  (opcional)
```

---

## ⚙️ Cómo simular el prototipo

1. Abrir el proyecto original en Wokwi: **https://wokwi.com/projects/472250559337371649**
   *(o crear un nuevo proyecto ESP32 en [wokwi.com](https://wokwi.com), pegar el contenido de `hardware/wokwi/diagram.json` como `diagram.json`, `firmware/sketch.ino` como `sketch.ino`, `firmware/libraries.txt` como `libraries.txt`, y los 3 pares de archivos `.chip.c` / `.chip.json` de `hardware/wokwi/chips/` como *custom chips*).*
2. Compilar y correr la simulación (▶️).
3. Mover los controles (sliders) de temperatura, humedad, presión e irradiancia solar de los chips personalizados, y ajustar la distancia del sensor ultrasónico `HC-SR04`, para observar en el **Monitor Serial** y en la **pantalla OLED** cómo cambia el estado del sistema: 🟢 `NORMAL` → 🟡 `PRECAUCION` → 🔴 `CRITICO` (LED + buzzer).

## 🧩 Componentes principales

| Variable | Sensor / Actuador | Interfaz |
|---|---|---|
| Temperatura, humedad, presión atmosférica | BME280 (chip personalizado Wokwi) | I²C (`0x76`) |
| Radiación solar (aprox.) | Mini panel solar + INA219 (chip personalizado Wokwi) | I²C (`0x40`) |
| Nivel del reservorio | HC-SR04 / OKY3261 | GPIO TRIG/ECHO |
| Visualización local | OLED SSD1306 128×64 | I²C (`0x3C`) |
| Alarma visual | LED verde / amarillo / rojo | GPIO digital |
| Alarma sonora | Buzzer | GPIO digital (PWM `tone`) |
| Procesamiento central | ESP32 DevKit | — |

## 👥 Equipo — Challenge #1, Equipo 1

| Integrante | Rol principal |
|---|---|
| Mateo Ramírez Cabrera | Hardware e integración de sensores |
| Antonio Benítez Rueda | Firmware y lógica de fusión de datos |
| Jorge Andrés Rodríguez Huertas | Documentación, pruebas y gestión del proyecto |

Detalle de contribuciones en [`wiki/09-Equipo-Roles.md`](wiki/09-Equipo-Roles.md).

## 📜 Licencia

Este proyecto se distribuye bajo licencia [MIT](LICENSE) con fines académicos.

## 🙏 Uso de Inteligencia Artificial

Este proyecto usó asistencia de IA (Claude, Anthropic) para apoyo en documentación y estructuración del código. Ver la declaración completa, obligatoria según el enunciado, en [`wiki/08-Uso-de-IA.md`](wiki/08-Uso-de-IA.md).
