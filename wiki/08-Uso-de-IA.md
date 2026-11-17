[⬅ Volver al índice](00-Home.md)

# 8. Uso de Inteligencia Artificial

Esta sección está hecha con el fin de informar de manera transparente el uso de herramientas de Inteligencia Artificial durante el desarrollo y la documentación de nuestro proyecto.

## 8.1 Herramientas de IA utilizadas

Durante el desarrollo del proyecto nos apoyamos principalmente en **Claude (Anthropic)** como herramienta de asistencia para tareas de investigación, documentación, validación técnica y revisión del trabajo realizado. En el Challenge #2 también usamos **Claude Code** como asistente de programación del firmware y del tablero de control.

También utilizamos **Claude Design** como apoyo para el modelado 3D del hardware y para la generación de algunos recursos visuales utilizados en el material audiovisual del proyecto.

La Inteligencia Artificial se utilizó como una herramienta de apoyo durante diferentes etapas del proyecto. Las decisiones finales, pruebas, conexiones, mediciones, montaje físico y validación fueron realizadas y revisadas por el equipo.

## 8.2 Uso de la IA durante el desarrollo del proyecto

El uso de Inteligencia Artificial estuvo presente en diferentes etapas de WREWS.

### Investigación y búsqueda de información

Claude se utilizó como apoyo para realizar investigación técnica relacionada con el proyecto.

Esto incluyó:

- búsqueda y análisis de artículos, papers y documentación relacionada con monitoreo hídrico;
- investigación de sistemas y proyectos similares;
- búsqueda de información relacionada con evaporación, VPD, irradiancia y monitoreo de nivel;
- revisión de fórmulas y metodologías utilizadas en trabajos existentes;
- búsqueda y análisis de documentación técnica de sensores, módulos y componentes utilizados en el proyecto.

A partir de esta investigación, el equipo revisaba la información obtenida y la contrastaba con documentación técnica, fuentes externas y los resultados de las pruebas realizadas.

### Validación de conexiones y componentes

Claude también se utilizó como apoyo para revisar las conexiones eléctricas realizadas durante el desarrollo.

Como una de las principales fuentes de referencia para las conexiones y configuración de componentes con ESP32, el equipo utilizó **Random Nerd Tutorials**, específicamente su sección de proyectos y tutoriales para ESP32:

https://randomnerdtutorials.com/projects-esp32/

El proceso consistía en consultar primero la documentación y los tutoriales correspondientes, realizar una propuesta de conexión y posteriormente proporcionar esa información a Claude para obtener una segunda revisión.

Por ejemplo, se le indicaban los componentes utilizados, los pines seleccionados y las conexiones realizadas, junto con las referencias consultadas, para verificar si existían inconsistencias o aspectos que debían corregirse.

Esto se utilizó para revisar aspectos como:

- alimentación de los componentes;
- conexiones SDA y SCL del bus I²C;
- selección de pines del ESP32;
- conexión de TRIG y ECHO del sensor ultrasónico;
- integración del INA219;
- conexión del BME280;
- integración de la pantalla;
- conexión de LEDs y buzzer.

La revisión mediante IA funcionó como una segunda validación y no sustituyó las pruebas realizadas posteriormente sobre el hardware físico.

### Desarrollo y simulación en Wokwi

Durante la etapa inicial del proyecto se utilizó Claude como apoyo para el desarrollo de algunos de los componentes utilizados en la simulación de Wokwi.

Esto incluyó apoyo en:

- estructura del código de componentes personalizados;
- desarrollo y ajuste de *custom chips*;
- revisión de la lógica utilizada para simular sensores;
- depuración de errores durante la simulación;
- revisión del comportamiento de las variables simuladas.

La simulación permitió probar parte de la arquitectura y de la lógica antes de realizar el montaje físico del sistema.

### Desarrollo del firmware y del tablero del Challenge #2

