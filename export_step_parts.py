#!/usr/bin/env python3
"""
export_step_parts.py
====================
Exportiert jeden Bauteiltyp des Gewächshauses als einzelne STEP-Datei.
Ausführung:  FreeCADCmd export_step_parts.py
             oder:  /usr/lib64/FreeCAD/bin/FreeCADCmd export_step_parts.py

Bauteile mit Verbindungsgeometrie (GWH_01–05, GWH_14) werden mit
Boolean Cuts (Ausklinkungen / Zapfentaschen) exportiert.
Schrägteile (Dach-Seitenträger) werden als gerades Rechteckprofil
exportiert; der Schnittwinkel ist in der Index-Datei vermerkt.
Alle übrigen Bauteile werden als Rohgeometrie ohne Cuts exportiert.
"""

import sys, os, math

# ── FreeCAD-Pfad einhängen, falls nötig ──────────────────────────────────────
for candidate in [
    "/usr/lib64/FreeCAD/lib",
    "/usr/lib/freecad/lib",
    "/usr/lib/freecad-python3/lib",
    "/usr/local/lib/freecad/lib",
]:
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

import FreeCAD
from FreeCAD import Base
import Part


# ── Hilfsfunktion: Quader mit Boolean Cuts ───────────────────────────────────
def make_notched_box(lx, ly, lz, cuts):
    """
    Erstellt einen Quader (lx × ly × lz) mit Boolean Cuts.

    cuts: Liste von (cx, cy, cz, clx, cly, clz)
          cx/cy/cz  = Startpunkt des Cut-Quaders
          clx/cly/clz = Ausmaß des Cut-Quaders
    """
    shape = Part.makeBox(lx, ly, lz)
    for (cx, cy, cz, clx, cly, clz) in cuts:
        cut_box = Part.makeBox(clx, cly, clz, Base.Vector(cx, cy, cz))
        shape = shape.cut(cut_box)
    return shape

# ── Ausgabeverzeichnis ────────────────────────────────────────────────────────
OUT_DIR = "/home/herrvorragend/projekte/gewaechshaus/step_parts"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Abmessungsparameter (identisch zu freecad_model.py) ──────────────────────
_proj = "/home/herrvorragend/projekte/gewaechshaus"
try:
    import sys as _sys; _sys.path.insert(0, _proj)
    from params import B, T, H, OVER, P
    del _sys
except ImportError:
    B = 1200; T = 1200; H = 2200; OVER = 300; P = 50
del _proj
DT_P     = 30     # Türflügel-Profil [mm]
CW, CH   = 25, 10 # Klemmschiene B×H [mm]
QT_H = QT_B = 60  # KVH-Querträger [mm]
PLANK_W  = 116    # Dielenbreite [mm]
PLANK_T  = 22     # Dielendicke [mm]
TH_D, TH_H = 80, 40  # Trittholm [mm]

# Dachüberstand – aus params.py
RISE_ORIG  = 200   # Ursprüngliche Höhendiff über 1200 mm Tiefe
SLOPE = RISE_ORIG / 1200
RISE  = int((T + 2*OVER) * SLOPE)
DEPTH = T + 2*OVER
RAFTER_L = int(math.ceil(math.sqrt(DEPTH**2 + RISE**2)))
RAFTER_ANGLE_DEG = round(math.degrees(math.atan2(RISE, DEPTH)), 1)

# ── Bauteil-Definitionen ──────────────────────────────────────────────────────
#  Jeder Eintrag:
#  (nr, name, bezeichnung, shape_type, dims, material, anzahl, hinweis)
#
#  shape_type  "box"      → Part.makeBox(lx, ly, lz)
#              "cylinder" → Part.makeCylinder(r, h)

