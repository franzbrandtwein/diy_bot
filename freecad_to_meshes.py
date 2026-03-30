#!/usr/bin/env python3
"""
FreeCAD-Skript: Baut die Gewächshaus-Geometrie neu auf (aus freecad_model.py),
gruppiert Teile nach Material und exportiert je Gruppe eine STL-Datei.

Aufruf: FreeCADCmd freecad_to_meshes.py
"""
import cadquery as cq
from cadquery import Compound
import math, os, sys

OUT_DIR = "/tmp/gwh_meshes"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Maße (identisch mit freecad_model.py) ──────────────────────────────────
# Parameter werden von params.py importiert (Web-Konfigurator)
import os as _os
_proj = os.environ.get("GWH_PROJECT_DIR", "/home/herrvorragend/projekte/gewaechshaus")
try:
    import sys as _sys; _sys.path.insert(0, _proj)
    from params import B, T, H, OVER, P
    try:
        from params import DOOR_FRONT, DOOR_BACK, DOOR_LEFT, DOOR_RIGHT
    except ImportError:
        DOOR_FRONT = True; DOOR_BACK = False; DOOR_LEFT = False; DOOR_RIGHT = False
    del _sys
except ImportError:
    B = 1200; T = 1200; H = 2200; OVER = 300; P = 50
    DOOR_FRONT = True; DOOR_BACK = False; DOOR_LEFT = False; DOOR_RIGHT = False
del _os, _proj
P2 = P // 2
DW_SINGLE = (B - P) // 2; DW = B; DH = 1900; DT_P = 30
MITTELSTIEL_X = B // 2 - P // 2; CW = 25; CH = 10; DX = 0
QT_H = 60; QT_B = 60; N_QT = 4; PLANK_T = 22; PLANK_W = 116
N_PL = 9; PL_GAP = 4; TH_H = 40; TH_D = 80
STIEL_H = H - P2
SLOPE = 200 / 1200
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
    sh = cq.Workplane("XY").box(lx, ly, lz).translate((x+lx/2, y+ly/2, z+lz/2))
    if cuts:
        for (cx, cy, cz, clx, cly, clz) in cuts:
            if clx > 0 and cly > 0 and clz > 0:
                try:
                    c = cq.Workplane("XY").box(clx, cly, clz).translate((cx+clx/2, cy+cly/2, cz+clz/2))
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
    add(group, sh)
    return sh

def bolt_cyl(group, cx, cy, cz, axis, L=80, d=10):
    r = d / 2.0
    if axis == 'x':
        sh = cq.Workplane("YZ").cylinder(L, r).translate((cx+L/2, cy, cz))
    elif axis == 'y':
        sh = cq.Workplane("XZ").cylinder(L, r).translate((cx, cy+L/2, cz))
    else:
        sh = cq.Workplane("XY").cylinder(L, r).translate((cx, cy, cz+L/2))
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

# Trittholm wird in build_door_meshes('front') erzeugt

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

