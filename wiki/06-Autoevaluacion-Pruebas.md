[⬅ Volver al índice](00-Home.md)

# 6. Autoevaluación del protocolo de pruebas

Esta sección evalúa de forma crítica el protocolo de validación aplicado a WREWS, considerando tanto la etapa de simulación como la implementación física del prototipo.

---

## 6.1 Checklist de cobertura del protocolo

| Criterio | ¿Se cumple? | Evidencia / observación |
|---|---|---|
| Se prueban los tres estados de alerta: NORMAL, PRECAUCIÓN y CRÍTICO | ✅ Sí | Verificados en simulación y posteriormente sobre el prototipo físico |
| Se valida la lectura del nivel mediante sensor ultrasónico | ✅ Sí | La plataforma móvil permitió reproducir diferentes alturas y comprobar la variación del porcentaje de nivel |
| Se valida la adquisición de temperatura, humedad y presión | ✅ Sí | Lecturas obtenidas correctamente mediante el BME280 |
| Se valida el subsistema panel fotovoltaico + INA219 | ✅ Sí | La señal medida respondió a cambios de iluminación y fue utilizada para estimar irradiancia |
| Se valida el cálculo del VPD | ✅ Sí | Verificado durante las pruebas de simulación y procesamiento del firmware |
| Se valida el índice de condiciones favorables a la evaporación | ✅ Sí | Se comprobó la respuesta ante cambios en temperatura, humedad e irradiancia |
| Se valida la tasa de descenso | ✅ Sí | El firmware compara mediciones sucesivas del nivel para identificar descensos acelerados |
| Se valida la lógica de fusión de información | ✅ Sí | Se probaron escenarios de riesgo dependientes de nivel, evaporación, tendencia y riesgo combinado |
| Se valida la actuación visual mediante LEDs | ✅ Sí | Verde para NORMAL, amarillo para PRECAUCIÓN y rojo para CRÍTICO |
| Se valida la alarma sonora | ✅ Sí | El buzzer se activa correctamente en el estado CRÍTICO |
| Se valida la visualización local | ✅ Sí | La LCD 16×2 I²C presenta información del sistema y el estado correspondiente |
| Se valida el funcionamiento sin redes de comunicación | ✅ Sí | Toda la adquisición, procesamiento y actuación se realiza localmente en el ESP32 |
| Se prueba el prototipo físico completo | ✅ Sí | Se verificó la cadena completa desde los sensores hasta las alertas |
| Se prueban exactamente todos los valores en el borde de cada umbral | ⚠️ Parcial | Se probaron rangos representativos, pero no todos los valores límite exactos |
| Se realizan pruebas prolongadas de horas o días de operación continua | ❌ No | Fuera del alcance temporal de esta iteración |

### Pruebas añadidas en el Challenge #2

| Criterio del enunciado | ¿Se cumple? | Evidencia / observación |
|---|---|---|
| Calibración de sensores contra referencia, con error y factor de calibración | ✅ Parcial | Nivel contra regla, Presión con datos reales (no cambia mucho dentro de Bogotá, que es donde se comprobó) y BME280 contra termohigrómetro (Sección 5.7.1); K del panel pendiente de calibrar con sol contra una referencia |
| Emulación acelerada de condiciones reales | ✅ Sí | Vaciado del tubo, sol y sombra sobre el panel, secador sobre el BME280 (Sección 5.7.3) |
| Validación de la fusión y los umbrales, con falsos positivos y negativos | ✅ Sí | Casos F1–F8 (Sección 5.7.4). La prueba al sol con el tubo lleno detectó un falso positivo y motivó la regla de tope de la evaporación / De todas formas sigue arrojando errores tipo 1  y 2 |
| Latencia de la alerta y actualización del valor actual y del histórico | ✅ Sí | Actualización y avisos observados |
| Desactivación de la alarma desde el tablero | ✅ Sí | El buzzer se calla 15 min, los LEDs siguen y queda el evento |
| Pérdida y reconexión de la WLAN | ✅ Sí | La alarma local siguió funcionando; el tablero se recuperó solo después de la corrección (Sección 5.7.6) |
| Acceso restringido a dispositivos autorizados | ✅Si | Se intnetó acceder desde otra red y también usando contraseña y usuario incorrectos dentro de la misma red |
| Valores fuera de rango y fallo de sensores | ✅ Parcial | Nivel limitado a 0–100 %; FALLO por sensor solamente con el ECHO. El piranómetro y BME no avisan |
| Verificación del modelo de evaporación contra valores de referencia | ✅ Sí | Autotest en el ESP32 real, con diferencias de redondeo frente al cálculo independiente (Sección 5.7.2) |

---

## 6.2 Fortalezas del protocolo

### Validación en dos etapas

El desarrollo utilizó primero un entorno de simulación y posteriormente hardware físico.

Esto permitió seguir una secuencia de validación progresiva:

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

La simulación permitió modificar las entradas de manera controlada y verificar la lógica de fusión antes de incorporar las posibles fuentes de error propias del hardware real.

### Cobertura funcional completa

