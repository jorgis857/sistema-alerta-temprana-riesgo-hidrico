[⬅ Volver al índice](00-Home.md)

# 11. Checklist de cumplimiento frente a la rúbrica oficial

Esta página mapea explícitamente cada indicador de la rúbrica del curso (`Rubricas_EntregaCHx_IoT_20262v1.xlsx`, hoja `Team_1`) contra el contenido de esta Wiki, para que el equipo y el docente puedan verificar rápidamente la cobertura. **✅ = cubierto en esta documentación · ⚠️ = requiere una acción del equipo antes de entregar** (grabar, ejecutar, publicar, o completar un dato real).

## Competencia 1 — Diseño Ingenieril (60%)

| Indicador de nivel "Bueno" (H) exige... | Estado | Dónde |
|---|---|---|
| Criterios de diseño establecidos | ✅ | [Sección 3.1](03-Desarrollo-Modular.md#31-criterios-de-diseño-establecidos) |
| Diagrama de bloques de la arquitectura (hardware y software) | ✅ | [Sección 2.2](02-Solucion-Propuesta.md#22-arquitectura-propuesta) |
| Diagrama(s) UML y documentación del código de cada módulo software | ✅ | [Sección 3.3](03-Desarrollo-Modular.md#33-diagramas-uml) + `firmware/sketch.ino` documentado |
| Esquemáticos de interconexión hardware (prototipo funcional) | ✅ | [Sección 3.4](03-Desarrollo-Modular.md#34-esquemático-de-hardware) + `hardware/schematics/` |
| Viabilidad de la propuesta de diseño | ✅ | [Sección 2.1](02-Solucion-Propuesta.md#21-restricciones-de-diseño-identificadas) (restricciones) + [Sección 4.3](04-Modelo-de-Negocio.md#43-viabilidad-y-escalabilidad) |
| Modelo de negocio | ✅ | [Sección 4](04-Modelo-de-Negocio.md) |
| **Prototipo funcional (hardware) que conecte correctamente con la lógica software, con transiciones de todas las etapas** | ⚠️ | El firmware y los *custom chips* fueron entregados por el equipo y están incluidos íntegros (lógica sin alterar, verificada línea por línea). Los 8 casos de la [Sección 5.2](05-Configuracion-Experimental-Resultados.md#52-casos-de-prueba-y-resultados) fueron **recalculados matemáticamente de forma independiente** replicando las fórmulas del firmware, pero **no fueron ejecutados por mí dentro del simulador Wokwi real**. **El equipo debe correr estos 8 casos en Wokwi antes de sustentar**, para confirmar visualmente que la OLED/LEDs/buzzer se comportan como predice la tabla, y anexar capturas de pantalla si es posible. |

## Competencia 2 — Comunicación (30%)

| Indicador | Estado | Dónde |
|---|---|---|
| Documento escrito en formato Wiki, coherente y claro, que considera todos los requerimientos | ✅ | Las 11 páginas de esta Wiki |
| Tablas y figuras estéticamente armónicas, uso racional | ✅ | Tablas + diagramas Mermaid en cada sección |
| Citas y referencias en formato IEEE | ✅ | [Sección 7.4](07-Conclusiones-Trabajo-Futuro.md#74-referencias) |
| Referencias en su mayoría de los últimos 5 años | ⚠️ | Las 4 referencias del contexto del reto ([1]-[4]) son de 2026. Dos referencias técnicas de fabricante ([7] INA219, 2015; [10] FAO-56, 1998) son más antiguas por tratarse de estándares técnicos de referencia, no de literatura reciente — es una práctica común y defendible, pero si el jurado lo exige estrictamente, se recomienda agregar 1-2 fuentes académicas recientes (2021-2026) sobre IoT para monitoreo hídrico. |
| Expresión en una segunda lengua (inglés) | ✅ | [Sección 10 — Executive Summary (English)](10-English-Executive-Summary.md) |
| Documento sin errores ortográficos, fácil de leer, narrativa interesante | ⚠️ | Redactado con cuidado, pero se recomienda una relectura final por parte del equipo antes de publicar |
| **Habilidades de comunicación oral, dominio del auditorio, respuestas al jurado (sustentación de 18 min)** | ⚠️ | Fuera del alcance de este documento — depende de la práctica oral del equipo el día de la sustentación (24 u 27 de agosto). Se recomienda ensayar el pitch de 3 minutos usando el [guion de video](../video/GUION_VIDEO.md) como base. |

## Competencia 3 — Autoaprendizaje (10%)

| Indicador | Estado | Dónde |
|---|---|---|
| Apropiar nuevo conocimiento de IoT para resolver el problema | ✅ | [Sección 1.3](01-Resumen-Motivacion.md#13-justificación) (pertinencia IoT) + [Sección 7.2](07-Conclusiones-Trabajo-Futuro.md#72-retos-presentados-durante-el-desarrollo-del-proyecto) (retos técnicos aprendidos: I2C, custom chips, VPD, etc.) |
| Contribución al rol asignado, con acta de reunión y evaluación | ⚠️ | Plantilla completa en [Sección 9.3](09-Equipo-Roles.md#93-acta-de-reunión-y-evaluación-del-equipo) y autoevaluación en [Sección 9.4](09-Equipo-Roles.md#94-autoevaluación-de-la-contribución-individual). **El equipo debe completar la fecha real de la reunión, la modalidad y confirmar/ajustar los niveles de autoevaluación**, ya que estos datos no pueden generarse sin la reunión real del equipo. |

## Requisitos generales del enunciado (no puntuados por rúbrica pero exigidos para poder calificar)

| Requisito | Estado |
|---|---|
| Wiki alojada en GitHub/GitLab/Bitbucket | ⚠️ Contenido listo en `/wiki`; falta que el equipo publique el repositorio real (ver `COMO_PUBLICAR_EN_GITHUB.md`) |
| Compartir la wiki a `@afbeltranp` | ⚠️ Acción manual del equipo tras publicar |
| Sección de uso de IA | ✅ [Sección 8](08-Uso-de-IA.md) |
| Video demostrativo (≤5 min, todos con cámara) | ⚠️ Solo se entrega el guion (`video/GUION_VIDEO.md`); grabación pendiente del equipo |
| Subir enlace de repo + video + .zip a MS Teams | ⚠️ Acción manual del equipo |

## Resumen

De los **contenidos documentales** exigidos por el enunciado y la rúbrica (secciones 1 a 6, anexos, uso de IA, roles), **todo está redactado y completo**. Lo que queda pendiente y **no puede generarse sin la participación directa del equipo** son: (1) ejecutar/confirmar los casos de prueba dentro del simulador Wokwi real, (2) completar la fecha real y el resultado real del acta de reunión/autoevaluación, (3) grabar el video, y (4) publicar el repositorio y compartirlo con el docente.

---
[⬅ Anterior: Executive Summary (English)](10-English-Executive-Summary.md) · [⬆ Índice](00-Home.md)
