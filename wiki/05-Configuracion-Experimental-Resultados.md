[⬅ Volver al índice](00-Home.md)

# 5. Configuración experimental, resultados y análisis

## 5.1 Configuración experimental

La validación se realizó **100 % en simulación**, usando el simulador **Wokwi** con el proyecto disponible en <https://wokwi.com/projects/472250559337371649>. Se emplearon tres *custom chips* escritos en C (`wokwi-api.h`) que emulan de forma funcional el comportamiento físico real de los sensores:

| Chip personalizado | Emula | Entradas manipulables (sliders) | Salida hacia el ESP32 |
|---|---|---|---|
| `bme280custom` | BME280 | Temperatura (−10 a 50 °C), Humedad (0–100 %), Presión (800–1100 hPa) | Registros I²C en dirección `0x76`, compatibles con el mapa de registros real del BME280 (`0xF7`–`0xFE`, chip ID `0xD0`) |
| `solar-panel` | Mini panel solar | Irradiancia (0–1200 W/m²) | Salida analógica DAC 0–5 V proporcional a la irradiancia |
| `ina219custom` | INA219 | (recibe el voltaje del panel solar por sus pines `VIN+`/`VIN-`) | Corriente simulada (0–120 mA), leída por I²C en dirección `0x40`, registro `0x04` |

El sensor **HC-SR04** se simuló con el componente nativo de Wokwi (`wokwi-hc-sr04`), configurando su atributo `distance` para representar distintos niveles de agua en el reservorio (rango calibrado: 3 cm = 100 % lleno, 30 cm = 0 % lleno).

**Procedimiento de prueba:** para cada caso, se ajustaron los controles de los tres chips personalizados y la distancia del HC-SR04 a los valores objetivo, se esperó a la estabilización de las lecturas (varios ciclos de 500 ms) y se registraron los valores mostrados por el **Monitor Serial** (que imprime todas las variables intermedias) y por la **pantalla OLED** (visualización final para el usuario).

## 5.2 Casos de prueba y resultados

Se diseñaron 8 casos de prueba que cubren los tres estados del sistema y las distintas reglas que pueden dispararlos (nivel, índice evaporativo, tasa de descenso o riesgo combinado). Los valores de VPD, radiación, índice evaporativo y riesgo fueron **recalculados de forma independiente** (fuera del firmware, replicando exactamente sus fórmulas) para verificar la coherencia entre el modelo teórico y lo que efectivamente calcula el ESP32.

| Caso | Distancia | Temp. | Humedad | Irradiancia | Nivel | VPD | Radiación calc. | Índice evap. | Tasa descenso | Riesgo | Estado esperado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 — Escenario favorable | 4.0 cm | 18.0 °C | 70 % | 300 W/m² | 96.3 % | 0.62 kPa | 300 W/m² | 25.3 % | 0.0 pp/h | 9.4 % | 🟢 **NORMAL** |
| C2 — Precaución por riesgo combinado | 15.0 cm | 22.0 °C | 55 % | 600 W/m² | 55.6 % | 1.19 kPa | 600 W/m² | 49.8 % | 1.0 pp/h | 41.2 % | 🟡 **PRECAUCIÓN** |
| C3 — Precaución por nivel bajo | 20.0 cm | 24.0 °C | 45 % | 500 W/m² | 37.0 % | 1.64 kPa | 500 W/m² | 52.4 % | 1.5 pp/h | 53.2 % | 🟡 **PRECAUCIÓN** |
| C4 — Precaución por evaporación alta | 5.0 cm | 25.0 °C | 15 % | 650 W/m² | 92.6 % | 2.69 kPa | 650 W/m² | 77.4 % | 0.5 pp/h | 28.9 % | 🟡 **PRECAUCIÓN** |
| C5 — Crítico por nivel muy bajo | 27.0 cm | 20.0 °C | 60 % | 400 W/m² | 11.1 % | 0.94 kPa | 400 W/m² | 35.6 % | 0.5 pp/h | 57.1 % | 🔴 **CRÍTICO** |
| C6 — Crítico por evaporación extrema | 12.0 cm | 33.0 °C | 15 % | 1150 W/m² | 66.7 % | 4.28 kPa | 1150 W/m² | 100.0 % | 1.0 pp/h | 50.7 % | 🔴 **CRÍTICO** |
| C7 — Crítico por tasa de descenso | 14.0 cm | 21.0 °C | 60 % | 350 W/m² | 59.3 % | 0.99 kPa | 350 W/m² | 34.1 % | 6.0 pp/h | 50.6 % | 🔴 **CRÍTICO** |
| C8 — Crítico por riesgo combinado ≥ 70 % | 24.0 cm | 29.0 °C | 25 % | 900 W/m² | 22.2 % | 3.00 kPa | 900 W/m² | 95.0 % | 3.0 pp/h | 79.4 % | 🔴 **CRÍTICO** |

