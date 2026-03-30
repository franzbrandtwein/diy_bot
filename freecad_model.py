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

import FreeCAD
import Part
import math
import os

OUT = "/home/herrvorragend/projekte/gewaechshaus"
os.makedirs(OUT, exist_ok=True)

# === Maße =================================================================
B        = 1200   # Breite   (X-Achse)
T        = 1200   # Tiefe    (Y-Achse)
H        = 2200   # Wandhöhe – Oberkante Obergurt (Z-Achse)
P        = 50     # Profilquerschnitt 50x50
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
OVER     = 300         # Dachüberstand auf allen 4 Seiten (mm)
SLOPE    = 200 / 1200  # Dachneigung mm/mm (9.5 Grad, unveraendert)
H_DACH_V = H - int(OVER * SLOPE)     # = 2150 mm  (Vorderkante, Traufe)
H_DACH_H = 2400 + int(OVER * SLOPE)  # = 2450 mm  (Hinterkante, Scharnierpunkt)
RISE     = H_DACH_H - H_DACH_V        # = 300 mm  (Höhendiff. Dachrahmen 1800mm)

HNG_W = 100;  HNG_D = 20;  HNG_H = (H_DACH_H - H) + P + 60   # = 360 mm

doc        = FreeCAD.newDocument("Gewaechshaus_Ausklinkung")
all_shapes = []
all_feats  = []

# === Hilfsfunktionen =====================================================
def box_notched(name, x, y, z, lx, ly, lz, cuts=None):
    """Profilbalken mit optionalen Boolean-Cut-Ausklinkungen (Part::Cut)."""
    if lx <= 0 or ly <= 0 or lz <= 0:
        print("  SKIP %s: Null-Dim" % name)
        return None
    sh = Part.makeBox(lx, ly, lz, FreeCAD.Vector(x, y, z))
    if cuts:
        for (cx, cy, cz, clx, cly, clz) in cuts:
            if clx > 0 and cly > 0 and clz > 0:
                try:
                    cutter = Part.makeBox(clx, cly, clz, FreeCAD.Vector(cx, cy, cz))
                    sh = sh.cut(cutter)
                except Exception as e:
                    print("  WARN %s cut: %s" % (name, e))
    feat = doc.addObject("Part::Feature", name)
    feat.Shape = sh
    all_shapes.append(sh);  all_feats.append(feat)
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
    p1 = FreeCAD.Vector(x,       y_s,            z_s)
    p2 = FreeCAD.Vector(x,       y_s + ny*prof,  z_s + nz*prof)
    p3 = FreeCAD.Vector(x + x_w, y_s + ny*prof,  z_s + nz*prof)
    p4 = FreeCAD.Vector(x + x_w, y_s,            z_s)
    edges  = [Part.makeLine(p1, p2), Part.makeLine(p2, p3),
              Part.makeLine(p3, p4), Part.makeLine(p4, p1)]
    solid  = Part.Face(Part.Wire(edges)).extrude(FreeCAD.Vector(0, dy, dz))
    feat   = doc.addObject("Part::Feature", name)
    feat.Shape = solid
    all_shapes.append(solid);  all_feats.append(feat)
    return solid

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

# Trittholm: 80mm tief × 40mm hoch × 1200mm lang (volle Türbreite)
# Auf dem vorderen Bodenrahmen-Querriegel (z = P..P+TH_H = 50..90 mm)
box("TRITTHOLM", 0, 0, P, B, TH_D, TH_H)

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

# === 4. TÜRRAHMEN – Zweiflügelige Drehtür volle Breite ====================
# Mittelstiel 50×50 mm, x=575..625, z=P..P+DH (= 50..1950 mm)
box("MITTELSTIEL", MITTELSTIEL_X, 0, P, P, P, DH)
# Türsturz 50×50 mm, x=P..B-P (lichte Breite 1100 mm), z=DH..DH+P (= 1900..1950 mm)
box("TURSTURZ", P, 0, DH, B - 2*P, P, P)
# Oberfüllung zwischen Türsturz-OK und Obergurt-UK (Folie, 200 mm hoch)
_fh = H - P - (DH + P)   # = 200 mm
if _fh > 0:
    box("TUF", P, 0, DH + P, B - 2*P, P, _fh)

