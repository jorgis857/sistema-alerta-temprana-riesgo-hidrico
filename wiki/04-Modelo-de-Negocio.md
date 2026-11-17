[⬅ Volver al índice](00-Home.md)

# 4. Modelo de negocio

Aunque el proyecto nace como un reto académico, se plantea un modelo de negocio orientado a un despliegue real por parte de acueductos veredales, alcaldías municipales y la CAR Cundinamarca, bajo un esquema de **hardware de bajo costo + servicio de instalación/mantenimiento**, sin necesidad de conectividad ni suscripción a la nube (lo cual reduce drásticamente el costo operativo frente a soluciones IoT tradicionales basadas en la nube).

## 4.1 Business Model Canvas

| Bloque | Contenido |
|---|---|
| **Segmentos de clientes** | (1) Juntas administradoras de acueductos veredales de Sabana Centro. (2) Alcaldías municipales y Unidades de Gestión del Riesgo de Desastres (UGRD). (3) Distritos de riego agroindustriales. (4) CAR Cundinamarca (monitoreo distribuido complementario a su red institucional). |
| **Propuesta de valor** | Alerta temprana de riesgo hídrico **in situ**, sin dependencia de redes de comunicación ni de conectividad a Internet; instalación simple, bajo costo (< USD 50 en componentes), calibración replicable en distintos reservorios, y visualización comprensible para personal no técnico. Desde el Challenge #2, además, un **tablero de control web** en la WLAN local de la autoridad (sin nube ni suscripción) con valor actual, histórico, avisos, silencio de la alarma y calibración remota sin abrir el equipo. |
| **Canales** | Instalación directa por parte del equipo/empresa derivada del proyecto; alianzas con la CAR y alcaldías para despliegue en puntos críticos priorizados; difusión mediante juntas de acción comunal. |
| **Relación con el cliente** | Instalación asistida + capacitación inicial a la comunidad + mantenimiento preventivo periódico (limpieza de sensores, recalibración estacional, reemplazo de batería). |
| **Fuentes de ingreso** | Venta del kit de hardware ensamblado; contrato de mantenimiento anual; servicio de calibración por punto de instalación; posibles convenios institucionales (CAR, alcaldías) para despliegue masivo subsidiado. |
| **Recursos clave** | Firmware propio (lógica de fusión validada), diseño de hardware replicable, conocimiento del dominio hidrológico regional, relación con actores institucionales locales. |
| **Actividades clave** | Ensamblaje y calibración de nodos, instalación en campo, soporte técnico, actualización del firmware, generación de reportes agregados de riesgo regional (offline, por recolección manual de datos si se requiere históricos). |
| **Socios clave** | CAR Cundinamarca, IDEAM, alcaldías de Sabana Centro, proveedores de componentes electrónicos, juntas de acueductos veredales, Universidad de La Sabana (transferencia de conocimiento). |
| **Estructura de costos** | Componentes electrónicos por unidad (ESP32, sensores, LCD 16×2 I²C, batería, panel solar), carcasa/impermeabilización, mano de obra de ensamblaje e instalación, mantenimiento periódico, capacitación comunitaria. |

## 4.2 Estimación preliminar de costo por unidad (referencial)

| Componente | Costo aprox. (COP) |
|---|---|
| ESP32 DevKit-C | 35 000 |
| BME280 | 20 000 |
| HC-SR04 | 8 000 |
| Mini panel solar + INA219 | 30 000 |
| LCD 16×2 I²C | 0 |
| LEDs + resistencias + buzzer | 10 000 |
| Batería 18650 + TP4056 + MT3608 | 30 000 |
| Carcasa/protección IP + soportes mecánicos | 40 000 |
| **Total aproximado por nodo** | **≈ 193 000 COP** |

> Costos referenciales de mercado local para efectos de planeación; deben validarse con cotizaciones reales antes de un despliegue a escala.

