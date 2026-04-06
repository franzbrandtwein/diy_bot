#!/usr/bin/env python3
"""
Typ 2: Fenstergewächshaus – Technische Zeichnung
Erzeugt: PDF mit Grundriss, Ansichten, Schnitt
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

_proj = os.environ.get("GWH_PROJECT_DIR",
        "/home/herrvorragend/projekte/gewaechshaus")
os.makedirs(_proj, exist_ok=True)

import sys; sys.path.insert(0, _proj)
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

POST = FRAME_T; TOP_H = FRAME_T
WIN_ZONE_H = WIN_ROWS * WIN_H

SC = 1/10  # Maßstab 1:10 → mm → cm

# ── Farben ──────────────────────────────────────────────────────────────────
C_WOOD     = "#c8a060"
C_WOOD_D   = "#7a5020"
C_GLASS    = "#cce8ff"
C_DOOR     = "#a07840"
C_DIM      = "#2244aa"
C_BG       = "#f8f8f8"

fig = plt.figure(figsize=(42/2.54, 30/2.54), facecolor=C_BG)
fig.suptitle(
    f"Gewächshaus aus Altfenstern  –  {B}×{T}×{H} mm  |  "
    f"Fenster: {WIN_W}×{WIN_H} mm  |  Maßstab 1:10",
    fontsize=10, fontweight='bold', y=0.97, color='#1a1a2e'
)

gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3,
                       left=0.06, right=0.97, top=0.93, bottom=0.06)

# ── Hilfsfunktionen ──────────────────────────────────────────────────────────
def dim_h(ax, x1, x2, y, val, color=C_DIM, dy=0.15):
    ax.annotate('', xy=(x2*SC, (y-dy)*SC), xytext=(x1*SC, (y-dy)*SC),
                arrowprops=dict(arrowstyle='<->', color=color, lw=0.8))
    ax.text(((x1+x2)/2)*SC, (y-dy*2.2)*SC,
            f"{val:.0f}", ha='center', va='top', fontsize=6, color=color)

def dim_v(ax, x, y1, y2, val, color=C_DIM, dx=0.15):
    ax.annotate('', xy=((x+dx)*SC, y2*SC), xytext=((x+dx)*SC, y1*SC),
                arrowprops=dict(arrowstyle='<->', color=color, lw=0.8))
    ax.text((x+dx*2.5)*SC, ((y1+y2)/2)*SC,
            f"{val:.0f}", ha='left', va='center', fontsize=6, color=color,
            rotation=90)

def draw_window(ax, x, y, w, h, ft, is_door=False, show_glass=True):
    """Fenster/Tür als Rechteck mit Rahmen."""
    col = C_DOOR if is_door else C_WOOD
    # Außenrahmen
    ax.add_patch(mpatches.Rectangle((x*SC, y*SC), w*SC, h*SC,
                 linewidth=0.8, edgecolor=C_WOOD_D, facecolor=col, alpha=0.7))
    # Glas
    if show_glass and w > 2*ft and h > 2*ft:
        ax.add_patch(mpatches.Rectangle(
            ((x+ft)*SC, (y+ft)*SC), (w-2*ft)*SC, (h-2*ft)*SC,
            linewidth=0.5, edgecolor='#88aacc', facecolor=C_GLASS, alpha=0.6))

# ── 1. FRONTANSICHT ──────────────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_aspect('equal'); ax1.set_title("Frontansicht", fontsize=8, fontweight='bold')
ax1.set_facecolor(C_BG); ax1.axis('off')

# Kontur
ax1.add_patch(mpatches.Rectangle((0, 0), B*SC, H*SC,
              linewidth=1, edgecolor='#333', facecolor='none'))
# Schwelle
ax1.add_patch(mpatches.Rectangle((0, 0), B*SC, SILL_H*SC,
              facecolor=C_WOOD, alpha=0.5, linewidth=0))
# Obergurt
ax1.add_patch(mpatches.Rectangle((0, (H-TOP_H)*SC), B*SC, TOP_H*SC,
              facecolor=C_WOOD, alpha=0.5, linewidth=0))
# Eckpfosten
for px in [0, B-POST]:
    ax1.add_patch(mpatches.Rectangle((px*SC, 0), POST*SC, H*SC,
                  facecolor=C_WOOD_D, alpha=0.4, linewidth=0))
# Fenster
col_w = (B - 2*POST) / WIN_COLS_FRONT
row_h = WIN_ZONE_H / WIN_ROWS
door_col = WIN_COLS_FRONT // 2 if DOOR_FRONT else -1
for row in range(WIN_ROWS):
    for col in range(WIN_COLS_FRONT):
        is_d = DOOR_FRONT and row == 0 and col == door_col
        draw_window(ax1, POST + col*col_w, SILL_H + row*row_h,
                    col_w, row_h, POST, is_d)
# Bemaßung
dim_h(ax1, 0, B, H+OVER*0.3, B); dim_v(ax1, B, 0, H, H)
dim_v(ax1, B, 0, SILL_H, SILL_H)
ax1.set_xlim(-0.5, (B+OVER)*SC+1); ax1.set_ylim(-0.8, (H+OVER)*SC+1)

# ── 2. SEITENANSICHT (LINKS) ─────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_aspect('equal'); ax2.set_title("Seitenansicht links", fontsize=8, fontweight='bold')
ax2.set_facecolor(C_BG); ax2.axis('off')

ax2.add_patch(mpatches.Rectangle((0, 0), T*SC, H*SC,
              linewidth=1, edgecolor='#333', facecolor='none'))
ax2.add_patch(mpatches.Rectangle((0, 0), T*SC, SILL_H*SC,
              facecolor=C_WOOD, alpha=0.5, linewidth=0))
ax2.add_patch(mpatches.Rectangle((0, (H-TOP_H)*SC), T*SC, TOP_H*SC,
              facecolor=C_WOOD, alpha=0.5, linewidth=0))
for py in [0, T-POST]:
    ax2.add_patch(mpatches.Rectangle((py*SC, 0), POST*SC, H*SC,
                  facecolor=C_WOOD_D, alpha=0.4, linewidth=0))
s_col_w = (T - 2*POST) / WIN_COLS_LEFT
door_col_l = WIN_COLS_LEFT // 2 if DOOR_LEFT else -1
for row in range(WIN_ROWS):
    for col in range(WIN_COLS_LEFT):
        is_d = DOOR_LEFT and row == 0 and col == door_col_l
        draw_window(ax2, POST + col*s_col_w, SILL_H + row*row_h,
                    s_col_w, row_h, POST, is_d)
dim_h(ax2, 0, T, H+OVER*0.3, T)
ax2.set_xlim(-0.5, (T+OVER)*SC+1); ax2.set_ylim(-0.8, (H+OVER)*SC+1)

# ── 3. GRUNDRISS ─────────────────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_aspect('equal'); ax3.set_title("Grundriss (Schnitt Fensterzone)", fontsize=8, fontweight='bold')
ax3.set_facecolor(C_BG); ax3.axis('off')

# Außenmauern
for x, y, w, h in [(0,0,B,POST),(0,T-POST,B,POST),(0,0,POST,T),(B-POST,0,POST,T)]:
    ax3.add_patch(mpatches.Rectangle((x*SC, y*SC), w*SC, h*SC,
                  facecolor=C_WOOD, alpha=0.7, linewidth=0))
# Eckpfosten
for px, py in [(0,0),(B-POST,0),(0,T-POST),(B-POST,T-POST)]:
    ax3.add_patch(mpatches.Rectangle((px*SC, py*SC), POST*SC, POST*SC,
                  facecolor=C_WOOD_D, alpha=0.9, linewidth=0))
dim_h(ax3, 0, B, -OVER*0.4, B); dim_v(ax3, B, 0, T, T)
dim_h(ax3, POST, POST + col_w, -OVER*0.15, col_w)
ax3.set_xlim(-1, (B+OVER*0.5)*SC+1); ax3.set_ylim(-1, (T+OVER*0.5)*SC+1)

# ── 4. SCHNITT ECKE (Detail) ─────────────────────────────────────────────────
ax4 = fig.add_subplot(gs[1, 0])
ax4.set_aspect('equal'); ax4.set_title("Detail: Eckverbindung", fontsize=8, fontweight='bold')
ax4.set_facecolor(C_BG); ax4.axis('off')
# Eckpfosten
ax4.add_patch(mpatches.Rectangle((0,0), POST*SC*4, H*SC*0.3,
              facecolor=C_WOOD_D, alpha=0.8, edgecolor='#333', linewidth=0.5))
# Schwelle
ax4.add_patch(mpatches.Rectangle((POST*SC*4, 0), WIN_W*SC*0.8, SILL_H*SC*4,
              facecolor=C_WOOD, alpha=0.7, edgecolor='#333', linewidth=0.5))
# Fensterrahmen angedeutet
ax4.add_patch(mpatches.Rectangle((POST*SC*4, SILL_H*SC*4), POST*SC*4, WIN_H*SC*0.3,
              facecolor=C_WOOD, alpha=0.6, edgecolor='#333', linewidth=0.5))
ax4.text(0, H*SC*0.31, f"Eckpfosten\n{POST}×{POST} mm", fontsize=6, va='bottom')
ax4.text(POST*SC*4, H*SC*0.025, f"Schwelle {SILL_H} mm", fontsize=6, va='bottom')
ax4.set_xlim(-0.3, WIN_W*SC*0.85+1); ax4.set_ylim(-0.3, H*SC*0.32+0.5)

# ── 5. FENSTERDETAIL ─────────────────────────────────────────────────────────
ax5 = fig.add_subplot(gs[1, 1])
ax5.set_aspect('equal'); ax5.set_title(f"Fensterdetail  {WIN_W}×{WIN_H} mm", fontsize=8, fontweight='bold')
ax5.set_facecolor(C_BG); ax5.axis('off')
draw_window(ax5, 0, 0, WIN_W, WIN_H, POST, show_glass=True)
# Glasmark
ax5.text(WIN_W/2*SC, WIN_H/2*SC, "Glas", ha='center', va='center',
         fontsize=8, color='#336699', alpha=0.7)
dim_h(ax5, 0, WIN_W, -OVER*0.1, WIN_W)
dim_v(ax5, WIN_W, 0, WIN_H, WIN_H)
ax5.text(WIN_W/2*SC, -OVER*0.18*SC, f"Rahmen: {POST} mm Holz", ha='center',
         fontsize=6, color='#555')
ax5.set_xlim(-0.5, WIN_W*SC+1); ax5.set_ylim(-0.8, WIN_H*SC+0.5)

# ── 6. STÜCKLISTE KURZFORM ───────────────────────────────────────────────────
ax6 = fig.add_subplot(gs[1, 2])
ax6.axis('off'); ax6.set_title("Stückliste (Kurzform)", fontsize=8, fontweight='bold')
n_win_front = WIN_COLS_FRONT * WIN_ROWS
n_win_back  = WIN_COLS_BACK  * WIN_ROWS
n_win_left  = WIN_COLS_LEFT  * WIN_ROWS
n_win_right = WIN_COLS_RIGHT * WIN_ROWS
n_doors = sum([DOOR_FRONT, DOOR_BACK, DOOR_LEFT, DOOR_RIGHT])
n_windows = n_win_front + n_win_back + n_win_left + n_win_right - n_doors
rows_data = [
    ("Pos", "Bezeichnung", "Anzahl", "Maß"),
    ("01", "Fensterrahmen", str(n_windows), f"{WIN_W}×{WIN_H}"),
    ("02", "Balkontür", str(n_doors), f"{WIN_W}×{WIN_H*WIN_ROWS}"),
    ("03", "Eckpfosten", "4", f"100×100×{H}"),
    ("04", "Schwellbalken Front/Rück", "2", f"100×{B-2*POST}"),
    ("05", "Schwellbalken Seite", "2", f"100×{T-2*POST}"),
    ("06", "Obergurt Front/Rück", "2", f"100×{B-2*POST}"),
    ("07", "Obergurt Seite", "2", f"100×{T-2*POST}"),
    ("08", "Dachsparren", str(max(2,B//600)+2), f"~{T+2*OVER}"),
    ("09", "Winkelverbinder", "≥16", "90°, Stahl vzk."),
]
y0 = 0.97
for i, row in enumerate(rows_data):
    bg = '#e8f0f8' if i == 0 else ('#f4f8fc' if i % 2 == 0 else 'white')
    ax6.add_patch(mpatches.FancyBboxPatch((0, y0-0.07), 1, 0.065,
                  boxstyle="square,pad=0", facecolor=bg, transform=ax6.transAxes,
                  linewidth=0))
    fw = 'bold' if i == 0 else 'normal'
    for j, (txt, xp) in enumerate(zip(row, [0.02, 0.12, 0.72, 0.85])):
        ax6.text(xp, y0-0.035, txt, transform=ax6.transAxes, fontsize=6.5,
                 fontweight=fw, va='center')
    y0 -= 0.073

# ── Speichern ────────────────────────────────────────────────────────────────
out_pdf = os.path.join(_proj, "gewaechshaus_zeichnung.pdf")
out_png = os.path.join(_proj, "gewaechshaus_iso.png")
fig.savefig(out_pdf, dpi=150, bbox_inches='tight')
fig.savefig(out_png, dpi=120, bbox_inches='tight')
print(f"Zeichnung Typ 2 gespeichert: {out_pdf}")

# ── Stückliste als Text ───────────────────────────────────────────────────────
stueck_path = os.path.join(_proj, "gewaechshaus_stueckliste.txt")
with open(stueck_path, "w") as f:
    f.write(f"STÜCKLISTE – Fenstergewächshaus Typ 2\n")
    f.write(f"Gesamtmaße: {B} × {T} × {H} mm (B×T×H)\n")
    f.write(f"Fensterformat: {WIN_W} × {WIN_H} mm, {WIN_ROWS} Reihe(n)\n")
    f.write(f"Dachüberstand: {OVER} mm\n\n")
    for row in rows_data[1:]:
        f.write(f"  {row[0]:3s}  {row[1]:35s}  {row[2]:6s}  {row[3]}\n")
print(f"Stückliste: {stueck_path}")
