[⬅ Volver al índice](00-Home.md)

# 9. Equipo de trabajo: roles, actividades y contribuciones

## 9.1 Integrantes — Equipo 1

| Integrante | Rol principal | Correo / contacto |
|---|---|---|
| **Mateo Ramírez Cabrera** | Hardware e integración de sensores | mateoraca@unisabana.edu.co |
| **Antonio Benítez Rueda** | Firmware y lógica de fusión de datos | antonioberu@unisabana.edu.co |
| **Jorge Andrés Rodríguez Huertas** | Documentación, pruebas y gestión del proyecto | jorgerohu@unisabana.edu.co |

---

## 9.2 Descripción de roles y contribuciones

### Mateo Ramírez Cabrera — Hardware e integración de sensores

- Selección y dimensionamiento de los sensores utilizados en WREWS: BME280, sensor ultrasónico OKY3261/HC-SR04 e INA219 con mini panel fotovoltaico.
- Diseño del esquema inicial de conexión en Wokwi (`diagram.json`): mapeo de pines del ESP32, bus I²C compartido y conexión de los actuadores.
- Diseño y verificación de los *custom chips* de Wokwi (`bme280custom`, `ina219custom`, `solarpanel`) utilizados para simular el comportamiento de los sensores.
- Integración física de los sensores y actuadores con el ESP32.
- Participación en las pruebas y calibración del sensor ultrasónico para la medición del nivel.
- Participación en la construcción y ajuste de la maqueta utilizada para representar diferentes niveles de almacenamiento.
- Verificación del funcionamiento del BME280, INA219, panel fotovoltaico, LCD 16×2 I²C, LEDs y buzzer.
- Documentación del hardware y del esquema general de integración en la Wiki.

### Antonio Benítez Rueda — Firmware y lógica de fusión de datos

- Desarrollo y ajuste del firmware embebido para el ESP32.
- Implementación de la lectura de sensores mediante I²C y GPIO.
- Implementación del cálculo de nivel, VPD, irradiancia estimada, índice evaporativo, tasa de descenso e índice de riesgo hídrico.
- Implementación de la máquina de estados de alerta (`NORMAL`, `PRECAUCIÓN` y `CRÍTICO`) y de las reglas de seguridad independientes al promedio ponderado.
- Adaptación de la interfaz de visualización para la **LCD 16×2 I²C** utilizada en el prototipo físico.
- Implementación y ajuste del control de LEDs y buzzer.
- Participación en la calibración y depuración del prototipo físico.
- Apoyo en la construcción de los diagramas UML a partir de la arquitectura y lógica implementadas.

### Jorge Andrés Rodríguez Huertas — Documentación, pruebas y gestión del proyecto

- Redacción y estructuración de la Wiki técnica conforme a los requisitos del Challenge #1.
- Diseño y organización del protocolo de pruebas y de su autoevaluación.
- Verificación matemática independiente de los resultados y fórmulas utilizadas durante la etapa de simulación.
- Elaboración del modelo de negocio.
- Coordinación general del equipo y gestión del repositorio de GitHub.
- Documentación de los resultados obtenidos con el prototipo físico.
- Organización de la presentación final del proyecto.
- Preparación del guion y coordinación del video de demostración de WREWS.

---

## 9.3 Trabajo colaborativo

Aunque cada integrante contó con un rol principal, la integración final del proyecto requirió trabajo conjunto.

Entre las actividades realizadas colaborativamente se encuentran:

- definición de la problemática y alcance del sistema;
- selección de sensores y actuadores;
- definición de los estados de alerta;
- discusión de los pesos y umbrales de la lógica de riesgo;
- pruebas en Wokwi;
- integración del circuito físico;
- calibración del sensor de nivel;
- construcción y ajuste de la maqueta;
- validación de los estados NORMAL, PRECAUCIÓN y CRÍTICO;
- revisión de la documentación;
- preparación y grabación del video final.

El proyecto siguió un proceso iterativo en el que los resultados obtenidos durante la simulación y las pruebas físicas llevaron a realizar ajustes en el firmware, la calibración y la documentación.

---

## 9.4 Acta de reunión y evaluación del equipo

