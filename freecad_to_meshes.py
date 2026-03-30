#!/usr/bin/env python3
"""
FreeCAD-Skript: Baut die Gewächshaus-Geometrie neu auf (aus freecad_model.py),
gruppiert Teile nach Material und exportiert je Gruppe eine STL-Datei.

Aufruf: FreeCADCmd freecad_to_meshes.py
"""
import FreeCAD, Part, MeshPart, Mesh
import math, os, sys

OUT_DIR = "/tmp/gwh_meshes"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Maße (identisch mit freecad_model.py) ──────────────────────────────────
B = 1200; T = 1200; H = 2200; P = 50; P2 = P // 2
DW_SINGLE = (B - P) // 2; DW = B; DH = 1900; DT_P = 30
MITTELSTIEL_X = B // 2 - P // 2; CW = 25; CH = 10; DX = 0
QT_H = 60; QT_B = 60; N_QT = 4; PLANK_T = 22; PLANK_W = 116
N_PL = 9; PL_GAP = 4; TH_H = 40; TH_D = 80
STIEL_H = H - P2
OVER = 300; SLOPE = 200 / 1200
H_DACH_V = H - int(OVER * SLOPE)
H_DACH_H = 2400 + int(OVER * SLOPE)
RISE = H_DACH_H - H_DACH_V
HNG_W = 100; HNG_D = 20; HNG_H = (H_DACH_H - H) + P + 60
BOLT_M10 = 10; BOLT_M8 = 8

# ── Gruppen ────────────────────────────────────────────────────────────────
groups = {
    "steel_frame":  [],   # Eckstiele, Bodenrahmen, Obergurt, Mittelstiel, Sturz, TUF
    "roof_frame":   [],   # Dachrahmen-Profile (DR_*)
    "door_frame":   [],   # Türflügel-Profile TF_L_* / TF_R_*
    "hardware":     [],   # Scharniere (DHG_*, HNG_*), Gasdruckfeder (GDF), Riegel
    "wood":         [],   # Querträger, Dielen, Trittholm
    "clamping":     [],   # Klemmschienen KS_*
    "screws":       [],   # Schrauben-Zylinder SCR_*
}

# ── Hilfsfunktionen ────────────────────────────────────────────────────────
def add(group, shape):
    groups[group].append(shape)

def box_notched(group, x, y, z, lx, ly, lz, cuts=None):
    if lx <= 0 or ly <= 0 or lz <= 0:
        return None
    sh = Part.makeBox(lx, ly, lz, FreeCAD.Vector(x, y, z))
    if cuts:
        for (cx, cy, cz, clx, cly, clz) in cuts:
            if clx > 0 and cly > 0 and clz > 0:
                try:
                    c = Part.makeBox(clx, cly, clz, FreeCAD.Vector(cx, cy, cz))
                    sh = sh.cut(c)
                except Exception as e:
                    print("  WARN cut:", e)
    add(group, sh)
    return sh

def bx(group, x, y, z, lx, ly, lz):
    return box_notched(group, x, y, z, lx, ly, lz)

def rafter_yz(group, x, y_s, z_s, dy, dz, x_w=None, prof=None):
    if x_w is None: x_w = P
    if prof is None: prof = P
    L = math.sqrt(dy*dy + dz*dz)
    if L < 1e-6: return None
    ny = -dz / L; nz = dy / L
    p1 = FreeCAD.Vector(x,       y_s,           z_s)
    p2 = FreeCAD.Vector(x,       y_s+ny*prof,   z_s+nz*prof)
    p3 = FreeCAD.Vector(x+x_w,   y_s+ny*prof,   z_s+nz*prof)
    p4 = FreeCAD.Vector(x+x_w,   y_s,           z_s)
    edges = [Part.makeLine(p1,p2), Part.makeLine(p2,p3),
             Part.makeLine(p3,p4), Part.makeLine(p4,p1)]
    sh = Part.Face(Part.Wire(edges)).extrude(FreeCAD.Vector(0, dy, dz))
    add(group, sh)
    return sh

