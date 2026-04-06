#!/usr/bin/env python3
"""
Typ 2: Fenstergewächshaus – STL-Export nach Materialgruppen für GLB-Pipeline.
Gruppen: window_frame, door_frame, sill_beam, top_rail, corner_post,
         roof_frame, hardware
"""
import cadquery as cq
from cadquery import Compound
from cadquery.occ_impl.exporters import ExportTypes
import os, sys

OUT_DIR = "/tmp/gwh_meshes"
os.makedirs(OUT_DIR, exist_ok=True)

_proj = os.environ.get("GWH_PROJECT_DIR",
        "/home/herrvorragend/projekte/gewaechshaus")
sys.path.insert(0, _proj)
try:
    from params import (WIN_W, WIN_H, WIN_ROWS,
                        WIN_COLS_FRONT, WIN_COLS_BACK, WIN_COLS_LEFT, WIN_COLS_RIGHT,
                        FRAME_T, SILL_H, B, T, H, OVER,
                        DOOR_FRONT, DOOR_BACK, DOOR_LEFT, DOOR_RIGHT)
except ImportError:
    WIN_W=800; WIN_H=1200; WIN_ROWS=1
    WIN_COLS_FRONT=2; WIN_COLS_BACK=2; WIN_COLS_LEFT=2; WIN_COLS_RIGHT=2
    FRAME_T=60; SILL_H=100; B=1720; T=1720; H=1360; OVER=300
    DOOR_FRONT=True; DOOR_BACK=False; DOOR_LEFT=False; DOOR_RIGHT=False

POST  = FRAME_T
TOP_H = FRAME_T
FT    = FRAME_T
WIN_ZONE_H = WIN_ROWS * WIN_H
og_z = H - TOP_H

SLOPE    = 200 / 1200
H_DACH_V = H - int(OVER * SLOPE)
H_DACH_H = H + 200 + int(OVER * SLOPE)
RISE     = H_DACH_H - H_DACH_V

# ── Gruppen ──────────────────────────────────────────────────────────────────
groups = {
    "window_frame": [],
    "door_frame":   [],
    "sill_beam":    [],
    "top_rail":     [],
    "corner_post":  [],
    "roof_frame":   [],
    "hardware":     [],
}


def bx(group, x, y, z, lx, ly, lz):
    if lx <= 0 or ly <= 0 or lz <= 0:
        return
    sh = cq.Workplane("XY").box(lx, ly, lz).translate(
        (x+lx/2, y+ly/2, z+lz/2))
    groups[group].append(sh)
    return sh


def window_solid(x, y, z, w, h, depth, group):
    """Fensterrahmen als Hohlkörper."""
    outer = cq.Workplane("XY").box(w, depth, h).translate(
        (x+w/2, y+depth/2, z+h/2))
    inner_w = max(8, w - 2*FT)
    inner_h = max(8, h - 2*FT)
    inner = cq.Workplane("XY").box(inner_w, depth+2, inner_h).translate(
        (x+w/2, y+depth/2, z+h/2))
    frame = outer.cut(inner)
    groups[group].append(frame)


# ── 1. ECKPFOSTEN ─────────────────────────────────────────────────────────────
for px, py in [(0, 0), (B-POST, 0), (0, T-POST), (B-POST, T-POST)]:
    bx("corner_post", px, py, 0, POST, POST, H)

# ── 2. SCHWELLBALKEN ──────────────────────────────────────────────────────────
bx("sill_beam", POST, 0,      0, B-2*POST, POST, SILL_H)
bx("sill_beam", POST, T-POST, 0, B-2*POST, POST, SILL_H)
bx("sill_beam", 0,   POST,   0, POST, T-2*POST, SILL_H)
bx("sill_beam", B-POST, POST, 0, POST, T-2*POST, SILL_H)

