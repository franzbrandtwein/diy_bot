#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stueckliste_pdf.py
Stückliste mit 3D-Bauteil-Darstellungen – Gewächshaus 1200×1200×2200 mm
Ausgabe: gewaechshaus_stueckliste_3d.pdf
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401 (side-effect import)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyBboxPatch
from datetime import date
import os

# ──────────────────────────────────────────────────────────────────────────────
# FARB- UND STIL-KONSTANTEN
# ──────────────────────────────────────────────────────────────────────────────
C_STEEL   = "#b0b8c1"   # Stahl
C_STEEL_D = "#7a8a99"   # Stahl dunkel (Kanten)
C_WOOD    = "#c8a96e"   # Holz hell
C_WOOD_D  = "#8b6340"   # Holz dunkel
C_ALU     = "#d0d8e0"   # Alu
C_FOIL    = "#cce8ff"   # Folie / Kunststoff
C_SCREW   = "#888888"   # Schrauben

C_TITLE_BG  = "#1a3a5c"   # Dunkelblau
C_GROUP_BG  = "#2c5f8a"   # Mittelblau
C_HDR_BG    = "#e8f0f8"   # Hellblau
C_CARD_BG   = "#f7fafd"   # Karten-Hintergrund
C_BORDER    = "#2c5f8a"
C_TEXT      = "#1a1a2e"

FONT_TITLE  = {"fontsize": 22, "fontweight": "bold", "color": "white",    "fontfamily": "DejaVu Sans"}
FONT_SUB    = {"fontsize": 12, "fontweight": "normal","color": "#dde8f4",  "fontfamily": "DejaVu Sans"}
FONT_GROUP  = {"fontsize": 11, "fontweight": "bold", "color": "white",    "fontfamily": "DejaVu Sans"}
FONT_POS    = {"fontsize": 9,  "fontweight": "bold", "color": C_TITLE_BG, "fontfamily": "DejaVu Sans"}
FONT_NAME   = {"fontsize": 8,  "fontweight": "bold", "color": C_TEXT,     "fontfamily": "DejaVu Sans"}
FONT_SMALL  = {"fontsize": 7,  "fontweight": "normal","color": "#444",    "fontfamily": "DejaVu Sans"}

OUTPUT = "/home/herrvorragend/projekte/gewaechshaus/gewaechshaus_stueckliste_3d.pdf"
ISO_IMG = "/home/herrvorragend/projekte/gewaechshaus/gewaechshaus_iso.png"

# ──────────────────────────────────────────────────────────────────────────────
# 3D-HILFSFUNKTIONEN
# ──────────────────────────────────────────────────────────────────────────────