| Campo | Detalle |
|---|---|
| **Proyecto** | WREWS — Water Risk Early Warning System — Challenge #1 |
| **Curso** | Internet de las Cosas — 2026-2 — Universidad de La Sabana |
| **Fecha de la reunión** | 20/08/2026 |
| **Asistentes** | Mateo Ramírez Cabrera, Antonio Benítez Rueda, Jorge Andrés Rodríguez Huertas |
| **Modalidad** | Presencial |

### Temas tratados

1. Revisión del alcance del reto y de las restricciones técnicas del enunciado.
2. Validación del modelo de fusión de datos basado en nivel, condiciones ambientales y tasa de descenso.
3. Distribución de roles y actividades entre los tres integrantes.
4. Revisión de los resultados obtenidos durante las pruebas en Wokwi.
5. Planeación de la integración del prototipo físico.
6. Calibración y pruebas del sistema completo.
7. Planeación de la sustentación y del video de demostración.

### Compromisos y evaluación de participación

| Integrante | Compromiso adquirido | Cumplimiento | Observaciones |
|---|---|---|---|
| Mateo Ramírez Cabrera | Integrar el hardware, sensores y componentes necesarios para la medición y actuación del sistema | ✅ Cumplido | Participó además en calibración, maqueta y pruebas físicas |
| Antonio Benítez Rueda | Entregar y ajustar el firmware con lógica de fusión y estados de alerta | ✅ Cumplido | El firmware fue adaptado y probado sobre el prototipo físico |
| Jorge Andrés Rodríguez Huertas | Completar la documentación, protocolo de pruebas y organización del repositorio | ✅ Cumplido | Participó además en resultados, presentación y video final |

---

## 9.5 Autoevaluación de la contribución individual

Autoevaluación del equipo frente al indicador **“Contribuir al desarrollo de las actividades propias del rol asignado dentro del equipo de trabajo”**, utilizando la escala de la rúbrica del curso: **Novato / Aprendiz / Bueno / Experto**.

| Integrante | Nivel autoevaluado | Justificación breve |
|---|---|---|
| Mateo Ramírez Cabrera | **Experto** | Cumplió su responsabilidad de integración de hardware y sensores, participó en la simulación, montaje físico, calibración y validación funcional del prototipo. |
| Antonio Benítez Rueda | **Experto** | Desarrolló y ajustó el firmware, implementó la lógica de fusión y los estados de alerta y participó en la depuración del sistema físico. |
| Jorge Andrés Rodríguez Huertas | **Experto** | Estructuró la documentación, protocolo de pruebas y repositorio, verificó los resultados y coordinó la preparación de la entrega y presentación final. |

---

## 9.6 Resultado del trabajo del equipo

La distribución de responsabilidades y el trabajo colaborativo permitieron desarrollar el proyecto de manera progresiva:

```text
PROBLEMÁTICA
     ↓
DISEÑO
     ↓
SIMULACIÓN EN WOKWI
     ↓
DESARROLLO DEL FIRMWARE
     ↓
INTEGRACIÓN DEL HARDWARE
     ↓
CONSTRUCCIÓN DE LA MAQUETA
     ↓
CALIBRACIÓN
     ↓
PRUEBAS FÍSICAS
     ↓
DOCUMENTACIÓN Y VIDEO
     ↓
WREWS
```

El resultado final es un **prototipo físico funcional** capaz de adquirir múltiples variables, procesarlas localmente y generar una alerta temprana de riesgo hídrico mediante tres estados de fácil interpretación.

---

## 9.7 Contribuciones en el Challenge #2

Se mantuvieron los mismos roles principales.

### Mateo Ramírez Cabrera — Hardware, carcasa e integración

- Diseño de la carcasa en CadQuery (iteraciones v11 a v17) y su impresión en PETG: caja, tapa, piso intermedio, techo ventilado del BME280 y acople al tubo de PVC.
- Integración de los componentes en la carcasa y del sensor de nivel en el tubo de PVC.
- Diseño de la alimentación por pilas con interruptor y distribución de las filas de 5 V y 3.3 V.

### Antonio Benítez Rueda — Firmware, modelo y tablero de control

- Firmware v6: modelo de evaporación de Priestley-Taylor con FAO-56, ventana móvil, pesos AHP, nuevos umbrales y autotest de referencia.
- Firmware v7: tareas de FreeRTOS con mutex, Wi-Fi en modo estación con reconexión y dos redes, servidor web embebido, inicio de sesión, tablero con histórico, eventos y silencio de la alarma, y calibración desde el tablero guardada en flash.
- Diagnóstico y corrección de las fallas encontradas en las pruebas (tono del buzzer, recuperación del tablero, saturación del índice con sol, falsos positivos por evaporación).
- Hojas de referencias del modelo de evaporación y de pesos y umbrales.

