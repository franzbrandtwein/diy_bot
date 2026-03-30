#!/usr/bin/env python3
"""
Gewächshaus FreeCAD Model Builder – Aufklappbares Pultdach
Verbindungsmethode: Ausklinkungen (Klauen-/Zapfenverbindungen mit Schraubensicherung)

  Typ 1 – Vollausklinkung (Eckknoten Boden + Obergurt):
    Längsriegel (L/R) laufen durch (volle Länge), Querriegel (V/H) erhalten
    an beiden Enden eine 50x50 mm Kerbe -> bündige, formschlüssige Verbindung.
    Sicherung: 1x M8x60 von oben durch den Kreuzungspunkt.

  Typ 2 – Halbausklinkung / Überblattung (Kreuzknoten Zwischenpfetten):
    Beide Profile auf 25 mm Tiefe ausgeklinkt -> greifen ineinander.
    Sicherung: 1x M8x40.

  Typ 3 – Stiel-auf-Rahmen (Bodenknoten):
    50x50x25 mm Zapfensitz (Tasche) in OG des Bodenrahmen-Längsriegels.
    Stiel-Unterkante als Zapfen eingestellt.
    Sicherung: 2x M8x60 seitlich durch Bodenrahmen in den Stiel.

  Typ 4 – Obergurt auf Stiel (Kopfknoten):
    Stielkopf auf 25 mm Länge zu 50x25 mm abgefräst (Zapfen).
    Obergurt-Längsriegel hat 50x25x25 mm Tasche.
    Sicherung: 1x M10x80 von oben.

Ausführung: echo "exec(open('freecad_model.py').read()); quit()" | FreeCAD -c
"""

import cadquery as cq
from cadquery import Compound
import math
import os

OUT = os.environ.get("GWH_PROJECT_DIR", "/home/herrvorragend/projekte/gewaechshaus")
os.makedirs(OUT, exist_ok=True)

# === Maße =================================================================
# Parameter werden von params.py importiert (Web-Konfigurator)
try:
    import sys as _sys; _sys.path.insert(0, OUT)
    from params import B, T, H, OVER, P
    try:
        from params import DOOR_FRONT, DOOR_BACK, DOOR_LEFT, DOOR_RIGHT
    except ImportError:
        DOOR_FRONT = True; DOOR_BACK = False; DOOR_LEFT = False; DOOR_RIGHT = False
    del _sys
except ImportError:
    B = 1200; T = 1200; H = 2200; OVER = 300; P = 50
    DOOR_FRONT = True; DOOR_BACK = False; DOOR_LEFT = False; DOOR_RIGHT = False
P2       = P // 2 # = 25 mm  Ausklinkungstiefe / Zapfenlänge
DW_SINGLE = (B - P) // 2    # = 575 mm lichte Breite je Flügel
DW       = B                # = 1200 mm Gesamtbreite (volle Breite, zweiflügelig)
DH       = 1900             # Türhöhe (licht)
DT_P     = 30               # Türflügel-Rahmenprofil 30×30 mm
MITTELSTIEL_X = B // 2 - P // 2   # = 575 mm (X-Startpos. Mittelstiel)
CW       = 25     # Klemmschiene Breite
CH       = 10     # Klemmschiene Höhe
# DX entfällt – Tür über volle Breite
DX       = 0

# === Holzdielenboden ========================================================
QT_H    = 60    # Querträger KVH 60x60 – Höhe (mm)
QT_B    = 60    # Querträger-Breite (mm)
N_QT    = 4     # Anzahl Querträger
PLANK_T = 22    # Dielendicke Lärche (mm)
PLANK_W = 116   # Dielenbreite nominell ~120 mm
N_PL    = 9     # Anzahl Dielen
PL_GAP  = 4     # Fuge zwischen Dielen (mm)
TH_H    = 40    # Trittholm-Höhe (mm)
TH_D    = 80    # Trittholm-Tiefe (mm)

# Stielkopf-Zapfen (Typ 4): Zapfen z = H-P .. H-P+P2 = 2150..2175
# Stiel endet bei z = H-P+P2 = H-P2 = 2175 mm
STIEL_H  = H - P2   # = 2175 mm

