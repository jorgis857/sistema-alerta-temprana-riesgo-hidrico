[⬅ Volver al índice](00-Home.md)

# 12. Mejoras respecto al Challenge #1

Esta sección documenta cómo se atendieron en el Challenge #2 las deficiencias y la retroalimentación recibidas en el Challenge #1.

## 12.1 Retroalimentación del docente

La observación principal fue:

> "Falta justificar con una fuente externa los pesos (50/30/20) y los umbrales (15/40 % de nivel, 35/70 de riesgo, 60/85 de evaporación, 33/68 de tasa)… ningún valor se ancla a literatura o normativa."

También se pidieron más referencias de los últimos 5 años y los datasheets de los componentes.

La revisión del Challenge #1 (registrada en la hoja de trabajo del equipo) señaló además:

| Deficiencia / retroalimentación | Acción de mejora | Evidencia |
|---|---|---|
| **Contradicción:** la Wiki decía "100 % en simulación" y el video mostraba una maqueta física | Narrativa única: simulación (Ch. #1, etapa 1) → maqueta física (Ch. #1, etapa 2) → producto en carcasa (Ch. #2). Se sincronizó la carpeta `/wiki` del repositorio con la Wiki de GitHub | Secciones 1.4, 2.16 y 5.1; la frase "100 % en simulación" ya no aparece |
| **Wiki vs. código:** OLED vs. LCD 16×2, pp/h vs. pp/min, portada "Equipo 1" | La pantalla es la LCD 16×2 en todo el texto (la OLED solo se menciona como componente de la simulación); la tasa se expresa en pp/min (la tabla en pp/h de la Sección 5.4 se conserva como evidencia histórica, con nota); la portada dice "Equipo 2" | Secciones 0, 3.10, 5.4 y 9.1; trazabilidad Wiki ↔ código en la [Sección 3.20](03-Desarrollo-Modular.md) |
| **Referencias solo del enunciado** | Lista IEEE con datasheets, artículos de los últimos 5 años y normativa, citada en el texto | [Sección 7.5](07-Conclusiones-Trabajo-Futuro.md) |
| **IA sin prompts ni validación** | Sección de IA con las herramientas, el uso en cada etapa (incluido el desarrollo del firmware con Claude Code), los mecanismos de validación y el porcentaje de la Wiki | [Sección 8](08-Uso-de-IA.md) |
| **Restricciones regulatorias y temporales incompletas** | Tabla de restricciones con RETIE, RAS, IEC 60529, Ley 1523, Ley 1581, uso del espectro, plazos y muestreo | [Sección 2.2](02-Solucion-Propuesta.md) |
| **Faltaban pruebas de borde y de recuperación** | Matriz de 12 escenarios con valores exactos sobre los umbrales y la recuperación crítico → normal | [Sección 5.7.4](05-Configuracion-Experimental-Resultados.md) |
| **Una sola acta** | Actas semanales | ⟨completar: enlace a las actas⟩ |
| **Sustentación oral (2/4): el video hablaba del prototipo en futuro** | Video del Ch. #2 centrado en el prototipo real funcionando; pitch para *stakeholders* ensayado y banco de preguntas probables | [Video del Challenge #2](https://youtu.be/H0U9AYJEdTg) |

| Elemento | Challenge #1 | Challenge #2 | Dónde |
|---|---|---|---|
| Pesos del riesgo | 50/30/20, criterio del equipo | **54/30/16**, vector del **AHP** de Saaty [18] con CR = 0.008, el método usado en índices compuestos de sequía [19] | [3.2.5](03-Desarrollo-Modular.md) |
| Umbrales de nivel | 40 / 15 %, criterio operativo | **50 / 15 %**, fases de los **Planes Especiales de Sequía** de España [20], [21]; caso Chingaza 2024 [22] | [3.2.7](03-Desarrollo-Modular.md) |
| Umbrales de riesgo | 35 / 70, criterio operativo | **36.2 / 69.2**, derivados de los umbrales de nivel con la fórmula del riesgo | [3.2.7](03-Desarrollo-Modular.md) |
| Umbrales de evaporación | 60 / 85, sin respaldo | 60 / 85 **declarados como supuesto**, con el 100 % anclado a la física (ET de un día despejado) y el método para cerrarlos citado (percentiles del US Drought Monitor [23]) | [3.2.7](03-Desarrollo-Modular.md) |
| Umbrales de tasa | 33 / 68 pp/min, calibración experimental | Se mantienen; ahora editables desde el tablero para recalibrarlos con el tubo real | [3.17](03-Desarrollo-Modular.md) |
| Índice evaporativo | 50 % irradiancia + 50 % VPD, sin respaldo | **Priestley-Taylor** [5] con **FAO-56** [6] + 30 % de VPD justificado con Jansen et al. [11]; cada constante con su fuente | [3.2.3](03-Desarrollo-Modular.md) |
| Efecto de la altitud | Factor fijo ≈ 1.10 sobre la irradiancia | La presión medida entra directamente en γ y en Δ/(Δ+γ) | [3.2.3](03-Desarrollo-Modular.md) |
| Gestión de alarmas | Banda muerta y confirmación sin cita | Citadas a ANSI/ISA-18.2 [16] y EEMUA 191 [17] | [3.2.8](03-Desarrollo-Modular.md) |
| Referencias | Sin lista de referencias en la Wiki del repositorio | 37 referencias en formato IEEE, incluidas publicaciones de 2021 a 2024, los datasheets y la normativa colombiana aplicable | [7.5](07-Conclusiones-Trabajo-Futuro.md) |
| Supuestos | Implícitos | Declarados uno por uno (G ≈ 0, Rnl sobre agua, Ra fijo, modo demo, umbrales de evaporación) | [3.2.3](03-Desarrollo-Modular.md), [6.3](06-Autoevaluacion-Pruebas.md) |

## 12.2 Deficiencias técnicas detectadas y corregidas

| Deficiencia del Challenge #1 | Corrección en el Challenge #2 |
|---|---|
| Prototipo sobre una maqueta de laboratorio | Equipo en carcasa, con el sensor de nivel en un tubo de PVC, alimentación por pilas e interruptor ([3.19](03-Desarrollo-Modular.md)) |
| Notificación solo en sitio | Tablero de control web en la WLAN de la zona, con valor actual, histórico, avisos y silencio de la alarma ([3.16](03-Desarrollo-Modular.md)) |
| Toda la ejecución en un único `loop()` | Medición en su propia tarea de FreeRTOS, alarmas en otra y servidor en `loop()`, con mutex ([3.14](03-Desarrollo-Modular.md)) |
| Calibrar exigía modificar el código y reprogramar | Calibración desde el tablero, guardada en la flash ([3.17](03-Desarrollo-Modular.md)) |
| El cero del piranómetro se medía al arrancar pero el firmware no lo guardaba (seguía en 0) | Se guarda y se resta, solo si es menor de 1 mA, para no tomar la luz como cero ([5.5.1](05-Configuracion-Experimental-Resultados.md)) |
| Distancia de "lleno" (3 cm) dentro de la zona ciega del sensor | La calibración desde el tablero indica dejar "lleno" a 5 cm o más del sensor |
| Botón físico de silencio | Silencio desde el tablero, con evento registrado; los LEDs siguen mostrando el estado |
| Sin diagnóstico al arrancar del modelo de evaporación | Autotest con 7 casos de referencia en cada arranque ([3.18](03-Desarrollo-Modular.md)) |

## 12.3 Lo que sigue pendiente

Para no presentar como resuelto lo que no lo está:

- **Consumo y autonomía:** el Challenge #1 lo dejó pendiente y en el Challenge #2 sigue sin cerrarse; además el Wi-Fi sin ahorro de energía aumenta el consumo ⟨actualizar si se midió⟩.
- **Umbrales de evaporación con datos locales:** el método está citado, pero no se aplicó con datos del IDEAM.
- **Calibración de la irradiancia con un instrumento de referencia** ⟨actualizar si se hizo⟩.
- **Validación en un embalse real** y pruebas prolongadas.

## 12.4 Plan de trabajo vs. lo implementado

La hoja de trabajo del equipo fijó un plan al inicio del Challenge #2. Esta tabla registra en qué se apartó la implementación final y por qué.

| Elemento | Plan (hoja de trabajo) | Implementado | Motivo |
|---|---|---|---|
| Medición concurrente | *Timer* de hardware (ISR) que libera un semáforo + tarea en el núcleo 0 | Tarea de FreeRTOS en el núcleo 0 con periodo fijo (`vTaskDelayUntil`), sin ISR | Cumple la restricción ("hilo distinto al principal") con menos código; no hace falta ISR porque no hay sensores por pulsos |
| Caudal | Caudalímetro YF-S201 contado en una ISR, en la fusión | No implementado ⟨confirmar⟩ | ⟨completar⟩ |
| Sensor de nivel | JSN-SR04T impermeable | HC-SR04 dentro del tubo de PVC ⟨confirmar⟩ | El tubo protege el sensor y estabiliza la superficie |
| Velocidad del sonido | Compensada con la temperatura del BME280 | Constante (343 m/s) | Trabajo futuro |
| Servidor web | ESPAsyncWebServer, páginas en LittleFS, actualización por SSE o WebSocket | `WebServer` síncrono en `loop()`, páginas embebidas en el firmware, consulta periódica (2 s / 5 s) con cancelación por tiempo | Sin dependencias externas; las alarmas van en su propia tarea, así que el servidor nunca las bloquea |
| Gráficas | Librería de gráficas local | Gráficas dibujadas con `<canvas>` | Sin librerías ni Internet |
| Acceso | WPA2 + lista blanca de IP (reservas DHCP) + login; roles operador y administrador | WPA2 + misma subred + login con sesión; un solo usuario; registro de inicios de sesión e intentos fallidos | El hotspot de celular no permite reservas DHCP; los roles quedan como trabajo futuro |
| Histórico | 24 h (1 punto/min) en RAM con volcado a LittleFS y hora por NTP | 10 min en RAM (1 punto cada 2 s), tiempo relativo al arranque | Suficiente para la demostración; la persistencia queda como trabajo futuro |
| Calibración | Archivo de configuración en LittleFS | Flash NVS (`Preferences`), editable desde el tablero | Más simple y robusto para pocos parámetros |
| Pesos del riesgo | 50/30/20 justificados con fuente | 54/30/16 del AHP | El método citado da 54/30/16 |
| Recuperación de estado | Histéresis para bajar | Confirmación asimétrica (3 ciclos para bajar) y escalera de un peldaño | Evita la oscilación con el mismo efecto |
| LCD | Pantallas rotativas con botón | Rotación automática de 7 páginas, sin botón | Una entrada física menos en un equipo cerrado |
| BME280 | Brazo lateral con protector de radiación | Techo con rejillas sobre la carcasa | Integrado en la impresión 3D |
| Carcasa | Caja IP65 comercial o impresa en PETG/ASA, PCB perforada, prensaestopas | Carcasa impresa en PETG, electrónica en mini protoboard | ⟨completar⟩; el grado IP no se ensayó |
| Alimentación | Red 5 V con respaldo 18650 (TP4056 + MT3608) y panel solar | Portapilas 4×AA con interruptor ⟨confirmar⟩ | ⟨completar⟩ |
| Medición de consumo | INA219 adicional en la entrada | ⟨completar⟩ | ⟨completar⟩ |
| Seguimiento solar | No en el prototipo (panel fijo horizontal como sensor) | No implementado, como se decidió | El panel es el sensor de radiación global horizontal |

---

[⬅ Anterior: Conectividad IoT](11-Conectividad-IoT.md) · [⬆ Índice](00-Home.md)
