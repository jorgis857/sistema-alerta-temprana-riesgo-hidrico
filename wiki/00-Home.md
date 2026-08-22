# Wiki — Sistema de Alerta Temprana de Riesgo Hídrico (SATRH)

**Curso:** Internet de las Cosas — 2026-2
**Facultad de Ingeniería — Universidad de La Sabana**
**Challenge #1 — Equipo 1**
**Fecha de entrega:** 22 de agosto de 2026 · **Sustentación:** semana 6 (24 o 27 de agosto de 2026)

Bienvenidos a la Wiki técnica del proyecto **SATRH**, un prototipo IoT de bajo costo, basado en ESP32, que monitorea de forma continua el nivel de un reservorio de agua, las condiciones ambientales que favorecen su evaporación y la velocidad de descenso del nivel, fusionando estas señales en un único **índice de riesgo hídrico** que se comunica localmente mediante una pantalla OLED, LEDs de estado y un buzzer — sin usar redes de comunicación.

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
- Guion del video de demostración: [`/video/GUION_VIDEO.md`](../video/GUION_VIDEO.md)

> **Nota:** el enlace público de esta Wiki debe compartirse con `@afbeltranp` según lo exige el enunciado del Challenge #1, junto con el enlace del repositorio y el video en la actividad habilitada en MS Teams.