# === Pultdach =============================================================
OVER     = OVER            # Dachüberstand auf allen 4 Seiten (mm) – aus params.py
SLOPE    = 200 / 1200  # Dachneigung mm/mm (9.5 Grad, unveraendert)
H_DACH_V = H - int(OVER * SLOPE)     # = 2150 mm  (Vorderkante, Traufe)
H_DACH_H = 2400 + int(OVER * SLOPE)  # = 2450 mm  (Hinterkante, Scharnierpunkt)
RISE     = H_DACH_H - H_DACH_V        # = 300 mm  (Höhendiff. Dachrahmen 1800mm)

HNG_W = 100;  HNG_D = 20;  HNG_H = (H_DACH_H - H) + P + 60   # = 360 mm

all_shapes = []

# === Hilfsfunktionen =====================================================
def box_notched(name, x, y, z, lx, ly, lz, cuts=None):
    """Profilbalken mit optionalen Boolean-Cut-Ausklinkungen (Part::Cut)."""
    if lx <= 0 or ly <= 0 or lz <= 0:
        print("  SKIP %s: Null-Dim" % name)
        return None
    sh = cq.Workplane("XY").box(lx, ly, lz).translate((x+lx/2, y+ly/2, z+lz/2))
    if cuts:
        for (cx, cy, cz, clx, cly, clz) in cuts:
            if clx > 0 and cly > 0 and clz > 0:
                try:
                    cutter = cq.Workplane("XY").box(clx, cly, clz).translate((cx+clx/2, cy+cly/2, cz+clz/2))
                    sh = sh.cut(cutter)
                except Exception as e:
                    print("  WARN %s cut: %s" % (name, e))
    all_shapes.append(sh)
    return sh

def box(name, x, y, z, lx, ly, lz):
    return box_notched(name, x, y, z, lx, ly, lz)

def rafter_yz(name, x, y_s, z_s, dy, dz, x_w=None, prof=None):
    """Schrägprofil in der YZ-Ebene."""
    if x_w is None: x_w = P
    if prof is None: prof = P
    L = math.sqrt(dy * dy + dz * dz)
    if L < 1e-6:
        return None
    ny = -dz / L;  nz = dy / L
    pts = [
        (y_s,                z_s),
        (y_s + ny*prof,      z_s + nz*prof),
        (y_s + dy + ny*prof, z_s + dz + nz*prof),
        (y_s + dy,           z_s + dz),
    ]
    sh = (cq.Workplane("YZ")
          .moveTo(pts[0][0], pts[0][1])
          .lineTo(pts[1][0], pts[1][1])
          .lineTo(pts[2][0], pts[2][1])
          .lineTo(pts[3][0], pts[3][1])
          .close()
          .extrude(x_w)
          .translate((x, 0, 0)))
    all_shapes.append(sh)
    return sh

# === 1. ECKSTIELE  mit Zapfen Typ 4 =====================================
# Stiel = STIEL_H = 2175 mm (Zapfen bei z=2150..2175, Quer. 50x25)
# Zapfen: jeweils die "innere" Profilhälfte (in Y-Richtung) bleibt stehen,
# die äussere wird weggeschnitten.
_zap_z  = H - P     # = 2150
_zap_dz = P2        # = 25

# VL: x=0..P, y=0..P  -> Zapfen behält y=0..P2, schneidet y=P2..P weg
box_notched("EP_VL", 0,   0,   0, P, P, STIEL_H, [
    (0,   P2,   _zap_z, P, P2, _zap_dz),
])
box_notched("EP_VR", B-P, 0,   0, P, P, STIEL_H, [
    (B-P, P2,   _zap_z, P, P2, _zap_dz),
])
# HL: x=0..P, y=T-P..T -> Zapfen behält y=T-P..T-P2, schneidet y=T-P2..T weg
box_notched("EP_HL", 0,   T-P, 0, P, P, STIEL_H, [
    (0,   T-P2, _zap_z, P, P2, _zap_dz),
])
box_notched("EP_HR", B-P, T-P, 0, P, P, STIEL_H, [
    (B-P, T-P2, _zap_z, P, P2, _zap_dz),
])

# === 2. BODENRAHMEN  Typ 1 + Typ 3 ========================================
# Längsriegel BR_L/BR_R: durchlaufend y=0..T, Zapfensitz-Taschen an Ecken.
# Tasche (Typ 3): 50x50xP2 mm, in der Oberseite (z=P-P2..P = z=25..50).
_tas_z_br = P - P2   # = 25

