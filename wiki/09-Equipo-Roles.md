[⬅ Volver al índice](00-Home.md)

# 9. Equipo de trabajo: roles, actividades y contribuciones

## 9.1 Integrantes — Equipo 1

| Integrante | Rol principal | Correo / contacto |
|---|---|---|
| **Mateo Ramírez Cabrera** | Hardware e integración de sensores | *(completar)* |
| **Antonio Benítez Rueda** | Firmware y lógica de fusión de datos | *(completar)* |
| **Jorge Andrés Rodríguez Huertas** | Documentación, pruebas y gestión del proyecto | jorge · chatgptplus277@gmail.com |

> Los correos/contactos marcados como *(completar)* deben ser diligenciados por cada integrante antes de la publicación final de la Wiki.

## 9.2 Descripción de roles y contribuciones

### Mateo Ramírez Cabrera — Hardware e integración de sensores

- Selección y dimensionamiento de los sensores (BME280, HC-SR04, INA219 + mini panel solar) y de los componentes de alimentación (batería 18650, TP4056, MT3608).
- Diseño del esquema de conexión en Wokwi (`diagram.json`): mapeo de pines del ESP32, bus I²C compartido, divisor resistivo del pin ECHO y polaridad de los LEDs.
- Diseño y verificación de los *custom chips* de Wokwi (`bme280custom`, `ina219custom`, `solarpanel`) que emulan el comportamiento eléctrico real de los sensores.
- Documentación del esquemático de hardware y del mapa de pines (Sección 3.4 de la Wiki).

### Antonio Benítez Rueda — Firmware y lógica de fusión de datos

- Desarrollo del firmware embebido (`firmware/sketch.ino`) para el ESP32: lectura de sensores por I²C y GPIO, cálculo de nivel, VPD, radiación, índice evaporativo, tasa de descenso e índice de riesgo hídrico.
- Implementación de la máquina de estados de alerta (NORMAL/PRECAUCIÓN/CRÍTICO) y de las reglas de seguridad independientes al promedio ponderado.
- Implementación de la interfaz de usuario en la pantalla OLED (dos vistas alternantes) y del control de LEDs y buzzer.
- Apoyo en la construcción de los diagramas UML (estados, secuencia, componentes) a partir del código real.

### Jorge Andrés Rodríguez Huertas — Documentación, pruebas y gestión del proyecto

- Redacción y estructuración de la Wiki técnica conforme a los requisitos del enunciado del Challenge #1.
- Diseño y ejecución del protocolo de pruebas (Sección 5) y de la autoevaluación del mismo (Sección 6).
- Verificación matemática independiente de los resultados presentados (recalculo de fórmulas fuera del firmware).
- Elaboración del modelo de negocio (Sección 4), coordinación general del equipo, gestión del repositorio de GitHub y preparación del guion del video de sustentación.

## 9.3 Acta de reunión y evaluación del equipo

| Campo | Detalle |
|---|---|
| **Proyecto** | Sistema de Alerta Temprana de Riesgo Hídrico (SATRH) — Challenge #1 |
| **Curso** | Internet de las Cosas — 2026-2 — Universidad de La Sabana |
| **Fecha de la reunión** | *(completar con la fecha real de la reunión del equipo)* |
| **Asistentes** | Mateo Ramírez Cabrera, Antonio Benítez Rueda, Jorge Andrés Rodríguez Huertas |
| **Modalidad** | *(presencial / virtual — completar)* |

### Temas tratados

1. Revisión del alcance del reto y de las restricciones técnicas del enunciado (no Raspberry Pi, alerta *in situ* sin redes de comunicación).
2. Validación del modelo de fusión de datos (pesos 50/30/20 %) y de los umbrales de alerta propuestos.
3. Distribución de roles y actividades entre los tres integrantes (hardware, firmware, documentación/pruebas).
4. Revisión conjunta de los resultados de los casos de prueba en Wokwi.
5. Planeación de la sustentación (pitch de 3 minutos + 15 minutos de preguntas) y del video de demostración.

### Compromisos y evaluación de participación

| Integrante | Compromiso adquirido | Cumplimiento | Observaciones |
|---|---|---|---|
| Mateo Ramírez Cabrera | Entregar esquemático y *custom chips* funcionando en Wokwi | ✅ Cumplido | — |
| Antonio Benítez Rueda | Entregar firmware con lógica de fusión completa y probada | ✅ Cumplido | — |
| Jorge Andrés Rodríguez Huertas | Entregar Wiki completa, protocolo de pruebas y repositorio listo para publicar | ✅ Cumplido | — |

> **Nota:** esta acta se deja como plantilla base con la información disponible al momento de generar la documentación. Se recomienda que el equipo la complemente con fecha exacta, modalidad de la reunión y cualquier observación adicional antes de la entrega final, y que agregue actas de reuniones adicionales si el equipo sostuvo más de un encuentro de trabajo.

## 9.4 Autoevaluación de la contribución individual

Autoevaluación del equipo frente al indicador *"Contribuir al desarrollo de las actividades propias del rol asignado dentro del equipo de trabajo"* (competencia de Autoaprendizaje), usando la misma escala de la rúbrica del curso (Novato / Aprendiz / Bueno / Experto):

| Integrante | Nivel autoevaluado | Justificación breve |
|---|---|---|
| Mateo Ramírez Cabrera | Bueno / Experto *(a confirmar por el equipo)* | Entregó el esquemático completo y los tres *custom chips* de Wokwi funcionando y acoplados correctamente a la lógica del firmware. |
| Antonio Benítez Rueda | Bueno / Experto *(a confirmar por el equipo)* | Entregó el firmware completo con la lógica de fusión de datos y la máquina de estados de alerta funcionando según lo diseñado. |
| Jorge Andrés Rodríguez Huertas | Bueno / Experto *(a confirmar por el equipo)* | Entregó la Wiki completa, el protocolo de pruebas con verificación matemática independiente, y organizó el repositorio para su publicación. |

> **Importante:** esta autoevaluación fue redactada como plantilla junto con el resto de la documentación. El equipo debe revisarla en conjunto, ajustar el nivel real alcanzado por cada integrante y firmarla (o dejar constancia) antes de la entrega final, ya que la rúbrica exige explícitamente evidencia de acta de reunión **y** evaluación.

---
[⬅ Anterior: Uso de Inteligencia Artificial](08-Uso-de-IA.md) · [⬆ Índice](00-Home.md) · [Siguiente: Resumen ejecutivo en inglés ➡](10-English-Executive-Summary.md)
