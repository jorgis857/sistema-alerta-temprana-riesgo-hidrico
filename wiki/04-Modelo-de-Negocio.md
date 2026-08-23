[⬅ Volver al índice](00-Home.md)

# 4. Modelo de negocio

Aunque el proyecto nace como un reto académico, se plantea un modelo de negocio orientado a un despliegue real por parte de acueductos veredales, alcaldías municipales y la CAR Cundinamarca, bajo un esquema de **hardware de bajo costo + servicio de instalación/mantenimiento**, sin necesidad de conectividad ni suscripción a la nube (lo cual reduce drásticamente el costo operativo frente a soluciones IoT tradicionales basadas en la nube).

## 4.1 Business Model Canvas

| Bloque | Contenido |
|---|---|
| **Segmentos de clientes** | (1) Juntas administradoras de acueductos veredales de Sabana Centro. (2) Alcaldías municipales y Unidades de Gestión del Riesgo de Desastres (UGRD). (3) Distritos de riego agroindustriales. (4) CAR Cundinamarca (monitoreo distribuido complementario a su red institucional). |
| **Propuesta de valor** | Alerta temprana de riesgo hídrico **in situ**, sin dependencia de redes de comunicación ni de conectividad a Internet; instalación simple, bajo costo (< USD 50 en componentes), calibración replicable en distintos reservorios, y visualización comprensible para personal no técnico. |
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

La ausencia de costos recurrentes de conectividad (sin SIM, sin suscripción cloud) hace que el **costo marginal por nodo adicional sea bajo y predecible**, lo que favorece un despliegue distribuido en los 20 municipios identificados por la CAR en riesgo extremo de desabastecimiento [2]. La principal barrera de escalamiento no es tecnológica sino logística: la calibración física de cada punto (`DISTANCIA_LLENO`/`DISTANCIA_VACIO`) y el mantenimiento en campo, que se resuelven mediante el modelo de servicio de instalación/mantenimiento descrito arriba.

---
[⬅ Anterior: Desarrollo modular](03-Desarrollo-Modular.md) · [⬆ Índice](00-Home.md) · [Siguiente: Configuración experimental y resultados ➡](05-Configuracion-Experimental-Resultados.md)