box_notched("BR_L", 0,   0, 0, P, T, P, [
    (0,   0,   _tas_z_br, P, P, P2),   # Tasche VL
    (0,   T-P, _tas_z_br, P, P, P2),   # Tasche HL
])
box_notched("BR_R", B-P, 0, 0, P, T, P, [
    (B-P, 0,   _tas_z_br, P, P, P2),   # Tasche VR
    (B-P, T-P, _tas_z_br, P, P, P2),   # Tasche HR
])
# Querriegel BR_V/BR_H: Vollausklinkung an beiden Enden (Typ 1)
box_notched("BR_V", 0, 0,   0, B, P, P, [
    (0,   0,   0, P, P, P),
    (B-P, 0,   0, P, P, P),
])
box_notched("BR_H", 0, T-P, 0, B, P, P, [
    (0,   T-P, 0, P, P, P),
    (B-P, T-P, 0, P, P, P),
])

# === 2b. HOLZDIELENBODEN auf Querträgern =====================================
# Querträger: KVH 60x60 mm, Länge 1100 mm, liegen auf Bodenrahmen-Längsriegeln
# z = P (Bodenrahmen-OK) .. P+QT_H (= 50..110 mm)
_qt_inner = T - 2 * P                                      # innere Tiefe = 1100 mm
_qt_step  = (_qt_inner - N_QT * QT_B) // (N_QT - 1)       # Achsabstand ≈ 287 mm
_qt_ys    = [P + i * (QT_B + _qt_step) for i in range(N_QT)]
_qt_ys[-1] = T - P - QT_B                                  # letzten QT bündig an BR_H

for _qi, _qy in enumerate(_qt_ys):
    box("QT_%d" % (_qi + 1), P, _qy, P, B - 2*P, QT_B, QT_H)

# Holzdielen: Lärche 116×22 mm, Länge 1100 mm (Tiefe), verlegt in Y-Richtung
# z = P + QT_H (= 110) .. P + QT_H + PLANK_T (= 132 mm)
_pl_inner = B - 2 * P                                       # innere Breite = 1100 mm
_pl_total = N_PL * PLANK_W + (N_PL - 1) * PL_GAP           # = 9×116 + 8×4 = 1076 mm
_pl_x0    = P + (_pl_inner - _pl_total) // 2                # zentriert, x0 ≈ 62 mm

for _pi in range(N_PL):
    _px = _pl_x0 + _pi * (PLANK_W + PL_GAP)
    box("DIELE_%d" % (_pi + 1), _px, P, P + QT_H, PLANK_W, T - 2*P, PLANK_T)

# Trittholm wird in build_door('front') erzeugt (nur wenn DOOR_FRONT aktiv)

# === 3. OBERGURT  Typ 1 + Typ 4 ==========================================
# Längsriegel OG_L/OG_R: durchlaufend y=0..T, Tasche für Stielkopf-Zapfen.
# Tasche (Typ 4): P x P2 x P2 (50x25x25) an Ecken, Boden bei z=H-P.
_og_t_z  = H - P    # = 2150
_og_t_dz = P2       # = 25

box_notched("OG_L", 0,   0, H-P, P, T, P, [
    (0,   0,   _og_t_z, P, P2, _og_t_dz),   # Tasche VL
    (0,   T-P, _og_t_z, P, P2, _og_t_dz),   # Tasche HL
])
box_notched("OG_R", B-P, 0, H-P, P, T, P, [
    (B-P, 0,   _og_t_z, P, P2, _og_t_dz),   # Tasche VR
    (B-P, T-P, _og_t_z, P, P2, _og_t_dz),   # Tasche HR
])
# Querriegel OG_V/OG_H: Vollausklinkung (Typ 1)
box_notched("OG_V", 0, 0,   H-P, B, P, P, [
    (0,   0,   H-P, P, P, P),
    (B-P, 0,   H-P, P, P, P),
])
box_notched("OG_H", 0, T-P, H-P, B, P, P, [
    (0,   T-P, H-P, P, P, P),
    (B-P, T-P, H-P, P, P, P),
])

# === 4. TÜRRAHMEN – Zweiflügelige Drehtür (konfigurierbar) ================

