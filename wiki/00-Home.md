# Wiki — WREWS (Water Risk Early Warning System)

**Curso:** Internet de las Cosas — 2026-2
**Facultad de Ingeniería — Universidad de La Sabana**
**Challenge #3 — Equipo 2** (evolución del prototipo de los Challenges #1 y #2)
**Fecha de entrega:** 16 de noviembre de 2026 (MS Teams) · **Sustentación:** 19 de noviembre de 2026

Bienvenidos a la Wiki técnica del proyecto **WREWS (Water Risk Early Warning System)**, un prototipo IoT de bajo costo, basado en ESP32, que monitorea de forma continua el nivel de un reservorio de agua, las condiciones ambientales que favorecen su evaporación y la velocidad de descenso del nivel, fusionando estas señales en un único **índice de riesgo hídrico** que se comunica localmente mediante una pantalla LCD 16×2 I²C, LEDs de estado y un buzzer.
El desarrollo se realizó en dos etapas: primero se validó la arquitectura y la lógica del sistema mediante simulación en Wokwi y posteriormente se construyó y validó un prototipo físico funcional. La implementación física final utiliza una pantalla LCD 16×2 I²C como interfaz de visualización local.

En el **Challenge #2** el prototipo pasa a ser un **dispositivo autónomo en carcasa**, alimentado por pilas, que además de la alarma local publica un **tablero de control web** alojado en el propio ESP32 y accesible solo desde la WLAN de la zona y con usuario y contraseña. El tablero muestra el valor actual y el histórico reciente de las variables, notifica los cambios de estado, permite silenciar la alarma física y calibrar el equipo sin abrir la carcasa. El índice evaporativo se reemplazó por la **evaporación potencial de Priestley-Taylor con parámetros FAO-56**, y los pesos y umbrales se anclaron a métodos y normativa citados (ver [Mejoras respecto al Challenge #1](12-Mejoras-Challenge-1.md)).

En el **Challenge #3** WREWS pasa a ser un **ecosistema IoT completo**. El ESP32 publica todas sus mediciones, estados y eventos por **MQTT**, desde un hilo de FreeRTOS propio, a un **gateway en una Raspberry Pi** con Mosquitto (usuario, clave y permisos por usuario). El gateway **guarda todo en SQLite antes de reenviarlo**, lo valida y lo procesa (detección de anomalías, promedios por ventana, vigilancia del enlace) y lo sube a **Ubidots**, el tablero global, por MQTT con TLS. Desde Ubidots las autoridades ven el valor actual y el histórico, reciben notificaciones y pueden **desactivar la alarma física**. Un **módulo de IA** combina una predicción propia (regresión del nivel: minutos hasta el 15 %) con una recomendación en lenguaje natural redactada por **Claude** (Anthropic) a pedido de las autoridades. Un **canal móvil por Telegram**, solo para usuarios aprobados, entrega las alertas, un dashboard que se actualiza solo y la consulta a la IA. Lo nuevo está marcado como **(Challenge #3)** en cada sección.

## 🎥 Video de demostración

▶️ **Video de demostración de WREWS (Challenge #3):** en edición; el enlace se agrega aquí al publicarlo.

▶️ **[Ver video de demostración de WREWS (Challenge #2)](https://youtu.be/H0U9AYJEdTg)**

El funcionamiento completo del prototipo físico WREWS del Challenge #1, incluyendo la adquisición de variables, procesamiento y generación de los estados **NORMAL, PRECAUCIÓN y CRÍTICO**, puede observarse en el video final:

▶️ **[Ver video de demostración de WREWS (Challenge #1)](https://youtu.be/zUS3DWeHSsw)**

---

## Índice

1. [Resumen, motivación y justificación](01-Resumen-Motivacion.md)
2. [Solución propuesta: restricciones, arquitectura y diagrama de bloques](02-Solucion-Propuesta.md)
3. [Desarrollo modular: criterios de diseño, UML, esquemático y estándares](03-Desarrollo-Modular.md)
4. [Modelo de negocio](04-Modelo-de-Negocio.md)
5. [Configuración experimental, resultados y análisis](05-Configuracion-Experimental-Resultados.md)
6. [Autoevaluación del protocolo de pruebas](06-Autoevaluacion-Pruebas.md)
7. [Conclusiones, retos, trabajo futuro y referencias](07-Conclusiones-Trabajo-Futuro.md)
8. [Uso de Inteligencia Artificial](08-Uso-de-IA.md)
9. [Equipo de trabajo: roles y contribuciones](09-Equipo-Roles.md)
10. [Executive Summary (English)](10-English-Executive-Summary.md)
11. [Conectividad‐IoT](11-Conectividad-IoT.md)
12. [Mejoras respecto al Challenge #1](12-Mejoras-Challenge-1.md)

## Anexos

- **(Challenge #3)** Firmware v8 con cliente MQTT: [`/firmware/wrews/wrews.ino`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/wrews/wrews.ino)
- **(Challenge #3)** Gateway de la Raspberry Pi (SQLite, procesamiento, Ubidots, IA, Telegram): [`/gateway`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/tree/main/gateway)
- **(Challenge #3)** Guía de despliegue y pruebas en la Pi: [`/docs/GUIA_DESPLIEGUE_PI.md`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/docs/GUIA_DESPLIEGUE_PI.md)
- Código fuente completo y documentado (firmware v7, Challenge #2): [`/firmware/wrews/wrews.ino`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/wrews/wrews.ino)
- Páginas del tablero de control (inicio de sesión y tablero): [`/firmware/wrews/tablero.h`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/wrews/tablero.h)
- Plantilla de credenciales de la WLAN y del tablero: [`/firmware/wrews/secrets.example.h`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/wrews/secrets.example.h)
- Librerías utilizadas: [`/firmware/libraries.txt`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/libraries.txt)
- Diagrama de conexión Wokwi (Challenge #1): [`/hardware/wokwi/diagram.json`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/hardware/wokwi/diagram.json)
- Chips personalizados (BME280, INA219, panel solar): [`/hardware/wokwi/chips`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/tree/main/hardware/wokwi/chips)
- Esquemático / captura del circuito: [`/hardware/schematics/diagrama_circuito_wokwi.png`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/hardware/schematics/diagrama_circuito_wokwi.png)
- Proyecto simulable en Wokwi (firmware del Challenge #1): <https://wokwi.com/projects/472250559337371649>
- Modelos 3D de la carcasa (STL y script de CadQuery): [`/Carcasa_3D_/Carcasa_3D_v16`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/tree/main/Carcasa_3D_/Carcasa_3D_v16)