def _quader_faces(x0, y0, z0, dx, dy, dz):
    """Gibt 6 Flächen eines Quaders als Liste von 4-Punkt-Polygonen zurück."""
    x1, y1, z1 = x0+dx, y0+dy, z0+dz
    return [
        [[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]],  # Boden
        [[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],  # Deckel
        [[x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1]],  # Vorne
        [[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]],  # Hinten
        [[x0,y0,z0],[x0,y1,z0],[x0,y1,z1],[x0,y0,z1]],  # Links
        [[x1,y0,z0],[x1,y1,z0],[x1,y1,z1],[x1,y0,z1]],  # Rechts
    ]

def _quader_edges(x0, y0, z0, dx, dy, dz):
    """Gibt alle 12 Kanten eines Quaders als (xs,ys,zs) zurück."""
    x1,y1,z1 = x0+dx, y0+dy, z0+dz
    edges = [
        ([x0,x1],[y0,y0],[z0,z0]),([x0,x1],[y1,y1],[z0,z0]),
        ([x0,x1],[y0,y0],[z1,z1]),([x0,x1],[y1,y1],[z1,z1]),
        ([x0,x0],[y0,y1],[z0,z0]),([x1,x1],[y0,y1],[z0,z0]),
        ([x0,x0],[y0,y1],[z1,z1]),([x1,x1],[y0,y1],[z1,z1]),
        ([x0,x0],[y0,y0],[z0,z1]),([x1,x1],[y0,y0],[z0,z1]),
        ([x0,x0],[y1,y1],[z0,z1]),([x1,x1],[y1,y1],[z0,z1]),
    ]
    return edges

def draw_box_3d(ax, dx, dy, dz, x0=0, y0=0, z0=0,
                face_color=C_STEEL, alpha=0.82, edge_color="#333"):
    """Zeichnet einen Quader mit Poly3DCollection und Kantennachzug."""
    faces = _quader_faces(x0, y0, z0, dx, dy, dz)
    # Leichte Tönung pro Fläche für Tiefenwirkung
    shades = [0.70, 0.95, 0.85, 0.80, 0.88, 0.92]
    polys = []
    facecolors = []
    for f, s in zip(faces, shades):
        polys.append(f)
        r,g,b = matplotlib.colors.to_rgb(face_color)
        facecolors.append((r*s, g*s, b*s, alpha))
    coll = Poly3DCollection(polys, facecolor=facecolors, linewidth=0.4,
                            edgecolor=edge_color, zsort='average')
    ax.add_collection3d(coll)
    # Kanten noch einmal nachziehen
    for xs, ys, zs in _quader_edges(x0, y0, z0, dx, dy, dz):
        ax.plot(xs, ys, zs, color=edge_color, lw=0.5)


def draw_notched_box_3d(ax, dx, dy, dz, cuts, x0=0, y0=0, z0=0,
                         face_color=C_STEEL, alpha=0.82, edge_color="#333"):
    """
    Zeichnet einen Quader mit sichtbaren Ausklinkungen.

    cuts: Liste von (cx, cy, cz, clx, cly, clz) im Bauteil-Koordinatensystem.
          Alle Werte in denselben Einheiten wie dx/dy/dz (÷100 mm).
          cx/cy/cz = Startpunkt der Ausklinkung (Ecke näher am Ursprung)
          clx/cly/clz = Ausdehnung der Ausklinkung

    Darstellung:
      1. Basisquader in Bauteilfarbe
      2. Cut-Bereich mit weißer Füllung überlagert (simuliert Materialabtrag)
      3. Kanten der Ausklinkung als rote gestrichelte Linien hervorgehoben
    """
    # 1. Basisquader
    draw_box_3d(ax, dx, dy, dz, x0=x0, y0=y0, z0=z0,
                face_color=face_color, alpha=alpha, edge_color=edge_color)

    # 2. Für jeden Cut: weiße Überlagerungsflächen + rote Strichkanten
    for (cx, cy, cz, clx, cly, clz) in cuts:
        ax0, ay0, az0 = cx + x0, cy + y0, cz + z0
        # Weiße Füllung (simuliert abgetragenes Material)
        faces = _quader_faces(ax0, ay0, az0, clx, cly, clz)
        # Helle, fast opake Überlagerung
        cut_colors = [(1.0, 1.0, 1.0, 0.94)] * 6   # weiß
        coll = Poly3DCollection(
            faces,
            facecolor=cut_colors,
            linewidth=0.6,
            edgecolor='#cc0000',
            linestyle='--',
            zsort='average',
        )
        ax.add_collection3d(coll)
        # Rote gestrichelte Kanten explizit nachziehen (sicherstellt Sichtbarkeit)
        for xs, ys, zs in _quader_edges(ax0, ay0, az0, clx, cly, clz):
            ax.plot(xs, ys, zs, color='#cc0000', lw=1.3,
                    linestyle='--', alpha=0.95)

def draw_cylinder_3d(ax, r, h, x0=0, y0=0, z0=0,
                     face_color=C_SCREW, alpha=0.85, edge_color="#333", n=32):
    """Zeichnet einen aufrechten Zylinder."""
    theta = np.linspace(0, 2*np.pi, n)
    # Mantel
    xs = x0 + r*np.cos(theta)
    ys = y0 + r*np.sin(theta)
    zs_bot = np.full_like(theta, z0)
    zs_top = np.full_like(theta, z0+h)
    mantel = []
    for i in range(n-1):
        mantel.append([
            [xs[i],   ys[i],   zs_bot[i]],
            [xs[i+1], ys[i+1], zs_bot[i+1]],
            [xs[i+1], ys[i+1], zs_top[i+1]],
            [xs[i],   ys[i],   zs_top[i]],
        ])
    r_val, g_val, b_val = matplotlib.colors.to_rgb(face_color)
    mantel_fc = [(r_val*0.88, g_val*0.88, b_val*0.88, alpha)] * len(mantel)
    ax.add_collection3d(Poly3DCollection(mantel, facecolor=mantel_fc,
                                         edgecolor=edge_color, linewidth=0.3))
    # Deckel + Boden
    circle = [[xs[i], ys[i], z0+h] for i in range(n)]
    circle2= [[xs[i], ys[i], z0]   for i in range(n)]
    top_fc = (r_val*0.95, g_val*0.95, b_val*0.95, alpha)
    bot_fc = (r_val*0.65, g_val*0.65, b_val*0.65, alpha)
    ax.add_collection3d(Poly3DCollection([circle],  facecolor=[top_fc], edgecolor=edge_color, lw=0.3))
    ax.add_collection3d(Poly3DCollection([circle2], facecolor=[bot_fc], edgecolor=edge_color, lw=0.3))
    ax.plot(xs, ys, zs_top, color=edge_color, lw=0.5)
    ax.plot(xs, ys, zs_bot, color=edge_color, lw=0.5)

def draw_hinge_3d(ax, w, h, t, face_color=C_STEEL, alpha=0.85):
    """Zeichnet ein L-förmiges Scharnier (zwei flache Platten)."""
    # Platte 1 – horizontal
    draw_box_3d(ax, w, t, h/2, x0=0,   y0=0, z0=0,
                face_color=face_color, alpha=alpha)
    # Platte 2 – vertikal (nach hinten geklappt)
    draw_box_3d(ax, w, h/2, t, x0=0,   y0=t, z0=0,
                face_color=face_color, alpha=alpha)

def draw_flat_bar_3d(ax, dx, dy, dz, face_color=C_ALU, alpha=0.85):
    """Flachprofil / Klemmschiene."""
    draw_box_3d(ax, dx, dy, dz, face_color=face_color, alpha=alpha)

def draw_bolt_3d(ax, d, h, face_color=C_SCREW, alpha=0.9):
    """Schraube = Zylinder + kleiner Kopf-Zylinder."""
    r = d/2
    draw_cylinder_3d(ax, r,   h,   x0=0, y0=0, z0=0,
                     face_color=face_color, alpha=alpha)
    draw_cylinder_3d(ax, r*1.7, d*0.6, x0=0, y0=0, z0=h,
                     face_color=face_color, alpha=alpha)

def _setup_ax(ax, lx, ly, lz, elev=28, azim=40):
    """Standardeinstellungen für eine 3D-Achse."""
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)
    margin = 0.15
    ax.set_xlim(-lx*margin, lx*(1+margin))
    ax.set_ylim(-ly*margin, ly*(1+margin))
    ax.set_zlim(-lz*margin, lz*(1+margin))
    ax.set_box_aspect([lx, ly, lz])
    ax.set_facecolor("white")

# ──────────────────────────────────────────────────────────────────────────────
# BAUTEIL-DATEN
# ──────────────────────────────────────────────────────────────────────────────

