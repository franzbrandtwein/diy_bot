#!/usr/bin/env python3
"""
Gewächshaus Web-Konfigurator – Flask Backend
Startet mit: python3 app.py
Läuft auf:   http://0.0.0.0:5000
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

from flask import (Flask, Response, jsonify, render_template, request,
                   send_file, send_from_directory)

# ── Pfade ──────────────────────────────────────────────────────────────────
BASE_DIR    = pathlib.Path(os.environ.get("GWH_PROJECT_DIR",
              "/home/herrvorragend/projekte/gewaechshaus"))
CONFIG_FILE = BASE_DIR / "config.json"
PARAMS_FILE = BASE_DIR / "params.py"
GLB_FILE    = BASE_DIR / "gewaechshaus.glb"
STL_DIR     = pathlib.Path("/tmp/gwh_meshes")
PDF_DRAWING = BASE_DIR / "gewaechshaus_zeichnung.pdf"
PDF_STUECK  = BASE_DIR / "gewaechshaus_stueckliste_3d.pdf"
STEP_DIR    = BASE_DIR / "step_parts"

# ── Defaults ───────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "B": 1200, "T": 1200, "H": 2200, "OVER": 300, "P": 50,
    "GH_TYPE": 1,
    # Typ-2-Defaults
    "WIN_W": 800, "WIN_H": 1200, "WIN_ROWS": 1,
    "WIN_COLS_FRONT": 2, "WIN_COLS_BACK": 2,
    "WIN_COLS_LEFT": 2,  "WIN_COLS_RIGHT": 2,
    "FRAME_T": 60, "SILL_H": 100,
}

# ── Build-Status (globaler State) ──────────────────────────────────────────
build_status = {
    "building":  False,
    "progress":  0,
    "message":   "Bereit.",
    "error":     "",
    "log":       [],
}
_status_lock = threading.Lock()

# ── Bauteile-Metadaten ─────────────────────────────────────────────────────
PARTS_META = [
    {
        "nr": "01", "id": "steel_frame", "stl": "steel_frame",
        "name": "Eckstiel",
        "positions": "GWH_01",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 4,
        "group": "Hauptstruktur",
        "color": "#7a8a9a",
        "abmessungen": "50×50×2175 mm",
        "hinweis": "Typ-4-Zapfen am Kopf, Ausklinkungen",
    },
    {
        "nr": "02", "id": "bodenrahmen_laengs", "stl": "steel_frame",
        "name": "Bodenrahmen Längsriegel",
        "positions": "GWH_02",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 2,
        "group": "Hauptstruktur",
        "color": "#7a8a9a",
        "abmessungen": "1100×50×50 mm",
        "hinweis": "Typ-3-Zapfentaschen für Eckstiele",
    },
    {
        "nr": "03", "id": "bodenrahmen_quer", "stl": "steel_frame",
        "name": "Bodenrahmen Querriegel",
        "positions": "GWH_03",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 2,
        "group": "Hauptstruktur",
        "color": "#7a8a9a",
        "abmessungen": "50×1100×50 mm",
        "hinweis": "Typ-1-Vollausklinkung an den Enden",
    },
    {
        "nr": "04", "id": "obergurt_laengs", "stl": "steel_frame",
        "name": "Obergurt Längsriegel",
        "positions": "GWH_04",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 2,
        "group": "Hauptstruktur",
        "color": "#7a8a9a",
        "abmessungen": "1100×50×50 mm",
        "hinweis": "Typ-4-Zapfentaschen für Stielköpfe",
    },
    {
        "nr": "05", "id": "obergurt_quer", "stl": "steel_frame",
        "name": "Obergurt Querriegel",
        "positions": "GWH_05",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 2,
        "group": "Hauptstruktur",
        "color": "#7a8a9a",
        "abmessungen": "50×1100×50 mm",
        "hinweis": "Typ-1-Vollausklinkung an den Enden",
    },
    {
        "nr": "06-09", "id": "roof_frame", "stl": "roof_frame",
        "name": "Dachrahmen",
        "positions": "GWH_06–09",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 5,
        "group": "Dachrahmen",
        "color": "#5a7a9a",
        "abmessungen": "1800×1800 mm (inkl. Überstand)",
        "hinweis": "Vorderriegel, Hinterriegel, 2×Seitenträger, Mittelpfette",
    },
    {
        "nr": "10", "id": "scharnier_dach", "stl": "hardware",
        "name": "Schwerlast-Scharnier Dach",
        "positions": "GWH_10",
        "material": "Stahl verzinkt",
        "anzahl": 2,
        "group": "Beschläge",
        "color": "#555566",
        "abmessungen": "100×20×260 mm",
        "hinweis": "Verbindet Obergurt hinten mit Dachrahmen",
    },
    {
        "nr": "11", "id": "gasdruckfeder", "stl": "hardware",
        "name": "Gasdruckfeder",
        "positions": "GWH_11",
        "material": "Stahl, Gasdruckfeder",
        "anzahl": 1,
        "group": "Beschläge",
        "color": "#555566",
        "abmessungen": "Ø28×350 mm, Hub ~175 mm",
        "hinweis": "F ca. 300–400 N",
    },
    {
        "nr": "12", "id": "tuerfluegel_h", "stl": "door_frame",
        "name": "Türflügel Horizontalriegel",
        "positions": "GWH_12",
        "material": "Stahl S235, 30×30 RHS",
        "anzahl": 6,
        "group": "Türrahmen",
        "color": "#888899",
        "abmessungen": "575×30×30 mm",
        "hinweis": "3 Stk je Flügel (oben/mitte/unten)",
    },
    {
        "nr": "13", "id": "tuerfluegel_v", "stl": "door_frame",
        "name": "Türflügel Vertikalriegel",
        "positions": "GWH_13",
        "material": "Stahl S235, 30×30 RHS",
        "anzahl": 4,
        "group": "Türrahmen",
        "color": "#888899",
        "abmessungen": "30×30×1900 mm",
        "hinweis": "2 Stk je Flügel (links/rechts)",
    },
    {
        "nr": "14", "id": "mittelstiel", "stl": "steel_frame",
        "name": "Türmittelstiel",
        "positions": "GWH_14",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 1,
        "group": "Türrahmen",
        "color": "#7a8a9a",
        "abmessungen": "50×50×1900 mm",
        "hinweis": "Typ-4-Zapfen am Kopf",
    },
    {
        "nr": "15", "id": "tursturz", "stl": "steel_frame",
        "name": "Türsturz",
        "positions": "GWH_15",
        "material": "Stahl S235, 50×50 RHS",
        "anzahl": 1,
        "group": "Türrahmen",
        "color": "#7a8a9a",
        "abmessungen": "1100×50×50 mm",
        "hinweis": "",
    },
    {
        "nr": "16", "id": "scharnier_tuer", "stl": "hardware",
        "name": "Türscharnier",
        "positions": "GWH_16",
        "material": "Stahl verzinkt",
        "anzahl": 4,
        "group": "Beschläge",
        "color": "#555566",
        "abmessungen": "100×8×80 mm",
        "hinweis": "2 Stk je Flügel",
    },
    {
        "nr": "17", "id": "tuerriegel", "stl": "hardware",
        "name": "Türverschlussriegel",
        "positions": "GWH_17",
        "material": "Stahl S235",
        "anzahl": 2,
        "group": "Beschläge",
        "color": "#555566",
        "abmessungen": "50×30×150 mm",
        "hinweis": "1 Stk je Flügel",
    },
    {
        "nr": "18", "id": "trittholm", "stl": "wood",
        "name": "Trittholm",
        "positions": "GWH_18",
        "material": "KVH/Nadelholz",
        "anzahl": 1,
        "group": "Holzboden",
        "color": "#c8a060",
        "abmessungen": "1200×80×40 mm",
        "hinweis": "Türschwelle, volle Außenbreite",
    },
    {
        "nr": "19", "id": "quertraeger", "stl": "wood",
        "name": "KVH-Querträger",
        "positions": "GWH_19",
        "material": "KVH Si NSi 60×60",
        "anzahl": 4,
        "group": "Holzboden",
        "color": "#c8a060",
        "abmessungen": "60×1100×60 mm",
        "hinweis": "Achsabstand ~286 mm",
    },
    {
        "nr": "20", "id": "diele", "stl": "wood",
        "name": "Lärchendiele",
        "positions": "GWH_20",
        "material": "Lärche C24 gehobelt",
        "anzahl": 9,
        "group": "Holzboden",
        "color": "#c8a060",
        "abmessungen": "116×1100×22 mm",
        "hinweis": "4 mm Fuge; OK Boden z=132 mm",
    },
    {
        "nr": "21", "id": "klemmschiene", "stl": "clamping",
        "name": "Klemmschiene",
        "positions": "GWH_21",
        "material": "Stahl verzinkt 25×10",
        "anzahl": 12,
        "group": "Klemmschienen",
        "color": "#aab0b8",
        "abmessungen": "25×1100×10 mm (Repräsentativlänge)",
        "hinweis": "Verschiedene Längen; Folienbefestigung",
    },
    {
        "nr": "22", "id": "schraube_m10", "stl": "screws",
        "name": "Schraube M10×80",
        "positions": "GWH_22",
        "material": "Stahl 8.8 verzinkt",
        "anzahl": 8,
        "group": "Verbindungsmittel",
        "color": "#aaaaaa",
        "abmessungen": "Ø10×80 mm",
        "hinweis": "Obergurt-Stiel Typ-4-Verbindung",
    },
    {
        "nr": "23", "id": "schraube_m8", "stl": "screws",
        "name": "Schraube M8×60",
        "positions": "GWH_23",
        "material": "Stahl 8.8 verzinkt",
        "anzahl": 24,
        "group": "Verbindungsmittel",
        "color": "#aaaaaa",
        "abmessungen": "Ø8×60 mm",
        "hinweis": "Bodenknoten Typ-3, Querriegel-Sicherung",
    },
    {
        "nr": "24", "id": "schraube_m6", "stl": "screws",
        "name": "Schraube M6×30",
        "positions": "GWH_24",
        "material": "Stahl 8.8 verzinkt",
        "anzahl": 32,
        "group": "Verbindungsmittel",
        "color": "#aaaaaa",
        "abmessungen": "Ø6×30 mm",
        "hinweis": "Klemmschienen Folienbefestigung",
    },
]

# ── Bauteile-Metadaten Typ 2 (Fenstergewächshaus) ─────────────────────────
PARTS_META_T2 = [
    {
        "nr": "01", "id": "window_frame", "stl": "window_frame",
        "name": "Fensterrahmen",
        "positions": "FGH_01",
        "material": "Holz (Altfenster), Rahmen ca. 60×60 mm",
        "anzahl": 0,  # dynamisch
        "group": "Fenster & Türen",
        "color": "#c8a060",
        "abmessungen": "variabel",
        "hinweis": "Maße aus Konfiguration",
    },
    {
        "nr": "02", "id": "door_frame", "stl": "door_frame",
        "name": "Balkontür-Rahmen",
        "positions": "FGH_02",
        "material": "Holz (Altbalkon­tür), Rahmen ca. 60×60 mm",
        "anzahl": 0,
        "group": "Fenster & Türen",
        "color": "#a07840",
        "abmessungen": "variabel",
        "hinweis": "Ersetzt Fenster an konfigurierten Seiten",
    },
    {
        "nr": "03", "id": "sill_beam", "stl": "sill_beam",
        "name": "Schwellbalken",
        "positions": "FGH_03",
        "material": "KVH Fichte, druckimprägniert",
        "anzahl": 4,
        "group": "Holzrahmen",
        "color": "#8b6020",
        "abmessungen": "100×100 mm",
        "hinweis": "Unterer Abschluss, Feuchtigkeitsschutz",
    },
    {
        "nr": "04", "id": "top_rail", "stl": "top_rail",
        "name": "Obergurt-Balken",
        "positions": "FGH_04",
        "material": "KVH Fichte",
        "anzahl": 4,
        "group": "Holzrahmen",
        "color": "#a07840",
        "abmessungen": "100×100 mm",
        "hinweis": "Oberer Abschluss, Dachanschluss",
    },
    {
        "nr": "05", "id": "corner_post", "stl": "corner_post",
        "name": "Eckpfosten",
        "positions": "FGH_05",
        "material": "KVH Fichte",
        "anzahl": 4,
        "group": "Holzrahmen",
        "color": "#906030",
        "abmessungen": "100×100 mm",
        "hinweis": "Verbindet Schwelle, Obergurt und Eckfenster",
    },
    {
        "nr": "06", "id": "roof_frame", "stl": "roof_frame",
        "name": "Dachrahmen",
        "positions": "FGH_06",
        "material": "KVH Fichte oder Stahl",
        "anzahl": 3,
        "group": "Dach",
        "color": "#6a9a6a",
        "abmessungen": "50×100 mm",
        "hinweis": "Pultdach, aufklappbar (Scharniere)",
    },
    {
        "nr": "07", "id": "hardware", "stl": "hardware",
        "name": "Verbindungsmittel & Beschläge",
        "positions": "FGH_07",
        "material": "Stahl verzinkt",
        "anzahl": 0,
        "group": "Beschläge",
        "color": "#888888",
        "abmessungen": "diverse",
        "hinweis": "Winkelverbinder, Schrauben, Scharniere",
    },
]


app = Flask(__name__, template_folder="templates", static_folder="static")


# ── Hilfsfunktionen ────────────────────────────────────────────────────────

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    cfg["last_updated"] = datetime.now().isoformat(timespec="seconds")
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def write_params(cfg):
    """params.py neu schreiben – wird vor jeder Regenerierung aufgerufen."""
    gh_type = int(cfg.get("GH_TYPE", 1))
    lines = [
        "# params.py – automatisch generiert vom Web-Konfigurator\n",
        "# Wird bei jedem Build überschrieben.\n\n",
        f"GH_TYPE = {gh_type}   # 1 = Balken/Stahl, 2 = Fenstergewächshaus\n\n",
    ]
    if gh_type == 1:
        lines += [
            f"B    = {int(cfg['B'])}   # Breite   mm\n",
            f"T    = {int(cfg['T'])}   # Tiefe    mm\n",
            f"H    = {int(cfg['H'])}   # Wandhöhe mm\n",
            f"OVER = {int(cfg['OVER'])}  # Dachüberstand mm\n",
            f"P    = {int(cfg.get('P', 50))}   # Profilquerschnitt mm\n",
            "# Türpositionen: True = Tür vorhanden\n",
            f"DOOR_FRONT = {bool(cfg.get('DOOR_FRONT', True))}\n",
            f"DOOR_BACK  = {bool(cfg.get('DOOR_BACK',  False))}\n",
            f"DOOR_LEFT  = {bool(cfg.get('DOOR_LEFT',  False))}\n",
            f"DOOR_RIGHT = {bool(cfg.get('DOOR_RIGHT', False))}\n",
        ]
    else:
        # Typ 2: Abmessungen aus Fensterformat berechnen
        win_w = int(cfg.get("WIN_W", 800))
        win_h = int(cfg.get("WIN_H", 1200))
        win_rows = int(cfg.get("WIN_ROWS", 1))
        cols_f = int(cfg.get("WIN_COLS_FRONT", 2))
        cols_b = int(cfg.get("WIN_COLS_BACK",  2))
        cols_l = int(cfg.get("WIN_COLS_LEFT",  2))
        cols_r = int(cfg.get("WIN_COLS_RIGHT", 2))
        frame_t = int(cfg.get("FRAME_T", 60))
        sill_h  = int(cfg.get("SILL_H",  100))
        post    = frame_t  # Eckpfosten gleich Rahmendicke
        # Gesamtabmessungen: aus Front- und Seitenfenstern
        B_calc = cols_f * win_w + 2 * post
        T_calc = cols_l * win_w + 2 * post
        H_calc = win_rows * win_h + sill_h + post  # Sill + Fenster + Obergurt
        over   = int(cfg.get("OVER", 300))
        lines += [
            f"# Typ-2: Fenstergewächshaus\n",
            f"WIN_W  = {win_w}   # Fensterbreite mm\n",
            f"WIN_H  = {win_h}   # Fensterhöhe mm\n",
            f"WIN_ROWS = {win_rows}   # Fensterreihen\n",
            f"WIN_COLS_FRONT = {cols_f}\n",
            f"WIN_COLS_BACK  = {cols_b}\n",
            f"WIN_COLS_LEFT  = {cols_l}\n",
            f"WIN_COLS_RIGHT = {cols_r}\n",
            f"FRAME_T = {frame_t}   # Rahmendicke mm\n",
            f"SILL_H  = {sill_h}   # Schwellenhöhe mm\n",
            f"# Abgeleitete Gesamtmaße\n",
            f"B    = {B_calc}   # Gesamtbreite mm\n",
            f"T    = {T_calc}   # Gesamttiefe mm\n",
            f"H    = {H_calc}   # Wandhöhe mm\n",
            f"OVER = {over}     # Dachüberstand mm\n",
            f"P    = {frame_t}  # Profilquerschnitt (= Rahmendicke) mm\n",
            "# Türpositionen (Balkontür)\n",
            f"DOOR_FRONT = {bool(cfg.get('DOOR_FRONT', True))}\n",
            f"DOOR_BACK  = {bool(cfg.get('DOOR_BACK',  False))}\n",
            f"DOOR_LEFT  = {bool(cfg.get('DOOR_LEFT',  False))}\n",
            f"DOOR_RIGHT = {bool(cfg.get('DOOR_RIGHT', False))}\n",
        ]
    PARAMS_FILE.write_text("".join(lines))


def set_status(progress, message, error=""):
    with _status_lock:
        build_status["progress"] = progress
        build_status["message"] = message
        build_status["error"] = error
        if message:
            ts = datetime.now().strftime("%H:%M:%S")
            build_status["log"].append(f"[{ts}] {message}")
            # Nur letzten 50 Einträge behalten
            build_status["log"] = build_status["log"][-50:]


def run_step(cmd, cwd=None, timeout=300):
    """Führt ein Kommando aus und wirft bei Fehler eine Exception."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd or BASE_DIR),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "")[:800]
        raise RuntimeError(err)
    return result