PARTS = [
    # Nr  Dateiname-Schlüssel          Bezeichnung                         Typ              Dims (mm) + Cuts                                                                        Material               Anz   Hinweis
    # ── Stahlrahmen mit Ausklinkungen ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    ( 1, "eckstiel",                  "Eckstiel",
         "notched_box",
         # Grundkörper 50×50×2175; Typ-4-Zapfen am Kopf: hintere Hälfte (y=25..50) der oberen 25 mm abfräsen
         (P, P, 2175, [
             (0, 25, 2150, P, 25, 25),          # Kopfzapfen: y-hintere Hälfte, oberste 25 mm
         ]),
         "Stahl S235, 50×50 RHS", 4,
         "inkl. Ausklinkungen – Typ-4-Zapfen Kopfende (für Obergurt-Längsriegel)"),

    ( 2, "bodenrahmen_laengs",        "Bodenrahmen Längsriegel",
         "notched_box",
         # Grundkörper 1100×50×50; Typ-3-Zapfentaschen für 2 Eckstiele (je 50×50, 25 mm von oben)
         (1100, P, P, [
             ( 25, 0, 25, P, P, 25),            # linke  Stiel-Tasche (x=25..75)
             (1025, 0, 25, P, P, 25),            # rechte Stiel-Tasche (x=1025..1075)
         ]),
         "Stahl S235, 50×50 RHS", 2,
         "inkl. Ausklinkungen – Typ-3-Zapfentaschen für Eckstiele (2×)"),

    ( 3, "bodenrahmen_quer",          "Bodenrahmen Querriegel",
         "notched_box",
         # Grundkörper 50×1100×50; Typ-1-Vollausklinkung an beiden Enden (obere 25 mm = Einlegerbereich)
         (P, 1100, P, [
             (0,    0, 25, P, P, 25),            # linkes  Ende: vordere Seite auflagern
             (0, 1050, 25, P, P, 25),            # rechtes Ende: hintere Seite auflagern
         ]),
         "Stahl S235, 50×50 RHS", 2,
         "inkl. Ausklinkungen – Typ-1-Vollausklinkung Enden (liegt in Bodenrahmen-Längsriegel)"),

    ( 4, "obergurt_laengs",           "Obergurt Längsriegel",
         "notched_box",
         # Grundkörper 1100×50×50; Typ-4-Zapfentaschen (von unten, y-hintere Hälfte, 25 mm tief)
         (1100, P, P, [
             ( 25, 25, 0, P, 25, 25),            # linker  Stielkopf-Sitz (x=25..75)
             (1025, 25, 0, P, 25, 25),            # rechter Stielkopf-Sitz (x=1025..1075)
         ]),
         "Stahl S235, 50×50 RHS", 2,
         "inkl. Ausklinkungen – Typ-4-Zapfentaschen für Stielköpfe (2×)"),

    ( 5, "obergurt_quer",             "Obergurt Querriegel",
         "notched_box",
         # Grundkörper 50×1100×50; Typ-1-Vollausklinkung an beiden Enden (untere 25 mm = Einlegerbereich)
         (P, 1100, P, [
             (0,    0, 0, P, P, 25),             # vorderes Ende
             (0, 1050, 0, P, P, 25),             # hinteres Ende
         ]),
         "Stahl S235, 50×50 RHS", 2,
         "inkl. Ausklinkungen – Typ-1-Vollausklinkung Enden (liegt in Obergurt-Längsriegel)"),
    # ── Dachrahmen, Scharniere, Gasdruckfeder – keine Ausklinkungen ─────────────
    ( 6, "dach_vorderriegel",         "Dachrahmen Vorderriegel",         "box",      (1800, P, P),             "Stahl S235, 50×50 RHS", 1,   "Überstand 300 mm je Seite; z=2150 mm (Traufe)"),
    ( 7, "dach_hinterriegel",         "Dachrahmen Hinterriegel",         "box",      (1800, P, P),             "Stahl S235, 50×50 RHS", 1,   "Überstand 300 mm je Seite; z=2450 mm (First/Scharnier)"),
    ( 8, "dach_seitentraeger",        "Dachrahmen Seitenträger",         "box",      (P, RAFTER_L, P),         "Stahl S235, 50×50 RHS", 2,   f"Schrägmaß {RAFTER_L} mm; beidseitig auf {RAFTER_ANGLE_DEG}° ablängen (Pultdachneigung)"),
    ( 9, "dach_mittelpfette",         "Dachrahmen Mittelpfette",         "box",      (1800, P, P),             "Stahl S235, 50×50 RHS", 1,   "Überstand 300 mm je Seite; z=2300 mm (Mitte)"),
    (10, "scharnier_dach",            "Schwerlast-Scharnier Dach",       "box",      (100, 20, 260),           "Stahl verzinkt",        2,   "Scharniergröße 100×100×10 mm; Gesamthöhe montiert ~260 mm"),
    (11, "gasdruckfeder",             "Gasdruckfeder",                   "cylinder", (14, 350),                "Stahl, Gasdruckfeder",  1,   "Ø28 mm, Hub ~175 mm; hier als Vollzylinder Ø28×350 dargestellt"),
    # ── Türflügel ────────────────────────────────────────────────────────────────
    (12, "tuerfluegel_horizontal",    "Türflügel Horizontalriegel",      "box",      (575, DT_P, DT_P),        "Stahl S235, 30×30 RHS", 6,   "3 Stück je Flügel (oben / mitte / unten)"),
    (13, "tuerfluegel_vertikal",      "Türflügel Vertikalriegel",        "box",      (DT_P, DT_P, 1900),       "Stahl S235, 30×30 RHS", 4,   "2 Stück je Flügel (links / rechts)"),
    # ── Türmittelstiel mit Ausklinkung ───────────────────────────────────────────
    (14, "mittelstiel",               "Türmittelstiel",
         "notched_box",
         # Grundkörper 50×50×1900; Typ-4-ähnlich: Zapfen oben für Türsturz-Tasche (y-hintere Hälfte, oberste 25 mm)
         (P, P, 1900, [
             (0, 25, 1875, P, 25, 25),          # Kopfzapfen: y-hintere Hälfte, oberste 25 mm
         ]),
         "Stahl S235, 50×50 RHS", 1,
         "inkl. Ausklinkungen – Typ-4-Zapfen Kopfende (für Türsturz)"),
    # ── Übrige Türteile, Holz, Befestiger – keine Ausklinkungen ─────────────────
    (15, "tursturz",                  "Türsturz",                        "box",      (1100, P, P),             "Stahl S235, 50×50 RHS", 1,   ""),
    (16, "scharnier_tuer",            "Türscharnier",                    "box",      (100, 8, 80),             "Stahl verzinkt",        4,   "Maß 100×80×8 mm"),
    (17, "tuerriegel",                "Türverschlussriegel",             "box",      (50, 30, 150),            "Stahl S235",            2,   "Symbolisch; 1 je Flügel"),
    (18, "trittholm",                 "Trittholm",                       "box",      (1200, TH_D, TH_H),       "Holz Lärche C24",       1,   "80×40×1200 mm"),
    (19, "quertraeger",               "KVH-Querträger",                  "box",      (QT_B, 1100, QT_H),       "KVH Si NSi 60×60",      4,   ""),
    (20, "diele",                     "Lärchendiele",                    "box",      (PLANK_W, 1100, PLANK_T), "Lärche C24 gehobelt",   9,   "Nutzbreite ~116 mm; inkl. 4 mm Fuge"),
    (21, "klemmschiene",              "Klemmschiene",                    "box",      (CW, 1100, CH),           "Stahl verzinkt",        12,  "Repräsentativlänge 1100 mm; verschiedene Längen möglich"),
    (22, "schraube_m10",              "Schraube M10×80",                 "cylinder", (5, 80),                  "Stahl 8.8 verzinkt",    8,   "Ø10 mm; als Vollzylinder dargestellt"),
    (23, "schraube_m8",               "Schraube M8×60",                  "cylinder", (4, 60),                  "Stahl 8.8 verzinkt",    24,  "Ø8 mm; als Vollzylinder dargestellt"),
    (24, "schraube_m6",               "Schraube M6×30",                  "cylinder", (3, 30),                  "Stahl 8.8 verzinkt",    32,  "Ø6 mm; als Vollzylinder dargestellt"),
]