def build_door(side):
    """
    Baut eine zweiflügelige Tür auf der angegebenen Seite.
    side: 'front' (y=0), 'back' (y=T), 'left' (x=0), 'right' (x=B)

    Bauteile pro Tür:
    - Mittelstiel 50×50×DH mm
    - Türsturz 50×50×(W-2P) mm  (W = Wandbreite der Seite)
    - Oberfüllung zwischen Sturz-OK und Obergurt-UK (Folie)
    - 2× Türflügel-Rahmen (je 2 vertikale + 3 horizontale 30×30 mm)
    - 4× Scharniere (2 pro Flügel, außen)
    - 1× Türriegel
    - 1× Trittholm 80×40 mm (nur FRONT)
    """
    sfx = side[0].upper()   # Kürzel für Bauteilnamen: F/B/L/R

    if side in ('front', 'back'):
        # Breite der Wand = B, Tiefe-Koordinate = y_wall
        W      = B
        y_wall = 0 if side == 'front' else T
        y_sign = -1 if side == 'front' else 1   # Richtung nach außen
        ms_x   = B // 2 - P // 2                # Mittelstiel X-Start

        # --- Mittelstiel ---
        box("MITTELSTIEL_%s" % sfx, ms_x, y_wall, P, P, P, DH)

        # --- Türsturz ---
        box("TURSTURZ_%s" % sfx, P, y_wall, DH, B - 2*P, P, P)

        # --- Oberfüllung ---
        _fh = H - P - (DH + P)
        if _fh > 0:
            box("TUF_%s" % sfx, P, y_wall, DH + P, B - 2*P, P, _fh)

        # --- Türflügel LINKS ---
        _tf_x1 = P
        _tf_x2 = ms_x
        _mid_z = P + DH // 2 - DT_P // 2
        box("TF_%s_L_BOT" % sfx, _tf_x1,       y_wall, P,          _tf_x2-_tf_x1, P, DT_P)
        box("TF_%s_L_TOP" % sfx, _tf_x1,       y_wall, P+DH-DT_P, _tf_x2-_tf_x1, P, DT_P)
        box("TF_%s_L_SL"  % sfx, _tf_x1,       y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        box("TF_%s_L_SR"  % sfx, _tf_x2-DT_P,  y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        box("TF_%s_L_MID" % sfx, _tf_x1,       y_wall, _mid_z,    _tf_x2-_tf_x1, P, DT_P)

        # --- Türflügel RECHTS ---
        _tf_rx1 = ms_x + P
        _tf_rx2 = B - P
        box("TF_%s_R_BOT" % sfx, _tf_rx1,       y_wall, P,          _tf_rx2-_tf_rx1, P, DT_P)
        box("TF_%s_R_TOP" % sfx, _tf_rx1,       y_wall, P+DH-DT_P, _tf_rx2-_tf_rx1, P, DT_P)
        box("TF_%s_R_SL"  % sfx, _tf_rx1,       y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        box("TF_%s_R_SR"  % sfx, _tf_rx2-DT_P,  y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        box("TF_%s_R_MID" % sfx, _tf_rx1,       y_wall, _mid_z,    _tf_rx2-_tf_rx1, P, DT_P)

        # --- Scharniere ---
        DHG_W = 100; DHG_D = 20; DHG_H = 80
        _hinge_dy = DHG_D * y_sign
        box("DHG_%s_L1" % sfx, 0,        y_wall, 300,  DHG_W, _hinge_dy, DHG_H)
        box("DHG_%s_L2" % sfx, 0,        y_wall, 1500, DHG_W, _hinge_dy, DHG_H)
        box("DHG_%s_R1" % sfx, B-DHG_W,  y_wall, 300,  DHG_W, _hinge_dy, DHG_H)
        box("DHG_%s_R2" % sfx, B-DHG_W,  y_wall, 1500, DHG_W, _hinge_dy, DHG_H)

        # --- Türriegel ---
        _ry = -5 * y_sign
        box("TUERRIEGEL_%s" % sfx, ms_x + P//2 - 10, y_wall + _ry, DH//2 - 20, 20, 5, 40)

        # --- Trittholm (nur Vorderseite) ---
        if side == 'front':
            box("TRITTHOLM", 0, 0, P, B, TH_D, TH_H)

    else:  # 'left' oder 'right'
        # Breite der Wand = T, Längs-Koordinate = x_wall
        W      = T
        x_wall = 0 if side == 'left' else B
        x_sign = -1 if side == 'left' else 1   # Richtung nach außen
        ms_y   = T // 2 - P // 2               # Mittelstiel Y-Start

        # --- Mittelstiel ---
        box("MITTELSTIEL_%s" % sfx, x_wall, ms_y, P, P, P, DH)

        # --- Türsturz ---
        box("TURSTURZ_%s" % sfx, x_wall, P, DH, P, T - 2*P, P)

        # --- Oberfüllung ---
        _fh = H - P - (DH + P)
        if _fh > 0:
            box("TUF_%s" % sfx, x_wall, P, DH + P, P, T - 2*P, _fh)

        # --- Türflügel LINKS (in Y-Richtung) ---
        _tf_y1 = P
        _tf_y2 = ms_y
        _mid_z = P + DH // 2 - DT_P // 2
        box("TF_%s_L_BOT" % sfx, x_wall, _tf_y1,       P,          P, _tf_y2-_tf_y1, DT_P)
        box("TF_%s_L_TOP" % sfx, x_wall, _tf_y1,       P+DH-DT_P, P, _tf_y2-_tf_y1, DT_P)
        box("TF_%s_L_SL"  % sfx, x_wall, _tf_y1,       P+DT_P,    P, DT_P, DH-2*DT_P)
        box("TF_%s_L_SR"  % sfx, x_wall, _tf_y2-DT_P,  P+DT_P,    P, DT_P, DH-2*DT_P)
        box("TF_%s_L_MID" % sfx, x_wall, _tf_y1,       _mid_z,    P, _tf_y2-_tf_y1, DT_P)

        # --- Türflügel RECHTS (in Y-Richtung) ---
        _tf_ry1 = ms_y + P
        _tf_ry2 = T - P
        box("TF_%s_R_BOT" % sfx, x_wall, _tf_ry1,       P,          P, _tf_ry2-_tf_ry1, DT_P)
        box("TF_%s_R_TOP" % sfx, x_wall, _tf_ry1,       P+DH-DT_P, P, _tf_ry2-_tf_ry1, DT_P)
        box("TF_%s_R_SL"  % sfx, x_wall, _tf_ry1,       P+DT_P,    P, DT_P, DH-2*DT_P)
        box("TF_%s_R_SR"  % sfx, x_wall, _tf_ry2-DT_P,  P+DT_P,    P, DT_P, DH-2*DT_P)
        box("TF_%s_R_MID" % sfx, x_wall, _tf_ry1,       _mid_z,    P, _tf_ry2-_tf_ry1, DT_P)

        # --- Scharniere ---
        DHG_W = 100; DHG_D = 20; DHG_H = 80
        _hinge_dx = DHG_D * x_sign
        box("DHG_%s_L1" % sfx, x_wall, 0,       300,  _hinge_dx, DHG_W, DHG_H)
        box("DHG_%s_L2" % sfx, x_wall, 0,       1500, _hinge_dx, DHG_W, DHG_H)
        box("DHG_%s_R1" % sfx, x_wall, T-DHG_W, 300,  _hinge_dx, DHG_W, DHG_H)
        box("DHG_%s_R2" % sfx, x_wall, T-DHG_W, 1500, _hinge_dx, DHG_W, DHG_H)

        # --- Türriegel ---
        _rx = -5 * x_sign
        box("TUERRIEGEL_%s" % sfx, x_wall + _rx, ms_y + P//2 - 10, DH//2 - 20, 5, 20, 40)


# === TÜREN (konfigurierbar) ===============================================
if DOOR_FRONT: build_door('front')
if DOOR_BACK:  build_door('back')
if DOOR_LEFT:  build_door('left')
if DOOR_RIGHT: build_door('right')

# === 4b. QUERSTREBEN auf türlosen Seiten (dynamisch je nach Wandbreite) ====
# n_streben = max(1, Wandbreite // 1000)
#   < 2 m  → 1 Strebe (halbe Höhe)
#   2–3 m  → 2 Streben (1/3, 2/3 Höhe)
#   3–4 m  → 3 Streben (1/4, 2/4, 3/4 Höhe)  usw.
# Verbindung: Vollausklinkung Typ 1 (wie BR_V/OG_V)

def _qs_zpositions(n):
    """n gleichmäßig verteilte Z-Startpositionen (Profilunterkante) für Querstreben."""
    wall_h = H - 2 * P          # freie Wandhöhe zwischen Rahmen
    return [P + i * wall_h // (n + 1) - P // 2 for i in range(1, n + 1)]

def build_querstrebe(side):
    """Baut Querstreben auf halber (bzw. mehrfach unterteilter) Wandhöhe."""
    sfx   = side[0].upper()
    width = B if side in ('front', 'back') else T
    n     = max(1, width // 1000)
    for idx, qz in enumerate(_qs_zpositions(n), start=1):
        name = "QS_%s_%d" % (sfx, idx)
        if side == 'front':
            box_notched(name, 0, 0, qz, B, P, P, [
                (0,   0, qz, P, P, P),
                (B-P, 0, qz, P, P, P),
            ])
        elif side == 'back':
            box_notched(name, 0, T-P, qz, B, P, P, [
                (0,   T-P, qz, P, P, P),
                (B-P, T-P, qz, P, P, P),
            ])
        elif side == 'left':
            box_notched(name, 0, 0, qz, P, T, P, [
                (0, 0,   qz, P, P, P),
                (0, T-P, qz, P, P, P),
            ])
        elif side == 'right':
            box_notched(name, B-P, 0, qz, P, T, P, [
                (B-P, 0,   qz, P, P, P),
                (B-P, T-P, qz, P, P, P),
            ])

if not DOOR_FRONT: build_querstrebe('front')
if not DOOR_BACK:  build_querstrebe('back')
if not DOOR_LEFT:  build_querstrebe('left')
if not DOOR_RIGHT: build_querstrebe('right')

# Trittholm nur wenn KEINE Vordertür (dann gar kein Trittholm nötig)
# -> wird bereits in build_door('front') erzeugt

# === 5. DACHRAHMEN  (1800×1800 mm, Überstand 300 mm auf allen Seiten) ======
box("DR_V",  -OVER, -OVER,        H_DACH_V, B + 2*OVER, P, P)
box("DR_H",  -OVER, T + OVER - P, H_DACH_H, B + 2*OVER, P, P)
_z_mid = H_DACH_V + RISE // 2   # = 2300 mm
box("DR_M",  -OVER, T//2 - P//2, _z_mid,    B + 2*OVER, P, P)
rafter_yz("DR_SL", -OVER,        -OVER, H_DACH_V, T + 2*OVER, RISE)
rafter_yz("DR_SR", B + OVER - P, -OVER, H_DACH_V, T + 2*OVER, RISE)

# === 6. SCHARNIERE + GASDRUCKFEDER =======================================
box("HNG_1", 200,           T, H-50, HNG_W, HNG_D, HNG_H)
box("HNG_2", B-200-HNG_W,   T, H-50, HNG_W, HNG_D, HNG_H)
_gdf_dy = -(T // 2 - P)
_gdf_dz =  RISE // 2 + 100
rafter_yz("GDF", B//2 - 10, T - P, H + 80, _gdf_dy, _gdf_dz, x_w=20, prof=20)

# === 7. KLEMMSCHIENEN =====================================================
box("KS_V_BO",  0,   -CH,  0,        B,  CW, CH)
box("KS_V_TO",  0,   -CH,  H-CH,     B,  CW, CH)
box("KS_V_LO", -CH,  -CH,  0,        CH, CW, H)
box("KS_V_RO",  B,   -CH,  0,        CH, CW, H)
box("KS_H_BO",  0,    T,   0,        B,  CW, CH)
box("KS_H_TO",  0,    T,   H-CH,     B,  CW, CH)
box("KS_H_LO", -CH,   T,   0,        CH, CW, H)
box("KS_H_RO",  B,    T,   0,        CH, CW, H)
box("KS_L_BO", -CH,   0,   0,        CH, T,  CW)
box("KS_L_TO", -CH,   0,   H-CW,     CH, T,  CW)
box("KS_R_BO",  B,    0,   0,        CH, T,  CW)
box("KS_R_TO",  B,    0,   H-CW,     CH, T,  CW)
box("KS_DR_V", -OVER, -CH,        H_DACH_V, B + 2*OVER, CW, CH)
box("KS_DR_H", -OVER, T + OVER,   H_DACH_H, B + 2*OVER, CW, CH)

# === 8. SCHRAUBENVERBINDUNGEN – AUSKLINKUNG ===============================
# M10x80 (d=10): OG-Stiel Typ 4, von oben  -> 8 Stk
# M8x60  (d=8):  Bodenknoten Typ 3, seitl. -> 16 Stk
# M8x40  (d=8):  Türpfosten Typ 2          ->  4 Stk
BOLT_M10 = 10
BOLT_M8  = 8

def bolt_cyl(name, cx, cy, cz, axis, L=80, d=10):
    r = d / 2.0
    if axis == 'x':
        sh = cq.Workplane("YZ").cylinder(L, r).translate((cx+L/2, cy, cz))
    elif axis == 'y':
        sh = cq.Workplane("XZ").cylinder(L, r).translate((cx, cy+L/2, cz))
    else:
        sh = cq.Workplane("XY").cylinder(L, r).translate((cx, cy, cz+L/2))
    all_shapes.append(sh)
    return sh

_n_scr_before = len(all_shapes)
# Typ 4 – M10x80 von oben, 2x pro Ecke
_corners = [("VL", P//2, P//2), ("VR", B-P//2, P//2),
            ("HL", P//2, T-P//2), ("HR", B-P//2, T-P//2)]
for _lbl, _cx, _cy in _corners:
    bolt_cyl("SCR_OG_%s_1" % _lbl, _cx, _cy, H, 'z', L=80, d=BOLT_M10)
    _ox = P//4 if _cx < B//2 else -P//4
    bolt_cyl("SCR_OG_%s_2" % _lbl, _cx+_ox, _cy, H, 'z', L=80, d=BOLT_M10)

# Typ 3 – M8x60 seitlich (X-Richtung)
for _ly, _lab in [(P//2, "V"), (T-P//2, "H")]:
    bolt_cyl("SCR_BR_L_%s_1" % _lab,  0, _ly, P//4,   'x', L=60, d=BOLT_M8)
    bolt_cyl("SCR_BR_L_%s_2" % _lab,  0, _ly, P*3//4, 'x', L=60, d=BOLT_M8)
    bolt_cyl("SCR_BR_R_%s_1" % _lab,  B, _ly, P//4,   'x', L=60, d=BOLT_M8)
    bolt_cyl("SCR_BR_R_%s_2" % _lab,  B, _ly, P*3//4, 'x', L=60, d=BOLT_M8)
# Typ 3 – M8x60 seitlich (Y-Richtung)
for _lx, _lab in [(P//2, "L"), (B-P//2, "R")]:
    bolt_cyl("SCR_BR_V_%s_1" % _lab,  _lx, 0, P//4,   'y', L=60, d=BOLT_M8)
    bolt_cyl("SCR_BR_V_%s_2" % _lab,  _lx, 0, P*3//4, 'y', L=60, d=BOLT_M8)
    bolt_cyl("SCR_BR_H_%s_1" % _lab,  _lx, T, P//4,   'y', L=60, d=BOLT_M8)
    bolt_cyl("SCR_BR_H_%s_2" % _lab,  _lx, T, P*3//4, 'y', L=60, d=BOLT_M8)
# Mittelstiel – M8x40 Verbindung unten + oben
_ms_cx = MITTELSTIEL_X + P // 2
bolt_cyl("SCR_MS_B", _ms_cx, P//2, int(P*0.35),    'y', L=40, d=BOLT_M8)
bolt_cyl("SCR_MS_T", _ms_cx, P//2, int(DH-P*0.35), 'y', L=40, d=BOLT_M8)

_n_scr = len(all_shapes) - _n_scr_before
print("  -> %d Schrauben-Zylinder erstellt" % _n_scr)

# === 9. COMPOUND + EXPORT =================================================
print("Erstelle Compound aus %d Einzelteilen ..." % len(all_shapes))
compound = Compound.makeCompound([s.val() for s in all_shapes])
step = os.path.join(OUT, "gewaechshaus.step")
cq.exporters.export(compound, step)
print("ok STEP: %s" % step)

_angle = math.degrees(math.atan2(RISE, T + 2*OVER))
print("Pultdach-Neigung: %.1f Grad" % _angle)
print("Stiel-Hoehe: %d mm  |  Zapfen-Laenge: %d mm" % (STIEL_H, P2))
print("FreeCAD-Modell (Ausklinkung) fertig.")
