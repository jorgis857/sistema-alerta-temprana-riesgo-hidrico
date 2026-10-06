# WREWS – Carcasa v16 (el USB-C ya no choca con la cápsula del BME)

La caja mide **136 × 110 × 73 mm**. Reemplaza la v15. Son las 6 piezas completas, listas para imprimir.

## Qué cambió respecto a la v15

El problema real no era el agujerito de los cables del BME: era **el hueco del USB-C con su capucha**, que al ensanchar la caja en la v14 quedó justo encima de la cápsula del BME (la capucha del USB ocupaba X 1–25 mm y la cápsula X −15 a 15 mm, a la misma altura). Por eso en los intentos anteriores seguía viéndose igual.

- El hueco del USB-C se movió a **X = 42 mm** (hacia el lado de la proto, lejos del centro). Ahora queda **15 mm separado de la cápsula del BME** y 3 mm antes del tornillo de la esquina. Sigue estando dentro del ancho de la mini proto.
- Se devolvieron las **5 persianas** de la cápsula y el agujero de cables del BME a su posición original (nunca fueron el problema).
- Las 6 piezas se regeneraron y todas dan watertight = True.

**Importante al armar:** pongan el ESP32 en la mini proto de forma que su puerto USB-C quede mirando a la pared de atrás y corrido hacia el lado de afuera (a unos 9 mm del centro de la proto, hacia la pared lateral). Si al armar queda en otro lado, me dicen la medida y lo ajusto, o se usa un cable USB-C un poco más largo por dentro.

## Por qué la caja quedó más ancha que en versiones anteriores (heredado de la v14)

El portapilas real mide **61,5 × 52,6 × 15 mm** — mucho más grande en huella (y más plano) que lo que se había asumido antes (31 × 58 × 30 mm). Con el ancho anterior (104 mm interior) el portapilas real y la mini proto (85 × 56 mm) no cabían lado a lado sin chocar. Por eso el ancho interior pasó de 104 a 130 mm.

Además, a todo se le dejó margen de sobra, no medidas justas:

| Elemento | Medida real | Medida usada en el modelo | Margen |
|---|---|---|---|
| Mini proto (ESP32+INA219) | 85 × 56 mm | 89 × 59 mm | +3–4 mm |
| Portapilas 4×AA | 61,5 × 52,6 mm | 64,5 × 55,6 mm (lado corto hacia el ancho de la caja) | +3 mm |
| Interruptor (balancín 3 pines, foto) | ~19×13 mm el cuerpo | hueco 22×16 mm, marco 29×23 mm, capucha con 9 mm de fondo | holgado a propósito |
| Ventana LCD | pantalla 71,1×24,3 mm | 76,1×29,3 mm | +5 mm |
| Ranura USB-C | conector real | 16×10 mm | +1,5 mm más que en v13 |
| Bolsillo del panel solar | grosor real + 3 mm | grosor real + 4 mm | +1 mm más |

Entre la bandeja de la proto y la del portapilas quedan 11 mm de separación, y 2,2 mm de margen a cada pared lateral (más el borde estructural de 1,2 mm).

## Piezas (en `stl/`)

| # | Archivo | Tiempo aprox. | Cómo imprimir |
|---|---|---|---|
| 1 | `1_prueba_ajuste_tubo.stl` | 40 min | Plano. Es opcional |
| 2 | `2_acople_tubo.stl` | 2–3 h | Brida sobre la cama |
| 3 | `3_tapa.stl` | 2–3 h | Techo hacia arriba, con soportes solo desde la cama (debajo del labio) |
| 4 | `4_caja.stl` | 8–10 h | Piso sobre la cama, sin soportes |
| 5 | `5_piso_intermedio.stl` | 1 h | Plano sobre la cama, sin soportes |
| 6 | `6_techo_bme.stl` | 15 min | El tapón hueco va sobre la cama; el techito queda arriba |

Material PETG o ASA, capa de 0,2 mm, 3–4 perímetros y relleno de 30–40 %. La `4_caja` es la que más tarda — arráncenla primero.

## Lo que sigue pendiente (sin tocar, para más adelante)

- Posición real del USB-C (`USB_OFF_X`, estimado en -20).
- Grosor real del panel solar (`PANEL_ALTO`, estimado en 7 mm).
- El layout donde el ESP32 queda "metido en la del BME" — sigue anotado para reorganizar en otra versión, no era urgente para imprimir mañana.
