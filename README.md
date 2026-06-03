# 🔥 TheBurner — Web-basierte Lasercutter-Steuerung

> Browser-Oberfläche zum Zeichnen, Bearbeiten und Lasern — gehostet auf einem Mini-PC (z. B. Raspberry Pi) direkt am Lasercutter oder lokal auf Windows/Linux.
>
> Web-based laser cutter control — draw, edit and laser from your browser, hosted on a small PC (e.g. Raspberry Pi) right at the machine, or locally on Windows/Linux.

<p align="center">
  <img width="1790" height="1366" alt="image" src="https://github.com/user-attachments/assets/b6b48261-b762-420c-8eaa-de5a2a32061c" />
</p>

---

## 🌐 Sprache / Language

| 🇩🇪 Deutsch | 🇬🇧 English |
|:----------:|:----------:|
| **[➜ Vollständiges Handbuch](docs/de/HANDBUCH.md)** | **[➜ Full Manual](docs/en/MANUAL.md)** |

---

## ✨ Features

- **Zeichnen / Drawing:** Rechteck, Kreis, Linienzug (mit Winkel- & Magnet-Snapping), Vektor-Text (TTF/OTF), Formen-Bibliothek (14 Formen)
- **Box-Generator:** Finger-Joint-Kästen (Rechteck, Trapez, Pult, Parallelogramm) mit automatischer Winkelkompensation
- **Foto-Gravur:** Graustufen-Leistung oder Floyd-Steinberg-Dithering, Zuschneiden & In-Form-Clippen
- **Import:** SVG (in Einzelteile zerlegt) und Bilder
- **Ebenen:** Schneiden / Gravieren / Hilfslinie / Ignorieren — je Objekt mit Speed, Power, Durchläufen
- **Materialbibliothek:** serverseitig gespeichert (`materials.json`), für alle Clients im Netzwerk
- **Parameter-Test:** Gravur-/Schnitt-Matrix wie bei LightBurn, inkl. Bewertung & Material-Speicherung
- **Maschine:** USB (COM) & WLAN, Jog-Controller, Pumpensteuerung (M8/M9 mit Nachlauf)
- **Projekt:** Speichern/Laden aller Objekte (inkl. Bilder & SVG) mit Datei-Dialog
- **Mehrsprachig:** Deutsch, English, Español, 中文

---

## 🚀 Schnellstart / Quick Start

```bash
# Abhängigkeiten / dependencies
pip install pyserial websockets websocket-client svgelements

# Start
python agent.py
```

Danach im Browser öffnen / then open in browser: **http://localhost:8080**

> Auf einem Raspberry Pi am Lasercutter: über die IP des Pi aus dem Netzwerk erreichbar, z. B. `http://192.168.178.50:8080`.
>
> On a Raspberry Pi at the machine: reachable from the network via the Pi's IP, e.g. `http://192.168.178.50:8080`.

---

## 🧩 Architektur / Architecture

```
┌────────────────────────┐        WebSocket :8765        ┌────────────────────────┐
│   Browser (index.html) │  ◄──────── Status ──────────  │   agent.py (Python)    │
│   Fabric.js Oberfläche  │  ────────  Befehle ────────►  │                        │
│   - Zeichnen / Drawing  │                               │  - WebSocket-Server    │
│   - G-Code-Erzeugung    │        HTTP :8080             │  - HTTP-Server (UI)    │
│     (Foto/Raster)       │  ◄──── index.html ────────    │  - G-Code-Generierung  │
└────────────────────────┘                               │  - materials.json      │
                                                          └───────────┬────────────┘
                                                  USB/COM oder / or   │  WLAN (HTTP+WS)
                                                                      ▼
                                                          ┌────────────────────────┐
                                                          │   GRBL Lasercutter     │
                                                          └────────────────────────┘
```

Details: siehe **[Handbuch](docs/de/HANDBUCH.md)** / see **[Manual](docs/en/MANUAL.md)**.

---

## 📋 Voraussetzungen / Requirements

- **Python 3.9+**
- Pakete / packages: `pyserial`, `websockets`, `websocket-client`, `svgelements`
- Ein GRBL-kompatibler Lasercutter / a GRBL-compatible laser cutter (getestet mit / tested with **GRBL-ESP32 1.3a**)
- Moderner Browser (Chromium/Edge empfohlen — für „Speicherort wählen" beim Projekt-Speichern)

---

## 📁 Projektstruktur / Project structure

| Datei / File | Beschreibung / Description |
|---|---|
| `agent.py` | Python-Backend (Server, Laser-Kommunikation, G-Code) |
| `index.html` | Komplette Browser-Oberfläche (HTML/CSS/JS, Fabric.js) |
| `materials.json` | Materialbibliothek (wird automatisch angelegt / auto-created) |
| `docs/` | Diese Dokumentation / this documentation |

---

## ⚠️ Sicherheit / Safety

Ein Laser kann blenden, verbrennen und Brände auslösen. Betreibe den Lasercutter **niemals unbeaufsichtigt**, nutze Augenschutz und Absaugung. Diese Software steuert Hardware — prüfe Parameter immer erst mit einem Materialtest.

A laser can blind, burn and cause fire. **Never operate unattended**, use eye protection and fume extraction. This software controls hardware — always validate parameters with a material test first.

---

## 📜 Lizenz / License

MIT-License:

Copyright (c) 2026 Artur Pundsack
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
