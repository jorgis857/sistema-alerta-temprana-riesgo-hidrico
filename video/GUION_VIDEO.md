# Guion del video de demostración (máx. 5 minutos)

Requisito del enunciado: video demostrativo y explicativo de la etapa de validación del prototipo funcional, de máximo 5 minutos, reproducible dentro de MS Teams sin necesidad de descarga, con **todos los integrantes participando y con cámara encendida**.

## Estructura sugerida (5:00 min)

| Tiempo | Segmento | Quién habla | Contenido a mostrar/decir |
|---|---|---|---|
| 0:00 – 0:40 | Introducción del problema | Jorge Andrés Rodríguez Huertas | "Somos el Equipo 1 del curso Internet de las Cosas. Nuestro reto es el desabastecimiento hídrico en Sabana Centro por el Fenómeno de El Niño. Construimos SATRH, un sistema IoT que mide el nivel de un reservorio y las condiciones ambientales de evaporación, y alerta localmente sin usar redes de comunicación." Mostrar cámara + slide/README con el nombre del proyecto. |
| 0:40 – 1:30 | Arquitectura del sistema | Mateo Ramírez Cabrera | Mostrar el diagrama de bloques (Sección 2.2 de la Wiki) y el circuito armado en Wokwi. Explicar sensores: BME280 (temperatura/humedad/presión), INA219 + panel solar (radiación), HC-SR04 (nivel), y actuadores: OLED, LEDs, buzzer. Resaltar que todo corre localmente en el ESP32. |
| 1:30 – 2:30 | Lógica de fusión de datos | Antonio Benítez Rueda | Explicar en tablero/slide las fórmulas de VPD, índice evaporativo, tasa de descenso y riesgo hídrico (Sección 3.2 de la Wiki), y las reglas de seguridad que fuerzan el estado CRÍTICO. Mostrar brevemente el código correspondiente en `sketch.ino`. |
| 2:30 – 4:00 | Demostración en vivo (Wokwi) | Los tres integrantes, alternando | Ejecutar la simulación en Wokwi. Mostrar: (1) estado NORMAL con valores favorables — LED verde, OLED con mediciones; (2) cambiar sliders para forzar PRECAUCIÓN — LED amarillo; (3) forzar CRÍTICO (p. ej. bajando mucho el nivel o subiendo mucho la irradiancia/bajando la humedad) — LED rojo + buzzer sonando; mostrar el Monitor Serial con el detalle numérico de cada variable. |
| 4:00 – 4:40 | Resultados y validación | Jorge Andrés Rodríguez Huertas | Mostrar brevemente la tabla de casos de prueba de la Sección 5 de la Wiki y mencionar que los resultados fueron verificados matemáticamente de forma independiente. |
| 4:40 – 5:00 | Cierre | Los tres integrantes | Mencionar trabajo futuro (migración a hardware físico, calibración de campo) y agradecer. Cámara encendida con los tres integrantes visibles. |

## Recomendaciones técnicas de grabación

- Grabar en una resolución mínima de 720p, con el simulador de Wokwi visible y legible (aumentar zoom del navegador si es necesario).
- Usar una herramienta de grabación de pantalla + cámara simultánea (p. ej. OBS Studio, Loom, o la grabación nativa de Teams/Zoom) para poder mostrar pantalla y rostro a la vez, cumpliendo el requisito de "todos los integrantes con cámara encendida".
- Subir el video a una plataforma que permita reproducción embebida dentro de Teams **sin necesidad de descarga** (p. ej. Microsoft Stream/OneDrive, o subirlo directamente como archivo de video en la actividad de Teams).
- Verificar que el audio sea claro y que cada integrante se identifique por nombre al hablar por primera vez.

## Checklist antes de subir el video

- [ ] Duración ≤ 5 minutos.
- [ ] Los tres integrantes aparecen y participan con cámara encendida.
- [ ] Se muestra la demostración funcional completa (los 3 estados: NORMAL, PRECAUCIÓN, CRÍTICO).
- [ ] Se explica brevemente la lógica de fusión de datos.
- [ ] El video se reproduce dentro de Teams sin necesidad de descargarlo.