# Jeder Eintrag: (pos, name, dims_str, material, qty, weight_str, group, draw_fn_key, draw_params)
PARTS = [
    # ── Gruppe 1: Stahlrahmen 50×50 ──
    ("GWH_01", "Eckstiel",               "2175×50×50 mm",  "Stahl verzinkt",    "4×",  "≈6,4 kg/Stk",  "Stahlrahmen 50×50 mm",
     "notched_box", dict(dx=0.50, dy=0.50, dz=21.75, fc=C_STEEL,
                         cuts=[(0, 0.25, 21.50, 0.50, 0.25, 0.25)],
                         notch_label="Typ 4 – Kopfzapfen oben (1×)")),
    ("GWH_02", "Bodenrahmen Längsriegel","1100×50×50 mm",  "Stahl verzinkt",    "2×",  "≈3,2 kg/Stk",  "Stahlrahmen 50×50 mm",
     "notched_box", dict(dx=11.0, dy=0.50, dz=0.50, fc=C_STEEL,
                         cuts=[(0.25, 0, 0.25, 0.50, 0.50, 0.25),
                               (10.25, 0, 0.25, 0.50, 0.50, 0.25)],
                         notch_label="Typ 3 – Zapfentaschen (2×)")),
    ("GWH_03", "Bodenrahmen Querriegel", "1100×50×50 mm",  "Stahl verzinkt",    "2×",  "≈3,2 kg/Stk",  "Stahlrahmen 50×50 mm",
     "notched_box", dict(dx=11.0, dy=0.50, dz=0.50, fc=C_STEEL,
                         cuts=[(0,    0, 0.25, 0.50, 0.50, 0.25),
                               (10.50, 0, 0.25, 0.50, 0.50, 0.25)],
                         notch_label="Typ 1 – Vollausklinkung (2×)")),
    ("GWH_04", "Obergurt Längsriegel",   "1100×50×50 mm",  "Stahl verzinkt",    "2×",  "≈3,2 kg/Stk",  "Stahlrahmen 50×50 mm",
     "notched_box", dict(dx=11.0, dy=0.50, dz=0.50, fc=C_STEEL,
                         cuts=[(0.25,  0.25, 0, 0.50, 0.25, 0.25),
                               (10.25, 0.25, 0, 0.50, 0.25, 0.25)],
                         notch_label="Typ 4 – Zapfentaschen unten (2×)")),
    ("GWH_05", "Obergurt Querriegel",    "1100×50×50 mm",  "Stahl verzinkt",    "2×",  "≈3,2 kg/Stk",  "Stahlrahmen 50×50 mm",
     "notched_box", dict(dx=11.0, dy=0.50, dz=0.50, fc=C_STEEL,
                         cuts=[(0,    0, 0, 0.50, 0.50, 0.25),
                               (10.50, 0, 0, 0.50, 0.50, 0.25)],
                         notch_label="Typ 1 – Vollausklinkung (2×)")),
    # ── Gruppe 2: Dachrahmen ──
    ("GWH_06", "Dach Vorderriegel",      "1800×50×50 mm",  "Stahl verzinkt",    "1×",  "≈5,3 kg/Stk",  "Dachrahmen 50×50 mm  (Überstand 300 mm je Seite, z=2150 mm)",
     "box",  dict(dx=18.0, dy=0.50, dz=0.50, fc=C_STEEL)),
    ("GWH_07", "Dach Hinterriegel",      "1800×50×50 mm",  "Stahl verzinkt",    "1×",  "≈5,3 kg/Stk",  "Dachrahmen 50×50 mm  (Überstand 300 mm je Seite, z=2450 mm)",
     "box",  dict(dx=18.0, dy=0.50, dz=0.50, fc=C_STEEL)),
    ("GWH_08", "Dach Seitenträger",      "1825×50×50 mm",  "Stahl verzinkt ⚠️","2×",  "≈5,4 kg/Stk",  "Dachrahmen 50×50 mm",
     "box",  dict(dx=18.25,dy=0.50, dz=0.50, fc="#aac0d0")),
    ("GWH_09", "Dach Mittelpfette",      "1800×50×50 mm",  "Stahl verzinkt",    "1×",  "≈5,3 kg/Stk",  "Dachrahmen 50×50 mm  (Überstand 300 mm je Seite, z=2300 mm)",
     "box",  dict(dx=18.0, dy=0.50, dz=0.50, fc=C_STEEL)),
    # ── Gruppe 3: Dachzubehör ──
    ("GWH_10", "Scharnier Dach",         "100×100×10 mm",  "Stahl verzinkt",    "2×",  "≈0,5 kg/Stk",  "Dachzubehör",
     "hinge",dict(w=4.0,  h=4.0,  t=0.4,  fc=C_STEEL)),
    ("GWH_11", "Gasdruckfeder",          "Ø28×350 mm",     "Stahl/Kunststoff",  "1×",  "≈0,6 kg/Stk",  "Dachzubehör",
     "cyl",  dict(r=1.4,  h=17.5, fc="#aaaacc")),
    # ── Gruppe 4: Türrahmen ──
    ("GWH_14", "Mittelstiel",            "1900×50×50 mm",  "Stahl verzinkt",    "1×",  "≈5,6 kg/Stk",  "Türrahmen 50×50 mm",
     "notched_box", dict(dx=0.50, dy=0.50, dz=19.0, fc=C_STEEL,
                         cuts=[(0, 0.25, 18.75, 0.50, 0.25, 0.25)],
                         notch_label="Typ 4 – Kopfzapfen oben (1×)")),
    ("GWH_15", "Türsturz",              "1100×50×50 mm",  "Stahl verzinkt",    "1×",  "≈3,2 kg/Stk",  "Türrahmen 50×50 mm",
     "box",  dict(dx=11.0, dy=0.50, dz=0.50, fc=C_STEEL)),
    # ── Gruppe 5: Türflügel ──
    ("GWH_12", "Türflügel Horizontalrgl.","575×30×30 mm",  "Stahl verzinkt",    "6×",  "≈1,0 kg/Stk",  "Türflügel 30×30 mm",
     "box",  dict(dx=5.75, dy=0.30, dz=0.30, fc="#c0c8d0")),
    ("GWH_13", "Türflügel Vertikalrgl.", "1900×30×30 mm",  "Stahl verzinkt",    "4×",  "≈3,3 kg/Stk",  "Türflügel 30×30 mm",
     "box",  dict(dx=0.30, dy=0.30, dz=19.0, fc="#c0c8d0")),
    ("GWH_16", "Scharnier Tür",          "100×80×8 mm",    "Stahl verzinkt",    "4×",  "≈0,2 kg/Stk",  "Türflügel 30×30 mm",
     "hinge",dict(w=4.0,  h=3.2,  t=0.32, fc=C_STEEL)),
    ("GWH_17", "Türverschlussriegel",    "150×50×30 mm",   "Stahl verzinkt",    "1×",  "≈0,2 kg/Stk",  "Türflügel 30×30 mm",
     "box",  dict(dx=5.0,  dy=3.0, dz=1.5, fc=C_STEEL_D)),
    # ── Gruppe 6: Holzboden ──
    ("GWH_18", "Trittholm",              "1200×80×40 mm",  "Kiefer/Lärche",     "1×",  "≈3,1 kg/Stk",  "Holzboden",
     "box",  dict(dx=12.0, dy=0.80, dz=0.40, fc=C_WOOD)),
    ("GWH_19", "Querträger KVH",         "1100×60×60 mm",  "KVH Si/NSi",        "4×",  "≈2,6 kg/Stk",  "Holzboden",
     "box",  dict(dx=11.0, dy=0.60, dz=0.60, fc=C_WOOD)),
    ("GWH_20", "Lärchendiele N+F",       "1100×116×22 mm", "Lärche Nut+Feder",  "9×",  "≈1,8 kg/Stk",  "Holzboden",
     "box",  dict(dx=11.0, dy=1.16, dz=0.22, fc="#d4a96a")),
    # ── Gruppe 7: Klemmschienen & Verbindungsmittel ──
    ("GWH_21", "Klemmschiene",           "25×10×1100 mm",  "Alu/Stahl",         "~14×","≈0,3 kg/Stk",  "Verbindungsmittel",
     "box",  dict(dx=11.0, dy=0.25, dz=0.10, fc=C_ALU)),
    ("GWH_22", "Schraube M10×80",        "Ø10×80 mm",      "Stahl 8.8",         "~32×","≈0,06 kg",     "Verbindungsmittel",
     "bolt", dict(d=0.5,   h=4.0,  fc=C_SCREW)),
    ("GWH_23", "Schraube M8×60",         "Ø8×60 mm",       "Stahl 8.8",         "~40×","≈0,03 kg",     "Verbindungsmittel",
     "bolt", dict(d=0.4,   h=3.0,  fc=C_SCREW)),
    ("GWH_24", "Schraube M6×30",         "Ø6×30 mm",       "Stahl 8.8",         "~40×","≈0,01 kg",     "Verbindungsmittel",
     "bolt", dict(d=0.3,   h=1.5,  fc=C_SCREW)),
    # ── Gruppe 8: Folie ──
    ("—",      "PE-Folie 200 µm",        "4000×4000 mm (Z)","PE UV-stabilisiert","1 Ro","≈4,5 kg/Ro",   "Folie",
     "box",  dict(dx=8.0,  dy=8.0, dz=0.04, fc=C_FOIL)),
]