def bolt_cyl(group, cx, cy, cz, axis, L=80, d=10):
    r = d / 2.0
    if axis == 'x':
        origin = FreeCAD.Vector(cx, cy-r, cz-r); dv = FreeCAD.Vector(1,0,0)
    elif axis == 'y':
        origin = FreeCAD.Vector(cx-r, cy, cz-r); dv = FreeCAD.Vector(0,1,0)
    else:
        origin = FreeCAD.Vector(cx-r, cy-r, cz); dv = FreeCAD.Vector(0,0,1)
    sh = Part.makeCylinder(r, L, origin, dv)
    add(group, sh)
    return sh

# ── 1. ECKSTIELE ──────────────────────────────────────────────────────────
_zap_z = H - P; _zap_dz = P2
box_notched("steel_frame", 0,   0,   0, P, P, STIEL_H, [(0,   P2,   _zap_z, P, P2, _zap_dz)])
box_notched("steel_frame", B-P, 0,   0, P, P, STIEL_H, [(B-P, P2,   _zap_z, P, P2, _zap_dz)])
box_notched("steel_frame", 0,   T-P, 0, P, P, STIEL_H, [(0,   T-P2, _zap_z, P, P2, _zap_dz)])
box_notched("steel_frame", B-P, T-P, 0, P, P, STIEL_H, [(B-P, T-P2, _zap_z, P, P2, _zap_dz)])

# ── 2. BODENRAHMEN ────────────────────────────────────────────────────────
_tas_z_br = P - P2
box_notched("steel_frame", 0,   0, 0, P, T, P,
    [(0,   0,   _tas_z_br, P, P, P2), (0,   T-P, _tas_z_br, P, P, P2)])
box_notched("steel_frame", B-P, 0, 0, P, T, P,
    [(B-P, 0,   _tas_z_br, P, P, P2), (B-P, T-P, _tas_z_br, P, P, P2)])
box_notched("steel_frame", 0, 0,   0, B, P, P,
    [(0, 0, 0, P, P, P), (B-P, 0, 0, P, P, P)])
box_notched("steel_frame", 0, T-P, 0, B, P, P,
    [(0, T-P, 0, P, P, P), (B-P, T-P, 0, P, P, P)])

# ── 2b. HOLZBODEN ────────────────────────────────────────────────────────
_qt_inner = T - 2*P
_qt_step  = (_qt_inner - N_QT*QT_B) // (N_QT-1)
_qt_ys    = [P + i*(QT_B + _qt_step) for i in range(N_QT)]
_qt_ys[-1] = T - P - QT_B
for _qy in _qt_ys:
    bx("wood", P, _qy, P, B-2*P, QT_B, QT_H)

_pl_inner = B - 2*P
_pl_total = N_PL*PLANK_W + (N_PL-1)*PL_GAP
_pl_x0    = P + (_pl_inner - _pl_total) // 2
for _pi in range(N_PL):
    _px = _pl_x0 + _pi*(PLANK_W + PL_GAP)
    bx("wood", _px, P, P+QT_H, PLANK_W, T-2*P, PLANK_T)

bx("wood", 0, 0, P, B, TH_D, TH_H)  # Trittholm

# ── 3. OBERGURT ──────────────────────────────────────────────────────────
_og_t_z = H - P; _og_t_dz = P2
box_notched("steel_frame", 0,   0, H-P, P, T, P,
    [(0,   0,   _og_t_z, P, P2, _og_t_dz), (0,   T-P, _og_t_z, P, P2, _og_t_dz)])
box_notched("steel_frame", B-P, 0, H-P, P, T, P,
    [(B-P, 0,   _og_t_z, P, P2, _og_t_dz), (B-P, T-P, _og_t_z, P, P2, _og_t_dz)])