# ── 4. TÜRRAHMEN (konfigurierbar) ─────────────────────────────────────────
def build_door_meshes(side):
    """Erzeugt Türrahmen-Geometrie für die angegebene Seite."""
    if side in ('front', 'back'):
        W      = B
        y_wall = 0 if side == 'front' else T
        ms_x   = B // 2 - P // 2
        y_sign = -1 if side == 'front' else 1

        bx("steel_frame", ms_x, y_wall, P, P, P, DH)
        bx("steel_frame", P, y_wall, DH, B-2*P, P, P)
        _fh = H - P - (DH + P)
        if _fh > 0:
            bx("steel_frame", P, y_wall, DH+P, B-2*P, P, _fh)

        _tf_x1 = P; _tf_x2 = ms_x
        _mid_z = P + DH//2 - DT_P//2
        bx("door_frame", _tf_x1,       y_wall, P,          _tf_x2-_tf_x1, P, DT_P)
        bx("door_frame", _tf_x1,       y_wall, P+DH-DT_P, _tf_x2-_tf_x1, P, DT_P)
        bx("door_frame", _tf_x1,       y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        bx("door_frame", _tf_x2-DT_P,  y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        bx("door_frame", _tf_x1,       y_wall, _mid_z,    _tf_x2-_tf_x1, P, DT_P)

        _tf_rx1 = ms_x + P; _tf_rx2 = B - P
        bx("door_frame", _tf_rx1,       y_wall, P,          _tf_rx2-_tf_rx1, P, DT_P)
        bx("door_frame", _tf_rx1,       y_wall, P+DH-DT_P, _tf_rx2-_tf_rx1, P, DT_P)
        bx("door_frame", _tf_rx1,       y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        bx("door_frame", _tf_rx2-DT_P,  y_wall, P+DT_P,    DT_P, P, DH-2*DT_P)
        bx("door_frame", _tf_rx1,       y_wall, _mid_z,    _tf_rx2-_tf_rx1, P, DT_P)

        DHG_W=100; DHG_D=20; DHG_H=80
        _hd = DHG_D * y_sign
        bx("hardware", 0,       y_wall, 300,  DHG_W, _hd, DHG_H)
        bx("hardware", 0,       y_wall, 1500, DHG_W, _hd, DHG_H)
        bx("hardware", B-DHG_W, y_wall, 300,  DHG_W, _hd, DHG_H)
        bx("hardware", B-DHG_W, y_wall, 1500, DHG_W, _hd, DHG_H)
        _ry = -5 * y_sign
        bx("hardware", ms_x+P//2-10, y_wall+_ry, DH//2-20, 20, 5, 40)

        if side == 'front':
            bx("wood", 0, 0, P, B, TH_D, TH_H)  # Trittholm

    else:  # 'left' oder 'right'
        x_wall = 0 if side == 'left' else B
        x_sign = -1 if side == 'left' else 1
        ms_y   = T // 2 - P // 2

        bx("steel_frame", x_wall, ms_y, P, P, P, DH)
        bx("steel_frame", x_wall, P, DH, P, T-2*P, P)
        _fh = H - P - (DH + P)
        if _fh > 0:
            bx("steel_frame", x_wall, P, DH+P, P, T-2*P, _fh)

        _tf_y1 = P; _tf_y2 = ms_y
        _mid_z = P + DH//2 - DT_P//2
        bx("door_frame", x_wall, _tf_y1,       P,          P, _tf_y2-_tf_y1, DT_P)
        bx("door_frame", x_wall, _tf_y1,       P+DH-DT_P, P, _tf_y2-_tf_y1, DT_P)
        bx("door_frame", x_wall, _tf_y1,       P+DT_P,    P, DT_P, DH-2*DT_P)
        bx("door_frame", x_wall, _tf_y2-DT_P,  P+DT_P,    P, DT_P, DH-2*DT_P)
        bx("door_frame", x_wall, _tf_y1,       _mid_z,    P, _tf_y2-_tf_y1, DT_P)

        _tf_ry1 = ms_y + P; _tf_ry2 = T - P
        bx("door_frame", x_wall, _tf_ry1,       P,          P, _tf_ry2-_tf_ry1, DT_P)
        bx("door_frame", x_wall, _tf_ry1,       P+DH-DT_P, P, _tf_ry2-_tf_ry1, DT_P)
        bx("door_frame", x_wall, _tf_ry1,       P+DT_P,    P, DT_P, DH-2*DT_P)
        bx("door_frame", x_wall, _tf_ry2-DT_P,  P+DT_P,    P, DT_P, DH-2*DT_P)
        bx("door_frame", x_wall, _tf_ry1,       _mid_z,    P, _tf_ry2-_tf_ry1, DT_P)

        DHG_W=100; DHG_D=20; DHG_H=80
        _hd = DHG_D * x_sign
        bx("hardware", x_wall, 0,       300,  _hd, DHG_W, DHG_H)
        bx("hardware", x_wall, 0,       1500, _hd, DHG_W, DHG_H)
        bx("hardware", x_wall, T-DHG_W, 300,  _hd, DHG_W, DHG_H)
        bx("hardware", x_wall, T-DHG_W, 1500, _hd, DHG_W, DHG_H)
        _rx = -5 * x_sign
        bx("hardware", x_wall+_rx, ms_y+P//2-10, DH//2-20, 5, 20, 40)

if DOOR_FRONT: build_door_meshes('front')
if DOOR_BACK:  build_door_meshes('back')
if DOOR_LEFT:  build_door_meshes('left')
if DOOR_RIGHT: build_door_meshes('right')

# ── 4b. QUERSTREBEN auf türlosen Seiten ───────────────────────────────────
def _qs_zpositions(n):
    wall_h = H - 2 * P
    return [P + i * wall_h // (n + 1) - P // 2 for i in range(1, n + 1)]

def build_querstrebe_mesh(side):
    width = B if side in ('front', 'back') else T
    n     = max(1, width // 1000)
    for idx, qz in enumerate(_qs_zpositions(n), start=1):
        if side == 'front':
            box_notched("steel_frame", 0, 0, qz, B, P, P, [
                (0,   0, qz, P, P, P),
                (B-P, 0, qz, P, P, P),
            ])
        elif side == 'back':
            box_notched("steel_frame", 0, T-P, qz, B, P, P, [
                (0,   T-P, qz, P, P, P),
                (B-P, T-P, qz, P, P, P),
            ])
        elif side == 'left':
            box_notched("steel_frame", 0, 0, qz, P, T, P, [
                (0, 0,   qz, P, P, P),
                (0, T-P, qz, P, P, P),
            ])
        elif side == 'right':
            box_notched("steel_frame", B-P, 0, qz, P, T, P, [
                (B-P, 0,   qz, P, P, P),
                (B-P, T-P, qz, P, P, P),
            ])

if not DOOR_FRONT: build_querstrebe_mesh('front')
if not DOOR_BACK:  build_querstrebe_mesh('back')
if not DOOR_LEFT:  build_querstrebe_mesh('left')
if not DOOR_RIGHT: build_querstrebe_mesh('right')

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
    try:
        group_compound = Compound.makeCompound([s.val() for s in shapes])
        out_path = os.path.join(OUT_DIR, "%s.stl" % gname)
        cq.exporters.export(group_compound, out_path, cq.exporters.ExportTypes.STL)
        print("  OK  %s  (-> %s)" % (gname, out_path))
    except Exception as e:
        print("  ERR %s: %s" % (gname, e))

print("CadQuery-Export abgeschlossen.")
