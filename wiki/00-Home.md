# Wiki — WREWS (Water Risk Early Warning System)

**Curso:** Internet de las Cosas — 2026-2
**Facultad de Ingeniería — Universidad de La Sabana**
**Challenge #2 — Equipo 2** (evolución del prototipo del Challenge #1)
**Fecha de entrega:** ⟨completar⟩ · **Sustentación:** ⟨completar⟩
*Challenge #1: entrega el 22 de agosto de 2026 · sustentación en la semana 6 (24 o 27 de agosto de 2026)*

Bienvenidos a la Wiki técnica del proyecto **WREWS (Water Risk Early Warning System)**, un prototipo IoT de bajo costo, basado en ESP32, que monitorea de forma continua el nivel de un reservorio de agua, las condiciones ambientales que favorecen su evaporación y la velocidad de descenso del nivel, fusionando estas señales en un único **índice de riesgo hídrico** que se comunica localmente mediante una pantalla LCD 16×2 I²C, LEDs de estado y un buzzer.
El desarrollo se realizó en dos etapas: primero se validó la arquitectura y la lógica del sistema mediante simulación en Wokwi y posteriormente se construyó y validó un prototipo físico funcional. La implementación física final utiliza una pantalla LCD 16×2 I²C como interfaz de visualización local.

En el **Challenge #2** el prototipo pasa a ser un **dispositivo autónomo en carcasa**, alimentado por pilas, que además de la alarma local publica un **tablero de control web** alojado en el propio ESP32 y accesible solo desde la WLAN de la zona y con usuario y contraseña. El tablero muestra el valor actual y el histórico reciente de las variables, notifica los cambios de estado, permite silenciar la alarma física y calibrar el equipo sin abrir la carcasa. El índice evaporativo se reemplazó por la **evaporación potencial de Priestley-Taylor con parámetros FAO-56**, y los pesos y umbrales se anclaron a métodos y normativa citados (ver [Mejoras respecto al Challenge #1](12-Mejoras-Challenge-1.md)).

## 🎥 Video de demostración

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

- Código fuente completo y documentado (firmware v7): [`/firmware/wrews/wrews.ino`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/wrews/wrews.ino)
- Páginas del tablero de control (inicio de sesión y tablero): [`/firmware/wrews/tablero.h`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/wrews/tablero.h)
- Plantilla de credenciales de la WLAN y del tablero: [`/firmware/wrews/secrets.example.h`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/wrews/secrets.example.h)
- Librerías utilizadas: [`/firmware/libraries.txt`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/firmware/libraries.txt)
- Diagrama de conexión Wokwi (Challenge #1): [`/hardware/wokwi/diagram.json`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/hardware/wokwi/diagram.json)
- Chips personalizados (BME280, INA219, panel solar): [`/hardware/wokwi/chips`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/tree/main/hardware/wokwi/chips)
- Esquemático / captura del circuito: [`/hardware/schematics/diagrama_circuito_wokwi.png`](https://github.com/jorgis857/sistema-alerta-temprana-riesgo-hidrico/blob/main/hardware/schematics/diagrama_circuito_wokwi.png)
- Proyecto simulable en Wokwi (firmware del Challenge #1): <https://wokwi.com/projects/472250559337371649>
- Modelos 3D de la carcasa: ⟨completar: enlace a los STL / script CadQuery de la versión final⟩