En el Challenge #2 se utilizó **Claude Code** (Anthropic) como asistente de programación. A partir de especificaciones escritas por el equipo (por ejemplo, la del modelo de Priestley-Taylor con sus constantes, ecuaciones y pruebas de referencia) y de las decisiones de diseño tomadas por el equipo (pesos, umbrales, red Wi-Fi, comportamiento de la alarma), Claude Code implementó el firmware v6/v7 (`wrews.ino`) y las páginas del tablero (`tablero.h`): el modelo de evaporación, las tareas de FreeRTOS, el servidor web con inicio de sesión, el histórico, los eventos, el silencio de la alarma y la calibración desde el tablero.

El equipo compiló y probó cada versión en el hardware y reportó los problemas encontrados (el tono de crítico que sonaba a clics, el tablero que no se recuperaba tras una caída de la WLAN, el índice evaporativo saturado con sol real), que se corrigieron a partir de esa evidencia. Varias propuestas no funcionaron a la primera: por ejemplo, el primer arreglo del buzzer lo dejó sin sonido, y fue el barrido de frecuencias hecho por el equipo lo que mostró el límite de 2000 Hz.

Claude también se usó para preparar las hojas de referencias del modelo de evaporación y de pesos y umbrales, y para actualizar esta Wiki.

### Desarrollo del sistema del Challenge #3

En el Challenge #3 se usó primero **Claude** (chat en claude.ai) para generar, a partir del enunciado y del contexto del proyecto, un borrador del firmware v8, del gateway y de la guía de despliegue. Ese borrador no se había compilado ni probado. Después se usó **Claude Code** (Anthropic) en el computador del equipo para revisarlo de forma crítica, implementar la versión final y probarla: el hilo MQTT del ESP32 (`wrews.ino`), el gateway de la Raspberry Pi (`gateway/`: SQLite, procesamiento local, puente con Ubidots, módulo de IA y bot de Telegram), sus 22 pruebas automáticas y las guías de despliegue y del video. Las decisiones de diseño las tomó el equipo: usar Claude como proveedor de la IA del sistema, consultarla solo a pedido para no gastar créditos, pasar las alertas de SMS a Telegram y restringir el bot con clave y aprobación del administrador.

El equipo montó el prototipo, ejecutó las pruebas con el hardware real, configuró Ubidots y el bot, y reportó lo que encontró. Algunas fallas solo aparecieron con el equipo real y se corrigieron a partir de esa evidencia. Por ejemplo, la temperatura saltaba a 180 °C por un contacto flojo del BME280 y generaba una precaución falsa; el gateway dejó de encontrarse cuando el computador cambió de IP; y el cupo de SMS de Ubidots se agotó con los reinicios de las pruebas. La revisión del borrador inicial también encontró errores antes de usarlo, como un servicio que se detenía si se reiniciaba el broker y una orden vieja de Ubidots que podía silenciar la alarma por error.

En este challenge la IA se usó para **aterrizar las ideas del equipo**: el equipo definía qué quería que hiciera el sistema y Claude ayudaba a concretar cómo implementarlo. **Claude no tomó decisiones**: cada propuesta la revisó el equipo, que eligió entre las opciones, la aceptó, la ajustó o la descartó. Claude también se usó para redactar el borrador de las secciones del Challenge #3 de esta Wiki, que el equipo revisó y completó con sus resultados. En resumen, a Claude Code se le pidió:

- revisar de forma crítica el borrador inicial y señalar sus errores antes de usarlo;
- implementar y compilar el firmware v8 y el gateway, y escribir sus pruebas automáticas;
- explicar Ubidots, Mosquitto y la Raspberry Pi, y guiar paso a paso la configuración del tablero, de los eventos de notificación y del bot de Telegram;
- preparar el kit de instalación de la Pi, la guía para grabar la microSD y el guion del video;
- acompañar el despliegue en la universidad, por ejemplo para encontrar la Pi en el hotspot cuando no aparecía;
- extraer de la base de datos y del registro de la Pi los resultados de las pruebas para esta Wiki, y buscar los precios de referencia del modelo de negocio.

Todas las decisiones (la arquitectura, el uso de Claude como IA del sistema, consultarla solo a pedido, Telegram en vez de SMS, el acceso con clave y aprobación, los umbrales y el reparto de roles), el montaje, las pruebas con el hardware y la revisión final del texto las hizo el equipo.

### La IA como parte del sistema (Challenge #3)

