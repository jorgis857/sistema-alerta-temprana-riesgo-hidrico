[⬅ Volver al índice](00-Home.md)

# 8. Uso de Inteligencia Artificial

Esta sección se incluye de forma **obligatoria** conforme al enunciado del Challenge #1, que exige declarar el uso de herramientas de Inteligencia Artificial generativa durante el desarrollo del reto y/o la redacción de la Wiki.

## 8.1 Herramienta de IA consultada

**Claude (Anthropic)**, en su modalidad Cowork/Claude Code, fue utilizada como asistente de apoyo técnico y de redacción durante la etapa final de documentación y empaquetado del proyecto.

## 8.2 Alcance del uso de la IA

El diseño conceptual del sistema (arquitectura de sensores, modelo matemático de fusión de datos — VPD, índice evaporativo, tasa de descenso, riesgo hídrico —, umbrales de alerta, esquema de conexión en Wokwi y el firmware base) fue desarrollado previamente por el equipo, incluyendo el documento de diseño propio *"Sistema de Alerta Temprana de Riesgo Hídrico"* y los archivos de simulación (`sketch.ino`, `diagram.json`, *custom chips* en C para BME280, INA219 y panel solar).

Sobre esa base ya construida por el equipo, se usó Claude para:

1. **Estructurar y redactar la Wiki técnica** siguiendo exactamente los siete puntos exigidos en el enunciado del Challenge #1 (resumen, solución propuesta, configuración experimental, autoevaluación, conclusiones, anexos, uso de IA).
2. **Generar diagramas UML y de bloques** (diagrama de estados, de secuencia, de componentes y de bloques hardware/software) en formato Mermaid a partir de la lógica ya implementada en `sketch.ino`.
3. **Verificar de forma independiente los cálculos del modelo** (VPD, índice evaporativo, radiación estimada y riesgo hídrico) para los casos de prueba de la Sección 5, ejecutando el mismo conjunto de fórmulas del firmware en un script de Python separado y comparando resultados.
4. **Redactar un modelo de negocio (Business Model Canvas)** y una tabla de restricciones/estándares de ingeniería, a partir del contexto del problema descrito en el enunciado oficial.

## 8.3 Validación de la veracidad de las respuestas de la IA y su aplicación a la solución

- **Fórmulas y umbrales:** todos los valores numéricos, fórmulas y umbrales presentados en la Wiki (Sección 3.2, 3.2.6) se tomaron **directamente del código fuente** (`firmware/sketch.ino`) y del documento de diseño propio del equipo, no fueron inventados por la IA. La IA se usó para explicarlos y diagramarlos, no para definirlos.
- **Casos de prueba:** los resultados de la Sección 5 (VPD, radiación, índice evaporativo, riesgo, estado) fueron **recalculados de forma independiente en Python**, replicando exactamente las fórmulas del firmware y de los *custom chips*, y comparados con lo que debería mostrar el Monitor Serial/LCD del ESP32 en Wokwi. Este recalculo permitió confirmar que los números presentados en la documentación son matemáticamente consistentes con la implementación real, y no una alucinación de la IA.
- **Diagramas UML y de bloques:** se verificó manualmente que cada diagrama generado (estados, secuencia, componentes) correspondiera exactamente al flujo de funciones definido en `sketch.ino` (`readTemperatureRaw`, `calcularVPD`, `calcularIndiceEvaporativo`, `actualizarTasaDescenso`, `calcularRiesgoHidrico`, `estadoNormal/Precaucion/Critico`), corrigiendo cualquier diagrama que no coincidiera con el código real.
- **Referencias bibliográficas del reto:** las referencias [1]–[4] de la Sección 7.4 se copiaron **textualmente del enunciado oficial** entregado por el docente, no fueron generadas ni alteradas por la IA. Las referencias técnicas adicionales [5]–[10] corresponden a documentación oficial pública de los fabricantes de los componentes (Espressif, Bosch, Texas Instruments, NXP) y de Wokwi, verificable por cualquier miembro del jurado.
- **Contenido no verificable de forma determinística** (p. ej., estimaciones de costos del modelo de negocio en la Sección 4.2) se presenta explícitamente como **referencial y sujeto a validación con cotizaciones reales**, evitando presentar como hecho comprobado algo que la IA solo puede aproximar.


---
[⬅ Anterior: Conclusiones y trabajo futuro](07-Conclusiones-Trabajo-Futuro.md) · [⬆ Índice](00-Home.md) · [Siguiente: Equipo de trabajo ➡](09-Equipo-Roles.md)