## 4.3 Viabilidad y escalabilidad

La ausencia de costos recurrentes de conectividad (sin SIM, sin suscripción cloud) hace que el **costo marginal por nodo adicional sea bajo y predecible**, lo que favorece un despliegue distribuido en los 20 municipios identificados por la CAR en riesgo extremo de desabastecimiento [2]. La principal barrera de escalamiento no es tecnológica sino logística: la calibración física de cada punto (distancias de lleno y vacío) y el mantenimiento en campo, que se resuelven mediante el modelo de servicio de instalación/mantenimiento descrito arriba. Desde el Challenge #2 esa calibración se hace desde el tablero de control, sin abrir el equipo ni reprogramarlo, lo que reduce el tiempo de instalación por punto. El tablero usa la WLAN que ya ofrece la autoridad local, sin costos recurrentes de conectividad.

## 4.4 Ajustes al modelo de negocio (Challenge #3)

El Challenge #3 agrega un **gateway** por zona y una capa en la nube, lo que cambia la propuesta de valor y la estructura de costos.

**Propuesta de valor ampliada.** La alerta in situ sigue funcionando sin Internet (no se pierde la ventaja anterior), y ahora las autoridades de la alcaldía o la gobernación **ven el estado de todos los puntos desde cualquier lugar**, reciben las alertas en el celular y pueden pedir una recomendación de acción basada en los datos. El histórico queda en la nube y, como respaldo, en la base local del gateway.

**Arquitectura de despliegue.** Un gateway (Raspberry Pi) atiende **varios nodos** de la misma zona: los tópicos MQTT llevan el identificador de cada equipo. El costo del gateway se reparte entre los nodos.

| Componente nuevo | Costo aprox. (COP) | Tipo |
|---|---|---|
| Raspberry Pi + fuente + microSD | ≈ $665.500: kit Raspberry Pi 4 de 4 GB con fuente de 5 V 3 A, microSD de 32 GB y caja (Demosspro, consultado el 16/11/2026) | Una vez por zona (compartido entre nodos) |
| Conectividad del gateway (hotspot o internet de la zona) | ≈ $15.000: plan prepago de 1 GB (Claro, según MejorPlan, 16/11/2026). El gateway gasta unos 70 MB al mes: en las pruebas subió 423 mensajes de ~300 bytes en 3,9 h | Mensual |
| Ubidots | 0 en el plan STEM (académico); plan Professional de USD 99 por mes, hasta 50 dispositivos (≈ $328.000 con la TRM de $3.316,70 del 16/11/2026). El plan Industrial se cotiza aparte | Mensual |
| Telegram (alertas y dashboard) | 0 | — |
| Claude (recomendación a pedido) | ≈ USD 0,02 por consulta; en las pruebas, 31 consultas costaron ≈ USD 0,56 | Por uso |

**Estructura de costos.** Aparece un costo recurrente (conectividad del gateway y plataforma en la nube) que no existía en el Challenge #2. Se mantiene bajo por tres decisiones de diseño:
- se suben promedios por minuto, no cada muestra;
- las alertas al celular van por Telegram, sin costo, en vez de SMS (el cupo de SMS del plan gratuito se agotó en las pruebas);
- el modelo de lenguaje se consulta solo cuando una autoridad lo pide.

**Nuevas fuentes de ingreso posibles.** Suscripción anual por zona que incluye el gateway, el tablero global y el canal de alertas por Telegram para las autoridades. Reportes mensuales para la alcaldía o la empresa de acueducto, generados a partir del histórico del gateway (consumo, tendencia del nivel y eventos). Un servicio de instalación y mantenimiento de los nodos y del gateway, cobrado por visita.

---
[⬅ Anterior: Desarrollo modular](03-Desarrollo-Modular.md) · [⬆ Índice](00-Home.md) · [Siguiente: Configuración experimental y resultados ➡](05-Configuracion-Experimental-Resultados.md)
