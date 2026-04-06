#!/usr/bin/env python3
"""
Typ 2: Fenstergewächshaus – Stückliste PDF mit 3D-Visualisierungen.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date
import os, sys

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

POST = FRAME_T; FT = FRAME_T
WIN_ZONE_H = WIN_ROWS * WIN_H
n_doors = sum([DOOR_FRONT, DOOR_BACK, DOOR_LEFT, DOOR_RIGHT])
n_total  = (WIN_COLS_FRONT + WIN_COLS_BACK + WIN_COLS_LEFT + WIN_COLS_RIGHT) * WIN_ROWS
n_windows = n_total - n_doors

OUTPUT = os.path.join(_proj, "gewaechshaus_stueckliste_3d.pdf")

C_TITLE  = "#1a3a5c"; C_GROUP = "#2c5f8a"; C_CARD = "#f7fafd"
C_WOOD   = "#c8a060"; C_WOOD_D = "#8b6040"
C_GLASS  = "#cce8ff"; C_METAL = "#b0b8c1"; C_TEXT = "#1a1a2e"


def draw_frame_3d(ax, w, h, ft, c_frame=C_WOOD, c_glass=C_GLASS, title="Fenster"):
    """Isometrische Darstellung eines Fensterrahmens."""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    ax.set_axis_off()
    depth = ft
    # Außenquader
    def quader(x0,y0,z0,dx,dy,dz,color,alpha=0.8):
        x1,y1,z1 = x0+dx,y0+dy,z0+dz
        faces = [
            [[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]],
            [[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],
            [[x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1]],
            [[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]],
            [[x0,y0,z0],[x0,y1,z0],[x0,y1,z1],[x0,y0,z1]],
            [[x1,y0,z0],[x1,y1,z0],[x1,y1,z1],[x1,y0,z1]],
        ]
        pc = Poly3DCollection(faces, alpha=alpha, linewidth=0.3, edgecolor='#555')
        pc.set_facecolor(color)
        ax.add_collection3d(pc)
    # Rahmenteile
    quader(0,0,0,w,depth,ft,c_frame)          # unten
    quader(0,0,h-ft,w,depth,ft,c_frame)       # oben
    quader(0,0,ft,ft,depth,h-2*ft,c_frame)    # links
    quader(w-ft,0,ft,ft,depth,h-2*ft,c_frame) # rechts
    # Glas
    if w > 2*ft and h > 2*ft:
        quader(ft,depth*0.4,ft,w-2*ft,depth*0.1,h-2*ft,c_glass,alpha=0.4)
    ax.set_xlim(0,w); ax.set_ylim(0,depth); ax.set_zlim(0,h)
    ax.set_title(title, fontsize=7, fontweight='bold', pad=2)


PARTS = [
    {
        "pos": "FGH_01", "name": "Fensterrahmen",
        "mat": "Holz (Altfenster)", "qty": n_windows,
        "dim": f"{WIN_W} × {WIN_H} mm", "hinweis": "Rahmen ca. 60 mm stark",
        "color": C_WOOD, "draw": "window",
    },
    {
        "pos": "FGH_02", "name": "Balkontür",
        "mat": "Holz (Altbalkon­tür)", "qty": n_doors,
        "dim": f"{WIN_W} × {WIN_ZONE_H} mm", "hinweis": "Ersetzt unterste Fensterreihe",
        "color": C_WOOD_D, "draw": "door",
    },
    {
        "pos": "FGH_03", "name": "Eckpfosten",
        "mat": "KVH Fichte 100×100, druckimpr.", "qty": 4,
        "dim": f"100 × 100 × {H} mm", "hinweis": "Verbindet alle 4 Wandebenen",
        "color": C_WOOD_D, "draw": "post",
    },
    {
        "pos": "FGH_04", "name": "Schwellbalken",
        "mat": "KVH Fichte 100×100, druckimpr.", "qty": 4,
        "dim": f"100 × {max(B,T)-2*POST} mm", "hinweis": "Feuchtigkeitsschutz",
        "color": C_WOOD, "draw": "beam",
    },
    {
        "pos": "FGH_05", "name": "Obergurt-Balken",
        "mat": "KVH Fichte 100×100", "qty": 4,
        "dim": f"100 × {max(B,T)-2*POST} mm", "hinweis": "Dachanschluss",
        "color": C_WOOD, "draw": "beam",
    },
    {
        "pos": "FGH_06", "name": "Dachsparren",
        "mat": "KVH Fichte 50×100", "qty": max(2, B//600)+2,
        "dim": f"50 × 100 × ~{T+2*OVER} mm", "hinweis": "Pultdach, aufklappbar",
        "color": "#6a9a6a", "draw": "beam",
    },
    {
        "pos": "FGH_07", "name": "Winkelverbinder 90°",
        "mat": "Stahl verzinkt", "qty": "≥16",
        "dim": "60×60×2 mm", "hinweis": "Eckverbindungen Pfosten/Balken",
        "color": C_METAL, "draw": "none",
    },
    {
        "pos": "FGH_08", "name": "Holzschraube TX",
        "mat": "Stahl 8.8 vzk.", "qty": "≥80",
        "dim": "Ø6×80 mm", "hinweis": "Rahmenverschraubung",
        "color": "#888", "draw": "none",
    },
]

with PdfPages(OUTPUT) as pdf:
    # ── Titelseite ────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(29.7/2.54, 21/2.54))
    fig.patch.set_facecolor(C_TITLE)
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.set_facecolor(C_TITLE)
    ax.text(0.5, 0.72, "STÜCKLISTE", ha='center', fontsize=28,
            color='white', fontweight='bold', transform=ax.transAxes)
    ax.text(0.5, 0.60, "Gewächshaus aus alten Fenstern und Balkontüren",
            ha='center', fontsize=14, color='#dde8f4', transform=ax.transAxes)
    ax.text(0.5, 0.48,
            f"Gesamtmaße: {B} × {T} × {H} mm  |  "
            f"Fenster: {WIN_W}×{WIN_H} mm  |  {WIN_ROWS} Reihe(n)",
            ha='center', fontsize=10, color='#aaccee', transform=ax.transAxes)
    ax.text(0.5, 0.38, f"Generiert: {date.today().strftime('%d.%m.%Y')}",
            ha='center', fontsize=9, color='#7799bb', transform=ax.transAxes)
    pdf.savefig(fig, bbox_inches='tight'); plt.close(fig)

    # ── Bauteil-Seiten ────────────────────────────────────────────────────────
    per_page = 4
    for page_start in range(0, len(PARTS), per_page):
        page_parts = PARTS[page_start:page_start+per_page]
        fig = plt.figure(figsize=(29.7/2.54, 21/2.54), facecolor='white')
        for idx, p in enumerate(page_parts):
            row, col = divmod(idx, 2)
            ax_3d = fig.add_axes([col*0.5+0.02, 0.52-row*0.5+0.05, 0.2, 0.38],
                                 projection='3d')
            if p["draw"] == "window":
                draw_frame_3d(ax_3d, WIN_W, WIN_H, FT, title=p["name"])
            elif p["draw"] == "door":
                draw_frame_3d(ax_3d, WIN_W, WIN_ZONE_H, FT,
                              c_frame=C_WOOD_D, title=p["name"])
            elif p["draw"] in ("post", "beam"):
                lx = POST if p["draw"]=="post" else max(B,T)-2*POST
                ly = POST; lz = H if p["draw"]=="post" else POST
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                ax_3d.set_axis_off()
                x1,y1,z1 = lx,ly,lz
                faces = [
                    [[0,0,0],[x1,0,0],[x1,y1,0],[0,y1,0]],
                    [[0,0,z1],[x1,0,z1],[x1,y1,z1],[0,y1,z1]],
                    [[0,0,0],[x1,0,0],[x1,0,z1],[0,0,z1]],
                    [[0,y1,0],[x1,y1,0],[x1,y1,z1],[0,y1,z1]],
                ]
                pc = Poly3DCollection(faces, alpha=0.8, edgecolor='#555', linewidth=0.3)
                pc.set_facecolor(p["color"]); ax_3d.add_collection3d(pc)
                ax_3d.set_xlim(0,x1); ax_3d.set_ylim(0,y1); ax_3d.set_zlim(0,z1)
                ax_3d.set_title(p["name"], fontsize=7, fontweight='bold', pad=2)
            else:
                ax_3d.set_axis_off()
                ax_3d.text(0.5, 0.5, 0.5, p["name"], ha='center', fontsize=8,
                           color=p["color"])
                ax_3d.set_title(p["name"], fontsize=7, fontweight='bold', pad=2)

            # Info-Block
            ax_info = fig.add_axes([col*0.5+0.24, 0.52-row*0.5+0.05, 0.24, 0.38])
            ax_info.axis('off')
            ax_info.add_patch(mpatches.FancyBboxPatch(
                (0,0), 1, 1, boxstyle="round,pad=0.02", linewidth=1,
                edgecolor=C_GROUP, facecolor=C_CARD, transform=ax_info.transAxes))
            lines = [
                (p["pos"], 16, 'bold', C_GROUP),
                (p["name"], 11, 'bold', C_TEXT),
                (f"Material: {p['mat']}", 8, 'normal', '#444'),
                (f"Anzahl: {p['qty']}", 9, 'bold', C_TEXT),
                (f"Maß: {p['dim']}", 8, 'normal', '#444'),
                (f"Hinweis: {p['hinweis']}", 7, 'normal', '#666'),
            ]
            y = 0.88
            for txt, fs, fw, fc in lines:
                ax_info.text(0.05, y, txt, fontsize=fs, fontweight=fw,
                             color=fc, transform=ax_info.transAxes, va='top',
                             wrap=True)
                y -= 0.14
        pdf.savefig(fig, bbox_inches='tight'); plt.close(fig)

print(f"Stückliste Typ 2 gespeichert: {OUTPUT}")