# ──────────────────────────────────────────────────────────────────────────────
# RENDER-HILFSFUNKTION: ein Bauteil-3D-Bild erzeugen
# ──────────────────────────────────────────────────────────────────────────────

def render_part_ax(ax, draw_key, params):
    fc = params.get("fc", C_STEEL)
    if draw_key == "box":
        dx,dy,dz = params["dx"],params["dy"],params["dz"]
        draw_box_3d(ax, dx, dy, dz, face_color=fc)
        _setup_ax(ax, dx, dy, dz)
    elif draw_key == "notched_box":
        dx, dy, dz = params["dx"], params["dy"], params["dz"]
        cuts = params.get("cuts", [])
        draw_notched_box_3d(ax, dx, dy, dz, cuts, face_color=fc)
        _setup_ax(ax, dx, dy, dz)
    elif draw_key == "cyl":
        r,h = params["r"],params["h"]
        draw_cylinder_3d(ax, r, h, face_color=fc)
        _setup_ax(ax, r*2, r*2, h, elev=20, azim=40)
    elif draw_key == "bolt":
        d,h = params["d"],params["h"]
        draw_bolt_3d(ax, d, h, face_color=fc)
        _setup_ax(ax, d*1.8, d*1.8, h+d*0.6, elev=20, azim=40)
    elif draw_key == "hinge":
        w,h,t = params["w"],params["h"],params["t"]
        draw_hinge_3d(ax, w, h, t, face_color=fc)
        _setup_ax(ax, w, h, h, elev=25, azim=40)

# ──────────────────────────────────────────────────────────────────────────────
# SEITEN-ERSTELLUNG
# ──────────────────────────────────────────────────────────────────────────────

def add_page_header(fig, page_title="Stückliste – Gewächshaus", page_num=None):
    """Fügt oben einen schmalen Header-Streifen hinzu."""
    ax_hdr = fig.add_axes([0, 0.955, 1, 0.045])
    ax_hdr.set_xlim(0,1); ax_hdr.set_ylim(0,1)
    ax_hdr.axis("off")
    ax_hdr.add_patch(plt.Rectangle((0,0),1,1, color=C_TITLE_BG, transform=ax_hdr.transAxes, zorder=0))
    ax_hdr.text(0.012, 0.5, "GWH-2024  |  " + page_title,
                va="center", ha="left", fontsize=9, color="white", fontweight="bold")
    ax_hdr.text(0.5, 0.5, "Gewächshaus 1200×1200×2200 mm  |  Pultdach  |  Zweiflügelige Tür",
                va="center", ha="center", fontsize=8, color="#aaccee")
    if page_num:
        ax_hdr.text(0.988, 0.5, f"Seite {page_num}",
                    va="center", ha="right", fontsize=8, color="#aaccee")

