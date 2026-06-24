<a id="top"></a>

# 🔥 TheBurner — Web-based Laser Cutter Control

<p align="center">
  <img width="1957" height="1235" alt="image" src="https://github.com/user-attachments/assets/b60302c8-f23a-46f2-9643-2c639e6ab46a" />
</p>

<p align="center">
  <b>🌐 Sprache / Language:</b>&nbsp;&nbsp;
  <a href="#-deutsch">🇩🇪 Deutsch</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#-english">🇬🇧 English</a>
</p>

---

<a id="-deutsch"></a>
## 🇩🇪 Deutsch

> WebLaser bietet eine intuitive, browserbasierte Oberfläche zum Zeichnen, Bearbeiten und Lasern. Die Software passt sich exakt dem jeweiligen Setup an: Sie kann entweder direkt als lokale Webanwendung auf einem Windows- oder Linux-PC gestartet werden, oder sie läuft direkt auf einem in den Lasercutter integrierten Mini-PC (wie einem Raspberry Pi), auf den bequem per Netzwerk über den Browser zugegriffen wird.

📖 **[➜ Vollständiges Handbuch](docs/de/HANDBUCH.md)**

### ✨ Funktionen

- **Zeichnen:** Rechteck, Kreis, Linienzug (Winkel- & Magnet-Snapping, Live-Anzeige von Länge & Winkel, Eckpunkte verschieben/verbinden), Vektor-Text (TTF/OTF), Formen-Bibliothek (14 Formen)
- **Box-Generator:** Finger-Joint-Kästen (Rechteck, Trapez, Pult, Parallelogramm) mit automatischer Winkelkompensation
- **Foto-Gravur:** Graustufen-Leistung oder Floyd-Steinberg-Dithering, Zuschneiden & In-Form-Clippen
- **Import:** SVG (in Einzelteile zerlegt) und Bilder
- **Ebenen:** Schneiden / Gravieren / Hilfslinie / Ignorieren — je Objekt mit Speed, Power, Durchläufen
- **Materialbibliothek:** serverseitig gespeichert (`materials.json`), für alle Clients im Netzwerk
- **Parameter-Test:** Gravur-/Schnitt-Matrix wie bei LightBurn, inkl. Bewertung & Material-Speicherung
- **Maschine:** USB (COM) & WLAN (**FluidNC** & Grbl_ESP32, Firmware-Auto-Erkennung, Telnet/WebUI), Jog-Controller, Befehls-Historie (↑/↓), Pumpensteuerung (M8/M9 mit Nachlauf)
- **Kamera:** Hintergrundbild (CSI/USB), Kalibrierung (entzerrt, Thin-Plate-Spline), Kantenerkennung → Vektor
- **Raspberry Pi:** automatische MKS-DLC32-Verbindung, Software-Update per Web-UI-Button, **mobile Touch-Bedienseite + PWA** fürs Handy
- **Projekt:** Speichern/Laden aller Objekte (inkl. Bilder & SVG) mit Datei-Dialog
- **Mehrsprachig:** Deutsch, English, Español, 中文

### 🚀 Download & Schnellstart

**🪟 Windows (fertige Anwendung — kein Python nötig):**

