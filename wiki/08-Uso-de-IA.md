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

Todo el contenido fue revisado por el equipo. Los datos medidos (calibraciones, pruebas, fotos y resultados) provienen del trabajo del equipo.

---

[⬅ Anterior: Conclusiones y trabajo futuro](07-Conclusiones-Trabajo-Futuro.md) · [⬆ Índice](00-Home.md) · [Siguiente: Equipo de trabajo ➡](09-Equipo-Roles.md)
