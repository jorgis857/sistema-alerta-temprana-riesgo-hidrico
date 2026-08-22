[⬅ Volver al índice](00-Home.md)

# 7. Conclusiones, retos, trabajo futuro y referencias

## 7.1 Conclusiones

1. Se diseñó y validó en simulación un **prototipo funcional de sistema IoT de bajo costo** capaz de medir en tiempo real el nivel de un reservorio de agua, las condiciones ambientales favorables a la evaporación y la velocidad de descenso del nivel, cumpliendo el objetivo del Challenge #1 para la región Sabana Centro (Cundinamarca).
2. La **lógica de fusión de datos** propuesta (déficit de nivel 50 % + índice evaporativo 30 % + tasa de descenso 20 %, complementada con reglas de seguridad independientes) demostró, en los ocho casos de prueba de la Sección 5, ser capaz de generar alertas coherentes ante escenarios muy distintos, sin que ninguna variable individualmente crítica quedara enmascarada por el promedio general.
3. Se cumplió la restricción central del reto — **notificación in situ sin redes de comunicación** — mediante actuación 100 % local (pantalla OLED, LEDs semafóricos y buzzer), con toda la inteligencia de decisión ejecutándose embebida en el ESP32.
4. El uso de **Wokwi y chips personalizados en C** permitió validar de forma rigurosa la arquitectura completa (sensores → fusión → actuación) antes de invertir en hardware físico, reduciendo el riesgo de iteración del proyecto dentro del tiempo académico disponible.
5. El sistema resultante es **replicable y de bajo costo**, calibrable a distintos reservorios mediante solo dos parámetros, lo que lo hace viable como herramienta comunitaria complementaria a las redes institucionales de monitoreo hidrometeorológico de la CAR y el IDEAM.

## 7.2 Retos presentados durante el desarrollo del proyecto

- **Modelado de sensores no disponibles físicamente en la etapa de diseño:** al no contar aún con el hardware real (INA219, BME280, panel solar), fue necesario desarrollar *custom chips* de Wokwi en C que emularan fielmente el comportamiento eléctrico esperado de cada sensor (p. ej., la relación irradiancia → voltaje → corriente → registro I²C del INA219), lo cual exigió comprender a fondo el protocolo I²C y el mapa de registros de cada dispositivo real.
- **Escala de tiempo de los fenómenos hídricos:** el descenso de nivel y la evaporación ocurren en horas, mientras que una sesión de simulación dura minutos. Resolverlo exigió introducir una escala de tiempo acelerada configurable (`INTERVALO_TASA_MS`), documentando claramente la diferencia entre el comportamiento en simulación y en un despliegue real.
- **Evitar que el promedio ponderado "esconda" un riesgo real:** un primer diseño basado únicamente en el promedio ponderado de las tres señales podía, en teoría, dejar pasar un caso extremo en una sola variable (p. ej., nivel casi vacío pero buen entorno) sin activar la alerta crítica. Esto llevó a incorporar explícitamente las reglas de seguridad independientes descritas en la Sección 3.2.6.
- **División de voltaje para el pin ECHO de 5 V:** el HC-SR04 entrega su señal ECHO a 5 V, mientras que los GPIO del ESP32 están especificados para 3.3 V; se diseñó un divisor resistivo (1 kΩ/2 kΩ) para proteger el microcontrolador.

## 7.3 Trabajo futuro

- **Migración a hardware físico real:** ensamblar el prototipo con componentes físicos (ESP32 DevKit, BME280, HC-SR04 u OKY3261, mini panel solar + INA219, OLED SSD1306, LEDs, buzzer) siguiendo el esquemático de la Sección 3.4, y repetir el protocolo de pruebas de la Sección 5 en campo.
- **Calibración de campo:** determinar experimentalmente `DISTANCIA_LLENO` y `DISTANCIA_VACIO` para un reservorio real específico de Sabana Centro, en lugar de los valores de maqueta (3 cm / 30 cm).
- **Protección ambiental (IP):** diseñar una carcasa con protección IP54 o superior para operación exterior prolongada, considerando exposición a lluvia, humedad y radiación solar directa.
- **Cobertura de pruebas ampliada:** ejecutar los casos de borde y de recuperación de estado identificados como pendientes en la autoevaluación (Sección 6.3), y realizar una prueba de operación continua de larga duración (*soak test*).
- **Registro histórico local:** incorporar almacenamiento local (tarjeta microSD) para mantener un historial de mediciones y alertas sin depender de conectividad, útil para análisis posterior por parte de la comunidad o autoridades.
- **Panel solar de mayor potencia y gestión de energía:** dimensionar la superficie del panel solar real y validar la autonomía energética efectiva del sistema con la cadena batería–TP4056–MT3608 descrita en la Sección 3.5.
- **Validación estadística de umbrales:** ajustar los umbrales de alerta (Sección 3.2.6) con datos históricos reales de la región, en vez de los valores iniciales de diseño propuestos.

## 7.4 Referencias

Referencias del contexto del reto (tomadas del enunciado oficial del Challenge #1):

[1] Ministerio de Ambiente y Desarrollo Sostenible, "Gobierno confirma inicio del fenómeno de El Niño y alerta sobre su alcance," Minambiente, Bogotá, Colombia, jun. 2026. [En línea]. Disponible: https://www.minambiente.gov.co/gobierno-confirma-inicio-del-fenomeno-de-el-nino-y-alerta-sobre-su-alcance/

[2] Caracol Radio, "Fenómeno del Niño: los municipios en Cundinamarca con mayor riesgo de desabastecimiento de agua," Caracol Radio Bogotá, Sección Nacional, jun. 16, 2026. [En línea]. Disponible: https://caracol.com.co/2026/06/16/fenomeno-del-nino-los-municipios-en-cundinamarca-con-mayor-riesgo-de-desabastecimiento-de-agua/

[3] Infobae, "Fenómeno de El Niño en Colombia: estos son los 16 escenarios de riesgo que podría vivir Bogotá," Infobae Colombia, Sección Medio Ambiente, jul. 8, 2026. [En línea]. Disponible: https://www.infobae.com/colombia/2026/07/08/fenomeno-de-el-nino-en-colombia-estos-son-los-16-escenarios-de-riesgo-que-podria-vivir-bogota/

[4] Gobernación de Cundinamarca, "Plan de Contingencia para el Fenómeno de El Niño," Unidad Administrativa Especial para la Gestión del Riesgo de Desastres (UAEGRD), Bogotá, Colombia, Inf. Técnico, 2026. [En línea]. Disponible: https://www.cundinamarca.gov.co/wcm/connect/107cf680-7a33-47d6-8f65-0d534e1de1e2/PLAN+DE+CONTIGENCIA+FEN%C3%93MENO+EL+NI%C3%91O.pdf


---
[⬅ Anterior: Autoevaluación del protocolo de pruebas](06-Autoevaluacion-Pruebas.md) · [⬆ Índice](00-Home.md) · [Siguiente: Uso de Inteligencia Artificial ➡](08-Uso-de-IA.md)