def add_page_footer(fig, revision="Rev. A"):
    ax_ft = fig.add_axes([0, 0, 1, 0.025])
    ax_ft.axis("off")
    ax_ft.add_patch(plt.Rectangle((0,0),1,1, color="#e8eef4", transform=ax_ft.transAxes))
    ax_ft.text(0.012, 0.5, f"Erstellt: {date.today().strftime('%d.%m.%Y')}  |  {revision}  |  Alle Maße in mm",
                va="center", ha="left", fontsize=7, color="#555")
    ax_ft.text(0.988, 0.5, "© 2024 – Fertigungsbegleitblatt – Vertraulich",
                va="center", ha="right", fontsize=7, color="#888")

# ──────────────────────────────────────────────────────────────────────────────
# DECKBLATT
# ──────────────────────────────────────────────────────────────────────────────

def make_cover_page(pdf):
    fig = plt.figure(figsize=(8.27, 11.69))  # A4
    fig.patch.set_facecolor("white")

    # ── Blauer Titel-Banner ──
    ax_banner = fig.add_axes([0, 0.82, 1, 0.18])
    ax_banner.axis("off")
    ax_banner.add_patch(plt.Rectangle((0,0),1,1, color=C_TITLE_BG))
    ax_banner.text(0.05, 0.72, "STÜCKLISTE",
                   **FONT_TITLE, transform=ax_banner.transAxes, va="top")
    ax_banner.text(0.05, 0.52, "Gewächshaus 1200 × 1200 × 2200 mm",
                   fontsize=16, fontweight="bold", color="#ddeeff",
                   transform=ax_banner.transAxes, va="top")
    ax_banner.text(0.05, 0.30, "Pultdach aufklappbar  |  Zweiflügelige Tür  |  Holzdielenboden",
                   **FONT_SUB, transform=ax_banner.transAxes, va="top")
    ax_banner.text(0.05, 0.10,
                   f"Datum: {date.today().strftime('%d.%m.%Y')}   |   Rev. A   |   Maßstab: ohne (Richtwerte)",
                   fontsize=9, color="#aaccee", transform=ax_banner.transAxes, va="top")

    # ── Isometrisches Gesamtbild ──
    ax_img = fig.add_axes([0.03, 0.46, 0.44, 0.34])
    ax_img.axis("off")
    ax_img.add_patch(plt.Rectangle((0,0),1,1, color="#f0f5fa",
                                    transform=ax_img.transAxes))
    if os.path.exists(ISO_IMG):
        img = plt.imread(ISO_IMG)
        ax_img.imshow(img, aspect="auto")
    else:
        ax_img.text(0.5, 0.5, "[Isometrische Ansicht]",
                    ha="center", va="center", color="#999", fontsize=10)
    ax_img.set_title("Isometrische Gesamtansicht", fontsize=8,
                     color=C_TITLE_BG, pad=3, fontweight="bold")

    # ── Kurzinfo-Kasten rechts neben Bild ──
    ax_info = fig.add_axes([0.52, 0.46, 0.45, 0.34])
    ax_info.axis("off")
    ax_info.add_patch(plt.Rectangle((0,0),1,1, color=C_HDR_BG,
                                     transform=ax_info.transAxes, lw=1.5,
                                     ec=C_BORDER))
    info_lines = [
        ("Projekt:",        "Gewächshaus – Eigenbau"),
        ("Abmessungen:",    "1200 × 1200 × 2200 mm (A×T×H)"),
        ("Dachneigung:",    "≈ 9,5°  |  Δ Höhe = 200 mm"),
        ("Türsystem:",      "Zweiflügelig 2× 575 mm licht"),
        ("Verbindung:",     "Ausklinkungen Typ 1–4"),
        ("Revision:",       "A – Erstausgabe"),
        ("Erstellt:",       date.today().strftime("%d.%m.%Y")),
        ("Dokument-Nr.:",   "GWH-SL-2024-001"),
        ("Maßstab:",        "ohne (alle Maße in mm)"),
        ("Gewicht Stahl:",  "≈ 70 kg"),
        ("Gewicht Holz:",   "≈ 15 kg"),
        ("Profilmeter:",    "≈ 30 m (50×50) + ≈ 11 m (30×30)"),
        ("Folie:",          "≈ 10,6 m² PE 200 µm"),
    ]
    ax_info.text(0.05, 0.97, "Projekt-Informationen",
                 va="top", ha="left", fontsize=9, fontweight="bold",
                 color=C_TITLE_BG, transform=ax_info.transAxes)
    for i, (lbl, val) in enumerate(info_lines):
        y = 0.88 - i*0.065
        ax_info.text(0.05, y, lbl, va="top", ha="left", fontsize=7.5,
                     color="#555", fontweight="bold", transform=ax_info.transAxes)
        ax_info.text(0.42, y, val, va="top", ha="left", fontsize=7.5,
                     color=C_TEXT, transform=ax_info.transAxes)

    # ── Gruppen-Übersichtstabelle ──
    ax_tbl = fig.add_axes([0.03, 0.06, 0.94, 0.38])
    ax_tbl.axis("off")
    ax_tbl.add_patch(plt.Rectangle((0,0),1,1, color="#f7fafd",
                                    transform=ax_tbl.transAxes, lw=1.5, ec=C_BORDER))
    ax_tbl.text(0.02, 0.965, "Gesamtübersicht – Bauteilgruppen",
                va="top", ha="left", fontsize=10, fontweight="bold",
                color=C_TITLE_BG, transform=ax_tbl.transAxes)

    groups = [
        ("Gr. 1", "Stahlrahmen 50×50 mm",         "13",  "28,0 m",  "≈ 55 kg",  "Stahl verzinkt"),
        ("Gr. 2", "Dachrahmen 50×50 mm",            "4",   "5,8 m",  "≈ 17 kg",  "Stahl verzinkt"),
        ("Gr. 3", "Dachzubehör",                    "2",     "—",    "≈  1 kg",  "Stahl / Kunststoff"),
        ("Gr. 4", "Türrahmen 50×50 mm",             "2",   "3,0 m",  "≈  9 kg",  "Stahl verzinkt"),
        ("Gr. 5", "Türflügel 30×30 mm",             "4",  "11,1 m",  "≈ 12 kg",  "Stahl verzinkt"),
        ("Gr. 6", "Holzboden",                      "3",  "15,5 lm", "≈ 15 kg",  "Kiefer / Lärche"),
        ("Gr. 7", "Klemmschienen & Verbind.",        "4",  "20,8 m",  "≈  4 kg",  "Alu / Stahl 8.8"),
        ("Gr. 8", "Folie",                           "1",    "—",    "≈  5 kg",  "PE 200 µm UV-stab."),
    ]
    col_x   = [0.01, 0.07, 0.38, 0.56, 0.68, 0.80]
    col_hdr = ["#", "Gruppe / Bezeichnung", "Pos.", "Längen", "Gewicht", "Material"]
    col_w   = [0.06, 0.30, 0.08, 0.12, 0.12, 0.20]

    # Header-Zeile
    for cx, ch in zip(col_x, col_hdr):
        ax_tbl.add_patch(plt.Rectangle((cx, 0.875), col_w[col_x.index(cx)], 0.07,
                                        color=C_GROUP_BG, transform=ax_tbl.transAxes, clip_on=False))
        ax_tbl.text(cx+0.005, 0.905, ch, va="center", ha="left", fontsize=8,
                    fontweight="bold", color="white", transform=ax_tbl.transAxes)

    for ri, row in enumerate(groups):
        y = 0.85 - ri*0.102
        bg = "#eef3f8" if ri % 2 == 0 else "white"
        ax_tbl.add_patch(plt.Rectangle((0.01, y-0.015), 0.98, 0.095,
                                        color=bg, transform=ax_tbl.transAxes, clip_on=False))
        for ci, (cx, val) in enumerate(zip(col_x, row)):
            ax_tbl.text(cx+0.005, y+0.030, val, va="center", ha="left",
                        fontsize=8, color=C_TEXT, transform=ax_tbl.transAxes,
                        fontweight="bold" if ci == 0 else "normal")

    # Trennlinie
    ax_tbl.axhline(0.875, xmin=0.01, xmax=0.99, color=C_BORDER, lw=1)

    add_page_footer(fig)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)

