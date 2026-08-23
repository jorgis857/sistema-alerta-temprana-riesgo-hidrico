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
| No se ejecutó una prueba prolongada de operación continua | No se evaluó el comportamiento del sistema durante varios días de funcionamiento |
| No se cubrieron todos los valores exactos de borde de los umbrales | Podrían realizarse pruebas adicionales específicamente sobre cada límite matemático | El extremo lleno del rango (3 cm) cae dentro de la zona ciega del sensor ultrasónico | Por debajo de ~5 cm el transductor sigue resonando por su propio pulso cuando ya retorna el eco. Se observaron lecturas fallidas ocasionales con la plataforma en posición alta | Elevar el sensor de modo que el extremo lleno quede por encima de 10 cm; esto alarga además el recorrido y reduce el peso relativo del ruido |
| La escala temporal del banco de pruebas difiere en dos órdenes de magnitud de la de campo | Con el ruido y la geometría del montaje, la banda muerta supera ampliamente los umbrales que tendrían sentido en un reservorio real, por lo que ese régimen no es alcanzable con este sensor | Migrar a un transductor de presión sumergible o sensor radar, cuya resolución permite ventanas de estimación de horas |
| No se caracterizó el consumo energético | El diseño contempla alimentación por panel y batería, pero no se midió el consumo por modo ni se dimensionó la autonomía | Medir consumo en operación y reposo; implementar *deep sleep* con despertar por condición de alarma |

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

---

[⬅ Anterior: Configuración experimental y resultados](05-Configuracion-Experimental-Resultados.md) · [⬆ Índice](00-Home.md) · [Siguiente: Conclusiones y trabajo futuro ➡](07-Conclusiones-Trabajo-Futuro.md)
