#!/usr/bin/env python3
"""
Gewächshaus – Technische Zeichnung  (Aufklappbares Pultdach)
Verbindungsmethode: Ausklinkungen (Klauen-/Zapfenverbindungen)
  Typ 1  Vollausklinkung   – Eckknoten Boden + Obergurt
  Typ 2  Halbausklinkung   – Kreuzknoten Pfetten
  Typ 3  Zapfensitz        – Stiel auf Bodenrahmen
  Typ 4  Zapfen / Tasche   – Obergurt auf Stielkopf

Erzeugt: PDF (6 Ansichten + Ausklinkungsdetail), gewaechshaus_iso.png,
         gewaechshaus_front.png, gewaechshaus_stueckliste.txt
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import math
import os

OUT = "/home/herrvorragend/projekte/gewaechshaus"
os.makedirs(OUT, exist_ok=True)

# --- Masse (mm) --------------------------------------------------------------
B        = 1200
T        = 1200
H        = 2200
P        = 50
P2       = P // 2   # = 25 mm
DW_SINGLE = (B - P) // 2    # = 575 mm lichte Breite je Flügel
DW       = B                # = 1200 mm Gesamtbreite (volle Breite, zweiflügelig)
DH       = 1900             # Türhöhe (licht)
DT_P     = 30               # Türflügel-Rahmenprofil 30×30 mm
MITTELSTIEL_X = B // 2 - P // 2   # = 575 mm (X-Startpos. Mittelstiel)
CW       = 25
CH       = 10
DX       = 0                # Türoffset = 0 (volle Breite)
STIEL_H  = H - P2           # = 2175 mm

# --- Holzdielenboden -------------------------------------------------------
QT_H    = 60;  QT_B    = 60;  N_QT  = 4
PLANK_T = 22;  PLANK_W = 116; N_PL  = 9;  PL_GAP = 4
TH_H    = 40;  TH_D    = 80
_qt_inner = T - 2*P
_qt_step  = (_qt_inner - N_QT*QT_B) // (N_QT - 1)      # ≈ 287 mm
_qt_ys    = [P + i*(QT_B + _qt_step) for i in range(N_QT)]
_qt_ys[-1] = T - P - QT_B
_pl_inner = B - 2*P
_pl_total = N_PL*PLANK_W + (N_PL-1)*PL_GAP              # = 1076 mm
_pl_x0    = P + (_pl_inner - _pl_total) // 2             # zentriert, x0 ≈ 62 mm

OVER     = 300         # Dachüberstand auf allen 4 Seiten (mm)
SLOPE    = 200 / 1200  # Neigung mm/mm (9.5 Grad, unveraendert)
H_DACH_V = H - int(OVER * SLOPE)     # = 2150 mm
H_DACH_H = 2400 + int(OVER * SLOPE)  # = 2450 mm
RISE     = H_DACH_H - H_DACH_V        # = 300 mm

_z_mid   = H_DACH_V + RISE // 2   # = 2300 mm
HNG_W = 100;  HNG_D = 20;  HNG_H = (H_DACH_H - H) + P + 60   # = 360 mm
_roof_angle = math.degrees(math.atan2(RISE, T + 2*OVER))  # unchanged ~9.5°
_rafter_slope = round(math.sqrt((T + 2*OVER)**2 + RISE**2))  # ≈ 1825 mm

# --- Farben ------------------------------------------------------------------
STEEL  = "#3a6fbf"
DOOR   = "#2ca059"
ROOF   = "#7b5ea7"
HINGE  = "#cc3300"
GAS    = "#888888"
RAIL   = "#d4890a"
NOTCH  = "#c0392b"   # Ausklinkung / Schrauben
WOOD   = "#8B5E3C"   # Holzboden (Querträger + Dielen)

# --- Bauteil-Listen ----------------------------------------------------------
members_wall = []
members_roof = []

def _b(lst, name, group, x, y, z, lx, ly, lz, color=STEEL):
    lst.append(dict(type="box", name=name, group=group,
                    x=x, y=y, z=z, lx=lx, ly=ly, lz=lz, color=color))

def _c8(lst, name, group, corners, color=STEEL):
    lst.append(dict(type="corners8", name=name, group=group,
                    corners=np.array(corners, dtype=float), color=color))

def tilted_yz(x, y_s, z_s, dy, dz, x_w=P, prof=P):
    L  = math.sqrt(dy**2 + dz**2)
    ny = -dz / L;  nz = dy / L
    cs = np.array([
        [x,      y_s,           z_s],
        [x,      y_s + ny*prof, z_s + nz*prof],
        [x + x_w, y_s + ny*prof, z_s + nz*prof],
        [x + x_w, y_s,           z_s],
    ])
    ext = np.array([0, dy, dz])
    return np.vstack([cs, cs + ext])

W = members_wall
R = members_roof

# == WAND =====================================================================
# Eckstiele (mit Zapfen, Stiel = STIEL_H = 2175 mm)
_b(W,"EP_VL","Eckstiel", 0,   0,   0, P,     P,     STIEL_H)
_b(W,"EP_VR","Eckstiel", B-P, 0,   0, P,     P,     STIEL_H)
_b(W,"EP_HL","Eckstiel", 0,   T-P, 0, P,     P,     STIEL_H)
_b(W,"EP_HR","Eckstiel", B-P, T-P, 0, P,     P,     STIEL_H)
# Bodenrahmen – Längsriegel (durchlaufend y=0..T)
_b(W,"BR_L","Bodenrahmen", 0,   0,   0, P,     T,     P)
_b(W,"BR_R","Bodenrahmen", B-P, 0,   0, P,     T,     P)
# Bodenrahmen – Querriegel (Vollausklinkung, effektiv x=P..B-P)
_b(W,"BR_V","Bodenrahmen", P,   0,   0, B-2*P, P,     P)
_b(W,"BR_H","Bodenrahmen", P,   T-P, 0, B-2*P, P,     P)
# Obergurt – Längsriegel (durchlaufend y=0..T)
_b(W,"OG_L","Obergurt", 0,   0,   H-P, P,     T,     P)
_b(W,"OG_R","Obergurt", B-P, 0,   H-P, P,     T,     P)
# Obergurt – Querriegel (Vollausklinkung, effektiv x=P..B-P)
_b(W,"OG_V","Obergurt", P,   0,   H-P, B-2*P, P,     P)
_b(W,"OG_H","Obergurt", P,   T-P, H-P, B-2*P, P,     P)
# Zweiflügelige Tür – Hauptstruktur (50×50 mm)
# Mittelstiel (50×50 mm, x=575..625, z=50..1950)
_b(W,"MITTELSTIEL","Türrahmen", MITTELSTIEL_X, 0, P, P, P, DH, DOOR)
# Türsturz / Obergurt-Querriegel (50×50 mm, z=1900..1950, lichte Br. 1100 mm)
_b(W,"TURSTURZ","Türrahmen", P, 0, DH, B-2*P, P, P, DOOR)
# Oberfüllung (50×50 mm, z=1950..2150, mit Folie abgedeckt)
_fh = H - P - (DH + P)   # = 200 mm
if _fh > 0:
    _b(W,"TUF","Türrahmen", P, 0, DH+P, B-2*P, P, _fh, DOOR)
# Türflügel LINKS – Rahmen 30×30 mm, Außenmaß 575×1900 mm
_tf_x1 = P; _tf_x2 = MITTELSTIEL_X          # x=50..575
_mid_z  = P + DH//2 - DT_P//2               # z=985 mm
_b(W,"TF_L_BOT","Türflügel", _tf_x1,      0, P,          _tf_x2-_tf_x1, P, DT_P, DOOR)
_b(W,"TF_L_TOP","Türflügel", _tf_x1,      0, P+DH-DT_P, _tf_x2-_tf_x1, P, DT_P, DOOR)
_b(W,"TF_L_SL", "Türflügel", _tf_x1,      0, P+DT_P,    DT_P, P, DH-2*DT_P, DOOR)
_b(W,"TF_L_SR", "Türflügel", _tf_x2-DT_P, 0, P+DT_P,    DT_P, P, DH-2*DT_P, DOOR)
_b(W,"TF_L_MID","Türflügel", _tf_x1,      0, _mid_z,     _tf_x2-_tf_x1, P, DT_P, DOOR)
# Türflügel RECHTS – Rahmen 30×30 mm, Außenmaß 575×1900 mm
_tf_rx1 = MITTELSTIEL_X+P; _tf_rx2 = B-P    # x=625..1150
_b(W,"TF_R_BOT","Türflügel", _tf_rx1,       0, P,          _tf_rx2-_tf_rx1, P, DT_P, DOOR)
_b(W,"TF_R_TOP","Türflügel", _tf_rx1,       0, P+DH-DT_P, _tf_rx2-_tf_rx1, P, DT_P, DOOR)
_b(W,"TF_R_SL", "Türflügel", _tf_rx1,       0, P+DT_P,    DT_P, P, DH-2*DT_P, DOOR)
_b(W,"TF_R_SR", "Türflügel", _tf_rx2-DT_P,  0, P+DT_P,    DT_P, P, DH-2*DT_P, DOOR)
_b(W,"TF_R_MID","Türflügel", _tf_rx1,       0, _mid_z,     _tf_rx2-_tf_rx1, P, DT_P, DOOR)
# Scharniere
_b(W,"HNG_1","Scharnier", 200,          T, H-50, HNG_W, HNG_D, HNG_H, HINGE)
_b(W,"HNG_2","Scharnier", B-200-HNG_W,  T, H-50, HNG_W, HNG_D, HNG_H, HINGE)
# Klemmschienen
_b(W,"KS_V_BO","Klemmschiene", 0,  -CH, 0,     B,  CW, CH, RAIL)
_b(W,"KS_V_TO","Klemmschiene", 0,  -CH, H-CH,  B,  CW, CH, RAIL)
_b(W,"KS_H_BO","Klemmschiene", 0,   T,  0,     B,  CW, CH, RAIL)
_b(W,"KS_H_TO","Klemmschiene", 0,   T,  H-CH,  B,  CW, CH, RAIL)
_b(W,"KS_L_BO","Klemmschiene",-CH,  0,  0,     CH, T,  CW, RAIL)
_b(W,"KS_L_TO","Klemmschiene",-CH,  0,  H-CW,  CH, T,  CW, RAIL)
_b(W,"KS_R_BO","Klemmschiene", B,   0,  0,     CH, T,  CW, RAIL)
_b(W,"KS_R_TO","Klemmschiene", B,   0,  H-CW,  CH, T,  CW, RAIL)

# == HOLZDIELENBODEN ==========================================================
for _qi, _qy in enumerate(_qt_ys):
    _b(W, "QT_%d" % (_qi+1), "Quertraeger", P, _qy, P, B-2*P, QT_B, QT_H, WOOD)
for _pi in range(N_PL):
    _px = _pl_x0 + _pi*(PLANK_W + PL_GAP)
    _b(W, "DIELE_%d" % (_pi+1), "Diele", _px, P, P+QT_H, PLANK_W, T-2*P, PLANK_T, WOOD)
_b(W, "TRITTHOLM", "Trittholm", 0, 0, P, B, TH_D, TH_H, WOOD)

# == DACH =====================================================================
_b(R,"DR_V","Dachrahmen", -OVER, -OVER,        H_DACH_V, B+2*OVER, P, P, ROOF)
_b(R,"DR_H","Dachrahmen", -OVER, T+OVER-P,     H_DACH_H, B+2*OVER, P, P, ROOF)
_b(R,"DR_M","Dachrahmen", -OVER, T//2-P//2,    _z_mid,   B+2*OVER, P, P, ROOF)
_c8(R,"DR_SL","Dachrahmen", tilted_yz(-OVER,        -OVER, H_DACH_V, T+2*OVER, RISE), ROOF)
_c8(R,"DR_SR","Dachrahmen", tilted_yz(B+OVER-P,     -OVER, H_DACH_V, T+2*OVER, RISE), ROOF)
_b(R,"KS_DR_V","Klemmschiene", -OVER, -CH,       H_DACH_V, B+2*OVER, CW, CH, RAIL)
_b(R,"KS_DR_H","Klemmschiene", -OVER, T+OVER,    H_DACH_H, B+2*OVER, CW, CH, RAIL)
_gdf_dy = -(T // 2 - P)
_gdf_dz =  RISE // 2 + 100
_c8(R,"GDF","Gasdruckfeder",
    tilted_yz(B//2-10, T-P, H+80, _gdf_dy, _gdf_dz, x_w=20, prof=20), GAS)

members = members_wall + members_roof

# --- Eckpunkte ---------------------------------------------------------------
def get_corners(m):
    if m["type"] == "corners8":
        return m["corners"]
    x,y,z    = m["x"],  m["y"],  m["z"]
    lx,ly,lz = m["lx"], m["ly"], m["lz"]
    return np.array([
        [x,   y,   z  ],[x+lx,y,   z  ],[x+lx,y+ly,z  ],[x,   y+ly,z  ],
        [x,   y,   z+lz],[x+lx,y,   z+lz],[x+lx,y+ly,z+lz],[x,   y+ly,z+lz],
    ])

def rotate_open(corners, angle_deg=90):
    c = np.array(corners, dtype=float)
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    dy = c[:,1] - T;  dz = c[:,2] - H_DACH_H
    c[:,1] = T + ca*dy - sa*dz
    c[:,2] = H_DACH_H + sa*dy + ca*dz
    return c

def proj_front(p): return p[:,[0,2]]
def proj_side(p):  return p[:,[1,2]]
def proj_top(p):   return p[:,[0,1]]
def proj_iso(p):
    c30 = math.cos(math.radians(30));  s30 = math.sin(math.radians(30))
    return np.column_stack([(p[:,0]-p[:,1])*c30, (p[:,0]+p[:,1])*s30+p[:,2]])

EDGES = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]

try:
    from scipy.spatial import ConvexHull as _CH
    _SCIPY = True
except ImportError:
    _SCIPY = False

def _draw_edges(ax, p2, color, lw, alpha, zo, ls):
    for i,j in EDGES:
        ax.plot([p2[i,0],p2[j,0]],[p2[i,1],p2[j,1]],
                color=color, lw=lw, alpha=alpha, zorder=zo, ls=ls)

def draw_member(ax, corners, color, proj_fn, lw=0.6, alpha=0.88, zo=2, ls="-"):
    p2 = proj_fn(np.array(corners, dtype=float))
    if _SCIPY and len(p2) >= 3:
        try:
            hull = _CH(p2)
            ax.add_patch(plt.Polygon(p2[hull.vertices], closed=True,
                         facecolor=color, edgecolor="none", alpha=alpha*0.35, zorder=zo))
            hv = np.vstack([p2[hull.vertices], p2[hull.vertices[0]]])
            ax.plot(hv[:,0],hv[:,1], color=color, lw=lw, alpha=alpha, zorder=zo+1, ls=ls)
            return
        except Exception:
            pass
    _draw_edges(ax, p2, color, lw, alpha, zo, ls)

def draw_list(ax, mlist, proj_fn, lw=0.6, alpha=0.88, zo=2, transform=None, ls="-"):
    for m in mlist:
        c = get_corners(m)
        if transform:
            c = transform(c.copy())
        draw_member(ax, c, m["color"], proj_fn, lw, alpha, zo, ls)

def dim_line(ax, x1, y1, x2, y2, text, offset=60, fontsize=6.5, color="#222"):
    cx,cy = (x1+x2)/2, (y1+y2)/2
    dx,dy_ = x2-x1, y2-y1
    L = math.sqrt(dx**2 + dy_**2)
    if L < 1: return
    nx,ny_ = -dy_/L, dx/L
    ox,oy  = cx+nx*offset, cy+ny_*offset
    ax.annotate("", xy=(x2+nx*offset*0.3, y2+ny_*offset*0.3),
                xytext=(x1+nx*offset*0.3, y1+ny_*offset*0.3),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.7), zorder=10)
    ax.plot([x1,x1+nx*offset*0.6],[y1,y1+ny_*offset*0.6],
            color=color, lw=0.5, ls="--", zorder=9)
    ax.plot([x2,x2+nx*offset*0.6],[y2,y2+ny_*offset*0.6],
            color=color, lw=0.5, ls="--", zorder=9)
    ax.text(ox,oy, text, ha="center", va="center",
            fontsize=fontsize, color=color, zorder=11,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))

LEGEND = [
    mpatches.Patch(color=STEEL, label="Hauptstruktur 50x50"),
    mpatches.Patch(color=DOOR,  label="Türrahmen/Sturz 50x50"),
    mpatches.Patch(color=DOOR,  label="Türflügel 30x30", alpha=0.5),
    mpatches.Patch(color=ROOF,  label="Dachrahmen 50x50"),
    mpatches.Patch(color=HINGE, label="Scharnier 100x100"),
    mpatches.Patch(color=GAS,   label="Gasdruckfeder"),
    mpatches.Patch(color=RAIL,  label="Klemmschiene 25x10"),
    mpatches.Patch(color=NOTCH, label="Ausklinkung / M10-M8"),
    mpatches.Patch(color=WOOD,  label="Holzboden (KVH/Laerche)"),
]

# ============================================================================
# A)  TECHNISCHE ZEICHNUNG  – PDF  (DIN-A3-ähnlich)
#     6 Ansichten: Vorne, Seite, Iso, Draufsicht, Offen, Detail Ausklinkung
# ============================================================================
MM2IN = 1/25.4
fig = plt.figure(figsize=(420*MM2IN, 297*MM2IN), dpi=150)
fig.patch.set_facecolor("white")

LM,RM,BM,TM = 0.03, 0.02, 0.12, 0.02
GH,GV        = 0.015, 0.025
CW3 = (1 - LM - RM - 2*GH) / 3
RH2 = (1 - BM - TM - GV)   / 2

def mk(col, row):
    return fig.add_axes([LM + col*(CW3+GH), BM + row*(RH2+GV), CW3, RH2])

ax_front = mk(0,1)
ax_side  = mk(1,1)
ax_iso   = mk(2,1)
ax_top   = mk(0,0)
ax_open  = mk(1,0)
ax_det   = mk(2,0)   # Detail A: Ausklinkung Obergurt-Eckstiel

for _ax in (ax_front,ax_side,ax_iso,ax_top,ax_open,ax_det):
    _ax.set_aspect("equal")
    _ax.set_facecolor("#f9f9f9")
    for sp in _ax.spines.values():
        sp.set_linewidth(0.4); sp.set_edgecolor("#666")
    _ax.tick_params(left=False,bottom=False,labelleft=False,labelbottom=False)
    _ax.grid(True, lw=0.2, color="#cccccc")

# -- Hilfsfunktion: Ausklinkungskerbe als kleines gehatchtes Rechteck --------
def draw_notch_mark(ax, x, z, size=18, axis='v', color=NOTCH):
    """Zeigt Ausklinkungskerbe als kleines farbiges Rechteck mit Schraffur."""
    if axis == 'v':   # vertikale Kerbe (an Seite eines Stiels)
        rect = mpatches.FancyBboxPatch((x - size*0.5, z), size, size*0.5,
            boxstyle="square,pad=0", lw=0.8, edgecolor=color,
            facecolor=color, alpha=0.25, zorder=7)
        ax.add_patch(rect)
        ax.plot([x - size*0.5, x + size*0.5], [z, z],
                color=color, lw=1.0, zorder=8)
    else:             # horizontale Kerbe (an Ende eines Riegels)
        rect = mpatches.FancyBboxPatch((x, z - size*0.5), size*0.5, size,
            boxstyle="square,pad=0", lw=0.8, edgecolor=color,
            facecolor=color, alpha=0.25, zorder=7)
        ax.add_patch(rect)
        ax.plot([x, x], [z - size*0.5, z + size*0.5],
                color=color, lw=1.0, zorder=8)

# ============================================================================
# Vorderansicht (XZ)
# ============================================================================
ax_front.set_title("Vorderansicht  (Türseite)", fontsize=7, pad=2, fontweight="bold")
draw_list(ax_front, members, proj_front, lw=0.7)
ax_front.set_xlim(-400, 1620); ax_front.set_ylim(-200, 2700)
ax_front.tick_params(labelleft=True,labelbottom=True,labelsize=5,left=True,bottom=True)
ax_front.set_xlabel("Breite [mm]", fontsize=5.5)
ax_front.set_ylabel("Hoehe [mm]",  fontsize=5.5)
dim_line(ax_front,  0,  -120, B,    -120, "B=%d" % B, offset=28, fontsize=5.5)
dim_line(ax_front,-150,   0, -150,   H,   "H=%d" % H, offset=22, fontsize=5.5)
dim_line(ax_front,-150,   H, -150,   H_DACH_V+P, "+%d" % P, offset=22, fontsize=4.5)
# Zweiflügelige Tür: Einzelbemaßung je Flügel
dim_line(ax_front, P, -80, MITTELSTIEL_X, -80, "%d" % DW_SINGLE, offset=12, fontsize=4.5)
dim_line(ax_front, MITTELSTIEL_X+P, -80, B-P, -80, "%d" % DW_SINGLE, offset=12, fontsize=4.5)
dim_line(ax_front, 0, -120, B, -120, "2x%d+50=%d (volle Breite)" % (DW_SINGLE, DW), offset=28, fontsize=5)
ax_front.annotate("", xy=(B+60,DH), xytext=(B+60,0),
                  arrowprops=dict(arrowstyle="<->",color="#555",lw=0.6), zorder=10)
ax_front.text(B+90, DH/2, "%d" % DH, fontsize=5, color="#555", va="center")
ax_front.axhline(H_DACH_V, xmin=0.05, xmax=0.95, color=ROOF, lw=0.6, ls=":", zorder=5)
ax_front.text(B+50, H_DACH_V+10, "Dach %d" % H_DACH_V, fontsize=4.5, color=ROOF)

# Trittholm-Annotation in Vorderansicht (volle Breite 1200 mm)
ax_front.add_patch(mpatches.FancyBboxPatch((0, P), B, TH_H,
    boxstyle="square,pad=0", lw=1.2, edgecolor=WOOD, facecolor=WOOD,
    alpha=0.55, zorder=6))
ax_front.text(B/2, P + TH_H/2, "Trittholm\n80×40×1200", ha="center", va="center",
    fontsize=4.0, color="white", fontweight="bold", zorder=7)
ax_front.annotate("Dielenboden OK\n(z = +%d mm)" % (P+QT_H+PLANK_T),
    xy=(B-P, P+QT_H+PLANK_T),
    xytext=(B+60, P+QT_H+PLANK_T+60),
    arrowprops=dict(arrowstyle="->", color=WOOD, lw=0.7),
    fontsize=4.0, color=WOOD, va="center", zorder=10)
# Mittelstiel-Annotation
ax_front.annotate("Mittelstiel\n50×50",
    xy=(MITTELSTIEL_X+P/2, DH*0.4),
    xytext=(MITTELSTIEL_X-200, 400),
    arrowprops=dict(arrowstyle="->", color=DOOR, lw=0.6),
    fontsize=4.0, color=DOOR, ha="center", zorder=10)

# Ausklinkungskerben in Vorderansicht (Typ 4: Stielkopf-Zapfen, Typ 1: Ecken)
_nk = 16   # Kerbengrösse [mm]
for _sx in [P/2, B-P/2]:
    # Bodenknoten (Typ 3): kleine Kerbe am Stiel-Fuss
    draw_notch_mark(ax_front, _sx, 0, size=_nk, axis='v', color=NOTCH)
    # Obergurt-Knoten (Typ 4): Zapfen-Kerbe am Stielkopf
    draw_notch_mark(ax_front, _sx, H-P, size=_nk, axis='v', color=NOTCH)
    # Typ 1-Vollausklinkung Obergurt-Querriegel
    draw_notch_mark(ax_front, _sx, H-P, size=_nk, axis='h', color=NOTCH)

# M10x80 Schrauben-Symbole von oben (kreuz) an OG-Ecken
_scr_r = 13
for _sx in [P/2, B-P/2]:
    ax_front.add_patch(mpatches.Circle((_sx, H+5), _scr_r,
        lw=1.0, edgecolor=NOTCH, facecolor="white", alpha=0.9, zorder=9))
    ax_front.plot([_sx-_scr_r*0.65, _sx+_scr_r*0.65], [H+5, H+5],
                  color=NOTCH, lw=0.8, zorder=10)
    ax_front.plot([_sx, _sx], [H+5-_scr_r*0.65, H+5+_scr_r*0.65],
                  color=NOTCH, lw=0.8, zorder=10)

# M8x60 seitlich an Bodenecken
for _sx in [P/2, B-P/2]:
    for _sz in [P*0.28, P*0.72]:
        ax_front.add_patch(mpatches.Circle((_sx, _sz), 9,
            lw=0.8, edgecolor="#e67e22", facecolor="white", alpha=0.85, zorder=9))
        ax_front.plot([_sx-5.5, _sx+5.5], [_sz, _sz], color="#e67e22", lw=0.6, zorder=10)
        ax_front.plot([_sx, _sx], [_sz-5.5, _sz+5.5], color="#e67e22", lw=0.6, zorder=10)
ax_front.text(5, H+50,
    "o M10x80 von oben (Typ 4)   o M8x60 seitl. (Typ 3) – Formschluss!",
    fontsize=4.0, color=NOTCH, zorder=12)

# ============================================================================
# Seitenansicht (YZ)
# ============================================================================
ax_side.set_title("Seitenansicht  (Neigung %.1f Grad)" % _roof_angle,
                  fontsize=7, pad=2, fontweight="bold")
draw_list(ax_side, members, proj_side, lw=0.7)
ax_side.set_xlim(-400, 1720); ax_side.set_ylim(-200, 2700)
ax_side.tick_params(labelleft=True,labelbottom=True,labelsize=5,left=True,bottom=True)
ax_side.set_xlabel("Tiefe [mm]",  fontsize=5.5)
ax_side.set_ylabel("Hoehe [mm]",  fontsize=5.5)
dim_line(ax_side, 0, -120, T, -120, "T=%d" % T, offset=28, fontsize=5.5)
dim_line(ax_side,-150,0, -150, H,   "H=%d" % H, offset=22, fontsize=5.5)
dim_line(ax_side, T+80, H_DACH_V, T+80, H_DACH_H, "D=%d" % RISE, offset=-25, fontsize=5)
# Überstand-Bemaßung Seitenansicht
dim_line(ax_side, -OVER, H_DACH_V-80, 0, H_DACH_V-80, "ÜST=%d" % OVER, offset=22, fontsize=5)
dim_line(ax_side, T, H_DACH_H+50, T+OVER, H_DACH_H+50, "ÜST=%d" % OVER, offset=-22, fontsize=5)
ax_side.plot([-OVER, -OVER], [H_DACH_V, H_DACH_V-80], color=ROOF, lw=0.5, ls=":", zorder=4)
ax_side.plot([0, 0], [H_DACH_V, H_DACH_V-80], color=ROOF, lw=0.5, ls=":", zorder=4)
ax_side.plot([T, T], [H_DACH_H, H_DACH_H+50], color=ROOF, lw=0.5, ls=":", zorder=4)
ax_side.plot([T+OVER, T+OVER], [H_DACH_H, H_DACH_H+50], color=ROOF, lw=0.5, ls=":", zorder=4)
ax_side.plot([-OVER, T+OVER],[H_DACH_V, H_DACH_H], color=ROOF, lw=1.0, ls="--", zorder=6)
_th = np.linspace(math.pi/2, math.pi/2 - math.radians(_roof_angle), 20)
ax_side.plot(180*np.cos(_th), H_DACH_V + 180*np.sin(_th), color=ROOF, lw=0.8, zorder=6)
ax_side.text(25, H_DACH_V+35, "%.1f Grad" % _roof_angle, fontsize=5.5, color=ROOF)
ax_side.plot(T, H_DACH_H, "o", color=HINGE, ms=4, zorder=8)
ax_side.text(T+15, H_DACH_H+15, "Scharnier", fontsize=4.5, color=HINGE)

# Ausklinkungskerben Seitenansicht
for _sy in [P/2, T-P/2]:
    draw_notch_mark(ax_side, _sy, 0,   size=_nk, axis='v', color=NOTCH)
    draw_notch_mark(ax_side, _sy, H-P, size=_nk, axis='v', color=NOTCH)

# M8x60 Schrauben Y-Richtung (Bodenecken)
for _sy in [P/2, T-P/2]:
    for _sz in [P*0.28, P*0.72]:
        ax_side.add_patch(mpatches.Circle((_sy, _sz), 9,
            lw=0.8, edgecolor="#e67e22", facecolor="white", alpha=0.85, zorder=9))
        ax_side.plot([_sy-5.5, _sy+5.5], [_sz, _sz], color="#e67e22", lw=0.6, zorder=10)
        ax_side.plot([_sy, _sy], [_sz-5.5, _sz+5.5], color="#e67e22", lw=0.6, zorder=10)
# M10x80 von oben an OG
for _sy in [P/2, T-P/2]:
    ax_side.add_patch(mpatches.Circle((_sy, H+5), _scr_r,
        lw=1.0, edgecolor=NOTCH, facecolor="white", alpha=0.9, zorder=9))
    ax_side.plot([_sy-_scr_r*0.65, _sy+_scr_r*0.65], [H+5, H+5],
                 color=NOTCH, lw=0.8, zorder=10)
    ax_side.plot([_sy, _sy], [H+5-_scr_r*0.65, H+5+_scr_r*0.65],
                 color=NOTCH, lw=0.8, zorder=10)

# ============================================================================
# Isometrie (geschlossen)
# ============================================================================
ax_iso.set_title("Isometrie  (geschlossen)", fontsize=7, pad=2, fontweight="bold")
ax_iso.set_facecolor("#eef2f8")
draw_list(ax_iso, members, proj_iso, lw=0.8, alpha=0.9)
ax_iso.autoscale_view(); ax_iso.margins(0.07)
ax_iso.legend(handles=LEGEND, loc="lower left", fontsize=4.2, framealpha=0.85,
              handlelength=1.0, borderpad=0.5)

# ============================================================================
# Draufsicht (XY)
# ============================================================================
ax_top.set_title("Draufsicht  (Grundriss)", fontsize=7, pad=2, fontweight="bold")
for m in members:
    pts = get_corners(m)
    p2  = proj_top(pts)
    p2[:,1] = T - p2[:,1]
    col = m["color"]
    if _SCIPY:
        try:
            hull = _CH(p2)
            ax_top.add_patch(plt.Polygon(p2[hull.vertices], closed=True,
                             facecolor=col, edgecolor=col, alpha=0.22, lw=0.5, zorder=2))
            hv = np.vstack([p2[hull.vertices], p2[hull.vertices[0]]])
            ax_top.plot(hv[:,0],hv[:,1], color=col, lw=0.5, zorder=3)
        except Exception:
            _draw_edges(ax_top, p2, col, 0.4, 0.8, 2, "-")
    else:
        _draw_edges(ax_top, p2, col, 0.4, 0.8, 2, "-")
ax_top.set_xlim(-400, 1700); ax_top.set_ylim(-400, 1700)
ax_top.tick_params(labelleft=True,labelbottom=True,labelsize=5,left=True,bottom=True)
ax_top.set_xlabel("Breite [mm]", fontsize=5.5)
ax_top.set_ylabel("Tiefe [mm]",  fontsize=5.5)
ax_top.invert_yaxis()
dim_line(ax_top,  0,-130, B,-130, "B=%d" % B, offset=22, fontsize=5.5)
dim_line(ax_top,-130, 0, -130, T, "T=%d" % T, offset=22, fontsize=5.5)
# Dachüberstand Draufsicht (zeigt 1800×1800 vs 1200×1200)
dim_line(ax_top, -OVER, -280, B+OVER, -280, "Dach-B=%d" % (B+2*OVER), offset=22, fontsize=5.5)
dim_line(ax_top, -280, -OVER, -280, T+OVER, "Dach-T=%d" % (T+2*OVER), offset=22, fontsize=5.5)
ax_top.annotate("Vorne (Tuer)", xy=(B/2,20), xytext=(B/2,-55),
                arrowprops=dict(arrowstyle="->",color="#c00",lw=0.8),
                fontsize=5, color="#c00", ha="center", zorder=12)
for _sx in [200, B-200-HNG_W]:
    ax_top.add_patch(mpatches.Rectangle((_sx, -(T-T+CW)), HNG_W, CW+5,
                     lw=0.8, edgecolor=HINGE, facecolor=HINGE, alpha=0.5, zorder=5))
ax_top.text(B/2, -80, "Scharnier", ha="center", fontsize=4.5, color=HINGE)

# ============================================================================
# Geöffneter Zustand
# ============================================================================
ax_open.set_title("Geoeffneter Zustand  (~90 Grad) – Seitenansicht",
                  fontsize=7, pad=2, fontweight="bold")
draw_list(ax_open, members_wall, proj_side, lw=0.6, alpha=0.85)
draw_list(ax_open, members_roof, proj_side, lw=0.5, alpha=0.4, ls="--")
draw_list(ax_open, members_roof, proj_side, lw=1.0, alpha=0.95,
          transform=lambda c: rotate_open(c, 90))
_ta = np.linspace(-math.pi/2, 0, 30)
_ra = 200
ax_open.plot(T + _ra*np.cos(_ta), H_DACH_H + _ra*np.sin(_ta), color=HINGE, lw=1.0)
ax_open.annotate("", xy=(T, H_DACH_H+_ra),
                xytext=(T+_ra*np.cos(-math.pi/8), H_DACH_H+_ra*np.sin(-math.pi/8)),
                arrowprops=dict(arrowstyle="->",color=HINGE,lw=1.0))
ax_open.text(T+_ra+15, H_DACH_H+_ra//2, "90 Grad", fontsize=6, color=HINGE)
ax_open.plot(T, H_DACH_H, "o", ms=6, color=HINGE, zorder=9)
ax_open.text(T+20, H_DACH_H+20, "Scharnier\nAchse", fontsize=4.5, color=HINGE)
_frt_y_open = T + (H_DACH_H - H_DACH_V)
_frt_z_open = H_DACH_H - T
ax_open.annotate("Vorderkante\nDach (offen)",
                 xy=(_frt_y_open, _frt_z_open+30),
                 xytext=(_frt_y_open+120, _frt_z_open+200),
                 arrowprops=dict(arrowstyle="->",color=ROOF,lw=0.7),
                 fontsize=4.5, color=ROOF)
ax_open.set_xlim(-400, 2000); ax_open.set_ylim(-200, 3000)
ax_open.tick_params(labelleft=True,labelbottom=True,labelsize=5,left=True,bottom=True)
ax_open.set_xlabel("Tiefe [mm]",  fontsize=5.5)
ax_open.set_ylabel("Hoehe [mm]",  fontsize=5.5)
ax_open.text(0.5,0.97,"– offen     – – geschlossen",
             transform=ax_open.transAxes,ha="center",va="top",fontsize=5,color="#555")

# ============================================================================
# Detail A: Ausklinkung Obergurt–Eckstiel  (Typ 4, M ca. 1:1)
# Aufbau: linke Hälfte = Draufsicht Kreuzung (XY), rechte Hälfte = Seitenansicht (YZ)
# ============================================================================
ax_det.set_title("Detail A: Ausklinkung Obergurt–Eckstiel  (Typ 4, M ca.1:1)",
                 fontsize=7, pad=2, fontweight="bold")
ax_det.set_facecolor("#fffff5")
ax_det.tick_params(labelleft=True, labelbottom=True, labelsize=5,
                   left=True, bottom=True)
ax_det.set_xlabel("X-Achse [mm]  /  linke Haelfte: Draufsicht  |  rechte Haelfte: Seitenansicht",
                  fontsize=4.5)
ax_det.set_ylabel("Hoehe / Tiefe [mm]", fontsize=4.5)

# Gemeinsame Einstellungen
_P   = P      # = 50
_P2  = P2     # = 25
_GAP = 30     # Abstand zw. den zwei Sub-Ansichten
_EXT = 80     # wie weit die Profile über den Knoten hinausragen

# ── Linke Hälfte: DRAUFSICHT der Kreuzung (XY-Ebene) ──────────────────────
# Ursprung bei (0,0) = linke obere Ecke des Kreuzungsbereichs
# Y-Achse nach unten (Tiefe), X-Achse nach rechts (Breite)
#
#  OG_L (Längsriegel, Y-Richtung, 50 mm breit): x = 0..50, y = -EXT .. 50+EXT
#  EP_VL (Eckstiel, dargestellt als 50x50 in Draufsicht): x=0..50, y=0..50
#  Ausklinkung des EP-Zapfens: EP hat Zapfen bei y=0..25 (y-Richtung)
#    → die andere Hälfte (y=25..50) des Stielkopfs wurde weggeschnitten

# OG_L in Draufsicht (durchlaufend)
ax_det.add_patch(mpatches.FancyBboxPatch((0, -_EXT), _P, _EXT + _P + _EXT,
    boxstyle="square,pad=0", lw=1.2, edgecolor=STEEL, facecolor=STEEL,
    alpha=0.15, zorder=2))
# Schraffur OG_L
for _yi in np.arange(-_EXT+5, _P+_EXT, 9):
    ax_det.plot([2, _P-2], [_yi, min(_yi+7, _P+_EXT-1)],
                color=STEEL, lw=0.3, alpha=0.4, zorder=3)

# EP_VL in Draufsicht (voller 50x50 Querschnitt)
ax_det.add_patch(mpatches.FancyBboxPatch((0, 0), _P, _P,
    boxstyle="square,pad=0", lw=1.5, edgecolor=STEEL, facecolor=STEEL,
    alpha=0.25, zorder=4))

# Weggeschnittener Teil des Stielkopfes (y=P2..P = hintere Hälfte)
ax_det.add_patch(mpatches.FancyBboxPatch((0, _P2), _P, _P2,
    boxstyle="square,pad=0", lw=1.0, edgecolor=NOTCH,
    facecolor="white", alpha=0.9, zorder=5,
    linestyle="--"))
ax_det.text(_P/2, _P2 + _P2/2, "WEGGE-\nFRÄST", ha="center", va="center",
            fontsize=3.5, color=NOTCH, zorder=6, fontweight="bold")

# Zapfen-Bereich (bleibt stehen)
ax_det.add_patch(mpatches.FancyBboxPatch((0, 0), _P, _P2,
    boxstyle="square,pad=0", lw=1.5, edgecolor=NOTCH,
    facecolor=NOTCH, alpha=0.18, zorder=5))
ax_det.text(_P/2, _P2/2, "ZAPFEN\n50x25", ha="center", va="center",
            fontsize=3.5, color=NOTCH, zorder=6, fontweight="bold")

# OG_L Tasche (weggeschnitten)
ax_det.add_patch(mpatches.FancyBboxPatch((0, 0), _P, _P2,
    boxstyle="square,pad=0", lw=1.5, edgecolor=NOTCH,
    facecolor="none", zorder=7, linestyle="-"))

# M10x80 Schraube von oben (als Kreis mit Kreuz = Stirnansicht)
_bx = _P/2;  _by = _P2/2
ax_det.add_patch(mpatches.Circle((_bx, _by), 6,
    lw=1.2, edgecolor=NOTCH, facecolor="white", alpha=0.95, zorder=9))
ax_det.plot([_bx-4, _bx+4], [_by, _by], color=NOTCH, lw=1.0, zorder=10)
ax_det.plot([_bx, _bx], [_by-4, _by+4], color=NOTCH, lw=1.0, zorder=10)
ax_det.annotate("M10x80\nvon oben",
                xy=(_bx+6, _by), xytext=(_bx+18, _by-15),
                fontsize=3.8, color=NOTCH,
                arrowprops=dict(arrowstyle="->", color=NOTCH, lw=0.5), zorder=11)

# Bemaßung Draufsicht
dim_line(ax_det, 0, _P+_EXT+12, _P, _P+_EXT+12,
         "50 mm", offset=10, fontsize=4.2)
dim_line(ax_det, _P+12, 0, _P+12, _P2,
         "25 mm\n(Zapfen)", offset=-14, fontsize=4.2)
dim_line(ax_det, _P+12, _P2, _P+12, _P,
         "25 mm\n(weggefr.)", offset=-16, fontsize=4.2)

ax_det.text(_P/2, -_EXT-8, "DRAUFSICHT  OG-EP  (XY)\n50x50 mm Quersch.",
            ha="center", fontsize=4.5, color=STEEL, fontweight="bold")

# Trennlinie
_SX = _P + _GAP + 15
ax_det.axvline(_SX - _GAP//2, color="#aaa", lw=0.8, ls=":", zorder=1)

# ── Rechte Hälfte: SEITENANSICHT des Knotens (YZ-Ebene) ───────────────────
# Ursprung: (_SX, 0)  |  Y-Achse = Tiefe, Z-Achse = Höhe (nach oben)
# Koordinaten: xr = _SX + y_local,  yr = z_local
# z_local=0 entspricht der OG-Unterkante (z_real = H-P = 2150)
# EP Zapfen: y=0..P2, z_local=0..P2  (50x25mm, 25mm tief)
# EP-Schaft: y=0..P, z_local=-EXT..0 (von unten kommend)
# OG:        y=0..P+EXT, z_local=0..P  (Obergurt)

# EP-Schaft (von unten)
ax_det.add_patch(mpatches.FancyBboxPatch((_SX, -_EXT), _P, _EXT,
    boxstyle="square,pad=0", lw=1.2, edgecolor=STEEL, facecolor=STEEL,
    alpha=0.15, zorder=2))
for _h in np.arange(-_EXT+5, 0, 9):
    ax_det.plot([_SX+2, _SX+_P-2], [_h, min(_h+7, -1)],
                color=STEEL, lw=0.3, alpha=0.4, zorder=3)
ax_det.text(_SX + _P/2, -_EXT/2, "Eckstiel\n50x50", ha="center", va="center",
            fontsize=3.5, color=STEEL, zorder=4)

# EP Zapfen (50x25 Querschnitt sichtbar als Rechteck, z=0..P2, y=0..P)
# In YZ-Ansicht: Zapfen-Tiefe y=0..P2=25 → nur vordere 25mm des Stiels,
# sichtbar als schmales Rechteck
ax_det.add_patch(mpatches.FancyBboxPatch((_SX, 0), _P2, _P2,
    boxstyle="square,pad=0", lw=1.5, edgecolor=NOTCH, facecolor=NOTCH,
    alpha=0.25, zorder=5))
ax_det.text(_SX + _P2/2, _P2/2, "Zapfen\n50x25\nx25mm", ha="center", va="center",
            fontsize=3.5, color=NOTCH, fontweight="bold", zorder=6)

# OG (50mm hoch, ragt vor und hinter Zapfen heraus)
ax_det.add_patch(mpatches.FancyBboxPatch((_SX - 10, 0), _P + _EXT + 10, _P,
    boxstyle="square,pad=0", lw=1.2, edgecolor=STEEL, facecolor=STEEL,
    alpha=0.15, zorder=2))
for _yi2 in np.arange(-5, _P + _EXT + 5, 9):
    ax_det.plot([_SX - 10 + _yi2, _SX - 10 + min(_yi2+7, _P+_EXT+9)],
                [2, _P-2], color=STEEL, lw=0.3, alpha=0.4, zorder=3)
ax_det.text(_SX + _P + _EXT/2, _P/2, "OG-L\n50x50", ha="center", va="center",
            fontsize=3.5, color=STEEL, zorder=4)

# OG Tasche (weggeschnitten, gestrichelter Rahmen)
ax_det.add_patch(mpatches.FancyBboxPatch((_SX, 0), _P2, _P2,
    boxstyle="square,pad=0", lw=1.5, edgecolor=NOTCH,
    facecolor="none", zorder=6, linestyle="--"))
ax_det.text(_SX + _P2 + 4, _P2/2, "Tasche\n50x25\nx25", fontsize=3.5,
            color=NOTCH, va="center", zorder=7)

# M10x80 Schraube von oben (in YZ-Ansicht: senkrechte Linie + Pfeil)
_bsx = _SX + _P2/2
ax_det.annotate("", xy=(_bsx, 0), xytext=(_bsx, _P + 22),
                arrowprops=dict(arrowstyle="-|>", color=NOTCH,
                                lw=1.2, mutation_scale=8))
ax_det.plot([_bsx - 5, _bsx + 5], [_P + 22, _P + 22],
            color=NOTCH, lw=2.0, zorder=8)
ax_det.text(_bsx + 8, _P + 15, "M10x80\n(von oben)",
            fontsize=3.8, color=NOTCH, va="center", zorder=9)

# Stoßfuge / Kontaktfläche
ax_det.plot([_SX - 10, _SX + _P2], [0, 0],
            color="#222", lw=2.5, zorder=7, solid_capstyle="butt")
ax_det.text(_SX + _P2 + 3, -4, "Kontaktfl.", fontsize=3.5, color="#444", va="top")

# Bemaßung Seitenansicht
dim_line(ax_det, _SX + _P + _EXT + 10, 0, _SX + _P + _EXT + 10, _P,
         "OG 50mm", offset=-18, fontsize=4.2)
dim_line(ax_det, _SX, -_EXT - 12, _SX + _P2, -_EXT - 12,
         "Zapfen\n25mm", offset=10, fontsize=4.2)

ax_det.text(_SX + _P/2, -_EXT - 8, "SEITENANSICHT  OG-EP  (YZ)\nTyp 4 Zapfen/Tasche",
            ha="center", fontsize=4.5, color=STEEL, fontweight="bold")

# Hinweistext (Formschluss)
_tx = (_SX + 20 + _P + _EXT) / 2
ax_det.text(_P/2 + (_SX/2), _P + 14,
            "Formschluessige Verbindung – Schraube nur zur Lagesicherung",
            ha="center", fontsize=4.8, color=NOTCH, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#fff8f0", ec=NOTCH, alpha=0.9,
                      lw=0.8), zorder=12)

# Achs-Limits für ax_det
ax_det.set_xlim(-32, _SX + _P + _EXT + 38)
ax_det.set_ylim(-_EXT - 28, _P + 38)

# ── Schriftfeld ──────────────────────────────────────────────────────────────
tb = fig.add_axes([LM, 0.003, 1-LM-RM, BM-0.005])
tb.set_axis_off(); tb.set_xlim(0,1); tb.set_ylim(0,1)
for (x0,y0,w_,h_) in [(0,0,1,1),(0,0.5,1,0),(0.25,0,0,1),(0.5,0,0,1),(0.75,0,0,1)]:
    tb.plot([x0,x0+w_],[y0,y0+h_],"k-",lw=0.5,transform=tb.transAxes)
for (fx,fy,lbl,val) in [
    (0.00,0.55,"Projekt","Gewaechshaus 1200x1200x2200  –  Aufklappbares Pultdach"),
    (0.00,0.02,"Massstab","1:20 (Referenz)"),
    (0.25,0.55,"Blatt","1 / 1"),
    (0.25,0.02,"Format","DIN A3"),
    (0.50,0.55,"Dachneigung","%.1f Grad  |  Delta = %d mm" % (_roof_angle, RISE)),
    (0.50,0.02,"Erstellt mit","Python / matplotlib"),
    (0.75,0.55,"Datum","2025"),
    (0.75,0.02,"Verbindung","Ausklinkungen Typ 1-4  (Formschluss + Schraubensicherung)"),
]:
    tb.text(fx+0.01,fy+0.28,lbl,fontsize=5,color="#555",transform=tb.transAxes,va="center")
    tb.text(fx+0.01,fy+0.02,val,fontsize=6.5,fontweight="bold",
            transform=tb.transAxes,va="bottom")
fig.add_artist(plt.Rectangle((0.01,0.01),0.98,0.98,
               fill=False,edgecolor="#222",lw=1.2,transform=fig.transFigure,zorder=20))

# ============================================================================
# ZWEITE SEITE: Bodenkonstruktion Details (3 Panels)
# ============================================================================
from matplotlib.backends.backend_pdf import PdfPages

fig2 = plt.figure(figsize=(420*MM2IN, 297*MM2IN), dpi=150)
fig2.patch.set_facecolor("white")

ax_gdr  = fig2.add_axes([LM,              BM, CW3, 1-BM-TM-0.02])
ax_saa  = fig2.add_axes([LM+CW3+GH,       BM, CW3, 1-BM-TM-0.02])
ax_dtl2 = fig2.add_axes([LM+2*(CW3+GH),   BM, CW3, 1-BM-TM-0.02])

for _ax2 in (ax_gdr, ax_saa, ax_dtl2):
    _ax2.set_facecolor("#f9f9f9")
    for sp in _ax2.spines.values():
        sp.set_linewidth(0.4); sp.set_edgecolor("#666")
    _ax2.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    _ax2.grid(True, lw=0.2, color="#cccccc")

# --------------------------------------------------------------------------
# Panel 1: Grundriss-Detail Dielenboden (XY-Draufsicht)
# --------------------------------------------------------------------------
ax_gdr.set_title("Grundriss – Holzdielenboden\n(Draufsicht, M ca. 1:10)",
                 fontsize=7, pad=3, fontweight="bold")
ax_gdr.set_aspect("equal")
ax_gdr.tick_params(labelleft=True, labelbottom=True, labelsize=5, left=True, bottom=True)

# Bodenrahmen-Outline
ax_gdr.add_patch(mpatches.FancyBboxPatch((0,0), B, T, boxstyle="square,pad=0",
    lw=1.5, edgecolor=STEEL, facecolor="none", zorder=2))
# BR_L, BR_R, BR_V, BR_H als Füllrechtecke
for _rx,_ry,_rw,_rh in [(0,0,P,T),(B-P,0,P,T),(0,0,B,P),(0,T-P,B,P)]:
    ax_gdr.add_patch(mpatches.FancyBboxPatch((_rx,_ry),_rw,_rh,
        boxstyle="square,pad=0", lw=0.5, edgecolor=STEEL, facecolor=STEEL,
        alpha=0.22, zorder=3))

# Querträger
for _qi, _qy in enumerate(_qt_ys):
    ax_gdr.add_patch(mpatches.FancyBboxPatch((P, _qy), B-2*P, QT_B,
        boxstyle="square,pad=0", lw=1.0, edgecolor=WOOD, facecolor=WOOD,
        alpha=0.45, zorder=4))
    ax_gdr.text(B/2, _qy + QT_B/2, "QT%d" % (_qi+1),
        ha="center", va="center", fontsize=4.5, color="white", fontweight="bold", zorder=6)

# Dielen
for _pi in range(N_PL):
    _px = _pl_x0 + _pi*(PLANK_W+PL_GAP)
    ax_gdr.add_patch(mpatches.FancyBboxPatch((_px, P), PLANK_W, T-2*P,
        boxstyle="square,pad=0", lw=0.5, edgecolor="#5a3510",
        facecolor=WOOD, alpha=0.22, zorder=5))

# Trittholm – volle Breite 1200 mm
ax_gdr.add_patch(mpatches.FancyBboxPatch((0, 0), B, TH_D,
    boxstyle="square,pad=0", lw=1.0, edgecolor=WOOD, facecolor=WOOD,
    alpha=0.5, zorder=6))
ax_gdr.text(B/2, TH_D/2, "Trittholm 1200 mm", ha="center", va="center",
    fontsize=4.0, color="white", fontweight="bold", zorder=7)

# Mittelstiel im Grundriss
ax_gdr.add_patch(mpatches.FancyBboxPatch((MITTELSTIEL_X, 0), P, P,
    boxstyle="square,pad=0", lw=1.2, edgecolor=DOOR, facecolor=DOOR,
    alpha=0.6, zorder=7))
ax_gdr.text(MITTELSTIEL_X+P/2, P/2, "MS", ha="center", va="center",
    fontsize=4.0, color="white", fontweight="bold", zorder=8)

# Türflügel-Öffnungsbögen (90° geöffnet, gestrichelt)
_theta = np.linspace(0, np.pi/2, 40)
# Linker Flügel: Scharnier bei (P, 0), Radius = DW_SINGLE = 575 mm
ax_gdr.plot(P + DW_SINGLE*np.cos(_theta), -DW_SINGLE*np.sin(_theta),
    color=DOOR, lw=0.9, ls="--", zorder=6, alpha=0.75)
ax_gdr.plot([P, P], [0, -DW_SINGLE], color=DOOR, lw=0.4, ls=":", zorder=5, alpha=0.5)
# Rechter Flügel: Scharnier bei (B-P, 0)
ax_gdr.plot(B-P - DW_SINGLE*np.cos(_theta), -DW_SINGLE*np.sin(_theta),
    color=DOOR, lw=0.9, ls="--", zorder=6, alpha=0.75)
ax_gdr.plot([B-P, B-P], [0, -DW_SINGLE], color=DOOR, lw=0.4, ls=":", zorder=5, alpha=0.5)
ax_gdr.text(B/2, -DW_SINGLE*0.45, "Öffnungsbögen 90°", ha="center", fontsize=4.0,
    color=DOOR, zorder=7, style="italic")

# Schnitt-Linie A-A (bei QT2)
_aa_y = _qt_ys[1] + QT_B/2
ax_gdr.axhline(_aa_y, color="red", lw=1.0, ls="-.", zorder=8, xmin=-0.1, xmax=1.1,
               clip_on=False)
for _aax in [-80, B+30]:
    ax_gdr.text(_aax, _aa_y, "A", ha="center", va="center",
                fontsize=8, color="red", fontweight="bold", zorder=9)

# Bemaßung Dielenbreite + Fuge
_dm_y = T + 80
dim_line(ax_gdr, _pl_x0, _dm_y, _pl_x0+PLANK_W, _dm_y, "%d mm" % PLANK_W,
         offset=18, fontsize=4.5)
dim_line(ax_gdr, _pl_x0+PLANK_W, _dm_y+12, _pl_x0+PLANK_W+PL_GAP, _dm_y+12,
         "%d mm" % PL_GAP, offset=10, fontsize=4.0)

# Bemaßung Querträger-Abstand
_dm_x = B + 90
dim_line(ax_gdr, _dm_x, _qt_ys[0]+QT_B, _dm_x, _qt_ys[1], "~%d mm" % _qt_step,
         offset=-30, fontsize=4.5)
dim_line(ax_gdr, _dm_x, _qt_ys[0], _dm_x, _qt_ys[0]+QT_B, "%d mm" % QT_B,
         offset=-25, fontsize=4.5)

dim_line(ax_gdr, 0, -100, B, -100, "B = %d mm" % B, offset=22, fontsize=5.5)
dim_line(ax_gdr, -140, 0, -140, T, "T = %d mm" % T, offset=25, fontsize=5.5)
dim_line(ax_gdr, P, -60, B-P, -60, "lichte Weite %d mm" % (B-2*P), offset=14, fontsize=4.5)

ax_gdr.text(B/2, T/2, "9× Diele\n116×22 Lärche\n4 mm Fuge\n\n4× QT KVH\n60×60 mm",
    ha="center", va="center", fontsize=4.5, color="#5a3510", zorder=7,
    bbox=dict(fc="white", ec=WOOD, alpha=0.8, boxstyle="round,pad=0.3", lw=0.7))

ax_gdr.text(P/2, T/2, "BR_L", ha="center", va="center", fontsize=4.0,
    color=STEEL, rotation=90, zorder=6)
ax_gdr.text(B-P/2, T/2, "BR_R", ha="center", va="center", fontsize=4.0,
    color=STEEL, rotation=90, zorder=6)

ax_gdr.set_xlim(-170, 1400); ax_gdr.set_ylim(-650, 1420)
ax_gdr.set_xlabel("Breite [mm]", fontsize=5.5)
ax_gdr.set_ylabel("Tiefe [mm]",  fontsize=5.5)
ax_gdr.invert_yaxis()

# --------------------------------------------------------------------------
# Panel 2: Schnitt A-A (XZ-Querschnitt durch Dielenboden)
# --------------------------------------------------------------------------
ax_saa.set_title("Schnitt A–A – Bodenquerschnitt\n(bei QT2, Blickrichtung +Y)",
                 fontsize=7, pad=3, fontweight="bold")
ax_saa.set_aspect("equal")
ax_saa.tick_params(labelleft=True, labelbottom=True, labelsize=5, left=True, bottom=True)
ax_saa.axhline(0, color="#888", lw=0.5, ls="--", zorder=1)

# BR_L (links)
ax_saa.add_patch(mpatches.FancyBboxPatch((0,0), P, P, boxstyle="square,pad=0",
    lw=1.2, edgecolor=STEEL, facecolor=STEEL, alpha=0.3, zorder=3))
for _sh in np.arange(4, P, 7):
    ax_saa.plot([2, P-2], [_sh, _sh], color=STEEL, lw=0.3, alpha=0.5, zorder=4)
ax_saa.text(P/2, P/2, "BR_L\n50×50", ha="center", va="center",
    fontsize=3.5, color=STEEL, fontweight="bold", zorder=5)

# BR_R (rechts)
ax_saa.add_patch(mpatches.FancyBboxPatch((B-P,0), P, P, boxstyle="square,pad=0",
    lw=1.2, edgecolor=STEEL, facecolor=STEEL, alpha=0.3, zorder=3))
for _sh in np.arange(4, P, 7):
    ax_saa.plot([B-P+2, B-2], [_sh, _sh], color=STEEL, lw=0.3, alpha=0.5, zorder=4)
ax_saa.text(B-P/2, P/2, "BR_R\n50×50", ha="center", va="center",
    fontsize=3.5, color=STEEL, fontweight="bold", zorder=5)

# Querträger (volle lichte Weite)
ax_saa.add_patch(mpatches.FancyBboxPatch((P, P), B-2*P, QT_H, boxstyle="square,pad=0",
    lw=1.2, edgecolor=WOOD, facecolor=WOOD, alpha=0.35, zorder=4))
for _sh in np.arange(P+5, P+QT_H, 7):
    ax_saa.plot([P+3, B-P-3], [_sh, _sh], color=WOOD, lw=0.3, alpha=0.35, zorder=5)
ax_saa.text(B/2, P+QT_H/2, "Querträger KVH 60×60 mm",
    ha="center", va="center", fontsize=5.0, color=WOOD, fontweight="bold", zorder=6)

# M6×40 Schrauben (links + rechts)
for _sx in [P/2, B-P/2]:
    ax_saa.add_patch(mpatches.Circle((_sx, P+QT_H*0.5), 5,
        lw=1.0, edgecolor="#e67e22", facecolor="white", alpha=0.95, zorder=8))
    ax_saa.plot([_sx-3, _sx+3], [P+QT_H*0.5, P+QT_H*0.5], color="#e67e22", lw=0.7, zorder=9)
    ax_saa.plot([_sx, _sx], [P+QT_H*0.5-3, P+QT_H*0.5+3], color="#e67e22", lw=0.7, zorder=9)
ax_saa.text(P/2-40, P+QT_H*0.5, "M6×40", ha="right", va="center",
    fontsize=4.0, color="#e67e22", zorder=9)

# 9 Dielen (Querschnitte)
for _pi in range(N_PL):
    _px = _pl_x0 + _pi*(PLANK_W+PL_GAP)
    ax_saa.add_patch(mpatches.FancyBboxPatch((_px, P+QT_H), PLANK_W, PLANK_T,
        boxstyle="square,pad=0", lw=0.8, edgecolor="#5a3510",
        facecolor=WOOD, alpha=0.55, zorder=5))
    if _pi in (0, 4, 8):
        ax_saa.text(_px+PLANK_W/2, P+QT_H+PLANK_T/2,
            "D%d" % (_pi+1), ha="center", va="center",
            fontsize=3.5, color="white", zorder=7)

# Fuge-Markierung (erste Fuge)
_fg_x = _pl_x0 + PLANK_W
ax_saa.fill_betweenx([P+QT_H, P+QT_H+PLANK_T], _fg_x, _fg_x+PL_GAP,
    color="#bbb", alpha=0.9, zorder=6)
ax_saa.annotate("Fuge\n4 mm",
    xy=(_fg_x+PL_GAP/2, P+QT_H+PLANK_T+2),
    xytext=(_fg_x-30, P+QT_H+PLANK_T+35),
    arrowprops=dict(arrowstyle="->", color="#555", lw=0.5),
    fontsize=4.0, color="#555", ha="center", zorder=9)

# Bemaßungslinien
dim_line(ax_saa, -60,   0,  -60, P,            "50mm",       offset=24, fontsize=4.5)
dim_line(ax_saa, -60,   P,  -60, P+QT_H,       "60mm",       offset=24, fontsize=4.5)
dim_line(ax_saa, -60,   P+QT_H, -60, P+QT_H+PLANK_T, "22mm", offset=22, fontsize=4.5)
dim_line(ax_saa, -110,  0,  -110, P+QT_H+PLANK_T, "132mm\ngesamt", offset=28, fontsize=5.0)
dim_line(ax_saa, 0,  -50,  B,  -50, "1200 mm", offset=18, fontsize=5.5)
dim_line(ax_saa, P,  -80,  B-P, -80, "1100 mm (lichte Weite)", offset=14, fontsize=4.5)
dim_line(ax_saa, _pl_x0, -50, _pl_x0+PLANK_W, -50, "%d mm" % PLANK_W, offset=10, fontsize=4.0)

ax_saa.set_xlim(-160, 1380); ax_saa.set_ylim(-120, 220)
ax_saa.set_xlabel("Breite [mm]", fontsize=5.5)
ax_saa.set_ylabel("Höhe [mm]",   fontsize=5.5)

# --------------------------------------------------------------------------
# Panel 3: Detail Bodenaufbau (Schicht für Schicht, M ca. 2:1)
# --------------------------------------------------------------------------
ax_dtl2.set_title("Detail Bodenaufbau – Querschnitt Schicht",
                  fontsize=7, pad=3, fontweight="bold")
ax_dtl2.set_facecolor("#fffff5")
ax_dtl2.set_aspect("equal")
ax_dtl2.tick_params(labelleft=True, labelbottom=True, labelsize=5, left=True, bottom=True)

_DLX  = 60    # x-Startposition der Layer-Darstellung
_DLW  = 150   # Breite der Layer im Diagramm (≈ 2× Maßstab)
_LBL  = _DLX + _DLW + 18  # x-Position für Labels

# Bodenrahmen-Profil (linker Rand: Längsriegel)
ax_dtl2.add_patch(mpatches.FancyBboxPatch((_DLX, 0), P, P, boxstyle="square,pad=0",
    lw=1.5, edgecolor=STEEL, facecolor=STEEL, alpha=0.3, zorder=3))
for _sh in np.arange(5, P, 8):
    ax_dtl2.plot([_DLX+3, _DLX+P-3], [_sh, _sh], color=STEEL, lw=0.4, alpha=0.5, zorder=4)
    ax_dtl2.plot([_DLX+3, _DLX+_sh//2], [_sh, min(_sh+5, P-3)],
        color=STEEL, lw=0.3, alpha=0.35, zorder=4)
ax_dtl2.text(_LBL, P/2, "← Bodenrahmen\n   Stahl/Alu 50×50 mm\n   Vierkantrohr",
    va="center", fontsize=4.5, color=STEEL, zorder=6)

# Querträger KVH
ax_dtl2.add_patch(mpatches.FancyBboxPatch((_DLX, P), _DLW, QT_H, boxstyle="square,pad=0",
    lw=1.5, edgecolor=WOOD, facecolor=WOOD, alpha=0.35, zorder=3))
for _sh in np.arange(P+5, P+QT_H, 8):
    ax_dtl2.plot([_DLX+3, _DLX+_DLW-3], [_sh, _sh], color=WOOD, lw=0.4, alpha=0.45, zorder=4)
ax_dtl2.text(_LBL, P+QT_H/2,
    "← Querträger\n   KVH 60×60 mm\n   L=1100 mm\n   2× M6×40 Schraube",
    va="center", fontsize=4.5, color=WOOD, zorder=6)

# M6×40 Schraube (seitlich durch Bodenrahmen in QT)
_scx = _DLX + P/2
ax_dtl2.add_patch(mpatches.Circle((_scx, P + QT_H*0.38), 5,
    lw=1.0, edgecolor="#e67e22", facecolor="white", alpha=0.95, zorder=8))
ax_dtl2.plot([_scx-3, _scx+3], [P+QT_H*0.38]*2, color="#e67e22", lw=0.8, zorder=9)
ax_dtl2.plot([_scx]*2, [P+QT_H*0.38-3, P+QT_H*0.38+3], color="#e67e22", lw=0.8, zorder=9)
ax_dtl2.add_patch(mpatches.Circle((_scx, P + QT_H*0.65), 5,
    lw=1.0, edgecolor="#e67e22", facecolor="white", alpha=0.95, zorder=8))
ax_dtl2.plot([_scx-3, _scx+3], [P+QT_H*0.65]*2, color="#e67e22", lw=0.8, zorder=9)
ax_dtl2.plot([_scx]*2, [P+QT_H*0.65-3, P+QT_H*0.65+3], color="#e67e22", lw=0.8, zorder=9)

# Diele 1 (volle Breite)
_d1x = _DLX
ax_dtl2.add_patch(mpatches.FancyBboxPatch((_d1x, P+QT_H), _DLW*0.55, PLANK_T,
    boxstyle="square,pad=0", lw=1.5, edgecolor="#5a3510", facecolor=WOOD,
    alpha=0.55, zorder=5))
for _sh in [P+QT_H+5, P+QT_H+11, P+QT_H+18]:
    ax_dtl2.plot([_d1x+4, _d1x+_DLW*0.55-4], [_sh, _sh],
        color="#5a3510", lw=0.4, alpha=0.45, zorder=6)

# Fuge
_fgx = _d1x + _DLW*0.55
ax_dtl2.add_patch(mpatches.FancyBboxPatch((_fgx, P+QT_H), PL_GAP*2, PLANK_T,
    boxstyle="square,pad=0", lw=0.8, edgecolor="#aaa", facecolor="#ddd",
    alpha=0.9, zorder=6))
ax_dtl2.annotate("4 mm\nFuge",
    xy=(_fgx+PL_GAP, P+QT_H+PLANK_T+2),
    xytext=(_fgx-5, P+QT_H+PLANK_T+32),
    arrowprops=dict(arrowstyle="->", color="#555", lw=0.5),
    fontsize=4.0, color="#555", ha="center", zorder=10)

# Diele 2 (nach Fuge)
_d2x = _fgx + PL_GAP*2
ax_dtl2.add_patch(mpatches.FancyBboxPatch((_d2x, P+QT_H), _DLW*0.40, PLANK_T,
    boxstyle="square,pad=0", lw=1.5, edgecolor="#5a3510", facecolor=WOOD,
    alpha=0.55, zorder=5))
for _sh in [P+QT_H+5, P+QT_H+11, P+QT_H+18]:
    ax_dtl2.plot([_d2x+4, _d2x+_DLW*0.40-4], [_sh, _sh],
        color="#5a3510", lw=0.4, alpha=0.45, zorder=6)

ax_dtl2.text(_LBL, P+QT_H+PLANK_T/2,
    "← Diele Lärche\n   ~120×22 mm\n   Nut+Feder\n   Dielenklammern",
    va="center", fontsize=4.5, color="#5a3510", zorder=7)

# Bodenrahmen-Unterkante / Erdreich
ax_dtl2.axhline(0, color="#888", lw=0.8, ls="--", zorder=2)
ax_dtl2.text(_DLX-5, -8, "Erdreich / UK Bodenrahmen", fontsize=4.0, color="#888", ha="left")

# Höhen-Bemaßung (linke Seite)
dim_line(ax_dtl2, _DLX-20,  0,          _DLX-20, P,            "50 mm",       offset=18, fontsize=5.0)
dim_line(ax_dtl2, _DLX-20,  P,          _DLX-20, P+QT_H,       "60 mm",       offset=18, fontsize=5.0)
dim_line(ax_dtl2, _DLX-20,  P+QT_H,     _DLX-20, P+QT_H+PLANK_T, "22 mm",    offset=18, fontsize=5.0)
dim_line(ax_dtl2, _DLX-55,  0,          _DLX-55, P+QT_H+PLANK_T,
         "132 mm\nGesamt", offset=22, fontsize=5.5)

# Breiten-Bemaßung unten
dim_line(ax_dtl2, _d1x,  -35, _d1x+_DLW*0.55, -35, "~116 mm (Diele)", offset=14, fontsize=4.5)
dim_line(ax_dtl2, _DLX,  -60, _DLX+P,          -60, "50 mm (BR)", offset=12, fontsize=4.5)

# Gesamtbox
ax_dtl2.add_patch(mpatches.FancyBboxPatch((_DLX-5, -5), _DLW+10, P+QT_H+PLANK_T+10,
    boxstyle="square,pad=0", lw=1.5, edgecolor="#333", facecolor="none", zorder=10,
    linestyle="--"))
ax_dtl2.text(_DLX+_DLW/2, P+QT_H+PLANK_T+20,
    "OK Dielenboden = +%d mm\nüber Bodenrahmen-Unterkante" % (P+QT_H+PLANK_T),
    ha="center", fontsize=4.8, color=WOOD, fontweight="bold",
    bbox=dict(fc="white", ec=WOOD, alpha=0.85, boxstyle="round,pad=0.2", lw=0.8), zorder=11)

ax_dtl2.set_xlim(_DLX-90, _LBL+220)
ax_dtl2.set_ylim(-75, P+QT_H+PLANK_T+75)
ax_dtl2.set_xlabel("Breite [mm]",  fontsize=5.5)
ax_dtl2.set_ylabel("Höhe [mm]",    fontsize=5.5)

# Schriftfeld Seite 2
tb2 = fig2.add_axes([LM, 0.003, 1-LM-RM, BM-0.005])
tb2.set_axis_off(); tb2.set_xlim(0,1); tb2.set_ylim(0,1)
for (x0,y0,w_,h_) in [(0,0,1,1),(0,0.5,1,0),(0.25,0,0,1),(0.5,0,0,1),(0.75,0,0,1)]:
    tb2.plot([x0,x0+w_],[y0,y0+h_],"k-",lw=0.5,transform=tb2.transAxes)
for (fx,fy,lbl,val) in [
    (0.00,0.55,"Projekt","Gewaechshaus 1200x1200x2200  –  Holzdielenboden auf Querträgern"),
    (0.00,0.02,"Massstab","1:10 (Grundriss/Schnitt)  |  Detail ca. 2:1"),
    (0.25,0.55,"Blatt","2 / 2"),
    (0.25,0.02,"Format","DIN A3"),
    (0.50,0.55,"Bodenaufbau","Bodenrahmen 50mm + KVH 60×60mm + Lärche 22mm = 132mm Gesamt"),
    (0.50,0.02,"Erstellt mit","Python / matplotlib"),
    (0.75,0.55,"Datum","2025"),
    (0.75,0.02,"Materialien","KVH 60×60 | Lärche 116×22 | M6×40 | Trittholm 80×40"),
]:
    tb2.text(fx+0.01,fy+0.28,lbl,fontsize=5,color="#555",transform=tb2.transAxes,va="center")
    tb2.text(fx+0.01,fy+0.02,val,fontsize=6.5,fontweight="bold",
             transform=tb2.transAxes,va="bottom")
fig2.add_artist(plt.Rectangle((0.01,0.01),0.98,0.98,
               fill=False,edgecolor="#222",lw=1.2,transform=fig2.transFigure,zorder=20))

# PDF: beide Seiten speichern
pdf_path = os.path.join(OUT,"gewaechshaus_zeichnung.pdf")
with PdfPages(pdf_path) as _pdf:
    _pdf.savefig(fig,  bbox_inches="tight", dpi=150)
    plt.close(fig)
    _pdf.savefig(fig2, bbox_inches="tight", dpi=150)
    plt.close(fig2)
print("ok PDF: %s (2 Seiten)" % pdf_path)

# ============================================================================
# B)  PNG – Isometrische Ansicht
# ============================================================================
fig_iso, ax_i = plt.subplots(1,1, figsize=(14,10))
fig_iso.patch.set_facecolor("#1a1a2e")
ax_i.set_facecolor("#1a1a2e");  ax_i.set_aspect("equal");  ax_i.axis("off")

def iso_pt(x,y,z):
    c30=math.cos(math.radians(30)); s30=math.sin(math.radians(30))
    return (x-y)*c30, (x+y)*s30+z

_bx=[iso_pt(x,y,0)[0] for x,y in [(0,0),(B,0),(B,T),(0,T),(0,0)]]
_by=[iso_pt(x,y,0)[1] for x,y in [(0,0),(B,0),(B,T),(0,T),(0,0)]]
ax_i.fill(_bx,_by, color="#0a2040", alpha=0.5, zorder=0)
ax_i.plot(_bx,_by, color="#1e90ff", lw=0.4, alpha=0.3, zorder=1)

for m in members:
    c   = get_corners(m)
    p2  = proj_iso(c)
    col = m["color"]
    lw_m = 1.2 if m["group"] in ("Eckstiel","Dachrahmen","Scharnier") else 0.7
    if _SCIPY:
        try:
            hull = _CH(p2)
            ax_i.add_patch(plt.Polygon(p2[hull.vertices], closed=True,
                           facecolor=col, edgecolor="none", alpha=0.28, zorder=3))
        except Exception:
            pass
    for i,j in EDGES:
        ax_i.plot([p2[i,0],p2[j,0]],[p2[i,1],p2[j,1]],
                  color=col, lw=lw_m, alpha=0.95, zorder=4)

# Ausklinkungsmarkierungen an Ecken (isometrisch)
for (_ix, _iy) in [(0,0),(B,0),(0,T),(B,T)]:
    for _iz in [0, H-P]:
        _ip = iso_pt(_ix, _iy, _iz)
        ax_i.plot(_ip[0], _ip[1], 's', color=NOTCH, ms=5, alpha=0.8, zorder=8)

for _lbl,_pt3,_ct in [
    ("B = 1200 mm",     (B/2, -80,-80),      "#aaddff"),
    ("T = 1200 mm",     (B+80, T/2,-80),     "#aaddff"),
    ("H = 2200 mm",     (-120, 0, H/2),      "#aaddff"),
    ("Dach 2150-2450\nÜbst. 300mm",  (B/2, T/2, H_DACH_H+100), "#cc99ff"),
    ("Ausklinkung Typ 1-4", (B/2, T/2, H/2), NOTCH),
]:
    _px,_py = iso_pt(*_pt3)
    ax_i.text(_px,_py,_lbl, fontsize=9 if "Ausklinkung" not in _lbl else 8,
              color=_ct, ha="center", va="center", fontweight="bold",
              bbox=dict(boxstyle="round,pad=0.3",fc="#1a1a2e",ec=_ct,alpha=0.7,lw=0.6),
              zorder=15)

_sx1,_sy1 = iso_pt(200, T+HNG_D+5, H+HNG_H//2)
ax_i.annotate("Scharnier (2x)\n100x%dmm" % HNG_H,
              xy=(_sx1,_sy1), xytext=(_sx1+120,_sy1+120),
              arrowprops=dict(arrowstyle="->",color=HINGE,lw=1.0),
              fontsize=7.5, color=HINGE,
              bbox=dict(boxstyle="round,pad=0.3",fc="#1a1a2e",ec=HINGE,alpha=0.7),
              zorder=16)

ax_i.set_title("Gewaechshaus 1200x1200x2200 mm  –  Aufklappbares Pultdach + Überstand 300mm  –  Ausklinkungsverbindung",
               fontsize=13, color="white", pad=14, fontweight="bold")
ax_i.legend(handles=LEGEND, loc="lower right", fontsize=8, framealpha=0.7,
            facecolor="#222", edgecolor="#aaa", labelcolor="white", handlelength=1.5)
ax_i.autoscale_view();  ax_i.margins(0.07)
iso_png = os.path.join(OUT,"gewaechshaus_iso.png")
fig_iso.savefig(iso_png, dpi=180, bbox_inches="tight",
                facecolor=fig_iso.get_facecolor())
plt.close(fig_iso)
print("ok ISO: %s" % iso_png)

# ============================================================================
# C)  PNG – Vorderansicht
# ============================================================================
fig_fr, ax_f = plt.subplots(1,1, figsize=(10,11))
fig_fr.patch.set_facecolor("white")
ax_f.set_facecolor("#f5f5f5");  ax_f.set_aspect("equal")
draw_list(ax_f, members, proj_front, lw=1.0, alpha=0.9)
ax_f.set_xlim(-440, 1640);  ax_f.set_ylim(-260, 2820)
ax_f.set_xlabel("Breite [mm]", fontsize=10)
ax_f.set_ylabel("Hoehe [mm]",  fontsize=10)
ax_f.set_title("Gewaechshaus – Vorderansicht  (Türseite)  –  Ausklinkungsverbindung",
               fontsize=11, fontweight="bold", pad=12)
ax_f.grid(True, lw=0.3, color="#ccc");  ax_f.tick_params(labelsize=8)
dim_line(ax_f,  0,-160, B, -160, "Breite = %d mm" % B, offset=44)
dim_line(ax_f,-190, 0, -190, H,  "H = %d mm" % H, offset=35)
dim_line(ax_f,-190, H, -190, H_DACH_V+P, "+%d" % P, offset=35, fontsize=7)
# Türbemaßung: je Flügel einzeln
dim_line(ax_f, P,              -160, MITTELSTIEL_X, -160,
         "%d mm" % DW_SINGLE, offset=22)
dim_line(ax_f, MITTELSTIEL_X+P, -160, B-P,          -160,
         "%d mm" % DW_SINGLE, offset=22)
# Linker Türflügel (Füllbereich)
ax_f.add_patch(mpatches.FancyBboxPatch((P, P), DW_SINGLE, DH-P,
               boxstyle="square,pad=0", lw=1.2,
               edgecolor=DOOR, facecolor=DOOR, alpha=0.06, zorder=1))
ax_f.text(P + DW_SINGLE/2, DH/2, "Flügel L\n%d×%d" % (DW_SINGLE, DH),
          ha="center", va="center",
          fontsize=9, color=DOOR, fontweight="bold", zorder=5,
          bbox=dict(fc="white",ec=DOOR,alpha=0.7,boxstyle="round,pad=0.3"))
# Rechter Türflügel (Füllbereich)
ax_f.add_patch(mpatches.FancyBboxPatch((MITTELSTIEL_X+P, P), DW_SINGLE, DH-P,
               boxstyle="square,pad=0", lw=1.2,
               edgecolor=DOOR, facecolor=DOOR, alpha=0.06, zorder=1))
ax_f.text(MITTELSTIEL_X+P + DW_SINGLE/2, DH/2,
          "Flügel R\n%d×%d" % (DW_SINGLE, DH),
          ha="center", va="center",
          fontsize=9, color=DOOR, fontweight="bold", zorder=5,
          bbox=dict(fc="white",ec=DOOR,alpha=0.7,boxstyle="round,pad=0.3"))
# Scharniere (je 2 pro Flügel)
for _sh_x in [P/2, B-P/2]:
    for _sh_z in [350, 1600]:
        ax_f.add_patch(mpatches.Circle((_sh_x, _sh_z), 18,
            lw=1.5, edgecolor=HINGE, facecolor=HINGE, alpha=0.75, zorder=8))
        ax_f.text(_sh_x, _sh_z, "Sch", ha="center", va="center",
                  fontsize=5, color="white", fontweight="bold", zorder=9)
# Mittelstiel-Annotation
ax_f.annotate("Mittelstiel\n50×50 mm",
    xy=(MITTELSTIEL_X+P/2, DH*0.35),
    xytext=(MITTELSTIEL_X-260, 350),
    arrowprops=dict(arrowstyle="->", color=DOOR, lw=1.0),
    fontsize=8, color=DOOR, ha="center", zorder=10,
    bbox=dict(fc="white", ec=DOOR, alpha=0.85, boxstyle="round,pad=0.2"))
ax_f.axhline(H_DACH_V, color=ROOF, lw=0.8, ls="--", xmin=0.02, xmax=0.97, zorder=5)
ax_f.text(B+OVER+20, H_DACH_V+12, "Dachrahmen\nVK = %d mm" % H_DACH_V, fontsize=7, color=ROOF)
# Dachüberstand-Bemaßung Vorderansicht (links und rechts je 300 mm)
dim_line(ax_f, -OVER, -220, 0, -220, "ÜST=%d" % OVER, offset=30, fontsize=8)
dim_line(ax_f, B, -220, B+OVER, -220, "ÜST=%d" % OVER, offset=30, fontsize=8)
dim_line(ax_f, -OVER, -220, B+OVER, -220, "Dach-B=%d" % (B+2*OVER), offset=46, fontsize=8)

# Ausklinkungsmarkierungen gross
for _sx in [P/2, B-P/2]:
    # Boden
    ax_f.add_patch(mpatches.FancyBboxPatch((_sx-12, 0), 24, 14,
        boxstyle="square,pad=0", lw=1.0, edgecolor=NOTCH,
        facecolor=NOTCH, alpha=0.3, zorder=7))
    ax_f.text(_sx, 7, "T3", ha="center", va="center",
              fontsize=5, color=NOTCH, fontweight="bold", zorder=8)
    # OG Zapfen
    ax_f.add_patch(mpatches.FancyBboxPatch((_sx-12, H-P), 24, 14,
        boxstyle="square,pad=0", lw=1.0, edgecolor=NOTCH,
        facecolor=NOTCH, alpha=0.3, zorder=7))
    ax_f.text(_sx, H-P+7, "T4", ha="center", va="center",
              fontsize=5, color=NOTCH, fontweight="bold", zorder=8)
    # M10x80 von oben
    ax_f.add_patch(mpatches.Circle((_sx, H+8), 18,
        lw=1.2, edgecolor=NOTCH, facecolor="white", alpha=0.9, zorder=9))
    ax_f.plot([_sx-11, _sx+11],[H+8,H+8], color=NOTCH, lw=1.0, zorder=10)
    ax_f.plot([_sx,_sx],[H-3,H+19], color=NOTCH, lw=1.0, zorder=10)
ax_f.text(10, 22, "T3 = Zapfensitz Boden", fontsize=8, color=NOTCH)
ax_f.text(10, H-P+22, "T4 = Obergurt-Zapfen  |  o = M10x80 von oben",
          fontsize=8, color=NOTCH)
# Trittholm + Dielenboden in Vorderansicht-PNG (volle Breite 1200 mm)
ax_f.add_patch(mpatches.FancyBboxPatch((0, P), B, TH_H,
    boxstyle="square,pad=0", lw=1.5, edgecolor=WOOD, facecolor=WOOD,
    alpha=0.55, zorder=6))
ax_f.text(B/2, P+TH_H/2, "Trittholm 80×40 mm  –  1200 mm breit",
    ha="center", va="center", fontsize=7, color="white", fontweight="bold", zorder=7)
ax_f.annotate("Dielenboden OK\nz = +%d mm" % (P+QT_H+PLANK_T),
    xy=(B-P, P+QT_H+PLANK_T),
    xytext=(B+80, P+QT_H+PLANK_T+100),
    arrowprops=dict(arrowstyle="->", color=WOOD, lw=1.0),
    fontsize=8, color=WOOD, va="center", zorder=10,
    bbox=dict(fc="white", ec=WOOD, alpha=0.85, boxstyle="round,pad=0.2"))
ax_f.legend(handles=LEGEND, loc="upper right", fontsize=8, framealpha=0.85)
front_png = os.path.join(OUT,"gewaechshaus_front.png")
fig_fr.savefig(front_png, dpi=180, bbox_inches="tight")
plt.close(fig_fr)
print("ok FRONT: %s" % front_png)

# ============================================================================
# D)  STÜCKLISTE
# ============================================================================
bom = []
A   = bom.append

A("=" * 74)
A("  STUECKLISTE – Gewaechshaus 1200 x 1200 x 2200 mm")
A("  Aufklappbares Pultdach  (Neigung ca. %.1f Grad  |  Delta-Hoehe = %d mm)" % (_roof_angle, RISE))
A("  Verbindungsmethode: AUSKLINKUNGEN  (Klauen-/Zapfenverbindungen)")
A("=" * 74)
A("")
A("─── 1. HAUPTSTRUKTUR  (50 x 50 mm Vierkantprofil, Stahl/Alu) ─────────────")
A("")
A("  %-34s %8s %4s %9s %7s" % ("Bezeichnung", "L (mm)", "Stk", "Summe(mm)", "Summe(m)"))
A("  " + "-" * 66)

struct = [
    ("Eckstiel  (Stiel-H = %d mm)" % STIEL_H,   STIEL_H,        4),
    ("Bodenrahmen Längsriegel (BR_L/R)",          T,              2),
    ("Bodenrahmen Querriegel  (BR_V/H)",          B - 2*P,        2),
    ("Obergurt Längsriegel    (OG_L/R)",          T,              2),
    ("Obergurt Querriegel     (OG_V/H)",          B - 2*P,        2),
    ("Mittelstiel  (50×50 × %d mm)" % DH,        DH,             1),
    ("Türsturz  (50×50 × %d mm)" % (B-2*P),      B - 2*P,        1),
    ("Oberfüllung über Tür  (50×50 × %d mm)" % (B-2*P), B-2*P,  1 if H-P-(DH+P)>0 else 0),
    ("Dachrahmen Vorderriegel  (Traufe)",         B+2*OVER,       1),
    ("Dachrahmen Hinterriegel  (Scharnier)",      B+2*OVER,       1),
    ("Dachrahmen Querstrebe  (Mitte)",            B+2*OVER,       1),
    ("Dachrahmen Seitenträger  (geneigt)",        _rafter_slope,  2),
]
_ts = 0.0
for nm,L,qty in struct:
    tot = L*qty;  m_ = tot/1000;  _ts += m_
    A("  %-34s %8d %4d %9d %7.2f" % (nm, L, qty, tot, m_))
A("  " + "-" * 66)
A("  %-34s %8s %4s %9s %7.2f m" % ("Summe Hauptstruktur", "", "", "", _ts))
A("")

A("─── 2. KLEMMSCHIENEN  (25 x 10 mm Flachprofil) ───────────────────────────")
A("")
A("  %-34s %8s %4s %9s %7s" % ("Bezeichnung", "L (mm)", "Stk", "Summe(mm)", "Summe(m)"))
A("  " + "-" * 66)
clamp = [
    ("Vorderwand horizontal  (U/O)",    B, 2),
    ("Vorderwand vertikal  (L/R)",      H, 2),
    ("Rückwand horizontal  (U/O)",      B, 2),
    ("Rückwand vertikal  (L/R)",        H, 2),
    ("Seitenwände horizontal  (je 2)",  T, 4),
    ("Dachrahmen Vorderkante",          B+2*OVER, 1),
    ("Dachrahmen Hinterkante",          B+2*OVER, 1),
]
_tc = 0.0
for nm,L,qty in clamp:
    tot = L*qty;  m_ = tot/1000;  _tc += m_
    A("  %-34s %8d %4d %9d %7.2f" % (nm, L, qty, tot, m_))
A("  " + "-" * 66)
A("  %-34s %8s %4s %9s %7.2f m" % ("Summe Klemmschienen", "", "", "", _tc))
A("")

A("─── 3. SCHARNIERE & AUFKLAPPMECHANISMUS ──────────────────────────────────")
A("")
A("  Schwerlast-Scharnier 100x100 mm Stahl, verzinkt    2 Stk")
A("    Position: je 200 mm von den Hinterecken entfernt")
A("    Montage:  aussen auf Obergurt hinten + Dachrahmen")
A("    Hoehe Scharnierkörper:  %d mm  (überbrückt Delta = %d mm)" % (HNG_H, RISE))
A("")
A("  Gasdruckfeder  F ca. 300-400 N,  Hub >= 350 mm     1 Stk")
A("    (alternativ: Teleskop-Stützstab mit Arretierstift)")
A("  Kugelzapfen-Halterung für Gasdruckfeder            2 Stk")
A("  Montageschrauben Scharnier M8x50 mm (verzinkt)     8 Stk")
A("  Unterlegscheiben M8 DIN 125                       16 Stk")
A("")

A("─── 4. FOLIENBEDARF  (PE 200 µm) ─────────────────────────────────────────")
A("")
_wf  = B*(H - DH - P)  # Oberfüllung Vorderwand (nur Bereich über Türsturz + Sturz selbst)
_wb  = B*H
_ws  = T*H
_wd  = (B + 2*OVER) * _rafter_slope
_net = _wf + _wb + 2*_ws + _wd
_gro = _net * 1.10
A("  Vorderwand (Oberfüllung, über Türsturz): %.2f m²" % (_wf/1e6))
A("  Rückwand:                       %.2f m²" % (_wb/1e6))
A("  Seitenwände je:                 %.2f m²  x 2" % (_ws/1e6))
A("  Dachfläche (Schrägmass %d mm): %.2f m²" % (_rafter_slope, _wd/1e6))
A("  ─")
A("  Summe Netto:                    %.2f m²" % (_net/1e6))
A("  + 10 %% Verschnitt:             %.2f m²" % (_gro/1e6))
A("")

A("─── 5. VERBINDUNGSMATERIAL – AUSKLINKUNGEN  (Formschluss) ────────────────")
A("")
A("  *** FORMSCHLÜSSIGE VERBINDUNG – Schrauben nur zur LAGESICHERUNG! ***")
A("  *** KEINE Eckverbinder erforderlich ***")
A("")
A("  Ausklinkungstypen:")
A("    Typ 1 – Vollausklinkung  (Eckknoten Boden + OG):")
A("       Längsriegel läuft durch, Querriegel mit 50x50 mm Kerbe an Enden.")
A("       Scherkräfte formschlüssig aufgenommen.")
A("    Typ 2 – Halbausklinkung / Überblattung  (Kreuzknoten Pfetten):")
A("       Beide Profile 25 mm tief ausgeklinkt, greifen ineinander.")
A("    Typ 3 – Zapfensitz  (Bodenknoten Stiel-auf-Rahmen):")
A("       50x50x25 mm Tasche im Längsriegel, Stiel eingestellt.")
A("    Typ 4 – Zapfen/Tasche  (Kopfknoten OG auf Stiel):")
A("       Stielkopf 25 mm lang auf 50x25 mm abgefräst, OG hat Tasche.")
A("")
A("  M10x80 mm + Mutter + Scheiben  DIN 931/934/125, verzinkt:")
A("    Obergurt-Stiel  Typ 4: 4 Ecken x 2 Schrauben     =  8 Stk")
A("  M10x80  Summe:                                     ca.  8 Stk")
A("")
A("  M8x60 mm + Mutter + Scheiben  DIN 931/934/125, verzinkt:")
A("    Bodenknoten Typ 3  (X + Y): 4 Ecken x 4 Schrauben = 16 Stk")
A("    Zwischenknoten + Querriegel-Sicherung Typ 1:        =  8 Stk")
A("  M8x60  Summe:                                      ca. 24 Stk")
A("")
A("  M8x40 mm + Mutter + Scheiben  DIN 931/934/125, verzinkt:")
A("    Halbausklinkungen Pfetten / Mittelstiel Typ 2:        =  4 Stk")
A("  M8x40  Summe:                                      ca.  4 Stk")
A("")
A("  M6x30 mm  DIN 933  (Klemmschienen Folie):          ca. 40 Stk")
A("")
A("  Sechskantmuttern M10  DIN 934, verzinkt:           ca.  8 Stk")
A("  Sechskantmuttern M8   DIN 934, verzinkt:           ca. 32 Stk")
A("  Sechskantmuttern M6   DIN 934:                     ca. 40 Stk")
A("  Unterlegscheiben M10  DIN 125, verzinkt:           ca. 16 Stk")
A("  Unterlegscheiben M8   DIN 125, verzinkt:           ca. 64 Stk")
A("  Unterlegscheiben M6   DIN 125:                     ca. 80 Stk")
A("  Dübel / Bodenhülsen 50x50 mm:                           4 Stk")
A("")
A("  KEINE Winkelverbinder / Eckverbinder!")
A("")

A("─── 6. AUSKLINKUNGSDETAILS – Fertigungsmasse ─────────────────────────────")
A("")
A("  Typ 1 – Vollausklinkung  50x50 mm Kerbe an Enden der Querriegel:")
A("    Massangabe: 50 mm Tiefe x 50 mm Breite (voller Profilquerschnitt)")
A("    Werkzeug:  Winkelschleifer / Bandsäge / Trennscheibe")
A("    Bohrloch:  1x M8 durch Kreuzungspunkt, senkrecht  (d=9 mm)")
A("")
A("  Typ 2 – Halbausklinkung  50x25 mm an beiden Profilen:")
A("    Massangabe: 50 mm breit x 25 mm tief (halbe Profilhöhe)")
A("    Werkzeug:  Fräser / Winkelschleifer")
A("    Bohrloch:  1x M8 durch Überblattung (d=9 mm)")
A("")
A("  Typ 3 – Zapfensitz  50x50x25 mm Tasche in Bodenrahmen-Längsriegel:")
A("    Massangabe: 50x50 mm Grundriss, 25 mm Tiefe (= halbe Profilhöhe)")
A("    Werkzeug:  Fräser oder Schweissnaht-Anschlag")
A("    Bohrlöcher: 2x M8 seitlich durch Rahmen in Stiel (d=9 mm)")
A("")
A("  Typ 4 – Zapfen am Stielkopf, Tasche im Obergurt:")
A("    Stiel:  Top 25 mm auf 50x25 mm abfräsen (hintere Hälfte entfernen)")
A("    OG:     50x25x25 mm Tasche in Unterseite fräsen")
A("    Stiel-Gesamtlänge: %d mm  (= H - P/2 = 2200 - 25)" % STIEL_H)
A("    Bohrloch: 1x M10 von oben, d=11 mm, durch OG in Stielkopf")
A("")

A("─── 7. HOLZDIELENBODEN auf Querträgern ────────────────────────────────────")
A("")
A("  *** NEUES BAUTEIL – integriert in Stahlbodenrahmen ***")
A("")
A("  Querträger (Lagerhölzer):")
A("    Material:   KVH 60x60 mm (Konstruktionsvollholz)")
A("    Länge:      1100 mm  (lichte Weite innen: B - 2×P = 1100 mm)")
A("    Anzahl:     4 Stück")
A("    Achsabstand: ca. %d mm" % _qt_step)
A("    Befestigung: 2× M6×40 je Auflager (links + rechts)")
A("    z-Position: Oberkante Bodenrahmen (z = %d mm) bis z = %d mm" % (P, P+QT_H))
A("")
_qt_len_total = N_QT * (B - 2*P)
A("  %-34s %8d %4d %9d %7.2f" % ("KVH 60x60 (Quertraeger)", B-2*P, N_QT,
                                   _qt_len_total, _qt_len_total/1000))
A("")
A("  Holzdielen (Laerche/Kiefer, Nut+Feder):")
A("    Material:   Laerchenholz 116×22 mm  (nom. ~120 mm Breite)")
A("    Länge:      1100 mm  (lichte Tiefe innen: T - 2×P = 1100 mm)")
A("    Anzahl:     %d Stück" % N_PL)
A("    Verlegerichtung: längs (Y-Richtung, parallel zu Seitenwänden)")
A("    Fuge:       %d mm zwischen den Dielen (Belüftung)" % PL_GAP)
A("    Befestigung: Dielenklammern oder 2× Edelstahlschraube 4×50 mm versetzt")
A("    OK Dielenboden: z = %d mm (%d + %d + %d) über UK Bodenrahmen" %
   (P+QT_H+PLANK_T, P, QT_H, PLANK_T))
A("")
_pl_len_total = N_PL * (T - 2*P)
A("  %-34s %8d %4d %9d %7.2f" % ("Laerche %d×%d mm (Dielen)" % (PLANK_W, PLANK_T),
                                   T-2*P, N_PL, _pl_len_total, _pl_len_total/1000))
A("")
A("  Trittholm (Türschwelle):")
A("    Material:   KVH/Nadelholz 80×40 mm")
A("    Länge:      1200 mm  (= volle Außenbreite B)")
A("    Anzahl:     1 Stück")
A("    Position:   Auf Bodenrahmen-Vorderriegel, gesamte Breite (x = 0..%d)" % B)
A("    z-Position: z = %d..%d mm" % (P, P+TH_H))
A("")
A("  %-34s %8d %4d %9d %7.2f" % ("Trittholm 80×40 mm", B, 1, B, B/1000))
A("")
A("  VERBINDUNGSMATERIAL Holzboden:")
A("")
A("  M6×40 mm DIN 933 verzinkt (QT-Befestigung):     8 Stk")
A("    (2 Schrauben je Auflager × 4 Querträger × 2 Auflagerpunkte)")
A("  Sechskantmuttern M6  DIN 934:                    8 Stk")
A("  Unterlegscheiben M6  DIN 125:                   16 Stk")
A("  Dielenklammern (A2-Edelstahl, 60mm):      ca.  60 Stk")
A("    (oder alternativ: Edelstahlschraube 4×50 mm,  ca. 80 Stk)")
A("  Holzschrauben Trittholm 5×60 mm:                 4 Stk")
A("")
A("  ZUSAMMENFASSUNG HOLZBODEN:")
A("")
_floor_wood_total = (_qt_len_total + _pl_len_total + B) / 1000
A("  KVH 60×60 mm (Querträger): 4× %d mm = %.1f m" % (B-2*P, _qt_len_total/1000))
A("  Laerche %d×%d mm (Dielen): %d× %d mm = %.1f m" % (PLANK_W, PLANK_T, N_PL, T-2*P, _pl_len_total/1000))
A("  Trittholm 80×40 mm:        1× %d mm = %.2f m" % (B, B/1000))
A("  Holzbedarf gesamt:                        %.1f lfdm" % _floor_wood_total)
A("")

A("─── 7b. ZWEIFLÜGELIGE TÜR – Konstruktionsdetails ─────────────────────────")
A("")
A("  Türgesamtbreite:      1200 mm (= volle Außenbreite)")
A("  Lichte Breite je Flügel: %d mm  (= (B - P_Mittelstiel) / 2)" % DW_SINGLE)
A("  Türhöhe (licht):     %d mm" % DH)
A("  Türsturz Höhe:       1950 mm  (= %d + 50)" % DH)
A("")
A("  Rahmenprofil Türflügel (30×30 mm Vierkantprofil):")
_tf_rail_len = 4 * DW_SINGLE + 4 * DH + 2 * DW_SINGLE  # 4 Außenrahmen + 2 Mittelstreben
A("  %-34s %8s %4s %9s %7.2f" % ("Türflügel-Rahmen 30×30 mm", "", "", "",
                                  _tf_rail_len / 1000))
A("    Je Flügel: 2× %d mm (horizontal) + 2× %d mm (vertikal) + 1× %d mm (Mittelstrebe)" %
  (DW_SINGLE, DH, DW_SINGLE))
A("    Gesamt: 2 Flügel × (2×%d + 2×%d + 1×%d) = ca. %d mm = %.1f m" %
  (DW_SINGLE, DH, DW_SINGLE, _tf_rail_len, _tf_rail_len/1000))
A("")
A("  Scharniere Türflügel:")
A("    100×80 mm Bandscharnier, Stahl verzinkt:      4 Stk")
A("    (je 2 pro Flügel, außen an Eckstielen)")
A("    Position: z = 300 mm und z = 1600 mm")
A("")
A("  Türverschluss:")
A("    Karabinerhaken / Riegel mittig am Mittelstiel: 1 Stk")
A("    Türgriff 100 mm innen/außen:                   2 Stk  (optional)")
A("")
A("  Schrauben Türflügel-Scharniere M8×50 mm:         8 Stk")
A("  Folie je Türflügel: %d × %d mm (Außenmaß Flügel)" % (DW_SINGLE, DH))
A("  Klemmschienen 25×10 mm je Flügel (Umfang):  ca. %.1f m" %
  ((2*DW_SINGLE + 2*DH) / 1000))
A("")
A("─── 8. ZUSAMMENFASSUNG (gesamt) ────────────────────────────────────────────")
A("")
A("  Vierkantprofil 50x50 mm:         %.1f m" % _ts)
A("  Vierkantprofil 30x30 mm (Türfl.): ca. %.1f m" % (_tf_rail_len/1000))
A("  Klemmschiene 25x10 mm:           %.1f m" % _tc)
A("  Folie PE 200 µm (inkl. 10 %%):   %.1f m²" % (_gro/1e6))
A("  KVH 60x60 mm (Querträger):       %.1f m  (4× 1100 mm)" % (_qt_len_total/1000))
A("  Laerche %d×%d mm (Dielen):  %.1f m  (%d× 1100 mm)" % (PLANK_W, PLANK_T, _pl_len_total/1000, N_PL))
A("  Trittholm 80×40 mm:              1× %d mm (volle Breite)" % B)
A("  Dachneigung:                      ca. %.1f Grad" % _roof_angle)
A("  Dachüberstand (alle 4 Seiten):      %d mm" % OVER)
A("  Dachrahmen-Abmessungen:             %d × %d mm  (B×T)" % (B+2*OVER, T+2*OVER))
A("  Dachrahmen Schrägmass (Seitentr.): %d mm" % _rafter_slope)
A("  Höhendifferenz Dach (Delta):       %d mm" % RISE)
A("  Scharniere Dach:                   2x Schwerlast 100x100 Stahl")
A("  Scharniere Türflügel:              4x Bandscharnier 100×80 mm")
A("  Gasdruckfeder:                     1x ca. 300-400 N, Hub >= 350 mm")
A("  Mittelstiel:                       1× 50×50 × %d mm" % DH)
A("  Türsturz:                          1× 50×50 × %d mm" % (B-2*P))
A("  Verbindung:                        Ausklinkungen Typ 1-4 – KEINE Eckverbinder")
A("  Stiel-Zapfen (Typ 4):             Stiel %d mm lang, Zapfen 25 mm" % STIEL_H)
A("  Dielenboden Aufbauhöhe:           %d mm  (%d+%d+%d)" % (P+QT_H+PLANK_T, P, QT_H, PLANK_T))
A("")
A("=" * 74)
A("  Hinweis: Profile 50x50 mm (t ca. 2-3 mm Stahl od. Massivprofil Alu).")
A("  Folie: PE-Gewächshausfolie 200 µm. Alle Masse in mm.")
A("  Ausklinkungen erzeugen Formschluss – Scherkräfte werden form-")
A("  schlüssig aufgenommen, Schrauben nur zur Lagesicherung (Abheben).")
A("  Bohrlöcher vorgebohren: d=11 mm (M10), d=9 mm (M8), d=7 mm (M6).")
A("  Schrauben galvanisch verzinkt (DIN EN ISO 10683 oder Feuerverzinkung).")
A("=" * 74)

bom_path = os.path.join(OUT,"gewaechshaus_stueckliste.txt")
with open(bom_path,"w",encoding="utf-8") as f:
    f.write("\n".join(bom))
print("ok BOM: %s" % bom_path)

print("")
print("-" * 65)
import os as _os
for fn in ["gewaechshaus_zeichnung.pdf","gewaechshaus_iso.png",
           "gewaechshaus_front.png","gewaechshaus_stueckliste.txt"]:
    p = _os.path.join(OUT,fn)
    s = _os.path.getsize(p) if _os.path.exists(p) else 0
    print("  %s  %s  (%d kB)" % ("ok" if s>0 else "FEHLER", p, s//1024))
print("-" * 65)
print("Matplotlib-Ausgabe (Ausklinkung) fertig.")
