"""
WREWS - Carcasa v16 (medidas reales del portapilas y la mini proto, con holgura extra para imprimir sin sustos)
Challenge #2 IoT - U. de La Sabana. CadQuery, medidas en mm.

- Nivel de abajo: el OKY centrado sobre el tubo. Atrás, el buzzer (lado del ESP32) y el interruptor ON/OFF
  (lado de la protoboard). Buzzer, interruptor y USB-C tienen capucha con el borde inclinado.
- Nivel de arriba (piso intermedio): ESP32 (izq.), portapilas 4 AA (centro) y mini protoboard (der.).
- Frente: LCD con techo y 3 LEDs separados, cada uno con su aro.
- Atrás: cápsula del BME280 con piso propio (el sensor va acostado en el piso), persianas,
  ménsula a 45° por debajo (se imprime sin soportes) y un techito que se inserta desde arriba.
- Tapa: techo de 4 aguas con alero, rayos de sol en relieve y plataforma para el panel.
- Acople a presión (costillas + tope), con canal para los pines del OKY.

Piezas: 1_prueba_ajuste_tubo, 2_acople_tubo, 3_tapa, 4_caja, 5_piso_intermedio, 6_techo_bme
Las medidas marcadas [MEDIR] se ajustan cuando estén los materiales (todo de Zamux).
"""
import cadquery as cq
import math, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")
os.makedirs(OUT, exist_ok=True)

HOLGURA = 0.4
# Tubo y acople
PVC_OD = 82.56
BRIDA_D, BRIDA_TORN_R = 96.0, 38.0
ANG_TORN = (90, 270)
MANGA_ALTO, TOPE_Z, COSTILLA_INTERF = 45.0, 15.0, 0.4
# OKY3261 / HC-SR04 -- medido: PCB 46x20.5, radio del transductor 16, separación entre círculos 10.2
US_TRANSD_D, US_TRANSD_CC = 16.0, 26.2
US_PCB = (46.0, 20.5)
PINES_CANAL = (14.0, 24.0)

# Caja -- v14: el portapilas real (61.5x52.6 mm) es mucho mas grande en huella que lo que se habia
# asumido (31x58 mm), asi que el ancho (INT_L) crece de 104 a 130 mm para que quepa junto a la mini
# proto con holgura de sobra (no justo al limite). La profundidad (INT_A) tambien crece un poco (100->104)
# para dar mas aire al cableado del frente.
PARED, PISO = 3.0, 3.0
INT_L, INT_A, INT_H = 130.0, 104.0, 70.0
EXT_L, EXT_A, EXT_H = INT_L + 2 * PARED, INT_A + 2 * PARED, INT_H + PISO
R_ESQ = 10.0
BOSS_D, TORN_PILOTO, TORN_PASO = 9.0, 2.8, 3.4
HOMBRO_D = 14.0

# Frente -- LCD medido: pantalla visible 71.1x24.3, módulo 80.2x36.2, ancho con jumpers 92.2 (cabe con
# margen en los 104 de ancho interior; el resto de la ventana se calcula solo a partir de este tamaño)
LCD_VENTANA = (76.1, 29.3)                    # pantalla real 71.1x24.3 + 5 mm de margen de montaje (mas holgado)
Z_LCD = PISO + 42.0
LED_D = 5.2
LEDS_X = (-18.0, 0.0, 18.0)                   # bien separados, cada uno con su aro
Z_FILA = PISO + 16.0

# Atrás (vista desde atrás: interruptor a un lado, buzzer al otro, cápsula al centro)
X_ATRAS = 30.0
Z_ATRAS = PISO + 13.0
INTERRUPTOR = (22.0, 16.0)                    # switch balancin 3 pines "normal" (foto) + margen holgado
BUZZER_D = 12.0                               # medido: diametro 12 mm (el "radio 12" era diametro), alto 9 mm
BUZZER_H = 9.0
MARCO_SW = (29.0, 23.0)                       # marco del interruptor, agrandado con mas margen
MARCO_BUZ = (22.0, 22.0)                      # marco del buzzer, con un poco mas de margen sobre el Ø12 real
CASA = (30.0, 24.0, 28.0)                     # cápsula BME: ancho, salida, alto (el chip mide 13.1x10.5, sobra espacio)
CABLE_D = 5.0

