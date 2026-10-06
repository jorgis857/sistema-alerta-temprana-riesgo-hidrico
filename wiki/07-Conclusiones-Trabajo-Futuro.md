[⬅ Volver al índice](00-Home.md)

# 7. Conclusiones, retos, trabajo futuro y referencias

## 7.1 Conclusiones

El desarrollo de WREWS permitió cumplir el objetivo principal del Challenge #1: construir un prototipo capaz de **monitorear variables relacionadas con la disponibilidad de agua, procesar la información localmente y generar alertas tempranas ante diferentes escenarios de riesgo hídrico**.

A partir del proceso de diseño, simulación, implementación y validación se obtuvieron las siguientes conclusiones:

### 1. El prototipo funcional fue implementado y validado físicamente

WREWS pasó de una primera etapa de diseño y simulación en Wokwi a una **implementación física funcional basada en ESP32**.

El montaje final permitió comprobar la adquisición de las variables, el procesamiento local, la visualización mediante LCD y la actuación mediante LEDs y buzzer.

De esta manera, la validación no se limitó al entorno simulado, sino que se comprobó el funcionamiento integrado del sistema utilizando sensores y actuadores reales.

### 2. El nivel por sí solo no representa completamente el riesgo

Una de las principales decisiones de diseño fue evitar que el sistema dependiera únicamente del nivel instantáneo del reservorio.

WREWS integra tres dimensiones:

```text
DISPONIBILIDAD ACTUAL
Déficit de nivel
        50 %
          │
          │
CONDICIONES AMBIENTALES
VPD + irradiancia
        30 %
          │
          ▼
    RIESGO HÍDRICO
          ▲
          │
TENDENCIA DEL NIVEL
Tasa de descenso
        20 %
```

Esto permite considerar no solamente **cuánta agua queda**, sino también las condiciones que favorecen la evaporación y **qué tan rápido está disminuyendo el nivel**.

### 3. La tasa de descenso aporta información sobre la evolución del sistema

Dos reservorios pueden presentar el mismo porcentaje de nivel y, sin embargo, encontrarse en situaciones diferentes si uno permanece estable y el otro está disminuyendo rápidamente.

Por esta razón, incorporar la tasa de descenso permite que WREWS analice la **tendencia** y no únicamente una medición instantánea.

### 4. Las variables ambientales complementan la evaluación del riesgo

La temperatura y la humedad obtenidas mediante el BME280 permiten calcular el **déficit de presión de vapor (VPD)**.

Este indicador se combina con la irradiancia estimada mediante el panel fotovoltaico y el INA219 para representar qué tan favorables son las condiciones ambientales para la evaporación.

La presión atmosférica se mantiene como una variable ambiental de contexto. Debido a su baja variación esperada en un punto fijo de instalación, no se utiliza directamente como disparador principal de las alertas.

### 5. La fusión de información permite una clasificación más completa

La combinación ponderada de déficit de nivel, condiciones evaporativas y tasa de descenso permite obtener un índice general de riesgo.

Además, las reglas de seguridad implementadas permiten que una condición individual extrema pueda elevar el estado del sistema aunque el promedio ponderado todavía no alcance por sí solo el umbral crítico.

De esta forma se obtienen tres estados fácilmente interpretables:

- 🟢 **NORMAL**
- 🟡 **PRECAUCIÓN**
- 🔴 **CRÍTICO**

### 6. Las alertas funcionan de manera completamente local

El ESP32 realiza localmente:

- adquisición de sensores;
- procesamiento de variables;
- cálculo de indicadores;
- fusión de información;
- clasificación del riesgo;
- control de los actuadores.

Por tanto, el prototipo puede generar una alerta sin depender de Wi-Fi, Internet o servicios externos.

La información se comunica mediante la **LCD 16×2 I²C**, los LEDs de estado y el buzzer.

### 7. La simulación fue una etapa útil antes de la implementación física

Wokwi permitió comprobar la arquitectura, las comunicaciones I²C, la lógica de procesamiento y diferentes escenarios antes de integrar el hardware real.

Posteriormente, la implementación física permitió ajustar el sistema a las características reales de los componentes y de la maqueta.