# ── Export ────────────────────────────────────────────────────────────────────
results = []   # (nr, filename, bezeichnung, dims_str, material, anzahl, hinweis, ok)

print("=" * 60)
print("GWH STEP-Export – Einzelbauteile (inkl. Ausklinkungen)")
print("=" * 60)

for entry in PARTS:
    nr, key, bezeichnung, shape_type, dims, material, anzahl, hinweis = entry

    filename = f"GWH_{nr:02d}_{key}.step"
    filepath = os.path.join(OUT_DIR, filename)

    # Geometrie erstellen
    try:
        if shape_type == "box":
            lx, ly, lz = dims
            shape = Part.makeBox(lx, ly, lz)
            dims_str = f"{lx}×{ly}×{lz} mm (L×B×H)"

        elif shape_type == "notched_box":
            lx, ly, lz, cuts = dims
            shape = make_notched_box(lx, ly, lz, cuts)
            dims_str = f"{lx}×{ly}×{lz} mm (L×B×H), {len(cuts)} Cut(s)"

        elif shape_type == "cylinder":
            r, h = dims
            shape = Part.makeCylinder(r, h)
            dims_str = f"Ø{r*2}×{h} mm"
        else:
            raise ValueError(f"Unbekannter shape_type: {shape_type}")

        # STEP-Export (exportStep direkt auf dem Shape-Objekt)
        shape.exportStep(filepath)

        ok = os.path.isfile(filepath) and os.path.getsize(filepath) > 0
        status = "OK  " if ok else "FAIL"
        size_kb = os.path.getsize(filepath) / 1024 if ok else 0
        notch_flag = " [Ausklinkungen]" if shape_type == "notched_box" else ""

        print(f"  [{status}] {filename:40s}  {size_kb:6.1f} kB   {dims_str}{notch_flag}")
    except Exception as exc:
        ok = False
        dims_str = str(dims)
        print(f"  [ERR ] {filename:40s}  FEHLER: {exc}")

    results.append((nr, filename, bezeichnung, dims_str, material, anzahl, hinweis, ok))