# ──────────────────────────────────────────────────────────────────────────────
# BAUTEIL-KATALOG-SEITEN  (3 Karten pro Zeile, 2 Zeilen = 6 pro Seite,
#                          aber wir machen 3 pro Seite für bessere Darstellung)
# ──────────────────────────────────────────────────────────────────────────────

COLS = 3   # Karten pro Zeile
ROWS = 2   # Zeilen pro Seite  → 6 Bauteile/Seite

def make_part_card(fig, rect, part, page_num):
    """
    Zeichnet ein Bauteil-Kästchen in die übergebene Achsen-Region [l,b,w,h].
    rect = (left, bottom, width, height) in figure-Koordinaten
    """
    l, b, w, h = rect
    # Rahmen-Hintergrund
    ax_bg = fig.add_axes([l, b, w, h])
    ax_bg.set_xlim(0,1); ax_bg.set_ylim(0,1)
    ax_bg.axis("off")
    ax_bg.add_patch(FancyBboxPatch((0.01,0.01), 0.98, 0.98,
                                   boxstyle="round,pad=0.01",
                                   facecolor=C_CARD_BG, edgecolor=C_BORDER,
                                   linewidth=1.0, transform=ax_bg.transAxes,
                                   zorder=1))

    pos, name, dims, mat, qty, weight, grp, draw_key, params = part

    # Positions-Nummer (blau, oben links)
    ax_bg.text(0.05, 0.955, pos,
               va="top", ha="left", fontsize=9, fontweight="bold",
               color=C_TITLE_BG, transform=ax_bg.transAxes, zorder=5)
    # Gruppe oben rechts
    ax_bg.text(0.95, 0.955, grp,
               va="top", ha="right", fontsize=6, color="#888",
               transform=ax_bg.transAxes, zorder=5, style="italic")

    # Trennlinie unter Header
    ax_bg.axhline(0.905, xmin=0.03, xmax=0.97, color=C_BORDER, lw=0.6, zorder=5)

    # 3D-Bauteil-Ansicht  (in ax_bg-Koordinaten: 0.05–0.95 × 0.34–0.90)
    ax3d = fig.add_axes([l + w*0.05, b + h*0.34, w*0.90, h*0.56], projection="3d")
    ax3d.set_facecolor("white")
    render_part_ax(ax3d, draw_key, params)

    # Info-Zeilen unten
    info = [
        ("Name:",  name),
        ("Maße:",  dims),
        ("Mat.:",  mat),
        ("Menge:", qty),
        ("Gew.:",  weight),
    ]
    for i, (lbl, val) in enumerate(info):
        y = 0.305 - i*0.058
        ax_bg.text(0.05, y, lbl, va="top", ha="left", fontsize=6.8,
                   color="#666", fontweight="bold", transform=ax_bg.transAxes, zorder=5)
        ax_bg.text(0.32, y, val, va="top", ha="left", fontsize=6.8,
                   color=C_TEXT, transform=ax_bg.transAxes, zorder=5,
                   wrap=True)

    # Rote Ausklinkungshinweis-Zeile (nur für Bauteile mit Ausklinkungen)
    notch_label = params.get("notch_label", None)
    if notch_label:
        ax_bg.add_patch(plt.Rectangle((0.03, 0.015), 0.94, 0.050,
                                      facecolor="#fff0f0", edgecolor="#cc0000",
                                      linewidth=0.7, transform=ax_bg.transAxes,
                                      zorder=4))
        ax_bg.text(0.06, 0.042, f"⚠  Ausklinkung:  {notch_label}",
                   va="center", ha="left", fontsize=6.5,
                   color="#cc0000", fontweight="bold",
                   transform=ax_bg.transAxes, zorder=5)