def regenerate(params):
    """Regeneriert alle Ausgabedateien mit neuen Parametern. Läuft in Thread."""
    with _status_lock:
        build_status["building"] = True
        build_status["log"] = []

    gh_type = int(params.get("GH_TYPE", 1))

    try:
        set_status(2, "💾 Parameter speichern…")
        save_config(params)
        write_params(params)

        if gh_type == 2:
            set_status(8, "🏗️  Fenstergewächshaus-Modell erstellen…")
            run_step(["python3", str(BASE_DIR / "window_gh_model.py")], timeout=300)

            set_status(35, "📐 STL-Meshes exportieren…")
            run_step(["python3", str(BASE_DIR / "window_gh_meshes.py")], timeout=300)

            set_status(62, "🔮 GLB assemblieren…")
            run_step(["python3", str(BASE_DIR / "assemble_glb.py")])

            set_status(75, "📄 Technische Zeichnung…")
            run_step(["python3", str(BASE_DIR / "matplotlib_drawing_t2.py")])

            set_status(85, "📋 Stückliste PDF…")
            run_step(["python3", str(BASE_DIR / "stueckliste_pdf_t2.py")])

            set_status(93, "📦 STEP exportieren…")
            run_step(["python3", str(BASE_DIR / "export_step_parts.py")], timeout=300)
        else:
            set_status(8, "🏗️  FreeCAD-Modell erstellen (kann 1–3 min dauern)…")
            run_step(["python3", str(BASE_DIR / "freecad_model.py")], timeout=300)

            set_status(35, "📐 STL-Meshes exportieren…")
            run_step(["python3", str(BASE_DIR / "freecad_to_meshes.py")], timeout=300)

            set_status(62, "🔮 GLB assemblieren…")
            run_step(["python3", str(BASE_DIR / "assemble_glb.py")])

            set_status(75, "📄 Technische Zeichnung…")
            run_step(["python3", str(BASE_DIR / "matplotlib_drawing.py")])

            set_status(85, "📋 Stückliste PDF…")
            run_step(["python3", str(BASE_DIR / "stueckliste_pdf.py")])

            set_status(93, "📦 STEP-Einzelbauteile exportieren…")
            run_step(["python3", str(BASE_DIR / "export_step_parts.py")], timeout=300)

        set_status(100, "✅ Fertig! Modell wurde erfolgreich regeneriert.")

    except subprocess.TimeoutExpired as e:
        set_status(build_status["progress"], "⏱️ Timeout!", error=str(e))
    except RuntimeError as e:
        set_status(build_status["progress"], f"❌ Fehler aufgetreten", error=str(e)[:600])
    except Exception as e:
        set_status(build_status["progress"], f"❌ Unbekannter Fehler", error=str(e)[:600])
    finally:
        with _status_lock:
            build_status["building"] = False


