#!/usr/bin/env python3
"""
Typ 2: Gewächshaus aus alten Fenstern und Balkontüren
Fensterrahmen als tragende Elemente – parametrisches CadQuery-Modell.

Koordinatensystem (wie Typ 1):
  X = Breite (Front = XZ-Ebene bei y=0)
  Y = Tiefe  (links → rechts)
  Z = Höhe   (0 = Boden)
"""
import cadquery as cq
from cadquery import Compound
import os, sys

_proj = os.environ.get("GWH_PROJECT_DIR",
        "/home/herrvorragend/projekte/gewaechshaus")
sys.path.insert(0, _proj)
from params import (WIN_W, WIN_H, WIN_ROWS,
                    WIN_COLS_FRONT, WIN_COLS_BACK, WIN_COLS_LEFT, WIN_COLS_RIGHT,
                    FRAME_T, SILL_H, B, T, H, OVER,
                    DOOR_FRONT, DOOR_BACK, DOOR_LEFT, DOOR_RIGHT)

OUT = os.path.join(_proj, "gewaechshaus.step")

# ── Abgeleitete Maße ─────────────────────────────────────────────────────────
POST   = FRAME_T        # Eckpfosten = Rahmendicke
TOP_H  = FRAME_T        # Obergurt-Höhe

# Wandhöhe ohne Schwelle: SILL_H .. SILL_H + WIN_ROWS*WIN_H
WIN_ZONE_H = WIN_ROWS * WIN_H   # Höhe der Fensterzone
WALL_H     = SILL_H + WIN_ZONE_H + TOP_H   # = H (sollte übereinstimmen)

# Dach (Pultdach, wie Typ 1)
SLOPE    = 200 / 1200
H_DACH_V = H - int(OVER * SLOPE)
H_DACH_H = H + 200 + int(OVER * SLOPE)
RISE     = H_DACH_H - H_DACH_V

all_shapes = []


def box(name, x, y, z, lx, ly, lz):
    if lx <= 0 or ly <= 0 or lz <= 0:
        return None
    sh = cq.Workplane("XY").box(lx, ly, lz).translate(
        (x + lx/2, y + ly/2, z + lz/2))
    all_shapes.append(sh)
    return sh


# ── 1. ECKPFOSTEN (4 Stück) ─────────────────────────────────────────────────
# Laufen von Boden (z=0) bis Obergurt-OK (z=H)
for px, py in [(0, 0), (B-POST, 0), (0, T-POST), (B-POST, T-POST)]:
    box("ECKPFOSTEN", px, py, 0, POST, POST, H)

# ── 2. SCHWELLBALKEN ─────────────────────────────────────────────────────────
# Front und Rück (Y-Richtung ausgespart für Seitenbalken)
box("SILL_FRONT", POST, 0,     0, B-2*POST, POST, SILL_H)
box("SILL_BACK",  POST, T-POST, 0, B-2*POST, POST, SILL_H)
box("SILL_LEFT",  0,   POST,   0, POST, T-2*POST, SILL_H)
box("SILL_RIGHT", B-POST, POST, 0, POST, T-2*POST, SILL_H)

# ── 3. OBERGURT ──────────────────────────────────────────────────────────────
og_z = H - TOP_H
box("OG_FRONT", POST, 0,      og_z, B-2*POST, POST, TOP_H)
box("OG_BACK",  POST, T-POST, og_z, B-2*POST, POST, TOP_H)
box("OG_LEFT",  0,   POST,   og_z, POST, T-2*POST, TOP_H)
box("OG_RIGHT", B-POST, POST, og_z, POST, T-2*POST, TOP_H)

# ── 4. FENSTERRAHMEN ─────────────────────────────────────────────────────────
# Jeder Fensterrahmen: äußeres Rechteck mit Rahmendicke FT
# Glasscheibe = Loch (wird nicht modelliert, nur der Rahmen)
FT = FRAME_T  # Rahmendicke