def make_parts_pages(pdf, parts, page_offset=2):
    n = len(parts)
    per_page = COLS * ROWS
    num_pages = (n + per_page - 1) // per_page

    margin_l = 0.03
    margin_r = 0.03
    margin_top = 0.04   # unter Header
    margin_bot = 0.04   # über Footer
    header_h = 0.045
    footer_h = 0.025
    usable_w = 1 - margin_l - margin_r
    usable_h = 1 - header_h - footer_h - margin_top - margin_bot

    card_w = usable_w / COLS
    card_h = usable_h / ROWS
    gap_x  = 0.008
    gap_y  = 0.010

    # Gruppen-Farb-Banner: welche Gruppe ist auf welcher Seite?
    for pg in range(num_pages):
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        pg_parts = parts[pg*per_page : (pg+1)*per_page]

        # Gruppen-Banner falls neue Gruppe beginnt
        grp_on_page = list(dict.fromkeys(p[6] for p in pg_parts))
        grp_label = "  ·  ".join(grp_on_page)
        ax_grp = fig.add_axes([0, 0.905, 1, 0.025])
        ax_grp.axis("off")
        ax_grp.add_patch(plt.Rectangle((0,0),1,1, color=C_GROUP_BG))
        ax_grp.text(0.012, 0.5, grp_label, va="center", ha="left",
                    **FONT_GROUP, transform=ax_grp.transAxes)

        add_page_header(fig, page_title="Bauteil-Katalog",
                        page_num=page_offset + pg)
        add_page_footer(fig)

        for idx, part in enumerate(pg_parts):
            row_i = idx // COLS
            col_i = idx % COLS
            left   = margin_l + col_i * (card_w + gap_x)
            bottom = (1 - header_h - margin_top - (row_i+1)*card_h - row_i*gap_y
                      + gap_y*0.5)
            rect   = (left, bottom, card_w - gap_x, card_h - gap_y)
            make_part_card(fig, rect, part, pg + page_offset)

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
    return page_offset + num_pages

# ──────────────────────────────────────────────────────────────────────────────
# ABSCHLUSSSEITE
# ──────────────────────────────────────────────────────────────────────────────