# ── Routen ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sw.js")
def service_worker():
    """Service Worker im Root-Scope ausliefern (Pflicht für volle PWA-Abdeckung)."""
    resp = send_from_directory(os.path.join(app.static_folder), "sw.js",
                               mimetype="application/javascript")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = load_config()
    cfg["status"] = "idle" if not build_status["building"] else "building"
    return jsonify(cfg)


@app.route("/api/config", methods=["POST"])
def post_config():
    if build_status["building"]:
        return jsonify({"error": "Build läuft bereits – bitte warten."}), 409

    data = request.get_json(force=True)
    gh_type = int(data.get("GH_TYPE", 1))
    try:
        if gh_type == 2:
            params = {
                "GH_TYPE": 2,
                "WIN_W":  max(400, min(2000, int(data.get("WIN_W", 800)))),
                "WIN_H":  max(400, min(2500, int(data.get("WIN_H", 1200)))),
                "WIN_ROWS": max(1, min(4, int(data.get("WIN_ROWS", 1)))),
                "WIN_COLS_FRONT": max(1, min(10, int(data.get("WIN_COLS_FRONT", 2)))),
                "WIN_COLS_BACK":  max(1, min(10, int(data.get("WIN_COLS_BACK",  2)))),
                "WIN_COLS_LEFT":  max(1, min(10, int(data.get("WIN_COLS_LEFT",  2)))),
                "WIN_COLS_RIGHT": max(1, min(10, int(data.get("WIN_COLS_RIGHT", 2)))),
                "FRAME_T": max(40, min(120, int(data.get("FRAME_T", 60)))),
                "SILL_H":  max(60, min(200, int(data.get("SILL_H",  100)))),
                "OVER": max(0, min(800, int(data.get("OVER", 300)))),
                "DOOR_FRONT": bool(data.get("DOOR_FRONT", True)),
                "DOOR_BACK":  bool(data.get("DOOR_BACK",  False)),
                "DOOR_LEFT":  bool(data.get("DOOR_LEFT",  False)),
                "DOOR_RIGHT": bool(data.get("DOOR_RIGHT", False)),
            }
        else:
            params = {
                "GH_TYPE": 1,
                "B":    max(600, min(5000, int(data["B"]))),
                "T":    max(600, min(5000, int(data["T"]))),
                "H":    max(1500, min(4000, int(data["H"]))),
                "OVER": max(0,   min(800,  int(data["OVER"]))),
                "P":    int(data.get("P", 50)),
                "DOOR_FRONT": bool(data.get("DOOR_FRONT", True)),
                "DOOR_BACK":  bool(data.get("DOOR_BACK",  False)),
                "DOOR_LEFT":  bool(data.get("DOOR_LEFT",  False)),
                "DOOR_RIGHT": bool(data.get("DOOR_RIGHT", False)),
            }
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Ungültige Parameter: {e}"}), 400

    threading.Thread(target=regenerate, args=(params,), daemon=True).start()
    return jsonify({"status": "started", "params": params})