box_notched("steel_frame", 0, 0,   H-P, B, P, P,
    [(0, 0, H-P, P, P, P), (B-P, 0, H-P, P, P, P)])
box_notched("steel_frame", 0, T-P, H-P, B, P, P,
    [(0, T-P, H-P, P, P, P), (B-P, T-P, H-P, P, P, P)])

# ── 4. TÜRRAHMEN ─────────────────────────────────────────────────────────
bx("steel_frame", MITTELSTIEL_X, 0, P, P, P, DH)
bx("steel_frame", P, 0, DH, B-2*P, P, P)
_fh = H - P - (DH + P)
if _fh > 0:
    bx("steel_frame", P, 0, DH+P, B-2*P, P, _fh)

# Türflügel LINKS
_tf_x1 = P; _tf_x2 = MITTELSTIEL_X
_mid_z = P + DH//2 - DT_P//2
bx("door_frame", _tf_x1,       0, P,          _tf_x2-_tf_x1, P, DT_P)
bx("door_frame", _tf_x1,       0, P+DH-DT_P, _tf_x2-_tf_x1, P, DT_P)
bx("door_frame", _tf_x1,       0, P+DT_P,    DT_P, P, DH-2*DT_P)
bx("door_frame", _tf_x2-DT_P,  0, P+DT_P,    DT_P, P, DH-2*DT_P)
bx("door_frame", _tf_x1,       0, _mid_z,    _tf_x2-_tf_x1, P, DT_P)

# Türflügel RECHTS
_tf_rx1 = MITTELSTIEL_X + P; _tf_rx2 = B - P
bx("door_frame", _tf_rx1,       0, P,          _tf_rx2-_tf_rx1, P, DT_P)
bx("door_frame", _tf_rx1,       0, P+DH-DT_P, _tf_rx2-_tf_rx1, P, DT_P)
bx("door_frame", _tf_rx1,       0, P+DT_P,    DT_P, P, DH-2*DT_P)
bx("door_frame", _tf_rx2-DT_P,  0, P+DT_P,    DT_P, P, DH-2*DT_P)
bx("door_frame", _tf_rx1,       0, _mid_z,    _tf_rx2-_tf_rx1, P, DT_P)