El proceso seguido puede resumirse como:

```text
DISEÑO
   ↓
SIMULACIÓN
   ↓
DEPURACIÓN
   ↓
IMPLEMENTACIÓN FÍSICA
   ↓
CALIBRACIÓN
   ↓
VALIDACIÓN
```

Esta metodología permitió reducir errores durante la integración final.

### 8. (Challenge #2) El prototipo pasó de maqueta a producto terminado con tablero de control

WREWS se integró en una carcasa con el sensor de nivel en un tubo de PVC, alimentación por pilas y un tablero de control web en la WLAN de la zona, alojado en el propio ESP32. El tablero cumple los requisitos mínimos del enunciado: valor actual e histórico reciente, notificaciones, desactivación de la alarma física y acceso restringido a dispositivos autorizados de la WLAN, sin MQTT ni nube. La alarma física se mantuvo independiente de la red: la medición y las alarmas corren en tareas propias, y una caída de la WLAN no las afecta.

### 9. (Challenge #2) Los valores del modelo quedaron anclados a métodos y normativa

El índice evaporativo pasó a ser la evaporación potencial de Priestley-Taylor con FAO-56; los pesos salen del AHP; los umbrales de nivel, de los Planes Especiales de Sequía; los de riesgo se derivan de los de nivel; y los de tasa, de una calibración experimental. Lo que no tiene fuente (los umbrales de evaporación 60/85, G ≈ 0, el mínimo de nubosidad, el modo demo) se declara como supuesto. Esto responde a la principal observación del Challenge #1.

### 10. (Challenge #2) Las pruebas en el equipo real encontraron fallas que la teoría no mostraba

El sol real saturaba el índice evaporativo en modo demo; la evaporación sola producía falsos positivos con el tubo lleno; el tablero no se recuperaba tras una caída de la WLAN; y el buzzer no reproducía el tono de crítico. Las cuatro se corrigieron gracias al banco de pruebas, lo que muestra el valor de validar sobre el equipo integrado y no solo sobre el modelo.

---

## 7.2 Retos encontrados durante el desarrollo

### Integración del sensor ultrasónico

Uno de los principales retos fue obtener mediciones estables y coherentes con las dimensiones de la maqueta.

La respuesta del sensor físico requirió pruebas y ajustes de calibración para transformar correctamente la distancia medida en un porcentaje representativo del nivel.

La implementación de una plataforma móvil permitió realizar estas pruebas de manera controlada y repetible.

### Integración de diferentes dispositivos I²C

El sistema utiliza varios componentes que comparten el bus I²C.

Fue necesario verificar las direcciones y el funcionamiento conjunto de los dispositivos para garantizar que el ESP32 pudiera adquirir correctamente la información.

### Estimación de irradiancia

El mini panel fotovoltaico no es un piranómetro calibrado.

Por esta razón, su señal junto con el INA219 se utiliza como una **estimación experimental de irradiancia**, suficiente para observar cambios relativos en las condiciones de iluminación dentro del alcance del prototipo.

Este punto fue importante para evitar presentar la medición como una lectura metrológica de precisión.

### Diferencias entre simulación y montaje físico

La simulación permitió trabajar con entradas ideales y fácilmente controlables.

En el montaje físico aparecieron aspectos adicionales como:

- variación en las lecturas;
- comportamiento real de los sensores;
- conexiones físicas;
- calibración;
- dimensiones reales de la maqueta;
- respuesta de los actuadores.

Esto hizo necesario ajustar algunos parámetros respecto a los utilizados inicialmente en Wokwi.

### Visualización en una LCD 16×2

El espacio disponible en la pantalla LCD es limitado frente a la cantidad de información procesada por WREWS.

Por ello, fue necesario priorizar y organizar la información mostrada para mantener una interfaz local comprensible sin afectar el procesamiento interno de todas las variables.

### (Challenge #2) Concurrencia entre medición, alarmas y servidor web

Pasar de un único `loop()` a tres hilos exigió proteger el estado compartido y el bus I²C con mutex, fijar el orden en que se toman los candados para evitar bloqueos mutuos y sacar la lectura lenta del ultrasónico (~100 ms) fuera del candado del estado, para que las alarmas no se frenaran.

