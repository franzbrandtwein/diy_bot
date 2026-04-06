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


def draw_window_2d(ax, w, h, ft, c_frame=C_WOOD, c_glass=C_GLASS,
                   title="Fenster", door=False):
    """Frontalansicht eines Fensterrahmens (2D, korrekte Proportionen)."""
    ax.set_aspect('equal')
    ax.axis('off')
    pad = 0.08
    scale = min((1 - 2*pad) / w, (1 - 2*pad) / h)
    sw = w * scale
    sh = h * scale
    ox = (1.0 - sw) / 2
    oy = (1.0 - sh) / 2
    sft = ft * scale

    # Schatten
    shadow = mpatches.Rectangle((ox+0.02, oy-0.02), sw, sh,
                                  fc='#aaa', ec='none', alpha=0.3, zorder=1)
    ax.add_patch(shadow)
    # Äußerer Rahmen
    outer = mpatches.Rectangle((ox, oy), sw, sh,
                                 fc=c_frame, ec='#4a3010', lw=1.5, zorder=2)
    ax.add_patch(outer)
    # Glas / Öffnung
    if sw > 2*sft and sh > 2*sft:
        gx, gy = ox + sft, oy + sft
        gw, gh = sw - 2*sft, sh - 2*sft
        if door:
            # Tür: offen unten → kein unterer Querriegel
            gy = oy
            gh = sh - sft
        glass = mpatches.Rectangle((gx, gy), gw, gh,
                                    fc=c_glass, ec='#6699bb', lw=0.8,
                                    alpha=0.55, zorder=3)
        ax.add_patch(glass)
        # Lichtreflex
        ax.plot([gx + gw*0.15, gx + gw*0.35], [gy + gh*0.75, gy + gh*0.88],
                color='white', lw=1.2, alpha=0.6, zorder=4)

    # Tiefeneffekt: rechte/obere Kante leicht dunkler
    ax.plot([ox+sw, ox+sw+0.01], [oy, oy-0.01], color='#4a3010', lw=0.5,
            alpha=0.5, zorder=5)

    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=7, fontweight='bold', pad=2)


def draw_beam_2d(ax, lx, lz, color, title):
    """Frontalansicht eines Balkens / Pfostens."""
    ax.set_aspect('equal')
    ax.axis('off')
    pad = 0.1
    scale = min((1-2*pad)/max(lx,1), (1-2*pad)/max(lz,1))
    sw, sh = lx*scale, lz*scale
    ox, oy = (1-sw)/2, (1-sh)/2
    shadow = mpatches.Rectangle((ox+0.02, oy-0.02), sw, sh,
                                  fc='#aaa', ec='none', alpha=0.3)
    ax.add_patch(shadow)
    rect = mpatches.Rectangle((ox, oy), sw, sh,
                                fc=color, ec='#333', lw=1.2)
    ax.add_patch(rect)
    # Maserung
    for i in range(1, 4):
        yl = oy + i * sh / 4
        ax.plot([ox+0.01*sw, ox+0.99*sw], [yl, yl+0.02*sh],
                color='#7a5020', lw=0.4, alpha=0.4)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
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
            ax_3d = fig.add_axes([col*0.5+0.02, 0.52-row*0.5+0.05, 0.2, 0.38])
            if p["draw"] == "window":
                draw_window_2d(ax_3d, WIN_W, WIN_H, FT, title=p["name"])
            elif p["draw"] == "door":
                draw_window_2d(ax_3d, WIN_W, WIN_ZONE_H, FT,
                               c_frame=C_WOOD_D, title=p["name"], door=True)
            elif p["draw"] in ("post", "beam"):
                lx = POST if p["draw"] == "post" else max(B, T) - 2*POST
                lz = H    if p["draw"] == "post" else POST
                draw_beam_2d(ax_3d, lx, lz, p["color"], title=p["name"])
            else:
                ax_3d.axis("off")
                ax_3d.text(0.5, 0.5, p["name"], ha="center", va="center",
                           fontsize=8, color=p["color"])
                ax_3d.set_title(p["name"], fontsize=7, fontweight="bold", pad=2)

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