# Tür-Scharniere
DHG_W=100; DHG_D=20; DHG_H=80
bx("hardware", 0,       0, 300,  DHG_W, DHG_D, DHG_H)
bx("hardware", 0,       0, 1500, DHG_W, DHG_D, DHG_H)
bx("hardware", B-DHG_W, 0, 300,  DHG_W, DHG_D, DHG_H)
bx("hardware", B-DHG_W, 0, 1500, DHG_W, DHG_D, DHG_H)
bx("hardware", MITTELSTIEL_X+P//2-10, -5, DH//2-20, 20, 5, 40)  # Riegel

# ── 5. DACHRAHMEN ─────────────────────────────────────────────────────────
bx("roof_frame", -OVER, -OVER,        H_DACH_V, B+2*OVER, P, P)
bx("roof_frame", -OVER, T+OVER-P,     H_DACH_H, B+2*OVER, P, P)
_z_mid = H_DACH_V + RISE//2
bx("roof_frame", -OVER, T//2-P//2,    _z_mid,   B+2*OVER, P, P)
rafter_yz("roof_frame", -OVER,        -OVER, H_DACH_V, T+2*OVER, RISE)
rafter_yz("roof_frame", B+OVER-P,     -OVER, H_DACH_V, T+2*OVER, RISE)

# ── 6. SCHARNIERE + GASDRUCKFEDER ─────────────────────────────────────────
bx("hardware", 200,         T, H-50, HNG_W, HNG_D, HNG_H)
bx("hardware", B-200-HNG_W, T, H-50, HNG_W, HNG_D, HNG_H)
_gdf_dy = -(T//2 - P)
_gdf_dz =  RISE//2 + 100
rafter_yz("hardware", B//2-10, T-P, H+80, _gdf_dy, _gdf_dz, x_w=20, prof=20)

# ── 7. KLEMMSCHIENEN ──────────────────────────────────────────────────────
bx("clamping", 0,    -CH,  0,      B,  CW, CH)
bx("clamping", 0,    -CH,  H-CH,   B,  CW, CH)
bx("clamping", -CH,  -CH,  0,      CH, CW, H)
bx("clamping", B,    -CH,  0,      CH, CW, H)
bx("clamping", 0,    T,    0,      B,  CW, CH)
bx("clamping", 0,    T,    H-CH,   B,  CW, CH)
bx("clamping", -CH,  T,    0,      CH, CW, H)
bx("clamping", B,    T,    0,      CH, CW, H)
bx("clamping", -CH,  0,    0,      CH, T,  CW)
bx("clamping", -CH,  0,    H-CW,   CH, T,  CW)
bx("clamping", B,    0,    0,      CH, T,  CW)
bx("clamping", B,    0,    H-CW,   CH, T,  CW)
bx("clamping", -OVER, -CH,       H_DACH_V, B+2*OVER, CW, CH)
bx("clamping", -OVER,  T+OVER,   H_DACH_H, B+2*OVER, CW, CH)

# ── 8. SCHRAUBEN ──────────────────────────────────────────────────────────
_corners = [("VL", P//2, P//2), ("VR", B-P//2, P//2),
            ("HL", P//2, T-P//2), ("HR", B-P//2, T-P//2)]
for _lbl, _cx, _cy in _corners:
    bolt_cyl("screws", _cx, _cy, H, 'z', L=80, d=BOLT_M10)
    _ox = P//4 if _cx < B//2 else -P//4
    bolt_cyl("screws", _cx+_ox, _cy, H, 'z', L=80, d=BOLT_M10)

for _ly in [P//2, T-P//2]:
    bolt_cyl("screws", 0, _ly, P//4,   'x', L=60, d=BOLT_M8)
    bolt_cyl("screws", 0, _ly, P*3//4, 'x', L=60, d=BOLT_M8)
    bolt_cyl("screws", B, _ly, P//4,   'x', L=60, d=BOLT_M8)
    bolt_cyl("screws", B, _ly, P*3//4, 'x', L=60, d=BOLT_M8)

for _lx in [P//2, B-P//2]:
    bolt_cyl("screws", _lx, 0, P//4,   'y', L=60, d=BOLT_M8)
    bolt_cyl("screws", _lx, 0, P*3//4, 'y', L=60, d=BOLT_M8)
    bolt_cyl("screws", _lx, T, P//4,   'y', L=60, d=BOLT_M8)
    bolt_cyl("screws", _lx, T, P*3//4, 'y', L=60, d=BOLT_M8)

_ms_cx = MITTELSTIEL_X + P//2
bolt_cyl("screws", _ms_cx, P//2, int(P*0.35),    'y', L=40, d=BOLT_M8)
bolt_cyl("screws", _ms_cx, P//2, int(DH-P*0.35), 'y', L=40, d=BOLT_M8)

# ── Export ─────────────────────────────────────────────────────────────────
print("Starte Export der Gruppen …")
for gname, shapes in groups.items():
    if not shapes:
        print("  SKIP %s (leer)" % gname)
        continue
    compound = Part.makeCompound(shapes)
    try:
        mesh = MeshPart.meshFromShape(Shape=compound,
                                      LinearDeflection=0.5,
                                      AngularDeflection=0.3)
        out_path = os.path.join(OUT_DIR, "%s.stl" % gname)
        mesh.write(out_path)
        print("  OK  %s  (%d Faces, -> %s)" % (gname, mesh.CountFacets, out_path))
    except Exception as e:
        print("  ERR %s: %s" % (gname, e))

print("FreeCAD-Export abgeschlossen.")