# Türflügel LINKS – Rahmen 30×30 mm, Außenmaß 575×1900 mm
_tf_x1 = P                           # x=50 (Eckstiel-Innenkante)
_tf_x2 = MITTELSTIEL_X               # x=575 (Mittelstiel-Linke Kante)
_mid_z = P + DH // 2 - DT_P // 2    # Mittelstrebe z=985 mm
box("TF_L_BOT", _tf_x1,       0, P,           _tf_x2-_tf_x1, P, DT_P)
box("TF_L_TOP", _tf_x1,       0, P+DH-DT_P,  _tf_x2-_tf_x1, P, DT_P)
box("TF_L_SL",  _tf_x1,       0, P+DT_P,     DT_P, P, DH-2*DT_P)
box("TF_L_SR",  _tf_x2-DT_P,  0, P+DT_P,     DT_P, P, DH-2*DT_P)
box("TF_L_MID", _tf_x1,       0, _mid_z,      _tf_x2-_tf_x1, P, DT_P)

# Türflügel RECHTS – Rahmen 30×30 mm, Außenmaß 575×1900 mm
_tf_rx1 = MITTELSTIEL_X + P          # x=625 (Mittelstiel-Rechte Kante)
_tf_rx2 = B - P                      # x=1150 (Eckstiel-Innenkante rechts)
box("TF_R_BOT", _tf_rx1,        0, P,           _tf_rx2-_tf_rx1, P, DT_P)
box("TF_R_TOP", _tf_rx1,        0, P+DH-DT_P,  _tf_rx2-_tf_rx1, P, DT_P)
box("TF_R_SL",  _tf_rx1,        0, P+DT_P,     DT_P, P, DH-2*DT_P)
box("TF_R_SR",  _tf_rx2-DT_P,   0, P+DT_P,     DT_P, P, DH-2*DT_P)
box("TF_R_MID", _tf_rx1,        0, _mid_z,      _tf_rx2-_tf_rx1, P, DT_P)

# Scharniere Türflügel (100×80 mm, je 2 Stk pro Flügel, außen an Eckstielen)
DHG_W = 100;  DHG_D = 20;  DHG_H = 80
box("DHG_L1", 0, 0, 300,  DHG_W, DHG_D, DHG_H)
box("DHG_L2", 0, 0, 1500, DHG_W, DHG_D, DHG_H)
box("DHG_R1", B-DHG_W, 0, 300,  DHG_W, DHG_D, DHG_H)
box("DHG_R2", B-DHG_W, 0, 1500, DHG_W, DHG_D, DHG_H)

# Verschluss / Türriegel (Karabinerhaken, mittig am Mittelstiel)
box("TUERRIEGEL", MITTELSTIEL_X + P//2 - 10, -5, DH//2 - 20, 20, 5, 40)

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
        origin  = FreeCAD.Vector(cx,       cy - r, cz - r)
        dir_vec = FreeCAD.Vector(1, 0, 0)
    elif axis == 'y':
        origin  = FreeCAD.Vector(cx - r, cy,       cz - r)
        dir_vec = FreeCAD.Vector(0, 1, 0)
    else:
        origin  = FreeCAD.Vector(cx - r, cy - r, cz)
        dir_vec = FreeCAD.Vector(0, 0, 1)
    sh   = Part.makeCylinder(r, L, origin, dir_vec)
    feat = doc.addObject("Part::Feature", name)
    feat.Shape = sh
    all_shapes.append(sh);  all_feats.append(feat)
    return sh

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

_n_scr = sum(1 for f in all_feats if f.Label.startswith('SCR_'))
print("  -> %d Schrauben-Zylinder erstellt" % _n_scr)

# === 9. COMPOUND + EXPORT =================================================
print("Erstelle Compound aus %d Einzelteilen ..." % len(all_shapes))
compound  = Part.makeCompound(all_shapes)
comp_feat = doc.addObject("Part::Feature", "Gewaechshaus_Ausklinkung")
comp_feat.Shape = compound

doc.recompute()

fcstd = os.path.join(OUT, "gewaechshaus.FCStd")
doc.saveAs(fcstd)
print("ok FCStd: %s" % fcstd)

step = os.path.join(OUT, "gewaechshaus.step")
Part.export(all_feats, step)
print("ok STEP: %s" % step)

_angle = math.degrees(math.atan2(RISE, T + 2*OVER))
print("Pultdach-Neigung: %.1f Grad" % _angle)
print("Stiel-Hoehe: %d mm  |  Zapfen-Laenge: %d mm" % (STIEL_H, P2))
print("FreeCAD-Modell (Ausklinkung) fertig.")
