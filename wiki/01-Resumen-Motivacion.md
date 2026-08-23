[⬅ Volver al índice](00-Home.md)

# 1. Resumen general, motivación, justificación y estructura de la documentación

## 1.1 Resumen ejecutivo

**SATRH (Sistema de Alerta Temprana de Riesgo Hídrico)** es un prototipo funcional de Internet de las Cosas construido sobre un microcontrolador **ESP32**, diseñado para monitorear en tiempo real la disponibilidad de agua en puntos críticos de suministro y almacenamiento (aljibes, tanques comunitarios, reservorios veredales) de la región Sabana Centro (Cundinamarca), y para **alertar de forma local e inmediata** — sin depender de Internet, Wi-Fi, redes celulares ni ningún otro medio de comunicación — cuando las condiciones se acercan a un escenario de desabastecimiento.

El sistema combina tres tipos de evidencia física para tomar una decisión de riesgo:

1. **Cuánta agua queda** — nivel del reservorio, medido con un sensor ultrasónico HC-SR04.
2. **Qué tan favorables son las condiciones ambientales para que esa agua se pierda por evaporación** — combinando temperatura, humedad relativa (sensor BME280) y radiación solar aproximada (mini panel solar + sensor de corriente INA219).
3. **Qué tan rápido está bajando el nivel** — estimando el cambio por medio de una regresión lineal de mínimos cuadrados.

Estas tres señales se funden mediante una función de ponderación (50 % déficit de nivel + 30 % índice evaporativo + 20 % tasa de descenso) más un conjunto de **reglas de seguridad** que garantizan que ninguna variable extremadamente crítica quede "escondida" por el promedio de las demás. El resultado se traduce en tres estados — 🟢 `NORMAL`, 🟡 `PRECAUCIÓN`, 🔴 `CRÍTICO` — que se comunican **in situ** mediante una pantalla LCD, LEDs de estado y un buzzer, cumpliendo así con la restricción técnica de notificación local sin infraestructura de comunicaciones.

## 1.2 Motivación

Durante 2026, el Gobierno Nacional y el IDEAM confirmaron el inicio anticipado del Fenómeno de El Niño, lo que agravó de forma crítica la disponibilidad hídrica en la Sabana de Bogotá y Cundinamarca [1]. La CAR identificó **20 municipios** de la región en riesgo extremo de desabastecimiento hídrico e incendios forestales por el agotamiento físico de fuentes superficiales y reservorios locales [2]. A esto se suman 16 escenarios de riesgo crítico tipificados por las autoridades distritales, entre los cuales el desabastecimiento crónico de agua potable y la caída de niveles en embalses ocupan un lugar central [3]. Aunque existen planes de contingencia institucionales [4], estos dependen de redes de monitoreo hidrometeorológico centralizadas que no necesariamente llegan con la granularidad y la velocidad de reacción que requieren los reservorios comunitarios rurales más pequeños y dispersos.

De ahí nace la motivación del proyecto: **llevar la vigilancia hidrometeorológica al punto exacto donde el agua se almacena**, con un dispositivo autónomo, de bajo costo, que no dependa de conectividad, y que traduzca variables físicas crudas en una alerta comprensible para cualquier persona de la comunidad — sin necesidad de interpretar datos técnicos.

## 1.3 Justificación

- **Pertinencia social:** los reservorios comunitarios y aljibes rurales de Sabana Centro son gestionados frecuentemente por juntas de acueductos veredales con recursos técnicos limitados; un sistema de bajo costo con alerta visual/sonora directa es más accesible que un sistema que dependa de una app o de conectividad a Internet.
- **Pertinencia técnica (IoT):** el reto exige aplicar los pilares de un ecosistema IoT — percepción (sensores ambientales e hidráulicos), procesamiento en el borde (*edge computing* en el ESP32, sin nube), fusión de datos multivariable y actuación local (HMI física) — todo dentro de un mismo nodo autónomo.
- **Restricción de comunicaciones:** al no poder usarse redes de comunicación convencionales, el diseño obliga a que **toda la inteligencia de decisión resida en el dispositivo**, lo cual es un ejercicio representativo de sistemas embebidos distribuidos ("edge intelligence") aplicables a zonas rurales sin cobertura.
- **Escalabilidad:** el mismo firmware y arquitectura de sensores puede replicarse en distintos puntos críticos (aljibes, tanques de distrito de riego, quebradas) simplemente recalibrando los parámetros `DISTANCIA_LLENO` / `DISTANCIA_VACIO` de cada reservorio.

## 1.4 Alcance del prototipo

El desarrollo se hizo en dos etapas. En la primera, la arquitectura y la lógica de
fusión se validaron en **simulación (Wokwi)** mediante *custom chips* escritos
en C que emulan funcionalmente un BME280, un INA219 acoplado a un mini panel solar 
y un HC-SR04. En la segunda, se realizó el **montaje físico** (ESP32 DevKit, 
BME280, sensor ultrasónico OKY3261, LCD 16×2 I²C, LEDs y buzzer pasivo), donde se 
ejecutaron la caracterización de ruido del sensor y se calibraron experimentalmente
los umbrales de tendencia.

El firmware corre en el ESP32 y no requiere ningún servicio externo. Las 
limitaciones remanentes —geometría del banco de pruebas y escala temporal— 
se detallan en la [Sección 6](06-Autoevaluacion-Pruebas.md).

## 1.5 Estructura de la documentación

Esta Wiki sigue la estructura solicitada en el enunciado del Challenge #1:

| Sección | Contenido |
|---|---|
| [2. Solución propuesta](02-Solucion-Propuesta.md) | Restricciones de diseño identificadas y arquitectura (diagrama de bloques hardware/software) |
| [3. Desarrollo modular](03-Desarrollo-Modular.md) | Criterios de diseño, diagramas UML, esquemático de hardware, estándares de ingeniería aplicados |
| [4. Modelo de negocio](04-Modelo-de-Negocio.md) | Business Model Canvas del sistema |
| [5. Configuración experimental, resultados y análisis](05-Configuracion-Experimental-Resultados.md) | Casos de prueba, mediciones y su interpretación |
| [6. Autoevaluación del protocolo de pruebas](06-Autoevaluacion-Pruebas.md) | Checklist de validación del propio protocolo |
| [7. Conclusiones, retos, trabajo futuro y referencias](07-Conclusiones-Trabajo-Futuro.md) | Cierre del proyecto y bibliografía IEEE |
| [8. Uso de Inteligencia Artificial](08-Uso-de-IA.md) | Declaración obligatoria de uso de IA generativa |
| [9. Equipo de trabajo](09-Equipo-Roles.md) | Roles, actividades y contribuciones de cada integrante |

---
[⬅ Volver al índice](00-Home.md) · [Siguiente: Solución propuesta ➡](02-Solucion-Propuesta.md)