# Piso intermedio -- ahora un solo bloque "PROTO" (protoboard con el ESP32 y el INA219 ya montados
# encima, medido con todo puesto) en vez de cuna de ESP32 + mini protoboard por separado.
# PROTO: ancho x largo x alto. El largo (86, con el conector USB-C incluido) va de frente hacia atrás,
# con el USB-C mirando a la pared trasera igual que antes. El alto (25) es el punto más alto: la INA219.
PISO2_Z = PISO + 26.0
PISO2_T = 3.0
FRENTE_LIBRE = 14.0                           # un poco mas de aire que en v13 para el cableado del frente
PISO2_Y0 = -INT_A / 2 + FRENTE_LIBRE
BORDE, BORDE_ALTO, BASE_ESP = 1.2, 3.0, 3.0
# Mini proto (ESP32+INA219 montados): medida real 85 x 56 mm -- casi igual a lo que ya teniamos, se le
# deja unos mm extra de margen para no ir exactos.
PROTO = (59.0, 89.0, 27.0)
PROTO_CX = INT_L / 2 - 1.0 - BORDE - PROTO[0] / 2
USB_RANURA = (16.0, 10.0)                     # [MEDIR] conector USB-C del cable (parte blanca) + margen holgado
USB_Z = PISO2_Z + PISO2_T + 10.0              # [MEDIR] altura del puerto USB-C del ESP32 ya montado en la proto
USB_OFF_X = 8.7                              # [MEDIR] desplazamiento en X del puerto dentro del ancho de la proto,
                                               # para que el hueco no choque con el interruptor -- verificar con la proto armada
# Portapilas real: 61.5 x 52.6 x 15 mm (mucho mas ancho/plano que lo que se habia asumido antes).
# Se orienta con el lado corto (52.6) a lo ancho de la caja (X) para que quepa junto a la proto, y el
# lado largo (61.5) a lo profundo (Y), que es donde sobra espacio. +3 mm de margen en cada lado.
PILAS = (55.6, 64.5, 18.0)
PILAS_CX = -INT_L / 2 + 1.0 + BORDE + PILAS[0] / 2
PILAS_Y0 = PISO2_Y0 + 3.0

# Tapa y panel -- medido: panel cuadrado 60.5x60.5, algo más de 6 mm de grueso
PANEL_LADO = 60.5
PANEL_ALTO = 7.0                              # [MEDIR] grosor real del panel; el bolsillo le deja 3 mm extra
TECHO_ALTO = 6.0
ALERO = 1.5                                   # la tapa sobresale 1,5 mm (gotero)


def exportar(obj, nombre):
    cq.exporters.export(obj, os.path.join(OUT, nombre + ".stl"), tolerance=0.05, angularTolerance=0.1)
    print("ok ->", nombre)


def esquinas():
    return [(sx * (INT_L / 2 - BOSS_D / 2 + 1), sy * (INT_A / 2 - BOSS_D / 2 + 1)) for sx in (-1, 1) for sy in (-1, 1)]


def rrect(w, h, alto, r):
    return cq.Workplane("XY").box(w, h, alto, centered=(True, True, False)).edges("|Z").fillet(r)


def anillo_costillas(interf, alto=8):
    r_in = (PVC_OD + 1.0) / 2
    a = cq.Workplane("XY").circle(r_in + 3).circle(r_in).extrude(alto)
    r_cost = PVC_OD / 2 - interf / 2
    for k in range(6):
        ang = math.radians(60 * k)
        prof = r_in - r_cost
        cost = (cq.Workplane("XY").rect(prof * 2 + 0.01, 2.2).extrude(alto)
                .edges("|Z").fillet(0.5)
                .translate((r_in, 0, 0)).rotate((0, 0, 0), (0, 0, 1), 60 * k))
        a = a.union(cost)
    return a


def prueba_ajuste_tubo():
    paso = PVC_OD + 12
    pos = [(0, 0, 0), (paso, 0, 0), (paso / 2, -paso * 0.87, 0)]
    piezas = None
    for i, interf in enumerate([0.2, 0.4, 0.6]):     # 1, 2 y 3 muescas = flojo, medio, apretado
        r = anillo_costillas(interf).translate(pos[i])
        r_out = (PVC_OD + 1.0) / 2 + 3
        for k in range(i + 1):
            r = r.cut(cq.Workplane("XY").box(2, 3, 3).translate((pos[i][0] + (k - i / 2) * 4, pos[i][1] + r_out, 7)))
        piezas = r if piezas is None else piezas.union(r)
    return piezas