# ── Index-Datei ───────────────────────────────────────────────────────────────
index_path = os.path.join(OUT_DIR, "GWH_parts_index.txt")
ok_count   = sum(1 for r in results if r[7])

with open(index_path, "w", encoding="utf-8") as f:
    f.write("=" * 100 + "\n")
    f.write("GEWÄCHSHAUS – STEP-Einzelbauteile  │  Teileliste / Parts Index\n")
    f.write("=" * 100 + "\n")
    f.write(f"Erstellt mit: export_step_parts.py\n")
    f.write(f"Ausgabepfad:  {OUT_DIR}\n")
    f.write(f"Bauteile:     {ok_count}/{len(PARTS)} erfolgreich exportiert\n")
    f.write("\n")
    f.write(f"{'Nr':>3}  {'Dateiname':<42} {'Bezeichnung':<30} {'Abmessungen':<25} {'Material':<28} {'Anz':>4}  Hinweis\n")
    f.write("-" * 160 + "\n")

    for nr, filename, bezeichnung, dims_str, material, anzahl, hinweis, ok in results:
        flag = "✓" if ok else "✗"
        f.write(
            f"{nr:>3}  {flag} {filename:<40} {bezeichnung:<30} {dims_str:<25} {material:<28} {anzahl:>4}  {hinweis}\n"
        )

    f.write("\n" + "=" * 100 + "\n")
    f.write("HINWEISE ZUR VERWENDUNG\n")
    f.write("-" * 100 + "\n")
    f.write("• Alle STEP-Dateien im AP214-Format (ISO 10303-21)\n")
    f.write("• Schrägbauteile (Nr. 08 Dach-Seitenträger) als gerades Rohmaß exportiert;\n")
    f.write(f"  Ablängwinkel: {RAFTER_ANGLE_DEG}° (Pultdachneigung, Höhenunterschied {RISE} mm auf {DEPTH} mm Tiefe)\n")
    f.write("• Schrauben/Scharnier als Vollzylinder/-quader – keine Gewindegeometrie\n")
    f.write("• Ausklinkungen und Zapfenverbindungen sind für GWH_01–05 und GWH_14 modelliert (Boolean Cuts):\n")
    f.write("    GWH_01 Eckstiel:              Typ-4-Kopfzapfen (25 mm, y-hintere Hälfte)\n")
    f.write("    GWH_02 Bodenrahmen Längs:     2× Typ-3-Zapfentaschen für Eckstiele (50×50×25 mm von oben)\n")
    f.write("    GWH_03 Bodenrahmen Quer:      2× Typ-1-Vollausklinkung Enden (50×50×25 mm, liegt in Längsriegel)\n")
    f.write("    GWH_04 Obergurt Längs:        2× Typ-4-Zapfentaschen für Stielköpfe (50×25×25 mm von unten)\n")
    f.write("    GWH_05 Obergurt Quer:         2× Typ-1-Vollausklinkung Enden (50×50×25 mm, liegt in Obergurt-Längs)\n")
    f.write("    GWH_14 Türmittelstiel:        Typ-4-Kopfzapfen (25 mm, y-hintere Hälfte) für Türsturz\n")
    f.write("• Alle übrigen Bauteile (Nr. 06–13, 15–24): Rohmaße ohne Ausklinkungen\n")
    f.write("• Klemmschienen (Nr. 21): Repräsentativlänge 1100 mm; bei Bedarf kürzen\n")
    f.write("• Gasdruckfeder (Nr. 11): Einbaulänge 350 mm, Einbauposition seitlich am Dachrahmen\n")

print()
print(f"Index-Datei:  {index_path}")
print(f"Ergebnis:     {ok_count}/{len(PARTS)} Bauteile erfolgreich exportiert")
print("=" * 60)