### (Challenge #2) Recuperación del tablero tras una caída de la WLAN

En la primera versión, al apagar y prender los datos del hotspot, el tablero se quedaba en "Sin conexión" y la página ni siquiera cargaba al recargar. Las causas fueron tres: las peticiones del navegador quedaban colgadas y bloqueaban a las nuevas; el reintento propio de conexión cortaba la reconexión automática del ESP32 a la mitad; y el ahorro de energía del radio hacía que el servidor no siempre respondiera. Se corrigió con cancelación de peticiones a los 4 s, un reintento que no interrumpe intentos en curso, el radio sin ahorro de energía y el reinicio del servidor al volver la red.

### (Challenge #2) Índice evaporativo saturado con sol real

El modo demo extrapolaba la ventana corta a 24 horas con la misma luz. Con la lámpara de laboratorio no se notaba, pero al sol (831 W/m²) daba 2.5 veces el máximo físico diario y el índice quedaba en 100 todo el tiempo. Se resolvió con el índice de claridad: la luz de la ventana se toma como el mediodía de un día con esa nubosidad.

### (Challenge #2) Falsos positivos por evaporación

Con el tubo lleno y un mediodía seco y soleado, el equipo pasaba a CRÍTICO solo por la evaporación. Se decidió que la evaporación, al ser un forzante y no la disponibilidad de agua, lleve por sí sola como máximo a PRECAUCIÓN, y que el paso a CRÍTICO venga del nivel, la tasa o el riesgo combinado.

### (Challenge #2) Tono de la alarma de crítico

El tono de crítico (2500 Hz) sonaba como clics. Un barrido de frecuencias mostró que el buzzer del prototipo no suena desde 2500 Hz, y que los clics venían de reconfigurar el PWM cada 10 ms. Se bajó el tono a 2000 Hz y el buzzer pasó a manejarse por ciclo útil, configurando la frecuencia solo cuando cambia el estado.

---

## 7.3 Trabajo futuro

Aunque el prototipo físico cumple los objetivos establecidos para esta etapa, existen oportunidades para continuar desarrollando WREWS.

### 1. Calibración en un reservorio real

La calibración actual corresponde a la maqueta construida para las pruebas.

Una implementación real requeriría medir las dimensiones y geometría del reservorio para convertir correctamente la distancia ultrasónica en nivel y, si se requiere, volumen de agua disponible.

### 2. Calibración de la irradiancia

El panel fotovoltaico permite obtener una señal relacionada con la radiación recibida.

Como trabajo futuro, esta señal podría compararse contra un piranómetro o instrumento de referencia para obtener una curva de calibración más precisa en W/m².

### 3. Ajuste de umbrales utilizando datos históricos

Los umbrales actuales permiten demostrar la lógica del sistema y validar el prototipo.

Una implementación en campo podría utilizar registros históricos de nivel y condiciones ambientales para ajustar los límites de NORMAL, PRECAUCIÓN y CRÍTICO según las características reales del lugar de instalación.

### 4. Pruebas prolongadas

Una siguiente etapa podría evaluar el sistema durante periodos de varios días o semanas para analizar:

- estabilidad de los sensores;
- comportamiento de la tasa de descenso;
- variaciones ambientales reales;
- falsas alarmas;
- funcionamiento continuo del sistema.

### 5. Protección para operación en exteriores

Para una implementación permanente sería necesario utilizar una carcasa adecuada para proteger el ESP32, conexiones y demás componentes frente a humedad, lluvia, polvo y exposición ambiental.

### 6. Validación de campo

El siguiente nivel de validación consistiría en instalar WREWS temporalmente sobre un punto real de almacenamiento de agua y comparar las estimaciones del sistema con mediciones de referencia.

### 7. (Challenge #2) Cerrar los umbrales de evaporación con datos locales

Calcular la evaporación con datos históricos de una estación del IDEAM en la Sabana (portal DHIME) y fijar precaución y crítico en los percentiles 80 y 95, como hace el US Drought Monitor [23]. Como verificación externa del orden de magnitud, convertir la evaporación de tanque clase A de una estación cercana con el coeficiente 0.7 de Kohler et al. [13].