def capsula_dims():
    cl, cs, ch = CASA
    return cl, cs, ch, EXT_A / 2, EXT_H - ch - 6


def capucha(x, zc, W, H, fondo_arriba=7.0, fondo_abajo=1.2, pared=2.0, r=5.0):
    """Marco hueco de esquinas redondas pegado a la pared de atrás. Sale `fondo_arriba` mm arriba y
    `fondo_abajo` mm abajo: el borde queda inclinado y la parte de arriba hace de techito."""
    by = EXT_A / 2
    z0, z1 = zc - H / 2, zc + H / 2
    perfil = (cq.Workplane("YZ").polyline([(by - 0.5, z0), (by + fondo_abajo, z0), (by + fondo_arriba, z1), (by - 0.5, z1)])
              .close().extrude(W + 2).translate((x - W / 2 - 1, 0, 0)))
    tubo = (cq.Workplane("XZ").rect(W, H).extrude(-(fondo_arriba + 2)).edges("|Y").fillet(r)
            .translate((x, by - 0.5, zc)))
    hueco = (cq.Workplane("XZ").rect(W - 2 * pared, H - 2 * pared).extrude(-(fondo_arriba + 4)).edges("|Y")
             .fillet(max(r - pared, 0.8)).translate((x, by - 1, zc)))
    return tubo.intersect(perfil).cut(hueco)