@app.route("/api/parts")
def get_parts():
    cfg = load_config()
    if int(cfg.get("GH_TYPE", 1)) == 2:
        # Anzahl dynamisch aus config berechnen
        meta = [dict(p) for p in PARTS_META_T2]
        cols_f = int(cfg.get("WIN_COLS_FRONT", 2))
        cols_b = int(cfg.get("WIN_COLS_BACK",  2))
        cols_l = int(cfg.get("WIN_COLS_LEFT",  2))
        cols_r = int(cfg.get("WIN_COLS_RIGHT", 2))
        rows   = int(cfg.get("WIN_ROWS", 1))
        door_sides = sum([
            cfg.get("DOOR_FRONT", True), cfg.get("DOOR_BACK", False),
            cfg.get("DOOR_LEFT",  False), cfg.get("DOOR_RIGHT", False),
        ])
        total_openings = (cols_f + cols_b + cols_l + cols_r) * rows
        for p in meta:
            if p["id"] == "window_frame":
                p["anzahl"] = total_openings - door_sides
            elif p["id"] == "door_frame":
                p["anzahl"] = door_sides
        return jsonify(meta)
    return jsonify(PARTS_META)


@app.route("/api/status")
def get_status():
    with _status_lock:
        return jsonify({
            "building": build_status["building"],
            "progress": build_status["progress"],
            "message":  build_status["message"],
            "error":    build_status["error"],
            "log":      build_status["log"][-10:],
        })