### 8. (Challenge #2) Calibrar α y el calor almacenado en el embalse

Calibrar el coeficiente α de Priestley-Taylor en el sitio (en trópico de altura se han reportado valores de 1.11 [14]) y estimar el calor almacenado G con perfiles de temperatura del agua, o usar una ventana de varios días en campo para reducir su efecto [11], [12].

### 9. (Challenge #2) Seguridad y operación del tablero

Servir el tablero por HTTPS, permitir cambiar las redes Wi-Fi sin reprogramar (por ejemplo, con un modo de configuración temporal) y guardar el historial en memoria no volátil para que sobreviva a reinicios.

### 10. (Challenge #2) Consumo y autonomía

Medir el consumo por estado, estimar la autonomía con pilas y evaluar modos de bajo consumo compatibles con el tablero, por ejemplo despertar periódico con el radio apagado entre consultas.

---

## 7.4 Cierre

WREWS demuestra que un sistema IoT de bajo costo puede combinar **nivel, condiciones ambientales y tendencia** para construir una evaluación local del riesgo hídrico.

El resultado final es un prototipo físico capaz de adquirir información mediante múltiples sensores, procesarla en un ESP32 y transformar los datos en tres estados de fácil interpretación.

```text
NIVEL
   +
CONDICIONES AMBIENTALES
   +
TASA DE DESCENSO
   ↓
RIESGO HÍDRICO
   ↓
NORMAL / PRECAUCIÓN / CRÍTICO
```

El proyecto permite demostrar de forma funcional el concepto de **alerta temprana**, pasando de la adquisición de datos a una decisión local y una respuesta física mediante indicadores visuales y sonoros.

---

## 7.5 Referencias

Formato IEEE. [1]–[4] se tomaron textualmente del enunciado oficial. [5]–[37] corresponden al modelo de evaporación, los pesos, los umbrales, los componentes, los estándares y la normativa del Challenge #2; en el firmware se citan con la numeración de las hojas de trabajo del equipo (`[Ev n]` y `[Pe n]`), con esta equivalencia:

| Código | Wiki | Código | Wiki | Código | Wiki |
|---|---|---|---|---|---|
| Ev 1 | [5] | Ev 9 | [13] | Pe 7 | [20] |
| Ev 2 = Pe 1 | [6] | Ev 10 | [14] | Pe 8 | [21] |
| Ev 3 | [7] | Ev 12 = Pe 14 | [15] | Pe 9 | [22] |
| Ev 4 | [8] | Pe 3 | [16] | Pe 10 | [23] |
| Ev 5 = Pe 2 | [9] | Pe 4 | [17] | Pe 11 | [24] |
| Ev 6 = Pe 15 | [10] | Pe 5 | [18] | Pe 12 · Pe 13 | [25] · [26] |
| Ev 7 | [11] | Pe 6 | [19] | Pe 16 · Pe 17 | [27] · [28] |
| Ev 8 | [12] | | | | |

**Contexto del reto**

[1] Ministerio de Ambiente y Desarrollo Sostenible, "Gobierno confirma inicio del fenómeno de El Niño y alerta sobre su alcance," Minambiente, Bogotá, Colombia, jun. 2026. [En línea]. Disponible: https://www.minambiente.gov.co/gobierno-confirma-inicio-del-fenomeno-de-el-nino-y-alerta-sobre-su-alcance/

[2] Caracol Radio, "Fenómeno del Niño: los municipios en Cundinamarca con mayor riesgo de desabastecimiento de agua," Caracol Radio Bogotá, Sección Nacional, jun. 16, 2026. [En línea]. Disponible: https://caracol.com.co/2026/06/16/fenomeno-del-nino-los-municipios-en-cundinamarca-con-mayor-riesgo-de-desabastecimiento-de-agua/

[3] Infobae, "Fenómeno de El Niño en Colombia: estos son los 16 escenarios de riesgo que podría vivir Bogotá," Infobae Colombia, Sección Medio Ambiente, jul. 8, 2026. [En línea]. Disponible: https://www.infobae.com/colombia/2026/07/08/fenomeno-de-el-nino-en-colombia-estos-son-los-16-escenarios-de-riesgo-que-podria-vivir-bogota/