def caja():
    c = rrect(EXT_L, EXT_A, EXT_H, R_ESQ).faces("<Z").edges().fillet(1.5)
    c = c.cut(rrect(INT_L, INT_A, INT_H + 1, R_ESQ - PARED).translate((0, 0, PISO)))
    for (x, y) in esquinas():
        c = c.union(cq.Workplane("XY").circle(HOMBRO_D / 2).extrude(PISO2_Z - PISO).translate((x, y, PISO)))
        c = c.union(cq.Workplane("XY").circle(BOSS_D / 2).extrude(INT_H).translate((x, y, PISO)))
        c = c.cut(cq.Workplane("XY").circle(TORN_PILOTO / 2).extrude(20).translate((x, y, EXT_H - 18)))
        c = c.cut(cq.Workplane("XY").circle(TORN_PILOTO / 2).extrude(8).translate((x, y, PISO2_Z - 7)))
    for sx in (-1, 1):
        prof = 7.0
        tri = (cq.Workplane("XZ").polyline([(0, 0), (-sx * prof, 0), (0, -prof)]).close().extrude(-10)
               .translate((sx * INT_L / 2, PISO2_Y0 + 2, PISO2_Z)))
        c = c.union(tri)
    c = c.intersect(rrect(EXT_L, EXT_A, EXT_H, R_ESQ))

    fy = -EXT_A / 2
    # --- LCD centrado con techo a 45°
    c = c.cut(cq.Workplane("XZ").rect(*LCD_VENTANA).extrude(-20).translate((0, fy - 5, Z_LCD)))
    ancho_t, sal = LCD_VENTANA[0] + 20, 12.0
    z0 = Z_LCD + LCD_VENTANA[1] / 2 + 1
    techo = (cq.Workplane("YZ").polyline([(0, 0), (-sal, sal), (-sal, sal + 3), (0, sal + 3)]).close()
             .extrude(ancho_t).translate((-ancho_t / 2, fy, z0)))
    c = c.union(techo)
    for sx in (-1, 1):
        aleta = (cq.Workplane("YZ").polyline([(0, 0), (-sal, sal), (0, sal)]).close()
                 .extrude(2).translate((sx * ancho_t / 2 - (2 if sx > 0 else 0), fy, z0)))
        c = c.union(aleta)
    marco = (cq.Workplane("XZ").rect(LCD_VENTANA[0] + 8, LCD_VENTANA[1] + 8).rect(LCD_VENTANA[0], LCD_VENTANA[1])
             .extrude(1.2).translate((0, fy, Z_LCD)))
    c = c.union(marco)
    # --- 3 LEDs separados, cada uno con su aro en relieve
    for x in LEDS_X:
        c = c.union(cq.Workplane("XZ").circle(5.0).circle(LED_D / 2 + 0.6).extrude(1.0).translate((x, fy, Z_FILA)))
        c = c.cut(cq.Workplane("XZ").circle(LED_D / 2).extrude(-20).translate((x, fy - 5, Z_FILA)))

    # --- atrás: cápsula del BME280 con piso, persianas y ménsula a 45°
    cl, cs, ch, by, zc = capsula_dims()
    ext = rrect(cl, cs, ch, 4).translate((0, by - 2 + cs / 2, zc))
    mens = (cq.Workplane("YZ").polyline([(by - 2, zc + 0.01), (by - 2 + cs, zc + 0.01), (by - 2, zc - cs)]).close()
            .extrude(cl).translate((-cl / 2, 0, 0)))
    mens = mens.intersect(rrect(cl, cs, ch, 4).translate((0, by - 2 + cs / 2, zc - cs)))
    caps = ext.union(mens)
    inn = cq.Workplane("XY").box(cl - 4, cs - 4, ch, centered=(True, False, False)).translate((0, by, zc + 2))
    caps = caps.cut(inn)
    # v15: se bajó de 5 a 3 persianas (antes se había bajado a 4, pero el hueco del cable seguía
    # quedando pegado al borde de arriba de la cápsula). Con 3 persianas queda una franja limpia de
    # ~12 mm en el centro-alto de la cápsula, lejos tanto de las persianas como del borde/techo,
    # para meter ahí el hueco del cable sin que se vea "metido" en nada.
    for i in range(5):
        z = zc + 4.5 + i * 4.2
        caps = caps.cut(cq.Workplane("XY").box(cl + 10, cs - 9, 1.8).translate((0, by + cs / 2 + 2, z)))
        caps = caps.cut(cq.Workplane("XY").box(cl - 12, 10, 1.8).translate((0, by + cs - 2, z)))
    caps = caps.cut(cq.Workplane("XY").circle(1.2).extrude(4).translate((0, by + cs - 5, zc - 1)))   # drenaje
    c = c.union(caps)
    # hueco del cable del BME: ahora va en el centro de la cápsula, en la franja libre que quedó
    # entre la ultima persiana y el techo (lejos de ambos bordes).
    c = c.cut(cq.Workplane("XZ").circle(CABLE_D / 2).extrude(-20).translate((0, by - 10, zc + ch - 9)))

    # --- atrás: "capuchas" (marcos que salen más arriba que abajo, con el borde inclinado)
    #     para el buzzer, el interruptor y el USB-C: protegen del agua y se imprimen sin soportes
    X_BUZ, X_SW = -X_ATRAS, X_ATRAS
    uw, uh = USB_RANURA
    c = c.union(capucha(X_BUZ, Z_ATRAS, *MARCO_BUZ))
    c = c.union(capucha(X_SW, Z_ATRAS, *MARCO_SW, fondo_arriba=9.0))   # switch balancin: mas fondo para su cuerpo
    c = c.union(capucha(PROTO_CX + USB_OFF_X, USB_Z, uw + 8, uh + 8, fondo_arriba=6.0, r=4.5))
    # interruptor
    c = c.cut(cq.Workplane("XZ").rect(*INTERRUPTOR).extrude(20).translate((X_SW, by + 5, Z_ATRAS)))
    # buzzer: rejilla (radio 12 mm real) + aro por dentro
    for dx in (-3.3, 0, 3.3):
        for dz in (-3.3, 0, 3.3):
            c = c.cut(cq.Workplane("XZ").circle(1.1).extrude(20).translate((X_BUZ + dx, by + 5, Z_ATRAS + dz)))
    c = c.union(cq.Workplane("XZ").circle(BUZZER_D / 2 + 1.6).circle(BUZZER_D / 2).extrude(5)
                .translate((X_BUZ, by - PARED, Z_ATRAS)))
    # USB-C: hueco justo para el conector del cable, alineado con el puerto del ESP32 ya montado en la proto
    c = c.cut(cq.Workplane("XZ").rect(uw, uh).extrude(20).edges("|Y").fillet(uh / 2 - 0.05)
              .translate((PROTO_CX + USB_OFF_X, by + 5, USB_Z)))

    # --- "WREWS" grabado en los dos costados
    for sgn in (-1, 1):
        try:
            pl = cq.Plane(origin=(sgn * EXT_L / 2, 0, EXT_H / 2 - 2), xDir=(0, sgn, 0), normal=(sgn, 0, 0))
            c = c.cut(cq.Workplane(pl).text("WREWS", 12, -0.8, kind="bold", halign="center", valign="center"))
        except Exception as e:
            print("texto omitido:", e)

    # --- piso: OKY + canal de pines, tornillos de la brida, drenaje
    c = c.cut(cq.Workplane("XY").rect(US_PCB[0] + 2, US_PCB[1] + 2).extrude(20).translate((0, 0, -5)))
    c = c.cut(cq.Workplane("XY").box(PINES_CANAL[0], PINES_CANAL[1], 20, centered=(True, False, False))
              .translate((0, US_PCB[1] / 2, -5)))
    for ang_d in ANG_TORN:
        a = math.radians(ang_d)
        c = c.cut(cq.Workplane("XY").circle(TORN_PASO / 2).extrude(20)
                  .translate((BRIDA_TORN_R * math.cos(a), BRIDA_TORN_R * math.sin(a), -5)))
    c = c.cut(cq.Workplane("XY").circle(1.5).extrude(20).translate((0, -INT_A / 2 + 6, -5)))
    return c


