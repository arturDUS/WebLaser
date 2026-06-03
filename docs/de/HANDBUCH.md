# 🔥 TheBurner — Handbuch (Deutsch)

> Vollständige Funktions- und Prozessdokumentation der Web-basierten Lasercutter-Steuerung.
> **English version:** [../en/MANUAL.md](../en/MANUAL.md)

---

## Inhaltsverzeichnis

1. [Überblick & Architektur](#1-überblick--architektur)
2. [Installation & Start](#2-installation--start)
3. [Aufbau der Oberfläche](#3-aufbau-der-oberfläche)
4. [Linke Leiste — Maschine & Steuerung](#4-linke-leiste--maschine--steuerung)
5. [Arbeitsbereich (Canvas)](#5-arbeitsbereich-canvas)
6. [Rechte Leiste — Werkzeuge & Ebenen](#6-rechte-leiste--werkzeuge--ebenen)
7. [Zeichenfunktionen im Detail](#7-zeichenfunktionen-im-detail)
8. [Generatoren](#8-generatoren)
9. [Bearbeiten & Anordnen](#9-bearbeiten--anordnen)
10. [Import & Foto-Gravur](#10-import--foto-gravur)
11. [Ebenen & Materialien](#11-ebenen--materialien)
12. [Parameter-Test](#12-parameter-test)
13. [Projekt speichern & laden](#13-projekt-speichern--laden)
14. [Mehrsprachigkeit](#14-mehrsprachigkeit)
15. [Prozessablauf (Standard-Workflow)](#15-prozessablauf-standard-workflow)
16. [Technik: G-Code-Erzeugung](#16-technik-g-code-erzeugung)
17. [Tastenkürzel](#17-tastenkürzel)
18. [Fehlerbehebung](#18-fehlerbehebung)

---

## 1. Überblick & Architektur

TheBurner besteht aus **zwei Teilen**:

| Teil | Datei | Aufgabe |
|---|---|---|
| **Backend** | `agent.py` | Python-Server: liefert die Oberfläche aus, spricht mit dem Laser, erzeugt G-Code, speichert Materialien |
| **Frontend** | `index.html` | Browser-Oberfläche auf Basis von [Fabric.js](http://fabricjs.com/) zum Zeichnen und Bedienen |

```
┌────────────────────────┐        WebSocket :8765        ┌────────────────────────┐
│   Browser (index.html) │  ◄──────── Status ──────────  │   agent.py (Python)    │
│                        │  ────────  Befehle ────────►  │                        │
│   Fabric.js Canvas     │                               │  WebSocket-Server      │
│   G-Code für Foto/     │        HTTP :8080             │  HTTP-Server (UI)      │
│   Raster im Frontend   │  ◄──── index.html ────────    │  G-Code-Generierung    │
└────────────────────────┘                               │  materials.json        │
                                                          └───────────┬────────────┘
                                            USB/COM  oder  WLAN (HTTP :8848 + WS :8849)
                                                                      ▼
                                                          ┌────────────────────────┐
                                                          │   GRBL-Lasercutter     │
                                                          └────────────────────────┘
```

**Idee:** Das System wird auf einem kleinen Rechner (z. B. Raspberry Pi) **direkt am Lasercutter** gehostet. Jeder im Netzwerk öffnet einfach die Webseite — die Materialbibliothek ist dann für alle gemeinsam verfügbar. Läuft das System auf einem Windows-/Linux-Rechner, gilt das ebenso lokal.

**Ports:**
- `8080` — HTTP (liefert `index.html`)
- `8765` — WebSocket (Browser ↔ agent.py)
- `8848`/`8849` — HTTP/WebSocket zum Netzwerk-Laser (nur bei WLAN-Betrieb)

---

## 2. Installation & Start

```bash
pip install pyserial websockets websocket-client svgelements
python agent.py
```

Beim Start öffnet sich der Browser automatisch auf `http://localhost:8080`. Im Netzwerk: `http://<IP-des-Hosts>:8080`.

> 📷 **Screenshot:** `docs/images/startup.png` — Konsole nach dem Start mit „Agent verbunden".

---

## 3. Aufbau der Oberfläche

Die Oberfläche ist dreigeteilt: **linke Leiste** (Maschine/Steuerung), **Arbeitsbereich** (Mitte) und **rechte Leiste** (Werkzeuge/Ebenen).

```
┌──────────────┬──────────────────────────────────┬──────────────────┐
│  ⚙️ Maschine  │  Arbeitsbereich  [🌐][⛶ 🔲 1:1][🎯 📍] │  🛠️ Werkzeuge     │
│              │  ┌────────────────────────────┐  │  ▭ ◯ ✒️ T ⭐     │
│  🎛️ Job       │  │      Lineal X              │  │  📦 ▦ │ 🔗 ⛓️‍💥   │
│  Kontrolle    │  │ L │                       │  │  ⇤ ↔ ⇥ │ ⤒ ↕ ⤓  │
│              │  │ i │   Zeichenfläche         │  │  📥 Importieren  │
│  🕹️ Steuerung │  │ n │   (mm-Raster)          │  │  📐 SVG  🖼️ Bild  │
│  & Konsole    │  │ e │                       │  │                  │
│  [Log]        │  │ a │                       │  │  📋 Objekte &     │
│              │  │ l │                       │  │     Ebenen       │
│              │  └────────────────────────────┘  │  [Tabelle]       │
│              │                                  │  ⚙️ Ebenen-Param. │
│              │                                  │  💾 Projektverw.  │
└──────────────┴──────────────────────────────────┴──────────────────┘
```

> 📷 **Screenshot:** `docs/images/overview.png` — Gesamtansicht der Oberfläche.

**Panels ein-/ausklappen:** Jede Panel-Überschrift (z. B. „🛠️ Werkzeuge") hat einen kleinen Pfeil **▾/▸**. Klick darauf rollt das Panel zusammen, sodass nur die Überschrift bleibt. Bei wenig Bildschirmhöhe lässt sich die ganze Leiste scrollen.

**Ein-/Ausblenden der Leisten:** Die Pfeil-Buttons `◀`/`▶` am Rand blenden die komplette linke bzw. rechte Leiste aus, um mehr Platz für die Zeichenfläche zu schaffen.

---

## 4. Linke Leiste — Maschine & Steuerung

### 4.1 ⚙️ Maschine

> 📷 **Screenshot:** `docs/images/panel-machine.png`

| Element | Funktion |
|---|---|
| 🔴/🟢 Status-Icon | Verbindungszustand des Lasers |
| **USB (COM) / WLAN** | Verbindungsart wählen |
| **Port + Baud** (USB) | COM-Port (`🔄` scannt verfügbare Ports) und Baudrate (Standard 115200) |
| **IP + Port** (WLAN) | IP-Adresse und Port des Netzwerk-Controllers |
| **🔌 Verbinden / 🛑 Trennen** | Verbindung auf-/abbauen |
| **📡 Daten** | Liest die Maschinen-Einstellungen via `$$` (z. B. Arbeitsbereichsgröße `$130/$131`, Max-Power `$30`, Lasermodus `$32`) und übernimmt sie automatisch |
| **📐 Arbeitsbereich** | Breite/Höhe in mm — definiert die Zeichenfläche (Button `✔️` wendet die Größe an) |

### 4.2 🎛️ Job Kontrolle

> 📷 **Screenshot:** `docs/images/panel-job.png`

| Element | Funktion |
|---|---|
| **▶ Job Lasern** | Erzeugt aus allen Objekten den G-Code und sendet ihn an den Laser. Schaltet zuerst die Pumpe ein (`M8`). |
| **⏹ STOP / ABBRUCH** | Bricht den laufenden Job sofort ab (GRBL Soft-Reset). Pumpe läuft danach noch ca. 10 s nach. |
| **Unlock** | Entsperrt einen GRBL-Alarm (`$X`). |
| Fortschrittsbalken | Zeigt den Bearbeitungsfortschritt in %. |

### 4.3 🕹️ Steuerung & Konsole

> 📷 **Screenshot:** `docs/images/panel-control.png`

| Element | Funktion |
|---|---|
| G-Code-Eingabe + `✉️` | Einzelne G-Code-Befehle direkt senden |
| **Home** | Referenzfahrt (`$H`) |
| **X0/Y0** | Aktuelle Position als Nullpunkt setzen |
| **Pumpe EIN/AUS** | Absaugung/Luft manuell schalten (`M8`/`M9`) |
| **🎯 Grafischer Jog-Controller** | Öffnet ein rundes Bedienfeld zum Verfahren der Achsen per Mausklick |
| **[Log]** | Konsolen-Ausgabe (Befehle, Antworten, Fehler) |

---

## 5. Arbeitsbereich (Canvas)

Die Zeichenfläche zeigt ein **mm-Raster** mit Linealen. Die obere Leiste enthält:

| Element | Funktion |
|---|---|
| 🌐 Sprach-Dropdown | Deutsch / English / Español / 中文 (siehe [Mehrsprachigkeit](#14-mehrsprachigkeit)) |
| **⛶** | Alle Objekte einpassen (Zoom auf Inhalt) |
| **🔲** | Auf den Arbeitsbereich zentrieren |
| **1:1** | 100 %-Ansicht |
| **🎯** | Laser zu einem angeklickten Punkt fahren |
| **📍** | Nullpunkt (Ursprung) per Klick setzen |

**Navigation:** Mausrad = Zoom, Ziehen mit der Maus = Auswahl/Verschieben. Der violette Marker 📍 zeigt den Nullpunkt, das rote Fadenkreuz die aktuelle Laserposition.

> 📷 **Screenshot:** `docs/images/workspace-toolbar.png` — obere Leiste des Arbeitsbereichs.

---

## 6. Rechte Leiste — Werkzeuge & Ebenen

### 6.1 🛠️ Werkzeuge

> 📷 **Screenshot:** `docs/images/panel-tools.png`

Die Werkzeuge sind in beschriftete Zeilen gruppiert:

| Zeile | Buttons | Funktion |
|---|---|---|
| **Zeichnen** | ▭ ◯ ✒️ T ⭐ | Rechteck, Kreis, Linienzug, Text, Formen-Bibliothek |
| **Generatoren / Gruppieren** | 📦 ▦ │ 🔗 ⛓️‍💥 | Box-Generator, Raster-Kopie │ Gruppieren, Gruppierung aufheben |
| **Ausrichten** | ⇤ ↔ ⇥ │ ⤒ ↕ ⤓ | Links, horizontal zentrieren, rechts │ oben, vertikal zentrieren, unten |

### 6.2 📥 Importieren

| Button | Funktion |
|---|---|
| **📐 SVG** | Vektor-SVG importieren (wird in freie Einzelteile zerlegt) |
| **🖼️ Bild** | Foto/Bild laden (öffnet die Foto-Gravur, siehe [10.2](#102-foto-gravur)) |

### 6.3 📋 Objekte & Ebenen

Tabelle aller Objekte. Pro Zeile: **Typ**, **Aktion** (Dropdown: ✂️ Schneiden / 🔥 Gravieren / 📏 Hilfslinie / ❌ Ignorieren) und ein **🗑️ Löschen**-Button.

> 📷 **Screenshot:** `docs/images/panel-objects.png`

### 6.4 ⚙️ Ebenen-Parameter

| Element | Funktion |
|---|---|
| **📚 Materialbibliothek** | Öffnet die Materialverwaltung (siehe [11.2](#112-materialbibliothek)) |
| **Abarbeitungs-Reihenfolge** | Gravieren zuerst / Schneiden zuerst / Reihenfolge wie in Tabelle |
| **✂️ Schneiden** | Speed, Power (%), Durchläufe für die Schneide-Ebene |
| **🔥 Gravieren** | Modus (Umriss / Fläche / Fläche+Umriss), Linienabstand, Speed, Power, Durchläufe |

### 6.5 💾 Projektverwaltung

Speichern/Laden des kompletten Projekts (siehe [13](#13-projekt-speichern--laden)). Sitzt ganz unten in der rechten Leiste.

---

## 7. Zeichenfunktionen im Detail

### 7.1 ▭ Rechteck & ◯ Kreis

Erzeugt ein Rechteck bzw. einen Kreis im Arbeitsbereich. Größe und Position werden danach mit den Maus-Griffen oder über die **Bemaßungs-Maßzahlen** geändert (Klick auf die angezeigte Maßzahl öffnet ein Eingabefeld).

> 📷 **Screenshot:** `docs/images/draw-rect.png` — Rechteck mit Bemaßung.

### 7.2 ✒️ Linienzug (Polylinie)

Klicke nacheinander Punkte, um einen Linienzug zu zeichnen. **ESC** beendet das Zeichnen.

- **Winkel-Snapping:** In der Nähe von 45°-Schritten rastet die Linie ein.
- **Magnet-Snapping:** In der Nähe anderer Objekte rastet der Cursor auf Endpunkte (stark, cyan), Kreuzungen (grün) oder Kanten (schwach, orange) ein. **Alt** gedrückt halten deaktiviert den Magneten kurzzeitig.
- **Bearbeiten:** *Einfachklick* auf ein Segment/Handle wählt es einzeln (Länge per Maßzahl änderbar, Eckpunkt per blauem Handle verschiebbar). *Doppelklick* wählt den **gesamten** Linienzug zum Verschieben/Drehen/Skalieren.

> 📷 **Screenshot:** `docs/images/polyline-snap.png` — Magnet-Snapping beim Zeichnen.

### 7.3 T Text

Öffnet den Text-Dialog. Eingabe von Text, Schrifthöhe und einer **TTF/OTF-Schriftart** (Button „📂 Schrift laden"). Der Text wird als **echter Vektor-Pfad** eingefügt (kein Bitmap), direkt laserbar. Eine Live-Vorschau zeigt den Laser-Fahrweg.

> 📷 **Screenshot:** `docs/images/dialog-text.png`

### 7.4 ⭐ Formen-Bibliothek

14 parametrische Formen: **Stern, Herz, Trapez, Parallelogramm, Sechseck, Fünfeck, Achteck, Dreieck, Pfeil, Kreuz, Tonne, Zahnrad, Blitz, Stadion**. Form anklicken, Parameter eingeben, *Einfügen*. Die Form landet mittig im sichtbaren Bereich und ist sofort bearbeitbar.

> 📷 **Screenshot:** `docs/images/dialog-shapes.png`

---

## 8. Generatoren

### 8.1 📦 Box-Generator (Finger-Joint)

Erzeugt fertige Schnittteile für Kästen mit **Finger-/Kerbverbindungen**.

> 📷 **Screenshot:** `docs/images/dialog-box.png`

**Box-Typen:**

| Typ | Beschreibung |
|---|---|
| **Rechteck** | Klassische Kiste |
| **Trapez** | Symmetrisch verjüngt (Trichter/Pflanzkübel) — Parameter „Breite oben" |
| **Pult** | Einseitig schräg (Lesepult) — eine Seite senkrecht, eine schräg |
| **Parallelogramm** | In X-Richtung geschert — Parameter „Versatz oben" |

**Parameter:** Breite, Tiefe, Höhe, Materialstärke, Finger-Breite (oder feste „Finger pro Kante"), Abstand der Teile, Deckel ja/nein, alle Teile gruppieren.

**Funktionsweise:**
- Stecker/Schlitz-System: Wandnasen stehen vor und greifen in Schlitze von Boden/Deckel und Nachbarwänden. Ecken sind immer bündig (keine „toten Ecken").
- Bei **Trapez/Parallelogramm/Pult** werden die Finger der schrägen Seitenwände automatisch tiefer berechnet (Faktor `slant/H`), damit sie trotz Winkel sauber greifen.
- Maße sind **Außenmaße**.

### 8.2 ▦ Raster-Kopie (Array)

Dupliziert die aktuelle Auswahl in einem Raster: Spalten/Zeilen und Abstände in X/Y.

> 📷 **Screenshot:** `docs/images/dialog-array.png`

---

## 9. Bearbeiten & Anordnen

### 9.1 🔗 Gruppieren / ⛓️‍💥 Aufheben

Mehrere Objekte zu einer Gruppe zusammenfassen bzw. wieder trennen. Überlappende Formen können beim Gruppieren zu einem **Verbundpfad** verschweißt werden (echte Löcher per Even-Odd-Regel — z. B. für Donut-Formen).

### 9.2 Ausrichten

Mehrere Objekte auswählen (das **zuerst** angeklickte ist die Referenz), dann eine Ausricht-Funktion wählen:

| Button | Funktion |
|---|---|
| ⇤ / ⇥ | Links / Rechts ausrichten |
| ↔ | Horizontal zentrieren (gleiche Mitte X) |
| ⤒ / ⤓ | Oben / Unten ausrichten |
| ↕ | Vertikal zentrieren (gleiche Mitte Y) |

> 💡 Für eine definierte Referenz die Objekte **einzeln mit Shift** anklicken (nicht per Rahmen).

> 📷 **Screenshot:** `docs/images/align.png` — vorher/nachher.

---

## 10. Import & Foto-Gravur

### 10.1 SVG-Import

Lädt eine SVG-Datei und zerlegt sie in **freie Einzelteile**, die einzeln bearbeitet und mit Ebenen versehen werden können.

### 10.2 Foto-Gravur

> 📷 **Screenshot:** `docs/images/dialog-photo.png`

Foto über **🖼️ Bild** laden → wird automatisch in **Graustufen** gewandelt und mittig platziert. Auswahl des Fotos + erneuter Klick auf **🖼️** öffnet den Dialog.

**Bild-Anpassung:** Helligkeit, Kontrast (Live-Vorschau), Invertieren.

**Beschneiden / In Form einpassen:** Foto **und** eine geschlossene Form (Rechteck/Polygon/Linienzug) gemeinsam markieren → „✂️ In Form einpassen". Alles außerhalb der Form wird nicht graviert. Für reines Rand-Beschneiden ein Rechteck nutzen. „Clip entfernen" macht es rückgängig.

**Gravur-Verfahren:**

| Verfahren | Beschreibung |
|---|---|
| **Graustufen-Leistung** | Dunkle Pixel → mehr Power (min…max). Pixel heller als die Weiß-Schwelle werden übersprungen. |
| **Dithering (S/W)** | Floyd-Steinberg → Laser an/aus pro Pixel, konstante Power. Oft bestes Foto-Ergebnis auf Holz/Papier. |

**Weitere Parameter:** Auflösung (mm/Pixel), Speed, Power min/max, Weiß-Schwelle. Der Raster-G-Code wird zeilenweise im Frontend erzeugt (Rotation, Skalierung und Clip werden korrekt berücksichtigt).

---

## 11. Ebenen & Materialien

### 11.1 Ebenen (Laser-Modus pro Objekt)

In der Tabelle **Objekte & Ebenen** legt das Dropdown pro Objekt fest:

| Modus | Bedeutung |
|---|---|
| ✂️ **Schneiden** | Vektor-Schnitt entlang der Kontur (rot) |
| 🔥 **Gravieren** | Umriss und/oder Flächenfüllung (blau) |
| 📏 **Hilfslinie** | Gestrichelt dargestellt, **wird nicht gelasert** — nur zur Ausrichtung. Dient auch als Magnet-Snap-Ziel. |
| ❌ **Ignorieren** | Bleibt auf dem Arbeitsbereich, wird aber nicht gelasert |

Die Parameter (Speed/Power/Durchläufe) gelten global je Ebene und werden im Bereich **⚙️ Ebenen-Parameter** eingestellt.

### 11.2 Materialbibliothek

> 📷 **Screenshot:** `docs/images/dialog-material.png`

Tabelle aller Materialien mit Schnitt- und Gravur-Parametern (Speed/Power/Durchläufe). Pro Zeile:
- **↩ Nutzen** — Parameter in die Hauptfelder übernehmen
- **✏️ Bearbeiten** / **🗑️ Löschen**

**Speicherort:** serverseitig in `materials.json` neben `agent.py`. Dadurch ist die Bibliothek für **alle Clients im Netzwerk** verfügbar (z. B. mehrere Browser am selben Raspberry Pi).

---

## 12. Parameter-Test

Ermittelt die optimalen Laserparameter für ein neues Material — analog zu LightBurn-Testmustern.

> 📷 **Screenshot:** `docs/images/dialog-mattest.png`

**Ablauf:**
1. In der Materialbibliothek **🧪 Parameter-Test erzeugen**.
2. Typ wählen: **Gravur** (gefüllte Quadrate) oder **Schnitt** (Konturen).
3. Power-/Speed-Bereich, Anzahl Zeilen (Power) × Spalten (Speed), Feldgröße, Durchläufe pro Feld.
4. **🧪 Testmuster erzeugen** → ein Raster wird zentriert im Arbeitsbereich platziert (Beschriftung am Rand, wird nicht gelasert).
5. **▶ Job Lasern** ausführen.
6. Nach dem Lasern erscheint die **Bewertung**: beste Spalte/Reihe eingeben → Speed/Power werden aufgelöst. Bei zu schwachem Ergebnis **➕ Weiteren Durchlauf lasern** (zählt automatisch hoch).
7. Name eingeben → **💾 Als Material speichern** (mit der aufgelaufenen Durchlaufzahl).

> 📷 **Screenshot:** `docs/images/dialog-eval.png` — Bewertungsdialog.

---

## 13. Projekt speichern & laden

**💾 Projekt speichern (.json):** Speichert **alle** Objekte des Arbeitsbereichs — inklusive importierter **Bilder** (mit Filtern/Clip) und **SVG-Grafiken**, Ebenen-Zuordnung und Arbeitsbereichsgröße. In Chromium/Edge öffnet sich ein **Datei-Dialog zur Speicherort-Wahl** (sonst klassischer Download).

**Projekt laden:** Über den Datei-Dialog eine `.json` wählen. Nur die Benutzerobjekte werden ersetzt; Hilfsobjekte (Raster, Ursprung) bleiben erhalten. Bildfilter werden neu angewendet, die Arbeitsbereichsgröße wird wiederhergestellt. Alte Projektdateien werden ebenfalls geladen.

> ⚠️ **Hinweis:** Linienzug-Bearbeitungsgriffe werden nicht mitgespeichert — geladene Polylinien sind sichtbar und verschiebbar, für punktgenaues Nachbearbeiten ggf. neu zeichnen.

---

## 14. Mehrsprachigkeit

Über das 🌐-Dropdown oben im Arbeitsbereich: **Deutsch, English, Español, 中文**. Die Wahl wird im Browser gespeichert (`localStorage`) und beim nächsten Start automatisch wieder eingestellt. Übersetzt sind die Hauptoberfläche und die Dialoge.

> 📷 **Screenshot:** `docs/images/language.png` — Sprach-Dropdown.

---

## 15. Prozessablauf (Standard-Workflow)

```
┌─────────────────────┐
│ 1. Verbinden        │  ⚙️ Maschine → USB/WLAN → 🔌 Verbinden → 📡 Daten
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. Arbeitsbereich   │  Breite/Höhe setzen (oder automatisch aus $130/$131)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. Nullpunkt        │  Laser fahren (🎯), Position als X0/Y0 setzen bzw. 📍
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 4. Objekte erstellen│  Zeichnen / Import / Box / Foto / Text …
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 5. Ebenen & Parameter│ Pro Objekt Schneiden/Gravieren wählen,
│                     │  Material aus Bibliothek übernehmen (📚)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ (optional) Material-│  🧪 Parameter-Test bei unbekanntem Material
│  test               │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 6. Job Lasern       │  ▶ → Pumpe EIN (M8) → Gravur zuerst, dann Schnitt
│                     │  → Fortschritt → Pumpe 10 s Nachlauf
└─────────────────────┘
```

**Abarbeitungs-Reihenfolge:** Standard ist „Gravieren, dann Schneiden" — sinnvoll, da nach dem Ausschneiden das Werkstück lose liegen könnte.

---

## 16. Technik: G-Code-Erzeugung

Der Job wird als „Mixed Job" an `agent.py` gesendet. Das Backend baut daraus eine G-Code-Liste mit Header `M8 G21 G90 M5`:

| Job-Item | Erzeugung |
|---|---|
| **Vektor** (Schnitt/Umriss) | `generate_gcode_from_svg()` — folgt der Kontur, Kurven werden in kurze Geraden zerlegt |
| **Raster** (Gravur-Fläche, Material-Test) | `generate_raster_gcode()` — zeilenweise Füllung |
| **raw** (Foto) | Vorgenerierte Zeilen aus dem Frontend (Graustufen/Dithering) |

- **Leistung:** Prozent → S-Wert über die Maschinen-Maxpower (`$30`). 100 % ≙ `S1000` bei `$30=1000`.
- **Durchläufe (Passes):** Das Objekt wird mehrfach in die Queue gelegt.
- **Flusskontrolle:** Bei **Netzwerk-Lasern** wartet der Server nach jedem Befehl auf `ok` (verhindert „modal group violation" durch zu schnelles Senden über WiFi). Bei USB wird der GRBL-Puffer per Byte-Zählung ausgelastet.
- **Pumpe:** `M8` zu Beginn, `M9` mit ~10 s Nachlauf nach Job-Ende/Abbruch.

---

## 17. Tastenkürzel

| Taste | Funktion |
|---|---|
| **ESC** | Linienzug-Zeichnen beenden |
| **Entf / Delete** | Markierte Objekte löschen |
| **Alt** (halten) | Magnet-Snapping beim Zeichnen kurzzeitig aus |
| **Doppelklick** (Polylinie) | Gesamten Linienzug auswählen |

---

## 18. Fehlerbehebung

| Problem | Ursache / Lösung |
|---|---|
| **`error: Gcode modal group violation`** | Meist zu schnelles Senden über WiFi (gelöst durch `ok`-Flusskontrolle) **oder** ein gespeicherter GRBL-Startup-Block. Mit `$$` prüfen, ggf. `$N0=` und `$N1=` leeren. |
| **`error: Expected GCode command letter`** | `$`-Befehl wurde an den G-Code-Parser gesendet — `$$`/`$H` etc. funktionieren je nach Controller nur über die passende Schnittstelle. |
| **Pumpe läuft nach Job-Test ständig weiter** | Der Durchlaufzähler erhöht sich bei jedem „Job Lasern", solange Testfelder auf dem Arbeitsbereich liegen — vor einem normalen Job die Testfelder löschen. |
| **Materialbibliothek leer auf anderem Gerät** | `materials.json` liegt beim Host. Bei eigener Instanz hat jedes Gerät seine eigene Datei. |
| **Kein „Speicherort wählen"-Dialog** | Nur Chromium/Edge unterstützen die File System Access API; sonst klassischer Download. |
| **`$30` ≠ 1000** | Dann entspricht 100 % einem anderen S-Wert; das System übernimmt `$30` automatisch als Maxpower. |

---

> 📷 **Hinweis zu Screenshots:** Die mit „📷 Screenshot" markierten Stellen verweisen auf Bilder in `docs/images/`. Eine Anleitung, welche Aufnahmen sinnvoll sind, steht in [docs/images/README.md](../images/README.md).