def window_frame(x, y, z, w, h, depth=POST, is_door=False):
    """Fensterrahmen als Hohlprofil: außen w×h, innen w-2FT × h-2FT."""
    outer = cq.Workplane("XY").box(w, depth, h).translate(
        (x+w/2, y+depth/2, z+h/2))
    inner_w = max(10, w - 2*FT)
    inner_h = max(10, h - 2*FT)
    inner = cq.Workplane("XY").box(inner_w, depth+2, inner_h).translate(
        (x+w/2, y+depth/2, z+h/2))
    frame = outer.cut(inner)
    all_shapes.append(frame)
    if is_door:
        # Türschwelle: unterer Riegel als separates Shape (vermeidet .union() OCP-Bug)
        sill = cq.Workplane("XY").box(inner_w, depth+2, FT).translate(
            (x+w/2, y+depth/2, z+FT/2))
        all_shapes.append(sill)
    return frame


def place_windows_on_wall(side, cols, rows, door_side):
    """Platziert cols×rows Fenster auf einer Wand."""
    if side == 'front':
        x0, y_off, w_total, axis = POST, 0, B-2*POST, 'x'
    elif side == 'back':
        x0, y_off, w_total, axis = POST, T-POST, B-2*POST, 'x'
    elif side == 'left':
        x0, y_off, w_total, axis = 0, POST, T-2*POST, 'y'
    else:  # right
        x0, y_off, w_total, axis = B-POST, POST, T-2*POST, 'y'

    col_w = w_total / cols
    row_h = WIN_ZONE_H / rows

    for row in range(rows):
        z = SILL_H + row * row_h
        for col in range(cols):
            is_door = door_side and row == 0 and col == cols // 2
            if axis == 'x':
                wx = x0 + col * col_w
                window_frame(wx, y_off, z, col_w, row_h,
                             depth=POST, is_door=is_door)
            else:
                wy = x0 + col * col_w
                # Für Seiten: Rahmen in YZ-Ebene
                outer = cq.Workplane("XY").box(POST, col_w, row_h).translate(
                    (y_off+POST/2, wy+col_w/2, z+row_h/2))
                inner_w = max(10, col_w - 2*FT)
                inner_h = max(10, row_h - 2*FT)
                inner = cq.Workplane("XY").box(POST+2, inner_w, inner_h).translate(
                    (y_off+POST/2, wy+col_w/2, z+row_h/2))
                frame = outer.cut(inner)
                all_shapes.append(frame)


place_windows_on_wall('front', WIN_COLS_FRONT, WIN_ROWS, DOOR_FRONT)
place_windows_on_wall('back',  WIN_COLS_BACK,  WIN_ROWS, DOOR_BACK)
place_windows_on_wall('left',  WIN_COLS_LEFT,  WIN_ROWS, DOOR_LEFT)
place_windows_on_wall('right', WIN_COLS_RIGHT, WIN_ROWS, DOOR_RIGHT)

# ── 5. DACHRAHMEN (Pultdach, aufklappbar) ───────────────────────────────────
box("DR_V", -OVER, -OVER, H_DACH_V, B+2*OVER, POST, POST)
box("DR_H", -OVER, T+OVER-POST, H_DACH_H-POST, B+2*OVER, POST, POST)
n_sparren = max(2, B // 600)
for i in range(n_sparren + 1):
    sx = int(-OVER + i * (B + 2*OVER) / n_sparren)
    box("SPARREN_%d" % i, sx, -OVER, H_DACH_V, POST, T+2*OVER, POST)

# Mittlere Dachpfette
box("DACH_MITTE", -OVER, (T-POST)//2, int(H_DACH_V + RISE/2),
    B+2*OVER, POST, POST)

# ── 6. SCHARNIERE (Dachscharnier, vereinfacht) ───────────────────────────────
for sx in [B//4, 3*B//4]:
    box("HNG", sx, T+OVER-POST-20, H_DACH_H-POST-20, 100, 20,
        (H_DACH_H-POST-H_DACH_V)+40)

# ── Export ───────────────────────────────────────────────────────────────────
print("Erstelle Compound aus %d Einzelteilen …" % len(all_shapes))
try:
    compound = Compound.makeCompound([s.val() for s in all_shapes])
    cq.exporters.export(compound, OUT)
    print("ok STEP:", OUT)
except Exception as e:
    print("WARN STEP:", e)
    # Fallback: einzeln exportieren
    for i, s in enumerate(all_shapes):
        try:
            cq.exporters.export(s.val(), OUT.replace(".step", f"_{i}.step"))
        except Exception:
            pass

print("Typ-2-Modell (Fenstergewächshaus) fertig.")
print(f"  B={B} T={T} H={H}  WIN={WIN_W}×{WIN_H}  Rows={WIN_ROWS}")