def techo_bme():
    """Techito de la cápsula: se inserta desde arriba (el tapón entra en la boca y el alero se apoya)."""
    cl, cs, ch, by, zc = capsula_dims()
    ztop = zc + ch
    y0, y1 = by + 0.2, by - 2 + cs + 1.5                 # no choca con la pared de la caja
    cy = (y0 + y1) / 2
    w = cl + 3
    placa = cq.Workplane("XY").box(w, y1 - y0, 2, centered=(True, True, False)).edges("|Z").fillet(3).translate((0, cy, ztop))
    loft = (cq.Workplane("XY").workplane(offset=ztop + 2).center(0, cy).rect(w, y1 - y0)
            .workplane(offset=3).rect(w - 14, y1 - y0 - 14).loft())
    loft = loft.intersect(cq.Workplane("XY").box(w, y1 - y0, 5, centered=(True, True, False)).edges("|Z").fillet(3)
                          .translate((0, cy, ztop + 2)))
    t = placa.union(loft)
    ix, iy = cl - 4 - 0.4, cs - 4 - 0.4
    tapon = (cq.Workplane("XY").box(ix, iy, 4, centered=(True, True, False)).translate((0, by + (cs - 4) / 2, ztop - 4))
             .faces("<Z").shell(-1.4))
    t = t.union(tapon)
    return t


def piso_intermedio():
    y0, y1 = PISO2_Y0, INT_A / 2 - 0.4
    ancho = INT_L - 0.8
    p = (cq.Workplane("XY").box(ancho, y1 - y0, PISO2_T, centered=(True, False, False))
         .edges("|Z").fillet(3).translate((0, y0, 0)))
    z = PISO2_T
    # bandeja de la protoboard (ESP32 + INA219 ya montados), pegada a la pared de atrás
    # para que el conector USB-C del ESP32 quede alineado con la capucha de la pared
    pw, plen, palto = PROTO
    py1p = y1 - 0.2                  # borde trasero de la bandeja, sin sobresalir del piso
    py0p = py1p - plen               # borde delantero
    p = p.union(cq.Workplane("XY").box(pw, plen, BASE_ESP, centered=(True, False, False))
                .translate((PROTO_CX, py0p, z)))
    for xs in (-1, 1):
        p = p.union(cq.Workplane("XY").box(BORDE, plen, BASE_ESP + 2.5, centered=(True, False, False))
                    .translate((PROTO_CX + xs * (pw / 2 + BORDE / 2), py0p, z)))
    # portapilas 4 AA (izquierda, a lo largo): topes adelante/atrás y rieles laterales
    py0, py1 = PILAS_Y0, PILAS_Y0 + PILAS[1] + 0.6
    for yy in (py0 - BORDE, py1):
        p = p.union(cq.Workplane("XY").box(PILAS[0] + 2 * BORDE, BORDE, 6, centered=(True, False, False))
                    .translate((PILAS_CX, yy, z)))
    for xs in (-1, 1):
        p = p.union(cq.Workplane("XY").box(BORDE, py1 - py0 + 2 * BORDE, 6, centered=(True, False, False))
                    .translate((PILAS_CX + xs * (PILAS[0] / 2 + 0.3 + BORDE / 2), py0 - BORDE, z)))
    # ranuras para una cinta de velcro que abraza el portapilas
    for yy in (py0 + 12, py1 - 12):
        p = p.cut(cq.Workplane("XY").rect(PILAS[0] - 4, 3.2).extrude(10).translate((PILAS_CX, yy, -1)))
    # muesca atrás para subir los cables del nivel de abajo (OKY, interruptor, buzzer, BME)
    p = p.cut(cq.Workplane("XY").box(22, y1 - py1 - 1.8, 10, centered=(True, False, False)).edges("|Z").fillet(2)
              .translate((PILAS_CX, py1 + 1.8, -1)))
    # huecos de paso para los tornillos que sujetan la tapa (se cortan al final, después de las bandejas,
    # para que ninguna bandeja les reponga material)
    for (x, y) in esquinas():
        if y > 0:
            p = p.cut(cq.Workplane("XY").circle(BOSS_D / 2 + 0.4).extrude(20).translate((x, y, -5)))
    return p.translate((0, 0, PISO2_Z))