# ── 3. OBERGURT ───────────────────────────────────────────────────────────────
bx("top_rail", POST, 0,      og_z, B-2*POST, POST, TOP_H)
bx("top_rail", POST, T-POST, og_z, B-2*POST, POST, TOP_H)
bx("top_rail", 0,   POST,   og_z, POST, T-2*POST, TOP_H)
bx("top_rail", B-POST, POST, og_z, POST, T-2*POST, TOP_H)

# ── 4. FENSTER & TÜREN ────────────────────────────────────────────────────────
def place_wall(side, cols, rows, is_door_wall):
    if side == 'front':
        x0, y_off, w_total, orient = POST, 0, B-2*POST, 'x'
    elif side == 'back':
        x0, y_off, w_total, orient = POST, T-POST, B-2*POST, 'x'
    elif side == 'left':
        x0, y_off, w_total, orient = 0, POST, T-2*POST, 'y'
    else:
        x0, y_off, w_total, orient = B-POST, POST, T-2*POST, 'y'

    col_w = w_total / cols
    row_h = WIN_ZONE_H / rows
    door_col = cols // 2 if is_door_wall else -1

    for row in range(rows):
        z = SILL_H + row * row_h
        for col in range(cols):
            is_door = is_door_wall and row == 0 and col == door_col
            grp = "door_frame" if is_door else "window_frame"
            if orient == 'x':
                window_solid(x0 + col*col_w, y_off, z, col_w, row_h, POST, grp)
            else:
                # Seitenwand: Rahmen in YZ-Ebene
                wy = x0 + col * col_w
                outer = cq.Workplane("XY").box(POST, col_w, row_h).translate(
                    (y_off+POST/2, wy+col_w/2, z+row_h/2))
                iw = max(8, col_w - 2*FT)
                ih = max(8, row_h - 2*FT)
                inner = cq.Workplane("XY").box(POST+2, iw, ih).translate(
                    (y_off+POST/2, wy+col_w/2, z+row_h/2))
                groups[grp].append(outer.cut(inner))


place_wall('front', WIN_COLS_FRONT, WIN_ROWS, DOOR_FRONT)
place_wall('back',  WIN_COLS_BACK,  WIN_ROWS, DOOR_BACK)
place_wall('left',  WIN_COLS_LEFT,  WIN_ROWS, DOOR_LEFT)
place_wall('right', WIN_COLS_RIGHT, WIN_ROWS, DOOR_RIGHT)

# ── 5. DACHRAHMEN ─────────────────────────────────────────────────────────────
bx("roof_frame", -OVER, -OVER,        H_DACH_V,       B+2*OVER, POST, POST)
bx("roof_frame", -OVER, T+OVER-POST,  H_DACH_H-POST,  B+2*OVER, POST, POST)
n_sp = max(2, B // 600)
for i in range(n_sp + 1):
    sx = int(-OVER + i * (B + 2*OVER) / n_sp)
    bx("roof_frame", sx, -OVER, H_DACH_V, POST, T+2*OVER, POST)
# Mittelpfette
bx("roof_frame", -OVER, (T-POST)//2, int(H_DACH_V + RISE/2),
   B+2*OVER, POST, POST)

# ── 6. SCHARNIERE ─────────────────────────────────────────────────────────────
for sx in [B//4, 3*B//4]:
    bx("hardware", sx, T-POST-15, H_DACH_H-POST-15, 100, 20, 60)

# ── Export ────────────────────────────────────────────────────────────────────
for gname, shapes in groups.items():
    if not shapes:
        print(f"  SKIP {gname} (leer)")
        continue
    try:
        solids = []
        for s in shapes:
            try:
                solids.append(s.val())
            except Exception:
                pass
        if not solids:
            continue
        compound = Compound.makeCompound(solids)
        out_path = os.path.join(OUT_DIR, f"{gname}.stl")
        cq.exporters.export(compound, out_path, ExportTypes.STL)
        print(f"  OK  {gname}  (-> {out_path})")
    except Exception as e:
        print(f"  FAIL {gname}: {e}")

print("CadQuery Typ-2-Export abgeschlossen.")