Las pruebas no se limitaron a comprobar sensores de forma independiente.

También se verificó la cadena completa:

```text
SENSORES
   ↓
ADQUISICIÓN
   ↓
PROCESAMIENTO
   ↓
FUSIÓN
   ↓
CLASIFICACIÓN
   ↓
LCD + LEDs + BUZZER
```

Esto permitió confirmar que los módulos funcionan conjuntamente como un sistema y no solamente de manera aislada.

### Pruebas de los tres estados

Se comprobaron los estados:

- 🟢 NORMAL
- 🟡 PRECAUCIÓN
- 🔴 CRÍTICO

Esto permitió verificar tanto la lógica de clasificación como la respuesta física de los actuadores.

### Separación entre simulación y hardware

Los valores utilizados en Wokwi se mantuvieron identificados como parámetros de simulación, mientras que la implementación física se ajustó a las dimensiones y comportamiento real de la maqueta.

Esto evita interpretar los valores de la simulación como una calibración definitiva para un reservorio real.

---

## 6.3 Limitaciones identificadas

Aunque el prototipo cumplió los objetivos funcionales del reto, el protocolo presenta algunas limitaciones propias de la etapa de prototipado.

| Limitación | Implicación |
|---|---|
| La validación física se realizó sobre una maqueta | Los resultados confirman funcionamiento a escala de laboratorio, pero no sustituyen pruebas sobre un reservorio real |
| La superficie del agua se representó mediante una plataforma móvil | Permite una prueba repetible del sensor ultrasónico, pero no reproduce fenómenos como oleaje o reflexiones irregulares |
| La irradiancia se obtiene mediante un panel fotovoltaico e INA219 | La lectura funciona como estimación; una medición precisa en W/m² requeriría calibración con un instrumento de referencia |
| Los umbrales son parámetros iniciales de diseño | Deben ajustarse con datos reales de la región y del reservorio donde se instale el sistema |
| No se cubrieron todos los valores exactos de borde de los umbrales | Podrían realizarse pruebas adicionales específicamente sobre cada límite matemático |
| El extremo lleno del rango (3 cm) cae dentro de la zona ciega del sensor ultrasónico: por debajo de ~5 cm el transductor sigue resonando por su propio pulso cuando ya retorna el eco | Se observaron lecturas fallidas ocasionales con la plataforma en posición alta. Elevar el sensor por encima de 10 cm alargaría además el recorrido y reduciría el peso relativo del ruido |
| La escala temporal del banco de pruebas difiere en dos órdenes de magnitud de la de campo | Con el ruido y la geometría del montaje, la banda muerta supera ampliamente los umbrales que tendrían sentido en un reservorio real; ese régimen exigiría un transductor de presión sumergible o un sensor radar |
| No se caracterizó el consumo energético | El diseño contempla alimentación por panel y batería, pero no se midió el consumo por modo ni se dimensionó la autonomía; queda pendiente implementar *deep sleep* con despertar por alarma |
| **(Ch. #2)** El Wi-Fi opera sin ahorro de energía | Necesario para que el tablero responda siempre con hotspots de celular, pero aumenta el consumo y reduce la autonomía con pilas |
| **(Ch. #2)** El tablero va por HTTP, sin TLS | La clave viaja una vez al iniciar sesión y solo la protege el WPA2 de la WLAN; las sesiones se pierden si el equipo se reinicia |
| **(Ch. #2)** Las redes Wi-Fi van grabadas en el firmware (hasta dos) | Usar otra red exige reprogramar el equipo |
| **(Ch. #2)** El modo demo supone que la luz medida es la del mediodía de un día típico de 12 h | Sirve para pruebas cortas; el valor de campo sale de la ventana de 24 h, que tarda 12 h en estar disponible |
| **(Ch. #2)** El banco de pruebas no es un embalse | Valida la cadena de cálculo y la respuesta del índice evaporativo, no los mm/día absolutos; G ≈ 0 es un supuesto que no se cumple en agua profunda |
| **(Ch. #2)** Umbrales de evaporación 60 / 85 sin datos locales | Siguen siendo un supuesto; el método para cerrarlos (percentiles de una estación del IDEAM) queda como trabajo futuro |
| **(Ch. #2)** La referencia de humedad y temperatura es del mismo orden de exactitud que el BME280 | La comparación es una verificación de consistencia, no una calibración formal |
| **(Ch. #2)** La caja impresa corresponde a una versión anterior del diseño | La tapa no ajusta, el USB-C no queda accesible, toca poner los componentes más apretados |

---

## 6.4 Evaluación del prototipo físico

La implementación física permitió validar aspectos que no podían comprobarse completamente en simulación.

Entre ellos:

- estabilidad de las lecturas del sensor ultrasónico;
- funcionamiento real del bus I²C;
- lectura del BME280;
- interacción entre panel fotovoltaico e INA219;
- visibilidad de la información en la LCD;
- actuación física de los LEDs;
- funcionamiento del buzzer;
- respuesta integrada del ESP32 ante cambios de nivel.

Uno de los aspectos más importantes fue comprobar que los estados calculados por el algoritmo producen una respuesta física coherente.

```text
NORMAL
→ LED verde
→ buzzer apagado

PRECAUCIÓN
→ LED amarillo
→ alerta visual

CRÍTICO
→ LED rojo
→ buzzer activo
```

---

## 6.5 Conclusión de la autoevaluación

El protocolo aplicado permitió validar satisfactoriamente el objetivo central de WREWS: **adquirir múltiples variables, procesarlas localmente, fusionar la información y generar alertas tempranas coherentes ante diferentes escenarios de riesgo hídrico**.

La combinación de simulación y prototipado físico fortaleció la validación, ya que permitió comprobar tanto la lógica matemática del sistema como su comportamiento real utilizando sensores y actuadores.

Las principales limitaciones restantes corresponden a una futura validación de campo, calibración metrológica y pruebas prolongadas, no al funcionamiento básico del prototipo presentado.

En el Challenge #2 el protocolo se amplió a los bloques que exige el enunciado (calibración, emulación acelerada, fusión, notificación, robustez y desempeño). Su valor principal estuvo en que **encontró fallas reales que se corrigieron**: la saturación del índice evaporativo con sol real en modo demo, el falso positivo de CRÍTICO por evaporación con el tubo lleno, el tablero que no se recuperaba tras una caída de la WLAN y el tono de crítico que el buzzer no podía reproducir.

---

## 6.6 Autoevaluación del protocolo del Challenge #3

| Criterio del enunciado | ¿Se cumple? | Evidencia / observación |
|---|---|---|
| Medición y transmisión en hilos independientes del principal | ✅ Sí | `tareaMedicion` y `tareaMqtt` (sección 3.21); con el broker caído la alarma local siguió igual (prueba 9) |
| Datos almacenados en una base local antes de la nube (SQLite) | ✅ Sí | El gateway guarda cada mensaje antes de procesarlo; la nube sale de `cola_nube` (pruebas 1 y 2) |
| Procesamiento local en el gateway | ✅ Sí | Validación por variable, anomalías con z robusto, ventanas de 60 s, vigilancia del enlace. Detectó en real las 59 lecturas imposibles del BME280 |
| MQTT dispositivo ↔ gateway y gateway ↔ nube | ✅ Sí | Mosquitto local y Ubidots por MQTT con TLS |
| Tablero global con valor actual, histórico y alertas | ✅ Sí | Tablero de Ubidots con medidor, gráficas, estado, tabla de la IA y switch |
| Notificaciones ante eventualidades | ✅ Sí | Eventos de Ubidots (SMS hasta agotar el cupo, correo) y avisos por Telegram |
| Desactivar la alarma física desde la nube | ✅ Sí | Switch de Ubidots → `ok: 1` (prueba 4) |
| Acceso restringido a usuarios autorizados | ✅ Sí | Broker con usuario, clave y ACL; Ubidots privado; bot con clave y aprobación |
| Módulo de IA (predicción, anomalías o recomendación) | ✅ Sí | Regresión propia (minutos hasta el 15 %), anomalías en el gateway y recomendación con Claude, con respaldo por reglas |
| Caída de Internet: datos guardados y enviados después | ✅ Sí | En la Pi: corte de 8 min de la red y corte de Internet; 10 mensajes guardados en SQLite y subidos con su hora al volver, cola en 0 (prueba 7) |
| Latencia de extremo a extremo medida | ✅ Sí | Gateway → Ubidots: mediana 0,8 s; cambio de estado → Telegram: unos 2 s; ESP32 caído detectado en 20,5–21 s; silenciar: 15–56 ms (pruebas 4, 8 y 10) |
| Funcionamiento en la Raspberry Pi | ✅ Sí | 13/11/2026: Raspberry Pi 5 instalada con un solo script en unos 10 min; 4 horas de operación con el prototipo real (1477 mediciones) |

**Fortalezas.** Las pruebas se hicieron primero con un simulador, luego con el prototipo real y un PC como gateway, y por último en la Pi, para que cada falla tuviera una sola causa posible. Las pruebas automáticas del gateway (22) cubren los casos difíciles de reproducir a mano, como un switch viejo de Ubidots o una clave errada en el bot. Las pruebas reales encontraron tres fallas que la simulación no mostraba (sección 5.8) y quedaron corregidas.

**Limitaciones.** No hubo prueba de larga duración (horas o días) del gateway. La latencia se midió con las marcas de tiempo del gateway y no con un cronómetro externo, así que no incluye el tramo ESP32 → gateway dentro de la misma WLAN. La orden de silenciar desde la consola de la Pi no se alcanzó a ejecutar. Si el gateway se apaga, los mensajes de ese intervalo no se recuperan: Mosquitto no los guarda para el gateway (ver 7.3).

---

[⬅ Anterior: Configuración experimental y resultados](05-Configuracion-Experimental-Resultados.md) · [⬆ Índice](00-Home.md) · [Siguiente: Conclusiones y trabajo futuro ➡](07-Conclusiones-Trabajo-Futuro.md)