➜ **[agent.exe herunterladen](https://github.com/arturDUS/WebLaser/releases/latest/download/agent.exe)** (neuestes Release)

Doppelklick auf `agent.exe` startet den Server und öffnet den Browser automatisch.

**🐧 Linux / Raspberry Pi / aus dem Quellcode:**

```bash
# Abhängigkeiten installieren
pip install pyserial websockets websocket-client svgelements

# Starten
python agent.py
```

Danach im Browser öffnen: **http://localhost:8080**

> Auf einem Raspberry Pi am Lasercutter ist die Oberfläche über die IP des Pi aus dem Netzwerk erreichbar, z. B. `http://192.168.178.50:8080`.

🍓 **Komplette Raspberry-Pi-Einrichtung mit Autostart (1-Zeilen-Installer):** [docs/RASPBERRY_PI.md](docs/RASPBERRY_PI.md)

### 🧩 Architektur

```
┌────────────────────────┐        WebSocket :8765        ┌────────────────────────┐
│   Browser (index.html) │  ◄──────── Status ──────────  │   agent.py (Python)    │
│   Fabric.js Oberfläche │  ────────  Befehle ────────►  │                        │
│   - Zeichnen           │                               │  - WebSocket-Server    │
│   - G-Code-Erzeugung   │        HTTP :8080             │  - HTTP-Server (UI)    │
│     (Foto/Raster)      │  ◄──── index.html ────────    │  - G-Code-Generierung  │
└────────────────────────┘                               │  - materials.json      │
                                                         └───────────┬────────────┘
                                                       USB/COM oder  │  WLAN (HTTP+WS)
                                                                     ▼
                                                         ┌────────────────────────┐
                                                         │   GRBL-Lasercutter     │
                                                         └────────────────────────┘
```

Details: siehe **[Handbuch](docs/de/HANDBUCH.md)**.

### 📋 Voraussetzungen

- **Python 3.9+**
- Pakete: `pyserial`, `websockets`, `websocket-client`, `svgelements`
- Ein GRBL-kompatibler Lasercutter (getestet mit **GRBL-ESP32 1.3a**)
- Moderner Browser (Chromium/Edge empfohlen — für „Speicherort wählen" beim Projekt-Speichern)

### 📁 Projektstruktur

| Datei | Beschreibung |
|---|---|
| `agent.py` | Python-Backend (Server, Laser-Kommunikation, G-Code) |
| `index.html` | Komplette Browser-Oberfläche (HTML/CSS/JS, Fabric.js) |
| `materials.json` | Materialbibliothek (wird automatisch angelegt) |
| `docs/` | Dokumentation |

### ⚠️ Sicherheit

Ein Laser kann blenden, verbrennen und Brände auslösen. Betreibe den Lasercutter **niemals unbeaufsichtigt**, nutze Augenschutz und Absaugung. Diese Software steuert Hardware — prüfe Parameter immer erst mit einem Materialtest.

### 📜 Lizenz

MIT — siehe [Lizenz / License](#-lizenz--license) am Ende.

<p align="right"><a href="#-english">🇬🇧 English ➜</a> &nbsp;|&nbsp; <a href="#top">⬆ nach oben</a></p>

---

<a id="-english"></a>
## 🇬🇧 English

> WebLaser offers an intuitive, browser-based interface for drawing, editing, and laser cutting. The software perfectly adapts to your specific setup: It can either be launched directly as a local web application on a Windows or Linux PC, or it can run directly on a mini-PC (such as a Raspberry Pi) integrated into the laser cutter, allowing for convenient network access via your web browser.

📖 **[➜ Full Manual](docs/en/MANUAL.md)**

### ✨ Features

- **Drawing:** rectangle, circle, polyline (angle & magnet snapping, live length & angle readout, move/connect vertices), vector text (TTF/OTF), shape library (14 shapes)
- **Box generator:** finger-joint boxes (rectangle, trapezoid, lectern, parallelogram) with automatic angle compensation
- **Photo engraving:** grayscale power or Floyd-Steinberg dithering, cropping & fit-into-shape clipping
- **Import:** SVG (split into individual parts) and images
- **Layers:** cut / engrave / guide / ignore — per object with speed, power, passes
- **Material library:** stored server-side (`materials.json`), shared across all clients on the network
- **Parameter test:** engrave/cut matrix like LightBurn, incl. evaluation & material saving
- **Machine:** USB (COM) & Wi-Fi (**FluidNC** & Grbl_ESP32, firmware auto-detection, Telnet/WebUI), jog controller, command history (↑/↓), pump control (M8/M9 with after-run)
- **Camera:** background image (CSI/USB), calibration (rectified, thin-plate-spline), edge detection → vector
- **Raspberry Pi:** automatic MKS DLC32 connection, software update via web-UI button, **mobile touch control page + PWA** for phones
- **Project:** save/load all objects (incl. images & SVG) via a file dialog
- **Multilingual:** Deutsch, English, Español, 中文

### 🚀 Download & Quick Start

**🪟 Windows (ready-to-run app — no Python required):**

➜ **[Download agent.exe](https://github.com/arturDUS/WebLaser/releases/latest/download/agent.exe)** (latest release)

Double-click `agent.exe` to start the server and open the browser automatically.

**🐧 Linux / Raspberry Pi / from source:**

```bash
# Install dependencies
pip install pyserial websockets websocket-client svgelements

# Start
python agent.py
```

Then open in your browser: **http://localhost:8080**

> On a Raspberry Pi at the machine, the interface is reachable from the network via the Pi's IP, e.g. `http://192.168.178.50:8080`.

🍓 **Full Raspberry Pi setup with autostart (1-line installer):** [docs/RASPBERRY_PI.md](docs/RASPBERRY_PI.md)

### 🧩 Architecture

```
┌────────────────────────┐        WebSocket :8765        ┌────────────────────────┐
│   Browser (index.html) │  ◄──────── Status ──────────  │   agent.py (Python)    │
│   Fabric.js interface  │  ────────  Commands ───────►  │                        │
│   - Drawing            │                               │  - WebSocket server    │
│   - G-code generation  │        HTTP :8080             │  - HTTP server (UI)    │
│     (photo/raster)     │  ◄──── index.html ────────    │  - G-code generation   │
└────────────────────────┘                               │  - materials.json      │
                                                         └───────────┬────────────┘
                                                       USB/COM  or   │  Wi-Fi (HTTP+WS)
                                                                     ▼
                                                         ┌────────────────────────┐
                                                         │   GRBL laser cutter    │
                                                         └────────────────────────┘
```

Details: see the **[Manual](docs/en/MANUAL.md)**.

### 📋 Requirements

- **Python 3.9+**
- Packages: `pyserial`, `websockets`, `websocket-client`, `svgelements`
- A GRBL-compatible laser cutter (tested with **GRBL-ESP32 1.3a**)
- A modern browser (Chromium/Edge recommended — for "choose location" when saving a project)

### 📁 Project Structure

| File | Description |
|---|---|
| `agent.py` | Python backend (server, laser communication, G-code) |
| `index.html` | Complete browser interface (HTML/CSS/JS, Fabric.js) |
| `materials.json` | Material library (auto-created) |
| `docs/` | Documentation |

### ⚠️ Safety

A laser can blind, burn and cause fire. **Never operate unattended**, use eye protection and fume extraction. This software controls hardware — always validate parameters with a material test first.

### 📜 License

MIT — see [Lizenz / License](#-lizenz--license) at the bottom.

<p align="right"><a href="#-deutsch">🇩🇪 Deutsch ➜</a> &nbsp;|&nbsp; <a href="#top">⬆ to top</a></p>

---

<a id="-lizenz--license"></a>
## 📜 Lizenz / License

MIT License

Copyright (c) 2026 Artur Pundsack

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