[4] Gobernación de Cundinamarca, "Plan de Contingencia para el Fenómeno de El Niño," Unidad Administrativa Especial para la Gestión del Riesgo de Desastres (UAEGRD), Bogotá, Colombia, Inf. Técnico, 2026. [En línea]. Disponible: https://www.cundinamarca.gov.co/wcm/connect/107cf680-7a33-47d6-8f65-0d534e1de1e2/PLAN+DE+CONTIGENCIA+FEN%C3%93MENO+EL+NI%C3%91O.pdf

**Modelo de evaporación**

[5] C. H. B. Priestley y R. J. Taylor, "On the assessment of surface heat flux and evaporation using large-scale parameters," *Monthly Weather Review*, vol. 100, no. 2, pp. 81–92, 1972, doi: 10.1175/1520-0493(1972)100<0081:OTAOSH>2.3.CO;2.

[6] R. G. Allen, L. S. Pereira, D. Raes y M. Smith, *Crop Evapotranspiration: Guidelines for Computing Crop Water Requirements*, FAO Irrigation and Drainage Paper 56. Roma: FAO, 1998. [En línea]. Disponible: https://www.fao.org/3/x0490e/x0490e00.htm

[7] D. O. Rosenberry, T. C. Winter, D. C. Buso y G. E. Likens, "Comparison of 15 evaporation methods applied to a small mountain lake in the northeastern USA," *Journal of Hydrology*, vol. 340, no. 3–4, pp. 149–166, 2007, doi: 10.1016/j.jhydrol.2007.03.018.

[8] R. E. Payne, "Albedo of the sea surface," *Journal of the Atmospheric Sciences*, vol. 29, no. 5, pp. 959–970, 1972.

[9] M. Rhiat, M. Karrouchi et al., "Design and simulation of a low-cost solar irradiance meter for PV applications," *E3S Web of Conferences*, vol. 469, art. 00076, 2023, doi: 10.1051/e3sconf/202346900076.

[10] Texas Instruments, *INA219 Zero-Drift, Bidirectional Current/Power Monitor with I2C Interface*, SBOS448.

[11] F. A. Jansen, R. Uijlenhoet, C. M. J. Jacobs y A. J. Teuling, "Evaporation from a large lowland reservoir – observed dynamics and drivers during a warm summer," *Hydrology and Earth System Sciences*, vol. 26, pp. 2875–2898, 2022, doi: 10.5194/hess-26-2875-2022.

[12] W. Xiao et al., "Evaluation of the maximum evaporation and the Priestley-Taylor models for inland waterbodies," *Journal of Geophysical Research: Atmospheres*, vol. 129, e2024JD041071, 2024, doi: 10.1029/2024JD041071.

[13] M. A. Kohler, T. J. Nordenson y W. E. Fox, "Evaporation from pans and lakes," U.S. Weather Bureau, Research Paper No. 38, Washington, mayo 1955.

[14] Y. Seleshi, "Calibration of the Priestley-Taylor evaporation model for Ethiopia," *Zede Journal of Ethiopian Engineers and Architects*, vol. 36, pp. 28–40, 2023.

[15] Bosch Sensortec, *BME280 Combined Humidity and Pressure Sensor – Datasheet*, BST-BME280-DS002.

**Gestión de alarmas, pesos y umbrales**

[16] *Management of Alarm Systems for the Process Industries*, ANSI/ISA-18.2-2016, International Society of Automation, 2016.

[17] *Alarm Systems: A Guide to Design, Management and Procurement*, EEMUA Publication 191, 3.ª ed. Londres: EEMUA, 2013.

[18] T. L. Saaty, "How to make a decision: The analytic hierarchy process," *European Journal of Operational Research*, vol. 48, no. 1, pp. 9–26, 1990, doi: 10.1016/0377-2217(90)90057-I.

[19] R. Z. B. Bravo, A. P. M. A. Cunha, A. Leiras y F. L. Cyrino Oliveira, "A new approach for a drought composite index," *Natural Hazards*, vol. 108, pp. 755–780, 2021, doi: 10.1007/s11069-021-04704-x.