### Jorge Andrés Rodríguez Huertas — Pruebas, documentación y video

- Diseño y ejecución del banco de pruebas del Challenge #2 .
- Actualización de la Wiki.
- Guion, grabación y edición del video.
- Verificación matemática independiente de las cifras del tablero (VPD, nivel, riesgo hídrico y energía diaria equivalente) frente a las fórmulas documentadas.
- Comparación de presión, temperatura y humedad del BME280 con instrumentos de referencia y registro de los errores obtenidos.
- Gestión del repositorio y de la Wiki del Challenge #2 y coordinación de la entrega.

### Acta de reunión del Challenge #2

| Campo | Detalle |
|---|---|
| **Proyecto** | WREWS — Water Risk Early Warning System — Challenge #2 |
| **Fecha de la reunión** | 04/10/2026 |
| **Asistentes** | Mateo Ramírez Cabrera, Antonio Benítez Rueda, Jorge Andrés Rodríguez Huertas |
| **Modalidad** | Presencial |
| **Temas tratados** | 1. Alcance del Challenge #2: prototipo terminado en carcasa, medición en hilo independiente y tablero embebido en la WLAN, sin MQTT. 2. Retroalimentación recibida en el Challenge #1 y cómo abordarla. 3. Arquitectura del firmware v7: tareas de FreeRTOS con mutex, reconexión Wi-Fi, servidor web, inicio de sesión y calibración guardada en flash. 4. Modelo de evaporación (Priestley-Taylor con FAO-56), pesos AHP (54 / 30 / 16) y nuevos umbrales. 5. Fallas detectadas en las pruebas: saturación del índice con sol y falsos positivos por evaporación, que llevaron a acotar la evaporación a PRECAUCIÓN y al modo DEMO de la irradiancia. 6. Diseño de la carcasa (iteraciones v11 a v17), alimentación por pilas y acople al tubo de PVC. 7. Plan del banco de pruebas: calibración contra referencias, emulación acelerada y prueba de campo en el lago. 8. Documentación en la Wiki, video de demostración y entrega. |
| **Compromisos y cumplimiento** | Mateo: carcasa, integración y alimentación — ✅ Cumplido. Antonio: firmware v6/v7, tablero y correcciones — ✅ Cumplido. Jorge: banco de pruebas, Wiki, repositorio y video — ✅ Cumplido. |

### Autoevaluación de la contribución individual (Challenge #2)

| Integrante | Nivel autoevaluado | Justificación breve |
|---|---|---|
| Mateo Ramírez Cabrera | **Experto** | Diseñó e imprimió la carcasa a lo largo de siete iteraciones, integró todos los módulos en un producto instalable sobre tubo, resolvió la alimentación por pilas con sus filas de 5 V y 3.3 V y participó en las pruebas de campo. |
| Antonio Benítez Rueda | **Experto** | Desarrolló dos versiones mayores del firmware con tareas concurrentes, servidor web con autenticación, modelo de evaporación y calibración persistente, y corrigió las fallas que aparecieron en las pruebas. |
| Jorge Andrés Rodríguez Huertas | **Experto** | Estructuró y publicó la documentación completa del Challenge #2, diseñó el banco de pruebas, verificó de forma independiente las cifras del tablero y coordinó el repositorio, el video y la entrega. |
---

## 9.8 Contribuciones en el Challenge #3