def tapa():
    L, A, R = EXT_L + 2 * ALERO, EXT_A + 2 * ALERO, R_ESQ + ALERO
    base = rrect(L, A, 3, R).edges(">Z").chamfer(0.8)
    top_w = PANEL_LADO + 16
    zt = 3 + TECHO_ALTO

    def techo(dz=0.0):
        lo = (cq.Workplane("XY").workplane(offset=3 + dz).rect(L, A)
              .workplane(offset=TECHO_ALTO).rect(top_w, top_w).loft())
        return lo.intersect(rrect(L, A, 3 + TECHO_ALTO + dz + 1, R))
    t = base.union(techo())
    # sol: 24 rayos triangulares en relieve (1 mm) que bajan por el techo, largos y cortos alternados
    zona = techo(1.0).union(rrect(L, A, 1.0, R).translate((0, 0, 3)))
    zona = zona.intersect(rrect(L - 6, A - 6, 20, R - 3))
    rayos = None
    for k in range(24):
        ang = math.radians(k * 15)
        c_, s_ = math.cos(ang), math.sin(ang)
        r0 = (top_w / 2 + 3.4) / max(abs(c_), abs(s_))
        r_borde = min(L / 2 / max(abs(c_), 1e-6), A / 2 / max(abs(s_), 1e-6))
        diagonal = abs(abs(c_) - abs(s_)) < 0.2
        if k % 2 == 0:
            largo, w0 = r_borde - 3.5, 5.0
        else:
            largo, w0 = r0 + (0.35 if diagonal else 0.6) * (r_borde - r0), 3.4
        pts = [(r0, -w0 / 2), (largo, -0.3), (largo, 0.3), (r0, w0 / 2)]
        pl = cq.Workplane("XY").polyline(pts).close().extrude(30).rotate((0, 0, 0), (0, 0, 1), k * 15)
        rayos = pl if rayos is None else rayos.union(pl)
    t = t.union(rayos.intersect(zona))
    # plataforma del panel con bisel y bolsillo: la plataforma se hace más alta que antes para que el
    # bolsillo (grosor real del panel + 3 mm de holgura) quepa completo sin perforar el techo hacia abajo
    bolsillo_prof = PANEL_ALTO + 4.0
    plat_alto = bolsillo_prof + 1.5            # 1,5 mm de piso debajo del bolsillo
    plat = (cq.Workplane("XY").rect(PANEL_LADO + 8, PANEL_LADO + 8).extrude(plat_alto).edges(">Z").chamfer(1.0)
            .translate((0, 0, zt)))
    t = t.union(plat)
    t = t.cut(cq.Workplane("XY").rect(PANEL_LADO + 1.2, PANEL_LADO + 1.2).extrude(bolsillo_prof)
              .translate((0, 0, zt + plat_alto - bolsillo_prof)))
    ranura = (cq.Workplane("XY").rect(top_w + 4, top_w + 4).rect(top_w + 2.4, top_w + 2.4).extrude(3)
              .translate((0, 0, zt - 1.4)))
    t = t.cut(ranura)
    # labio que encaja en la caja
    labio = rrect(INT_L - 0.8, INT_A - 0.8, 4, R_ESQ - PARED - 0.4).cut(rrect(INT_L - 4.8, INT_A - 4.8, 4, 2))
    t = t.union(labio.translate((0, 0, -4)))
    for (x, y) in esquinas():
        t = t.cut(cq.Workplane("XY").circle(BOSS_D / 2 + 1).extrude(4.5).translate((x, y, -4.5)))
        t = t.cut(cq.Workplane("XY").circle(TORN_PASO / 2).extrude(20).translate((x, y, -6)))
        t = t.cut(cq.Workplane("XY").circle(3.2).extrude(10).translate((x, y, 1.6)))
    for x in (-4, 4):
        t = t.cut(cq.Workplane("XY").circle(1.8).extrude(20).translate((x, 0, -6)))
    return t


