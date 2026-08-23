# Wiki — WREWS (Water Risk Early Warning System)

**Curso:** Internet de las Cosas — 2026-2
**Facultad de Ingeniería — Universidad de La Sabana**
**Challenge #1 — Equipo 1**
**Fecha de entrega:** 22 de agosto de 2026 · **Sustentación:** semana 6 (24 o 27 de agosto de 2026)

Bienvenidos a la Wiki técnica del proyecto **WREWS (Water Risk Early Warning System)**, un prototipo IoT de bajo costo, basado en ESP32, que monitorea de forma continua el nivel de un reservorio de agua, las condiciones ambientales que favorecen su evaporación y la velocidad de descenso del nivel, fusionando estas señales en un único **índice de riesgo hídrico** que se comunica localmente mediante una pantalla LCD 16×2 I²C, LEDs de estado y un buzzer.
El desarrollo se realizó en dos etapas: primero se validó la arquitectura y la lógica del sistema mediante simulación en Wokwi y posteriormente se construyó y validó un prototipo físico funcional. La implementación física final utiliza una pantalla LCD 16×2 I²C como interfaz de visualización local.

## 🎥 Video de demostración

El funcionamiento completo del prototipo físico WREWS, incluyendo la adquisición de variables, procesamiento y generación de los estados **NORMAL, PRECAUCIÓN y CRÍTICO**, puede observarse en el video final:

▶️ **[Ver video de demostración de WREWS](https://youtu.be/zUS3DWeHSsw)**

---

## Índice

1. [Resumen, motivación y justificación](01-Resumen-Motivacion.md)
2. [Solución propuesta: restricciones, arquitectura y diagrama de bloques](02-Solucion-Propuesta.md)
3. [Desarrollo modular: criterios de diseño, UML, esquemático y estándares](03-Desarrollo-Modular.md)
4. [Modelo de negocio](04-Modelo-de-Negocio.md)
5. [Configuración experimental, resultados y análisis](05-Configuracion-Experimental-Resultados.md)
6. [Autoevaluación del protocolo de pruebas](06-Autoevaluacion-Pruebas.md)
7. [Conclusiones, retos, trabajo futuro y referencias](07-Conclusiones-Trabajo-Futuro.md)
8. [Uso de Inteligencia Artificial](08-Uso-de-IA.md)
9. [Equipo de trabajo: roles y contribuciones](09-Equipo-Roles.md)
10. [Executive Summary (English)](10-English-Executive-Summary.md)

## Anexos

- Código fuente completo y documentado: [`/firmware/sketch.ino`](../firmware/sketch.ino)
- Librerías utilizadas: [`/firmware/libraries.txt`](../firmware/libraries.txt)
- Diagrama de conexión Wokwi: [`/hardware/wokwi/diagram.json`](../hardware/wokwi/diagram.json)
- Chips personalizados (BME280, INA219, panel solar): [`/hardware/wokwi/chips`](../hardware/wokwi/chips)
- Esquemático / captura del circuito: [`/hardware/schematics/diagrama_circuito_wokwi.png`](../hardware/schematics/diagrama_circuito_wokwi.png)
- Proyecto simulable en Wokwi: <https://wokwi.com/projects/472250559337371649>