| Integrante | Rol | GitHub |
|---|---|---|
| **Mateo Ramírez Cabrera** | Integración del sistema: firmware v8, gateway, módulo de IA y canal de Telegram | [technologybyteo](https://github.com/technologybyteo) |
| **Jorge Andrés Rodríguez Huertas** | Despliegue en la Raspberry Pi, protocolo de pruebas y evidencias | [jorgis857](https://github.com/jorgis857) |
| **Antonio Benítez Rueda** | Plataforma en la nube (Ubidots), arquitectura y UML, modelo de negocio, video y pitch | [antobeni07](https://github.com/antobeni07) |

### Mateo Ramírez Cabrera — Integración: firmware, gateway e IA

- Integración del firmware v8: hilo de comunicación MQTT con FreeRTOS, última voluntad, orden de silenciar desde la nube, filtro de plausibilidad del BME280 y búsqueda del gateway por mDNS.
- Gateway en Python: almacenamiento en SQLite antes de reenviar, validación y anomalías, ventanas de agregación, vigilancia del enlace y puente MQTT/TLS con Ubidots.
- Módulo de IA: regresión propia y recomendación con la API de Claude a pedido, con respaldo por reglas.
- Bot de Telegram con clave y aprobación del administrador, dashboard en imagen y dashboard en vivo.
- Pruebas con el prototipo real y un PC como gateway: silenciar desde Ubidots, ESP32 apagado, broker caído y diagnóstico de los incidentes de la sección 5.8.
- Uso de Claude Code como asistente de desarrollo (ver sección 8.6).
- Instalación del gateway en la Raspberry Pi y edición del video.

### Jorge Andrés Rodríguez Huertas — Despliegue en la Raspberry Pi y validación

- Preparación de la microSD de la Raspberry Pi en modo *headless* (hostname, usuario, Wi-Fi del hotspot y SSH), para que arrancara y se conectara sola en la universidad.
- Participación en el despliegue y en el protocolo de pruebas de extremo a extremo en la Pi (sección 5.8, etapa 3), con capturas y consultas a SQLite como evidencia.
- Grabación de la escena C del video: silenciar la alarma desde Ubidots y módulo de IA.
- Revisión de los resultados de las secciones 5 y 6 de la Wiki.

### Antonio Benítez Rueda — Nube, documentación y comunicación

- Responsable del área de nube: revisión del tablero global en Ubidots (widgets, eventos de notificación y switch para silenciar) frente a los requisitos del enunciado.
- Revisión de los diagramas de arquitectura y UML del Challenge #3 (secciones 2.18 y 3.28) frente al firmware y al gateway.
- Revisión de la cotización del modelo de negocio y redacción de las nuevas fuentes de ingreso (sección 4.4).
- Grabación de los clips de la persona B del video: operación normal y escalada de alarmas.
- Preparación y presentación del pitch de la sustentación.

### Acta de reunión del Challenge #3

| Campo | Detalle |
|---|---|
| **Proyecto** | WREWS — Water Risk Early Warning System — Challenge #3 |
| **Fecha de la reunión** | 13/11/2026 |
| **Asistentes** | Mateo Ramírez Cabrera, Jorge Andrés Rodríguez Huertas. Antonio Benítez Rueda no asistió; sus tareas se acordaron por mensaje |
| **Modalidad** | Presencial (Universidad de La Sabana) |
| **Temas tratados** | 1. Despliegue del gateway en la Raspberry Pi con la microSD preparada y el kit de instalación. 2. Ejecución de las 11 pruebas de extremo a extremo y copia de la base de datos y del registro como evidencia. 3. Grabación del video por escenas y reparto de las partes A, B y C. 4. Reparto de las tareas pendientes de la Wiki y preparación del pitch de la sustentación. |
| **Compromisos y cumplimiento** | Mateo: instalación del gateway, pruebas y edición del video — ✅ Cumplido. Jorge: microSD, pruebas y escena C del video — ✅ Cumplido. Antonio: clips de la persona B, revisión de la nube, los diagramas y el modelo de negocio, y pitch — en curso al cierre de la Wiki. |

### Autoevaluación de la contribución individual (Challenge #3)

| Integrante | Nivel autoevaluado | Justificación breve |
|---|---|---|
| Mateo Ramírez Cabrera | **Experto** | Integró el firmware v8, el gateway, el módulo de IA y el bot de Telegram, instaló el sistema en la Raspberry Pi y llevó las pruebas de extremo a extremo con el prototipo real. |
| Jorge Andrés Rodríguez Huertas | **Experto** | Preparó la microSD para el arranque automático de la Pi, participó en el despliegue y en las 11 pruebas en la universidad, y grabó la escena del control desde la nube y de la IA. |
| Antonio Benítez Rueda | **Avanzado** | Revisó el tablero de Ubidots, los diagramas y el modelo de negocio frente al enunciado, grabó su parte del video y preparó el pitch. Su firmware v7 fue la base del v8. |

---

[⬅ Anterior: Uso de Inteligencia Artificial](08-Uso-de-IA.md) · [⬆ Índice](00-Home.md) · [Siguiente: Resumen ejecutivo en inglés ➡](10-English-Executive-Summary.md)