@app.route("/api/status/stream")
def status_stream():
    """Server-Sent Events für Live-Status-Updates."""
    def event_gen():
        last_msg = ""
        while True:
            with _status_lock:
                msg = build_status["message"]
                data = json.dumps({
                    "building": build_status["building"],
                    "progress": build_status["progress"],
                    "message":  msg,
                    "error":    build_status["error"],
                })
            if data != last_msg:
                yield f"data: {data}\n\n"
                last_msg = data
            if not build_status["building"]:
                break
            time.sleep(0.4)
    return Response(event_gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                              "X-Accel-Buffering": "no"})


@app.route("/glb/greenhouse")
def serve_glb():
    if not GLB_FILE.exists():
        return jsonify({"error": "GLB nicht gefunden – bitte Modell generieren."}), 404
    response = send_file(str(GLB_FILE), mimetype="model/gltf-binary")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/stl/<name>")
def serve_stl(name):
    # Sicherheits-Check: nur alphanumerisch + Unterstrich
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        return jsonify({"error": "Ungültiger Name"}), 400
    stl_path = STL_DIR / f"{name}.stl"
    if not stl_path.exists():
        return jsonify({"error": f"STL '{name}.stl' nicht gefunden"}), 404
    response = send_file(str(stl_path), mimetype="application/octet-stream")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/pdf/drawing")