def make_summary_page(pdf, page_num):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    add_page_header(fig, page_title="Zusammenfassung & Montagehinweise", page_num=page_num)
    add_page_footer(fig)

    # ── Gesamtgewichte ──
    ax_gew = fig.add_axes([0.03, 0.73, 0.45, 0.19])
    ax_gew.axis("off")
    ax_gew.add_patch(plt.Rectangle((0,0),1,1, color=C_HDR_BG,
                                    transform=ax_gew.transAxes, lw=1.5, ec=C_BORDER))
    ax_gew.text(0.05, 0.93, "Gewichte & Mengen (gesamt)",
                va="top", fontsize=9, fontweight="bold", color=C_TITLE_BG,
                transform=ax_gew.transAxes)
    summary_weights = [
        ("Stahlkonstruktion gesamt:", "≈ 70 kg"),
        ("Holzboden gesamt:",         "≈ 15 kg"),
        ("Folie + Zubehör:",          "≈  5 kg"),
        ("Gesamtgewicht (ca.):",      "≈ 90 kg"),
    ]
    for i, (lbl, val) in enumerate(summary_weights):
        y = 0.78 - i*0.165
        ax_gew.text(0.05, y, lbl, va="top", fontsize=8, color="#444",
                    fontweight="bold", transform=ax_gew.transAxes)
        ax_gew.text(0.72, y, val, va="top", fontsize=8.5, color=C_TITLE_BG,
                    fontweight="bold", transform=ax_gew.transAxes)

    # ── Profilmeter ──
    ax_pm = fig.add_axes([0.52, 0.73, 0.45, 0.19])
    ax_pm.axis("off")
    ax_pm.add_patch(plt.Rectangle((0,0),1,1, color=C_HDR_BG,
                                   transform=ax_pm.transAxes, lw=1.5, ec=C_BORDER))
    ax_pm.text(0.05, 0.93, "Profilmeter & Flächenbedarf",
               va="top", fontsize=9, fontweight="bold", color=C_TITLE_BG,
               transform=ax_pm.transAxes)
    pm_data = [
        ("50×50 mm Vierkantprofil:", "≈ 30,0 m"),
        ("30×30 mm Vierkantprofil:", "≈ 11,1 m"),
        ("25×10 mm Klemmschiene:",   "≈ 20,8 m"),
        ("PE-Folie 200 µm:",         "≈ 10,6 m²"),
    ]
    for i, (lbl, val) in enumerate(pm_data):
        y = 0.78 - i*0.165
        ax_pm.text(0.05, y, lbl, va="top", fontsize=8, color="#444",
                   fontweight="bold", transform=ax_pm.transAxes)
        ax_pm.text(0.72, y, val, va="top", fontsize=8.5, color=C_TITLE_BG,
                   fontweight="bold", transform=ax_pm.transAxes)

    # ── Montagereihenfolge ──
    ax_mont = fig.add_axes([0.03, 0.41, 0.94, 0.29])
    ax_mont.axis("off")
    ax_mont.add_patch(plt.Rectangle((0,0),1,1, color="#f7fafd",
                                     transform=ax_mont.transAxes, lw=1.5, ec=C_BORDER))
    ax_mont.text(0.02, 0.96, "Montagereihenfolge (5 Schritte)",
                 va="top", fontsize=10, fontweight="bold", color=C_TITLE_BG,
                 transform=ax_mont.transAxes)
    steps = [
        ("Schritt 1 – Bodenrahmen:",
         "Querriegel mit Typ-1-Ausklinkung (50×50 mm) an Längsriegel ansetzen. "
         "4 Eckstiele mit Zapfen-Typ-3 in Bodentaschen einstellen. "
         "M8×60-Schrauben diagonal durch Boden-Knoten sichern."),
        ("Schritt 2 – Obergurt & Mittelstiel:",
         "Obergurt-Längsriegel mit Typ-4-Taschen über Stielköpfe setzen. "
         "Mittelstiel mittig, Türsturz mit Typ-1-Ausklinkung. "
         "Je 1× M10×80 von oben durch OG-Tasche in Stielkopf."),
        ("Schritt 3 – Dachrahmen & Scharniere:",
         "Schwerlastscharnierpaar (100×100 mm) auf Obergurt Hinten montieren. "
         "Dachrahmen auflegen und an Scharnieren befestigen (M8×50). "
         "Gasdruckfeder einbauen (Kugelzapfen-Halterungen)."),
        ("Schritt 4 – Folie & Klemmschienen:",
         "Folie straff über Wandfelder legen, mit 25×10-Klemmschienen "
         "und M6×30-Schrauben klemmend fixieren. Folie an Ecken einschneiden "
         "und mit Doppelband abdichten."),
        ("Schritt 5 – Türflügel & Holzboden:",
         "30×30-Türflügelrahmen zusammenschrauben, Folie aufkleben. "
         "Flügel mit 4 Bandscharnieren einhängen. KVH-Querträger verlegen, "
         "Lärchedielen (N+F) aufbringen, Trittholm vor der Tür befestigen."),
    ]
    for i, (title, text) in enumerate(steps):
        y = 0.845 - i*0.175
        # Nummerkreis
        circle = plt.Circle((0.022, y+0.025), 0.018, color=C_TITLE_BG,
                             transform=ax_mont.transAxes, clip_on=False)
        ax_mont.add_patch(circle)
        ax_mont.text(0.022, y+0.025, str(i+1), va="center", ha="center",
                     fontsize=7, color="white", fontweight="bold",
                     transform=ax_mont.transAxes)
        ax_mont.text(0.055, y+0.045, title, va="top", ha="left", fontsize=8,
                     fontweight="bold", color=C_TITLE_BG, transform=ax_mont.transAxes)
        ax_mont.text(0.055, y+0.005, text,  va="top", ha="left", fontsize=7.2,
                     color="#333", transform=ax_mont.transAxes, wrap=True)

    # ── Ausklinkungshinweise ──
    ax_ausk = fig.add_axes([0.03, 0.065, 0.94, 0.32])
    ax_ausk.axis("off")
    ax_ausk.add_patch(plt.Rectangle((0,0),1,1, color="#fff8f0",
                                     transform=ax_ausk.transAxes, lw=1.5,
                                     ec="#c87a20"))
    ax_ausk.text(0.02, 0.955, "Ausklinkungshinweise – Fertigungstoleranzen",
                 va="top", fontsize=10, fontweight="bold", color="#7a3e00",
                 transform=ax_ausk.transAxes)

    ausk = [
        ("Typ 1 – Vollausklinkung (Eckknoten Boden/OG):",
         "Querriegel erhält beidseitig 50×50 mm-Kerbe (voller Querschnitt). "
         "Längsriegel durchgehend. Scherkräfte formschlüssig. "
         "Bohrloch: 1× Ø9 mm senkrecht, M8×60 sichern."),
        ("Typ 2 – Halbausklinkung / Überblattung (Pfetten-Kreuzknoten):",
         "Beide Profile je 25 mm tief (= halbe Höhe) fräsen. "
         "Überblattungstiefe 50 mm. Bohrloch: 1× Ø9 mm, M8×40 sichern."),
        ("Typ 3 – Zapfensitz (Bodenknoten, Stiel auf Rahmen):",
         "50×50×25 mm Tasche in Längsriegel-Oberseite fräsen. "
         "Stiel eingestellt. 2× Ø9 mm seitlich, M8×60 sichern."),
        ("Typ 4 – Zapfen/Tasche (Kopfknoten OG auf Stiel):",
         "Stielkopf: Top 25 mm auf 50×25 mm abfräsen (hintere Hälfte weg). "
         "OG: 50×25×25 mm Tasche in Unterseite. Schraube 1× M10×80 von oben."),
    ]
    colors_ausk = ["#1a3a5c", "#2c5f8a", "#c87a20", "#7a3e00"]
    for i, (title, text) in enumerate(ausk):
        y = 0.875 - i*0.218
        ax_ausk.add_patch(plt.Rectangle((0.01, y-0.045), 0.008, 0.10,
                                         color=colors_ausk[i],
                                         transform=ax_ausk.transAxes, clip_on=False))
        ax_ausk.text(0.028, y+0.040, title, va="top", fontsize=8,
                     fontweight="bold", color=colors_ausk[i],
                     transform=ax_ausk.transAxes)
        ax_ausk.text(0.028, y+0.008, text,  va="top", fontsize=7.2,
                     color="#333", transform=ax_ausk.transAxes)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)

# ──────────────────────────────────────────────────────────────────────────────
# HAUPT-FUNKTION
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("Generiere Stückliste-PDF mit 3D-Bauteil-Darstellungen …")
    with PdfPages(OUTPUT) as pdf:
        # Meta-Daten
        d = pdf.infodict()
        d["Title"]   = "Stückliste – Gewächshaus 1200×1200×2200 mm"
        d["Author"]  = "CAD-Designer GWH-2024"
        d["Subject"] = "Fertigungsbegleitblatt mit 3D-Bauteildarstellungen"
        d["Keywords"]= "Gewächshaus Stückliste Stahlkonstruktion Holzboden"

        # Seite 1 – Deckblatt
        make_cover_page(pdf)

        # Seiten 2–N – Bauteil-Katalog
        next_page = make_parts_pages(pdf, PARTS, page_offset=2)

        # Abschlussseite
        make_summary_page(pdf, page_num=next_page)

    print(f"✅  PDF gespeichert: {OUTPUT}")
    size_kb = os.path.getsize(OUTPUT) // 1024
    print(f"   Dateigröße: {size_kb} KB")
    # Seitenanzahl ohne externe Abhängigkeit ermitteln
    with open(OUTPUT, "rb") as fh:
        raw = fh.read()
    n_pages = raw.count(b"/Type /Page") + raw.count(b"/Type/Page")
    print(f"   Seitenanzahl (ca.): {n_pages if n_pages else 'PDF korrekt gespeichert'}")

if __name__ == "__main__":
    main()