def acople_tubo():
    brida = cq.Workplane("XY").circle(BRIDA_D / 2).extrude(5).edges(">Z or <Z").chamfer(0.8)
    r_in = (PVC_OD + 1.0) / 2
    manga = cq.Workplane("XY").circle(r_in + 3.5).circle(r_in).extrude(MANGA_ALTO).translate((0, 0, -MANGA_ALTO))
    a = brida.union(manga)
    # costillas de presión (desde el tope hasta la boca)
    r_cost = PVC_OD / 2 - COSTILLA_INTERF / 2
    prof = r_in - r_cost
    largo = MANGA_ALTO - TOPE_Z
    for k in range(6):
        cost = (cq.Workplane("XY").rect(prof * 2 + 0.01, 2.2).extrude(largo).edges("|Z").fillet(0.5)
                .translate((r_in, 0, -MANGA_ALTO)).rotate((0, 0, 0), (0, 0, 1), 60 * k + 30))
        a = a.union(cost)
    # tope interno con chaflán de 45° por debajo (imprimible sin soportes)
    r_led = PVC_OD / 2 - 3
    z_apoyo = -TOPE_Z - 2
    perfil = [(r_led, z_apoyo), (r_in + 0.2, z_apoyo), (r_in + 0.2, z_apoyo + 1 + (r_in - r_led) + 0.2), (r_led, z_apoyo + 1)]
    tope = cq.Workplane("XZ").polyline(perfil).close().revolve(360, (0, 0, 0), (0, 1, 0))
    a = a.union(tope)
    # tornillos a la caja (3, a 90°, 210° y 330°: caen en zonas libres del piso)
    for ang_d in ANG_TORN:
        ang = math.radians(ang_d)
        a = a.cut(cq.Workplane("XY").circle(TORN_PASO / 2).extrude(20)
                  .translate((BRIDA_TORN_R * math.cos(ang), BRIDA_TORN_R * math.sin(ang), -5)))
    # OKY: cápsulas y cajeado de la tarjeta
    for sx in (-1, 1):
        a = a.cut(cq.Workplane("XY").circle(US_TRANSD_D / 2 + 0.3).extrude(20).translate((sx * US_TRANSD_CC / 2, 0, -10)))
    a = a.cut(cq.Workplane("XY").rect(US_PCB[0] + 0.6, US_PCB[1] + 0.6).extrude(2).translate((0, 0, 3.01)))
    # canal para los 4 pines del OKY (salen de lado, hacia atrás) y sus conectores dupont
    a = a.cut(cq.Workplane("XY").box(PINES_CANAL[0], PINES_CANAL[1], 3.2, centered=(True, False, False))
              .translate((0, US_PCB[1] / 2, 5 - 3.2)))
    # respiraderos: por encima del tope, siempre libres
    for ang in (0, 180):
        a = a.cut(cq.Workplane("YZ").circle(2.0).extrude(r_in + 10, both=True)
                  .rotate((0, 0, 0), (0, 0, 1), ang + 90).translate((0, 0, -TOPE_Z / 2)))
    return a



if __name__ == "__main__":
    import sys
    piezas = {"1_prueba_ajuste_tubo": prueba_ajuste_tubo, "2_acople_tubo": acople_tubo, "3_tapa": tapa,
              "4_caja": caja, "5_piso_intermedio": piso_intermedio, "6_techo_bme": techo_bme}
    for n, f in piezas.items():
        if len(sys.argv) == 1 or any(a in n for a in sys.argv[1:]):
            exportar(f(), n)
