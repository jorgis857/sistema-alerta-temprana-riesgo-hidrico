[⬅ Volver al índice](00-Home.md)

# 12. Mejoras respecto al Challenge #1

Esta sección documenta cómo se atendieron en el Challenge #2 las deficiencias y la retroalimentación recibidas en el Challenge #1.

## 12.1 Retroalimentación del docente

Las observaciones principales fueron:

> "Falta justificar con una fuente externa los pesos (50/30/20) y los umbrales (15/40 % de nivel, 35/70 de riesgo, 60/85 de evaporación, 33/68 de tasa)… ningún valor se ancla a literatura o normativa."

> "Falta justificar el modelo de evaporación potencial. El modelo actual está mal"

También se pidieron más referencias de los últimos 5 años y los datasheets de los componentes.

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
| Referencias | Sin lista de referencias en la Wiki del repositorio | 31 referencias en formato IEEE, incluidas publicaciones de 2021 a 2024 y los datasheets | [7.5](07-Conclusiones-Trabajo-Futuro.md) |
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

- **Consumo y autonomía:** el Challenge #1 lo dejó pendiente y en el Challenge #2 sigue sin cerrarse; además el Wi-Fi sin ahorro de energía aumenta el consumo.
- **Umbrales de evaporación con datos locales:** el método está citado, pero no se aplicó con datos del IDEAM.
- **Calibración de la irradiancia con un instrumento de referencia.**
- **Validación en un embalse real** y pruebas prolongadas.

---

[⬅ Anterior: Conectividad IoT](11-Conectividad-IoT.md) · [⬆ Índice](00-Home.md)
