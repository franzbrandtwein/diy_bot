#!/usr/bin/env python3
"""
Assembliert alle STL-Gruppen zu einer einzigen GLB-Datei mit Materialfarben.
Fügt zusätzlich transparente Folien-Panels hinzu.

Aufruf: python3 assemble_glb.py
"""

import trimesh
import trimesh.exchange.gltf as gltf_ex
import numpy as np
import json, struct, os

STL_DIR  = "/tmp/gwh_meshes"
_proj    = os.environ.get("GWH_PROJECT_DIR", "/home/herrvorragend/projekte/gewaechshaus")
OUT_GLB  = os.path.join(_proj, "gewaechshaus.glb")
try:
    import sys as _sys; _sys.path.insert(0, _proj)
    from params import B, T, H, OVER, P
    del _sys
except ImportError:
    B = 1200; T = 1200; H = 2200; OVER = 300; P = 50
P2 = P // 2; CH = 10; CW = 25
SLOPE = 200 / 1200
H_DACH_V = H - int(OVER * SLOPE)   # 2150
H_DACH_H = 2400 + int(OVER * SLOPE) # 2450
RISE     = H_DACH_H - H_DACH_V     # 300

# ── Materialfarben (RGBA 0–255) ────────────────────────────────────────────
COLORS = {
    # Typ 1 – Stahlprofil-Gewächshaus
    "steel_frame": [122, 122, 122, 255],
    "roof_frame":  [122, 122, 122, 255],
    "door_frame":  [136, 136, 136, 255],
    "hardware":    [85,  85,  85,  255],
    "wood":        [200, 160,  96, 255],
    "clamping":    [153, 153, 153, 255],
    "screws":      [170, 170, 170, 255],
    # Typ 2 – Fenstergewächshaus
    "window_frame": [200, 160,  96, 255],  # Holz warm
    "sill_beam":    [160, 110,  60, 255],  # Schwelle dunkler
    "top_rail":     [180, 130,  70, 255],  # Obergurt
    "corner_post":  [150, 100,  50, 255],  # Eckpfosten
}
FOIL_COLOR = np.array([180, 255, 180, 90], dtype=np.uint8)  # hellgrün, semi-transparent

# ── Lade STL-Gruppen ────────────────────────────────────────────────────────
scene = trimesh.scene.scene.Scene()
total_verts = 0
total_faces = 0

for gname, rgba in COLORS.items():
    stl_path = os.path.join(STL_DIR, "%s.stl" % gname)
    if not os.path.exists(stl_path):
        print("  SKIP %s (nicht gefunden)" % gname)
        continue

    mesh = trimesh.load(stl_path, force="mesh")
    if mesh is None or len(mesh.faces) == 0:
        print("  SKIP %s (leer)" % gname)
        continue

    # Farbe zuweisen
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh)
    mesh.visual.vertex_colors = np.tile(
        np.array(rgba, dtype=np.uint8),
        (len(mesh.vertices), 1)
    )

    scene.add_geometry(mesh, geom_name=gname, node_name=gname)
    print("  OK  %-15s  V=%6d  F=%6d" % (gname, len(mesh.vertices), len(mesh.faces)))
    total_verts += len(mesh.vertices)
    total_faces += len(mesh.faces)


# ── Transparente Folien-Panels ─────────────────────────────────────────────
# Alle Koordinaten in mm. 1 mm Dicke für die Quader.
# Die Folie sitzt innerhalb der Klemmschienen:
#   Vorderwand: y=0, x=0..B, z=0..H          -> Quader mit Tiefe 1 mm
#   Rückwand:   y=T, x=0..B, z=0..H
#   Linke Wand: x=0, y=0..T, z=0..H
#   Rechte Wand: x=B, y=0..T, z=0..H
#   Dachhaut: geneigtes Panel (vereinfacht als Quader auf Dachniveau)

FOIL_T = 1  # mm Dicke Folie

def make_foil_box(x, y, z, lx, ly, lz, color):
    """Erzeugt einen dünnen Quader als Folien-Mesh."""
    mesh = trimesh.creation.box(extents=[lx, ly, lz])
    mesh.apply_translation([x + lx/2, y + ly/2, z + lz/2])
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh)
    mesh.visual.vertex_colors = np.tile(color, (len(mesh.vertices), 1))
    return mesh

foil_panels = [
    # Vorderwand (y=0..FOIL_T)
    ("foil_front",  make_foil_box(0, -FOIL_T, 0, B, FOIL_T, H, FOIL_COLOR)),
    # Rückwand (y=T..T+FOIL_T)
    ("foil_back",   make_foil_box(0, T, 0, B, FOIL_T, H, FOIL_COLOR)),
    # Linke Wand (x=-FOIL_T..0)
    ("foil_left",   make_foil_box(-FOIL_T, 0, 0, FOIL_T, T, H, FOIL_COLOR)),
    # Rechte Wand (x=B..B+FOIL_T)
    ("foil_right",  make_foil_box(B, 0, 0, FOIL_T, T, H, FOIL_COLOR)),
]

# Dachhaut: vereinfachtes Panel entlang der Neigung
# Wir erzeugen einen angenäherten Quader auf mittlerer Dachhöhe
_dach_z_mid = (H_DACH_V + H_DACH_H) / 2
_dach_lz    = RISE + 2 * P   # etwas größer
_dach_ly    = T + 2 * OVER + 10
_dach_lx    = B + 2 * OVER
foil_panels.append(("foil_roof",
    make_foil_box(-OVER, -OVER, _dach_z_mid - _dach_lz/2, _dach_lx, _dach_ly, _dach_lz, FOIL_COLOR)))

# Folie deaktiviert (auf Wunsch weggelassen)
# for fname, fmesh in foil_panels:
#     scene.add_geometry(fmesh, geom_name=fname, node_name=fname)

# ── GLB-Export ─────────────────────────────────────────────────────────────
print("\nExportiere GLB …")
glb_bytes = scene.export(file_type="glb")
with open(OUT_GLB, "wb") as f:
    f.write(glb_bytes)

size_mb = os.path.getsize(OUT_GLB) / (1024 * 1024)
print("\n╔══════════════════════════════════════════╗")
print("║  GLB-Export erfolgreich                  ║")
print("╠══════════════════════════════════════════╣")
print("║  Datei : %s" % OUT_GLB)
print("║  Größe : %.2f MB" % size_mb)
print("║  Vertices gesamt : %d" % total_verts)
print("║  Faces gesamt    : %d" % total_faces)
print("║  Meshes (Gruppen): %d" % len(COLORS))
print("╚══════════════════════════════════════════╝")

# ── Validierung ────────────────────────────────────────────────────────────
if size_mb > 20:
    print("WARNUNG: Dateigröße > 20 MB!")
elif size_mb < 0.01:
    print("WARNUNG: Datei scheint leer zu sein!")
else:
    print("✓ Dateigröße OK (< 20 MB)")
