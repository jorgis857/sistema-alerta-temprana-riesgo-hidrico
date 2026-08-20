[⬅ Volver al índice](00-Home.md)

# 6. Autoevaluación del protocolo de pruebas

Esta sección evalúa críticamente el propio protocolo de pruebas descrito en la [Sección 5](05-Configuracion-Experimental-Resultados.md), identificando sus fortalezas y limitaciones.

## 6.1 Checklist de cobertura del protocolo

| Criterio | ¿Se cumple? | Evidencia / observación |
|---|---|---|
| Se prueban los tres estados de alerta (NORMAL, PRECAUCIÓN, CRÍTICO) | ✅ Sí | Casos C1 (NORMAL), C2–C4 (PRECAUCIÓN), C5–C8 (CRÍTICO) |
| Se prueba cada una de las 4 condiciones que disparan el estado CRÍTICO de forma aislada | ✅ Sí | C5 (nivel), C6 (evaporación), C7 (tasa de descenso), C8 (riesgo combinado) |
| Se prueba cada una de las 4 condiciones que disparan PRECAUCIÓN | ⚠️ Parcial | Se cubren nivel (C3) y evaporación (C4) y riesgo combinado (C2); no se aisló un caso "puro" de PRECAUCIÓN disparado únicamente por tasa de descenso ≥ 2 pp/h |
| Se valida la coherencia entre el modelo matemático teórico y el cálculo real del firmware | ✅ Sí | Recalculo independiente en Python de VPD, radiación, índice evaporativo y riesgo para los 8 casos (Sección 5.2) |
| Se valida la cadena completa de hardware simulado (panel solar → INA219 → ESP32) | ✅ Sí | Verificación de que la radiación recuperada coincide con la irradiancia configurada (Sección 5.3, punto 2) |
| Se prueban condiciones límite (*edge cases*) exactamente en los umbrales (35 %, 40 %, 60 %, 70 %, 85 %, 15 %, 2 pp/h, 5 pp/h) | ❌ No realizado | El protocolo actual prueba valores claramente dentro de cada rango, no exactamente en el borde del umbral; se recomienda como trabajo futuro |
| Se prueba la recuperación del sistema (de CRÍTICO a PRECAUCIÓN a NORMAL) | ❌ No realizado en esta iteración | Solo se validaron transiciones hacia estados de mayor riesgo; falta un caso de "mejora de condiciones" |
| Se valida el comportamiento del OLED en sus dos vistas (mediciones / análisis) | ✅ Sí (validación visual en Wokwi) | Alternancia cada 3 s verificada por inspección directa del simulador |
| Se valida la actuación física (LEDs y buzzer) para cada estado | ✅ Sí (validación visual/sonora en Wokwi) | Verificado en el simulador; polaridad activa en bajo confirmada contra el código |
| Se documenta el procedimiento de forma reproducible (parámetros exactos por caso) | ✅ Sí | Tabla de la Sección 5.2 con valores exactos de entrada por caso |

## 6.2 Fortalezas del protocolo

- Uso de un **recalculo matemático independiente** (fuera del firmware) para verificar cada resultado, en lugar de simplemente "creer" lo que muestra la pantalla — reduce el riesgo de validar un error sistemático de la propia implementación con sus propios resultados.
- Cobertura de **las cuatro rutas de disparo del estado CRÍTICO**, que es precisamente el mecanismo de diseño más crítico del sistema (reglas de seguridad).
- Los *custom chips* de Wokwi permiten variar cada entrada física de forma **aislada y determinística**, algo que sería mucho más difícil de controlar con hardware real en esta etapa del proyecto.

## 6.3 Limitaciones identificadas y acciones correctivas propuestas

| Limitación | Riesgo asociado | Acción correctiva |
|---|---|---|
| No se probaron condiciones exactamente en el borde de los umbrales | Posible comportamiento no determinístico por redondeo/truncamiento en el borde (p. ej., riesgo = 34.99 % vs. 35.00 %) | Añadir casos de prueba unitarios con valores exactos en el límite antes de pasar a hardware físico |
| No se validó la transición de recuperación (CRÍTICO → NORMAL) | El diagrama de estados (Sección 3.3.1) lo contempla, pero no fue ejercitado en pruebas | Diseñar un caso de prueba dinámico que mejore progresivamente las condiciones y confirme el regreso a NORMAL |
| Todas las pruebas se hicieron en simulación, no en hardware físico | Persisten riesgos no modelados en la simulación: ruido eléctrico, temperatura de la placa, calibración real del HC-SR04 en agua en movimiento, interferencia entre el bus I²C y el buzzer | Documentado explícitamente como trabajo futuro (Sección 7) antes de un despliegue en campo |
| No se realizaron pruebas de estrés de tiempo prolongado (horas de operación continua) | Posibles fugas de memoria o *drift* de la variable `nivelAnterior` no se descartan completamente | Ejecutar una prueba de *soak test* de varias horas simuladas una vez se cuente con hardware físico |

## 6.4 Conclusión de la autoevaluación

El protocolo de pruebas aplicado **cubre satisfactoriamente el objetivo central del reto** (validar que la lógica de fusión combina correctamente múltiples señales para generar alertas coherentes), pero **no agota** la validación necesaria para un despliegue en campo real. Se considera un protocolo adecuado para la etapa de **prototipado y simulación**, con limitaciones explícitamente reconocidas que se trasladan como recomendaciones de trabajo futuro.

---
[⬅ Anterior: Configuración experimental y resultados](05-Configuracion-Experimental-Resultados.md) · [⬆ Índice](00-Home.md) · [Siguiente: Conclusiones y trabajo futuro ➡](07-Conclusiones-Trabajo-Futuro.md)