def serve_pdf_drawing():
    if not PDF_DRAWING.exists():
        return jsonify({"error": "PDF nicht gefunden"}), 404
    return send_file(str(PDF_DRAWING), mimetype="application/pdf")


@app.route("/pdf/stueckliste")
def serve_pdf_stueck():
    if not PDF_STUECK.exists():
        return jsonify({"error": "PDF nicht gefunden"}), 404
    return send_file(str(PDF_STUECK), mimetype="application/pdf")


@app.route("/download/plaene")
def download_plaene():
    """ZIP mit allen generierten Plänen und Dateien."""
    import io, zipfile, datetime as dt

    files = [
        (PDF_DRAWING,                    "gewaechshaus_zeichnung.pdf"),
        (PDF_STUECK,                     "gewaechshaus_stueckliste.pdf"),
        (BASE_DIR / "gewaechshaus.step", "gewaechshaus.step"),
        (BASE_DIR / "gewaechshaus.glb",  "gewaechshaus.glb"),
        (BASE_DIR / "gewaechshaus_stueckliste.txt", "gewaechshaus_stueckliste.txt"),
    ]

    # Individuelle STEP-Bauteile
    step_dir = BASE_DIR / "step_parts"
    if step_dir.exists():
        for f in sorted(step_dir.glob("*.step")):
            files.append((f, f"step_parts/{f.name}"))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in files:
            if src.exists():
                zf.write(src, arcname)

    if buf.tell() == 0:
        return jsonify({"error": "Keine Dateien vorhanden – bitte zuerst Modell generieren"}), 404

    buf.seek(0)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"gewaechshaus_plaene_{ts}.zip"
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/api/stueckliste")
def get_stueckliste():
    """Stückliste als Text zurückgeben."""
    txt_file = BASE_DIR / "gewaechshaus_stueckliste.txt"
    if txt_file.exists():
        return txt_file.read_text(), 200, {"Content-Type": "text/plain; charset=utf-8"}
    return jsonify({"error": "Nicht gefunden"}), 404


# ── Start ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🌱  Gewächshaus Web-Konfigurator")
    print(f"    Projektpfad: {BASE_DIR}")
    print(f"    GLB-Datei:   {'✓' if GLB_FILE.exists() else '✗ (noch nicht generiert)'}")
    print(f"    STL-Meshes:  {'✓' if STL_DIR.exists() else '✗'}")
    print("    URL:         http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