Además de usarse para desarrollar, en el Challenge #3 la IA es un **componente de WREWS**. El módulo de recomendación usa la API de **Claude** (`claude-opus-5-5`). La predicción (minutos hasta el 15 %) la calcula el gateway con una regresión propia; el modelo de lenguaje solo convierte esos números en una recomendación para las autoridades, sin calcular cifras por su cuenta, y se consulta únicamente cuando alguien la pide. Cada respuesta queda guardada en SQLite con el prompt exacto que se le envió, y si no hay Internet responde una tabla de reglas (ver [Sección 3.25](03-Desarrollo-Modular.md)).

### Fórmulas y modelo de procesamiento

Claude fue utilizado como apoyo para investigar, revisar y comprender diferentes fórmulas y modelos relacionados con las variables del proyecto.

Entre ellos:

- cálculo del nivel a partir de distancia;
- déficit de presión de vapor (VPD);
- relación entre temperatura, humedad y evaporación;
- interpretación de la irradiancia;
- análisis de la tendencia del nivel;
- posibles formas de combinar diferentes variables dentro de un índice de riesgo.

Para esta parte se consultaron artículos, estudios, documentación técnica y trabajos relacionados con problemas similares.

A partir de esta investigación, el equipo evaluó qué conceptos podían ser utilizados o adaptados al alcance del prototipo.

### Validación y revisión del trabajo realizado

Durante el desarrollo se utilizó Claude como herramienta de revisión.

A medida que el equipo avanzaba en conexiones, código, fórmulas, pruebas o documentación, se utilizaba la IA para revisar lo realizado y señalar posibles errores, inconsistencias o aspectos que podían mejorarse.

Después de recibir estas observaciones, el equipo verificaba los cambios mediante:

- pruebas en Wokwi;
- pruebas con el hardware físico;
- revisión de documentación técnica;
- comparación con las especificaciones de los componentes;
- observación del comportamiento real del prototipo.

### Modelado 3D del hardware

Para el diseño y visualización de algunas partes físicas del proyecto se utilizó **Claude Design** como herramienta de apoyo.

El proceso comenzó con la recopilación de las dimensiones de los componentes.

Para esto, el equipo:

1. tomó mediciones físicas de los componentes disponibles;
2. consultó dimensiones adicionales en datasheets, documentación técnica y fuentes disponibles en Internet;
3. proporcionó esta información a Claude Design;
4. utilizó la herramienta como apoyo para desarrollar propuestas de modelado 3D;
5. revisó diferentes vistas y distribuciones de los componentes antes de definir el diseño final.

Claude Design permitió visualizar cómo podían organizarse los diferentes elementos del hardware y sirvió como apoyo durante el proceso de diseño de la estructura física.

### Diagramas y documentación técnica

Claude fue utilizado como apoyo para representar visualmente la arquitectura y el funcionamiento del sistema.

Esto incluyó ayuda para generar:

- diagramas de bloques;
- diagramas de estados;
- diagramas de secuencia;
- diagramas de componentes;
- representaciones del flujo general del sistema.

Los diagramas fueron posteriormente revisados por el equipo para verificar que correspondieran con la implementación real.

### Apoyo visual y audiovisual

**Claude Design** también fue utilizado como apoyo para algunos elementos visuales del material audiovisual del proyecto.

Su uso se concentró específicamente en:

- creación y exploración de recursos visuales;
- apoyo en elementos gráficos y animaciones;
- desarrollo del video de introducción;
- generación de propuestas visuales relacionadas con la presentación del proyecto.

La grabación, selección de contenido y edición final del video fueron realizadas por el equipo.

### Organización y redacción de la Wiki

Claude fue utilizado como apoyo para organizar y revisar la documentación técnica del proyecto.

Se utilizó para:

- estructurar las diferentes secciones de la Wiki;
- mejorar la claridad de algunos textos;
- organizar tablas;
- revisar coherencia entre secciones;
- transformar información técnica en explicaciones más comprensibles;
- identificar posibles inconsistencias entre código, resultados y documentación.

## 8.3 Validación de la información obtenida mediante IA

La información generada o sugerida por herramientas de Inteligencia Artificial no se tomó automáticamente como correcta.

Durante el proyecto se utilizaron diferentes mecanismos de validación.