[20] Ministerio para la Transición Ecológica, "Orden TEC/1399/2018, de 28 de noviembre, por la que se aprueba la revisión de los planes especiales de sequía…," *Boletín Oficial del Estado*, BOE-A-2018-17752, 2018.

[21] Dirección General del Agua, "Aspectos a destacar de los nuevos Planes Especiales de Sequía," MITECO, Madrid, jul. 2017. [En línea]. Disponible: https://www.miteco.gob.es/es/agua/temas/observatorio-nacional-de-la-sequia/aspectos-a-destacar-nuevos-pes_tcm30-436654.pdf

[22] I. Donado Henríquez, "Con nivel de 40,36 % en el sistema Chingaza se asoma fin del racionamiento en Bogotá," *La República*, 27 feb. 2025. [En línea]. Disponible: https://www.larepublica.co/economia/con-nivel-de-40-36-en-el-sistema-chingaza-se-asoma-fin-del-racionamiento-en-bogota-4073229

[23] M. Svoboda et al., "The Drought Monitor," *Bulletin of the American Meteorological Society*, vol. 83, no. 8, pp. 1181–1190, 2002, doi: 10.1175/1520-0477-83.8.1181.

[24] C. Cammalleri et al., "A revision of the Combined Drought Indicator (CDI) used in the European Drought Observatory (EDO)," *Natural Hazards and Earth System Sciences*, vol. 21, pp. 481–495, 2021, doi: 10.5194/nhess-21-481-2021.

**Proyectos similares**

[25] A. Kalyanapu, C. Owusu, T. Wright y T. Datta, "Low-cost real-time water level monitoring network for Falling Water River watershed: A case study," *Geosciences*, vol. 13, no. 3, art. 65, 2023, doi: 10.3390/geosciences13030065.

[26] M. F. Jusoh, M. F. A. Muttalib, N. S. Saedin y M. Mahmud, "Automatic monitoring of Class A pan evaporation using the Internet of Things (IoT)," *Advanced and Sustainable Technologies (ASET)*, vol. 3, 2024, doi: 10.58915/aset.v3i.586.

**Componentes, protocolos y plataforma**

[27] Espressif Systems, *ESP32 Series Datasheet*.

[28] Elecfreaks, *HC-SR04 Ultrasonic Ranging Module – Datasheet*.

[29] IEEE Standards Association, "IEEE 802.11-2020 — Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications," 2020.

[30] R. Fielding, M. Nottingham y J. Reschke, "HTTP Semantics," RFC 9110, IETF, jun. 2022. [En línea]. Disponible: https://www.rfc-editor.org/rfc/rfc9110

[31] Espressif Systems, "ESP-IDF Programming Guide — FreeRTOS (IDF)." [En línea]. Disponible: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/freertos_idf.html

**Normativa**

[32] Ministerio de Minas y Energía, *Reglamento Técnico de Instalaciones Eléctricas — RETIE*, Colombia. ⟨confirmar número y año de la resolución vigente⟩

[33] Ministerio de Vivienda, Ciudad y Territorio, "Resolución 0330 de 2017, por la cual se adopta el Reglamento Técnico para el Sector de Agua Potable y Saneamiento Básico — RAS," Colombia, 2017.

[34] *Degrees of Protection Provided by Enclosures (IP Code)*, IEC 60529, International Electrotechnical Commission.

[35] Congreso de la República de Colombia, "Ley 1523 de 2012, por la cual se adopta la política nacional de gestión del riesgo de desastres," abr. 2012.

[36] Congreso de la República de Colombia, "Ley Estatutaria 1581 de 2012, por la cual se dictan disposiciones generales para la protección de datos personales," oct. 2012.

[37] Agencia Nacional del Espectro (ANE), régimen de uso libre del espectro radioeléctrico para la banda de 2.4 GHz, Colombia. ⟨confirmar la resolución vigente⟩

---

[⬅ Anterior: Autoevaluación del protocolo de pruebas](06-Autoevaluacion-Pruebas.md) · [⬆ Índice](00-Home.md) · [Siguiente: Uso de Inteligencia Artificial ➡](08-Uso-de-IA.md)