> Nota metodológica: la "tasa de descenso" mostrada es el valor objetivo configurado para cada caso — en la simulación se logra dejando correr el sistema el tiempo necesario (múltiplos de `INTERVALO_TASA_MS` = 10 s) entre una medición de nivel y la siguiente, reduciendo progresivamente la distancia del HC-SR04 para forzar la caída de nivel deseada.

## 5.3 Análisis de resultados

1. **Cobertura de las tres rutas de alerta.** Los ocho casos confirman que el sistema puede llegar a `CRÍTICO` por **cuatro caminos distintos**: nivel bajo (C5), evaporación extrema (C6), tasa de descenso alta (C7) y riesgo combinado (C8) — validando el objetivo de diseño de que "ninguna variable crítica quede escondida por el promedio de las demás" (Sección 3.1).
2. **Consistencia del modelo de radiación solar simulado.** Al recalcular la cadena `irradiancia → voltaje DAC del panel → corriente INA219 → radiación estimada por el ESP32`, se verificó que el valor de radiación recuperado por el firmware coincide (dentro del error de cuantización de los registros de 16 bits) con la irradiancia configurada en el slider del panel solar, confirmando que el *custom chip* y el firmware están correctamente acoplados.
3. **Sensibilidad del índice evaporativo.** En el caso C4 (humedad relativa muy baja, 15 %) el VPD alcanza 2.69 kPa (89 % del valor de referencia de 3 kPa) incluso con una irradiancia moderada (650 W/m²), mostrando que el modelo captura adecuadamente el efecto de la humedad relativa —y no solo de la radiación— sobre el riesgo de evaporación, tal como exige la pregunta guía del reto ("radiación solar, temperatura, humedad y presión atmosférica").
4. **El promedio ponderado por sí solo no basta.** En C6 y C7, el riesgo ponderado (50.7 % y 50.6 % respectivamente) está **por debajo** del umbral de 70 % que activaría `CRÍTICO` únicamente por la fórmula de fusión; sin embargo, el sistema sí escala correctamente a `CRÍTICO` gracias a las reglas de seguridad independientes (índice evaporativo ≥ 85 % y tasa de descenso ≥ 5 pp/h). Esto valida empíricamente la necesidad de dichas reglas.
5. **Presión atmosférica.** Aunque el BME280 mide y muestra la presión (visualizada en la pantalla OLED y el monitor serial), esta variable **no participa en el cálculo del riesgo**, de forma consistente con el diseño documentado en la Sección 3: en un punto fijo de instalación, sus variaciones aportan poca información adicional para detectar desabastecimiento respecto al nivel, la evaporación potencial y la tendencia de descenso.
6. **Tiempo acelerado de simulación.** El uso de `INTERVALO_TASA_MS = 10000` (10 s = 1 hora simulada) permitió reproducir en minutos comportamientos que en un despliegue real tomarían horas, lo cual fue indispensable para poder demostrar el módulo de tasa de descenso dentro del tiempo de sustentación (18 minutos).

---
[⬅ Anterior: Modelo de negocio](04-Modelo-de-Negocio.md) · [⬆ Índice](00-Home.md) · [Siguiente: Autoevaluación del protocolo de pruebas ➡](06-Autoevaluacion-Pruebas.md)