### Documentación técnica

Las conexiones y características de los componentes fueron contrastadas con:

- datasheets;
- documentación de fabricantes;
- documentación de Wokwi;
- **Random Nerd Tutorials**;
- especificaciones de los módulos utilizados.

### Pruebas en simulación

En el Challenge #1, parte de la lógica del sistema se probó en Wokwi, lo que permitió detectar algunos errores de forma controlada. En el Challenge #2 no se usó simulación: el firmware se probó directamente sobre el hardware.

### Pruebas físicas

Las conexiones, cálculos, sensores y actuadores fueron probados directamente sobre el prototipo.

Las lecturas obtenidas y el comportamiento de los estados permitieron comprobar si lo planteado durante el desarrollo funcionaba correctamente en condiciones reales.

### Recálculo independiente

Las fórmulas del modelo de evaporación y sus casos de prueba se recalcularon de forma independiente en Python antes de implementarlos, y el mismo cálculo corre como autotest en el ESP32 real. Además, algunas lecturas reales del tablero se comprobaron a mano contra las fórmulas (Sección 5.7.2).

### Comparación entre fuentes

Cuando se investigaron fórmulas, métodos o modelos, se compararon diferentes fuentes antes de utilizarlos dentro del proyecto.

Esto fue especialmente importante en temas como:

- VPD;
- evaporación;
- irradiancia;
- comportamiento del sensor ultrasónico;
- análisis de tendencia;
- características eléctricas de los componentes.

### Pruebas del Challenge #3

En el Challenge #3, el firmware se compiló antes de cargarlo y el gateway se validó en tres pasos: pruebas automáticas, pruebas de extremo a extremo con un simulador del ESP32 y pruebas con el prototipo real, la cuenta real de Ubidots y la API real de Claude (ver [Sección 5.8](05-Configuracion-Experimental-Resultados.md)). Datos como el certificado TLS de Ubidots o los modelos disponibles en las APIs de IA se comprobaron contra la documentación oficial y no se tomaron como ciertos solo porque la IA los dijo.

## 8.4 Criterio de uso de Inteligencia Artificial

La Inteligencia Artificial se utilizó como una herramienta de apoyo durante el proyecto y no como un reemplazo del trabajo realizado por el equipo.

El equipo fue responsable de:

- seleccionar los componentes;
- realizar las conexiones;
- construir el montaje físico;
- tomar mediciones;
- realizar pruebas;
- verificar el comportamiento del sistema;
- interpretar los resultados;
- decidir qué recomendaciones de la IA eran útiles;
- corregir o descartar aquellas que no correspondían con la implementación real.

De esta manera, la IA funcionó principalmente como una herramienta adicional de investigación, revisión, validación, diseño y documentación durante el desarrollo de WREWS.

## 8.5 Porcentaje de la Wiki redactado con IA

Aproximadamente el **80 %** del texto de la Wiki se redactó con ayuda de IA y el **20 %** lo redactó directamente el equipo. El 80 % incluye texto que el equipo revisó y editó.

La estimación se hizo por número de palabras. Cerca de la mitad del texto actual corresponde a la actualización del Challenge #2, redactada con Claude Code a partir del código, los resultados y las decisiones del equipo. La otra mitad viene del Challenge #1 y de la Sección 11, que también se estructuraron y redactaron con apoyo de Claude y luego fueron editadas por el equipo.

En el Challenge #3, el borrador de las secciones marcadas "(Challenge #3)" se redactó con Claude Code a partir del código, los registros de las pruebas y las decisiones del equipo, y luego fue revisado y completado por el equipo. Con esas secciones (unas 8.300 palabras nuevas), la estimación por número de palabras queda en **cerca del 83 %** del texto redactado con ayuda de IA y el **17 %** directamente por el equipo.

Todo el contenido fue revisado por el equipo. Los datos medidos (calibraciones, pruebas, fotos y resultados) provienen del trabajo del equipo.

---

[⬅ Anterior: Conclusiones y trabajo futuro](07-Conclusiones-Trabajo-Futuro.md) · [⬆ Índice](00-Home.md) · [Siguiente: Equipo de trabajo ➡](09-Equipo-Roles.md)
