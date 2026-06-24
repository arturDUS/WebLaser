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
18. [Kamera, Mobil-Bedienung & Wartung](#18-kamera-mobil-bedienung--wartung)
19. [Fehlerbehebung](#19-fehlerbehebung)

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

<img width="276" height="53" alt="image" src="https://github.com/user-attachments/assets/53448762-df57-4643-bce9-1ceecda9d85d" />


---

## 3. Aufbau der Oberfläche

Die Oberfläche ist dreigeteilt: **linke Leiste** (Maschine/Steuerung), **Arbeitsbereich** (Mitte) und **rechte Leiste** (Werkzeuge/Ebenen).

<img width="1753" height="1246" alt="image" src="https://github.com/user-attachments/assets/4bb4f4b4-7bce-4595-b722-4f4f1dab2f19" />

**Panels ein-/ausklappen:** Jede Panel-Überschrift (z. B. „🛠️ Werkzeuge") hat einen kleinen Pfeil **▾/▸**. Klick darauf rollt das Panel zusammen, sodass nur die Überschrift bleibt. Bei wenig Bildschirmhöhe lässt sich die ganze Leiste scrollen.

**Ein-/Ausblenden der Leisten:** Die Pfeil-Buttons `◀`/`▶` am Rand blenden die komplette linke bzw. rechte Leiste aus, um mehr Platz für die Zeichenfläche zu schaffen.

---

## 4. Linke Leiste — Maschine & Steuerung

### 4.1 ⚙️ Maschine

<img width="324" height="318" alt="image" src="https://github.com/user-attachments/assets/ad3f977c-eb85-44d1-91ea-4ee48a4e8908" />

| Element | Funktion |
|---|---|
| 🔴/🟢 Status-Icon | Verbindungszustand des Lasers |
| **USB (COM) / WLAN** | Verbindungsart wählen |
| **Port + Baud** (USB) | COM-Port (`🔄` scannt verfügbare Ports) und Baudrate (Standard 115200) |
| **IP + Port** (WLAN) | IP-Adresse und Port des Netzwerk-Controllers |
| **Modus** (WLAN) | **Auto-Erkennung** (empfohlen), **Telnet** (FluidNC, Port 23) oder **WebUI** (ESP3D / Grbl_ESP32). Bei „Auto" probiert der Server zuerst Telnet und fällt sonst auf WebUI zurück. |
| **🔌 Verbinden / 🛑 Trennen** | Verbindung auf-/abbauen |
| **📡 Daten** | Liest die Maschinen-Einstellungen via `$$` (z. B. Arbeitsbereichsgröße `$130/$131`, Max-Power `$30`, Lasermodus `$32`) und übernimmt sie automatisch |

> 📐 **Arbeitsbereich-Größe:** Die Eingabefelder für Breite/Höhe (mm) befinden sich jetzt in der **oberen Leiste des Arbeitsbereichs** (siehe [Abschnitt 5](#5-arbeitsbereich-canvas)).

> 🔎 **Firmware-Erkennung:** Beim Verbinden erkennt das System automatisch die Firmware (**FluidNC** bzw. **Grbl/Grbl_ESP32**) und die Transportart und meldet sie im Log (z. B. „Verbunden: FluidNC über Telnet"). FluidNC v4 über WLAN wird per **Telnet** angesprochen.

### 4.2 🎛️ Job Kontrolle

<img width="321" height="182" alt="image" src="https://github.com/user-attachments/assets/94076b32-2cb2-41b8-b134-19266ec5d605" />

| Element | Funktion |
|---|---|
| **▶ Job Lasern** | Erzeugt aus allen Objekten den G-Code und sendet ihn an den Laser. Schaltet zuerst die Pumpe ein (`M8`). |
| **⏹ STOP / ABBRUCH** | Bricht den laufenden Job sofort ab (GRBL Soft-Reset). Pumpe läuft danach noch ca. 10 s nach. |
| **Unlock** | Entsperrt einen GRBL-Alarm (`$X`). |
| Fortschrittsbalken | Zeigt den Bearbeitungsfortschritt in %. |
| **📌 Relativ-Modus** (Schalter) | Lasert den Job **relativ zur aktuellen, manuell angefahrenen Laserposition** statt an absoluten Koordinaten (siehe unten). |

#### 4.2.1 📌 Relativ-Modus

Statt das Objekt an festen Maschinenkoordinaten zu lasern, kann der Job **relativ** zu der Stelle gelasert werden, an die du den Laserkopf gerade gefahren hast. Ideal, um ein Motiv passgenau auf ein bereits liegendes Werkstück zu setzen.

1. **Schalter „Relativ-Modus" einschalten.**
2. **📌 Referenzpunkt setzen:** in den Arbeitsbereich klicken — der Cursor **rastet magnetisch auf Eckpunkte** ein (oder klicke frei). Ein **oranger Rauten-Marker** zeigt den Punkt; sein Wert erscheint im Status. *Ohne* Referenzpunkt verweigert „Job Lasern" den Start.
3. **🔦 Pointer-Laser** (optional) einschalten, um den Laser mit **minimaler Leistung** als sichtbaren Punkt zu nutzen, und den Kopf manuell dorthin fahren, wo der Referenzpunkt liegen soll. Der Pointer-Laser geht **beim nächsten Klick** oder **nach 2 Minuten** automatisch wieder aus.
4. **▶ Job Lasern** — das Objekt wird so gelasert, dass der Referenzpunkt **genau an der aktuellen Kopfposition** liegt.

> ⚙️ **Technik:** Im Relativ-Modus wird der Referenzpunkt zum Koordinaten-Ursprung; das Backend setzt zu Beginn `G92 X0 Y0` (aktuelle Position = 0/0) und am Ende `G92.1` (Offset wieder aufheben). Die normale Nullung (`X0/Y0`-Button, `G10 L20`) bleibt davon **unberührt**.
>
> 🔦 **Pointer-Laser:** Bei aktivem Laser-Modus (`$32=1`) feuert der Laser im Stillstand nicht — daher wird `$32` kurz auf `0` gesetzt und beim Ausschalten wieder hergestellt. Leistung ≈ 1 % von `$30`.

### 4.3 🕹️ Steuerung & Konsole
<img width="327" height="657" alt="image" src="https://github.com/user-attachments/assets/6494e2bf-0dc2-4da1-89fc-64ffde0e84df" />

| Element | Funktion |
|---|---|
| G-Code-Eingabe + `✉️` | Einzelne G-Code-Befehle direkt senden. **Befehls-Historie wie im Terminal:** mit **↑/↓** durch die zuletzt gesendeten Befehle blättern. Die Historie bleibt über einen Programm-Neustart erhalten (`localStorage`, max. 50 Einträge). |
| **Home** | Referenzfahrt (`$H`) |
| **X0/Y0** | Aktuelle Position als Nullpunkt setzen |
| **Pumpe EIN/AUS** | Absaugung/Luft manuell schalten (`M8`/`M9`) |
| **🎯 Grafischer Jog-Controller** | Öffnet ein rundes Bedienfeld zum Verfahren der Achsen per Mausklick |
| **[Log]** | Konsolen-Ausgabe (Befehle, Antworten, Fehler) |

<img width="410" height="502" alt="image" src="https://github.com/user-attachments/assets/fe5cb0e6-6bc2-4959-ac58-4b99aea73fa2" />

---

## 5. Arbeitsbereich (Canvas)

Die Zeichenfläche zeigt ein **mm-Raster** mit Linealen. Die obere Leiste enthält:

| Element | Funktion |
|---|---|
| **📐 Breite × Höhe + ✔️** | **Arbeitsbereich-Größe** in mm festlegen (Button `✔️` wendet sie an) — aus dem Maschinen-Panel hierher verschoben |
| 🌐 Sprach-Dropdown | Deutsch / English / Español / 中文 (siehe [Mehrsprachigkeit](#14-mehrsprachigkeit)) |
| **⛶** | Alle Objekte einpassen (Zoom auf Inhalt) |
| **🔲** | Auf den Arbeitsbereich zentrieren |
| **1:1** | 100 %-Ansicht |
| **🎯** | Laser zu einem angeklickten Punkt fahren |
| **📍** | Nullpunkt (Ursprung) per Klick setzen |

**Navigation:** Mausrad = Zoom, Ziehen mit der Maus = Auswahl/Verschieben. Der violette Marker 📍 zeigt den Nullpunkt, das rote Fadenkreuz die aktuelle Laserposition.

> ⚠️ **Laserstrahlung-Warnung:** Während eines laufenden Jobs (oder bei aktivem Pointer-Laser) schwebt ein gut sichtbarer Warnhinweis oben über dem Arbeitsbereich.
<img width="1044" height="57" alt="image" src="https://github.com/user-attachments/assets/d58f7cf0-a1eb-42ed-b609-addc9ed1dcae" />

<img width="1019" height="107" alt="image" src="https://github.com/user-attachments/assets/d5d7e7a7-68d2-4152-915e-f69dbaddaa87" />

---

## 6. Rechte Leiste — Werkzeuge & Ebenen

### 6.1 🛠️ Werkzeuge

<img width="322" height="341" alt="image" src="https://github.com/user-attachments/assets/9ed21025-d370-4a4b-89e4-d6522415715b" />

Die Werkzeuge sind in beschriftete Zeilen gruppiert (alle Symbole einfarbig/monochrom):

| Zeile | Buttons | Funktion |
|---|---|---|
| **Zeichnen** | ⬉ │ ▭ ◯ ∠ T ★ | **Auswählen/Verschieben** │ Rechteck, Kreis, Linienzug, Text, Formen-Bibliothek |
| **Generatoren / Gruppieren** | ▣ ▦ │ ⛓ ⛓̸ | Box-Generator, Raster-Kopie │ Gruppieren, Gruppierung aufheben |
| **Ausrichten** | ⇤ ↔ ⇥ │ ⤒ ↕ ⤓ | Links, horizontal zentrieren, rechts │ oben, vertikal zentrieren, unten |

**Zeiger- vs. Zeichenmodus:** Das **⬉ Auswählen-Werkzeug** ist der Standard-Modus zum Markieren von Objekten und Verschieben von Eckpunkten. Mit **∠ Linienzug** wechselt man in den Zeichenmodus. Das **aktuell aktive Werkzeug ist in der Leiste hervorgehoben** (blauer Rahmen/Hintergrund). Im Zeichenmodus werden Objekte nicht „angegriffen" — so kann ein Linienzug auch **direkt auf einer anderen Linie oder Ecke** gestartet werden. ESC oder ein Klick auf **⬉** beendet den Zeichenmodus.

### 6.2 📥 Importieren

| Button | Funktion |
|---|---|
| **📐 SVG** | Vektor-SVG importieren (wird in freie Einzelteile zerlegt) |
| **🖼️ Bild** | Foto/Bild laden (öffnet die Foto-Gravur, siehe [10.2](#102-foto-gravur)) |

### 6.3 📋 Objekte & Ebenen

Tabelle aller Objekte. Pro Zeile: **Typ**, **Aktion** (Dropdown: ✂️ Schneiden / 🔥 Gravieren / 📏 Hilfslinie / ❌ Ignorieren) und ein **🗑️ Löschen**-Button.

<img width="324" height="656" alt="image" src="https://github.com/user-attachments/assets/9941d297-904e-4b5f-b7f6-c3250daf7488" />

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

Erzeugt ein Rechteck bzw. einen Kreis im Arbeitsbereich. Größe und Position werden danach mit den Maus-Griffen oder über die **Bemaßungs-Maßzahlen** geändert (Klick auf die angezeigte Maßzahl öffnet ein Eingabefeld). Wird ein Objekt **gedreht**, drehen sich die Maßlinien mit und liegen entlang der gedrehten Kanten.

<img width="670" height="357" alt="image" src="https://github.com/user-attachments/assets/836ce25f-8282-4f04-9300-3e64e07c6d12" />

### 7.2 ✒️ Linienzug (Polylinie)

Klicke nacheinander Punkte, um einen Linienzug zu zeichnen. **ESC** beendet das Zeichnen. Schon der **erste Punkt** rastet magnetisch an anderen Objekten/Ecken ein, und der Linienzug lässt sich **direkt auf einer anderen Linie starten** (siehe Zeiger-/Zeichenmodus in [6.1](#61--werkzeuge)).

- **Winkel-Snapping:** In der Nähe von 45°-Schritten rastet die Linie ein.
- **Magnet-Snapping:** In der Nähe anderer Objekte rastet der Cursor auf Endpunkte (stark, cyan), Kreuzungen (grün) oder Kanten (schwach, orange) ein. **Alt** gedrückt halten deaktiviert den Magneten kurzzeitig.
- **Fluchtlinien-Snap:** Fährst du mit der Maus über einen Eckpunkt, wird dieser als Referenz gemerkt. Setzt du danach einen Punkt in dessen waagerechter oder senkrechter **Flucht**, rastet die passende Achse ein und eine **hellblaue gestrichelte Hilfslinie** zeigt die Ausrichtung. Beim Verlassen des Fluchtbereichs verschwindet sie wieder.
- **Live-Maße beim Zeichnen:** Während du den Endpunkt einer Linie setzt, zeigt ein kleines Label am Cursor **Länge (mm) und Winkel**. Beim **ersten** Segment der Winkel **zur Y-Achse des Arbeitsbereichs** (0° = nach oben, 90° = rechts), bei jedem **weiteren** Segment der **Innenwinkel zur vorherigen Linie** (180° = gerade weiter, 90° = rechter Winkel).
- **Bearbeiten:** *Einfachklick* auf ein Segment/Handle wählt es einzeln (Länge per Maßzahl änderbar, Eckpunkt per Handle verschiebbar). *Doppelklick* wählt den **gesamten** Linienzug zum Verschieben/Drehen/Skalieren. Die Eckpunkt-Handles werden als kleine, ungefüllte Quadrate dargestellt.
- **Eckpunkte verschieben mit Magnet:** Beim Ziehen eines Eckpunkts rastet dieser ebenfalls magnetisch ein — auf andere Objekte **und auf die anderen Eckpunkte/Kanten der eigenen Polylinie**. Dabei zeigt das Label live die Länge(n) der betroffenen Segmente und (bei einem Mittelpunkt) den Winkel zwischen ihnen.
- **Eckpunkte verbinden (verschmelzen):** Lässt du einen Eckpunkt los, während er auf einem anderen Eckpunkt eingerastet ist, werden beide **dauerhaft verbunden**. Verschiebst du danach den gemeinsamen Punkt, folgen **alle** beteiligten Linien (z. B. um zwei Linienzüge zu koppeln oder eine Schleife zu schließen). *Hinweis:* Verbindungen gelten für die laufende Sitzung und werden nicht mit dem Projekt gespeichert.

<img width="240" height="201" alt="image" src="https://github.com/user-attachments/assets/df2e9432-b9cb-4c7c-8fbd-47385653c169" />

### 7.3 T Text

Öffnet den Text-Dialog. Eingabe von Text, Schrifthöhe und einer **TTF/OTF-Schriftart** (Button „📂 Schrift laden"). Der Text wird als **echter Vektor-Pfad** eingefügt (kein Bitmap), direkt laserbar. Eine Live-Vorschau zeigt den Laser-Fahrweg.

<img width="408" height="416" alt="image" src="https://github.com/user-attachments/assets/6e91009e-891e-4cf0-9d01-7011c933b598" />

### 7.4 ★ Formen-Bibliothek

14 parametrische Formen: **Stern, Herz, Trapez, Parallelogramm, Sechseck, Fünfeck, Achteck, Dreieck, Pfeil, Kreuz, Tonne, Zahnrad, Blitz, Stadion**. Form anklicken, Parameter eingeben, *Einfügen*. Die Form landet mittig im sichtbaren Bereich und ist sofort bearbeitbar.

<img width="607" height="412" alt="image" src="https://github.com/user-attachments/assets/f9688e54-528f-4869-819f-7b08ffdbbc05" />

---

## 8. Generatoren

### 8.1 ▣ Box-Generator (Finger-Joint)

Erzeugt fertige Schnittteile für Kästen mit **Finger-/Kerbverbindungen**.

<img width="489" height="657" alt="image" src="https://github.com/user-attachments/assets/506fa42c-8702-4557-8c72-2688c29cdda5" />

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

<img width="369" height="277" alt="image" src="https://github.com/user-attachments/assets/b7aee717-c027-4b61-8ece-61c2b4173475" />

---

## 9. Bearbeiten & Anordnen

### 9.1 ⛓ Gruppieren / ⛓̸ Aufheben

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

<img width="584" height="285" alt="image" src="https://github.com/user-attachments/assets/f1e5cbc1-de64-4167-83d3-cf2f7c464851" />
<img width="632" height="257" alt="image" src="https://github.com/user-attachments/assets/722b7648-359d-4a1d-9b95-ccb6b4eab521" />

---

## 10. Import & Foto-Gravur

### 10.1 SVG-Import

Lädt eine SVG-Datei und zerlegt sie in **freie Einzelteile**, die einzeln bearbeitet und mit Ebenen versehen werden können.

### 10.2 Foto-Gravur

<img width="507" height="695" alt="image" src="https://github.com/user-attachments/assets/f703ecb7-47ab-4119-8cfa-393cb8ef734e" />

<img width="556" height="562" alt="image" src="https://github.com/user-attachments/assets/a57505b8-7061-4b80-b0c4-50584950343a" />

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

<img width="768" height="493" alt="image" src="https://github.com/user-attachments/assets/82e0ee07-b740-404d-8eed-3f7d3a745217" />

Tabelle aller Materialien mit Schnitt- und Gravur-Parametern (Speed/Power/Durchläufe). Pro Zeile:
- **↩ Nutzen** — Parameter in die Hauptfelder übernehmen
- **✏️ Bearbeiten** / **🗑️ Löschen**

**Speicherort:** serverseitig in `materials.json` neben `agent.py`. Dadurch ist die Bibliothek für **alle Clients im Netzwerk** verfügbar (z. B. mehrere Browser am selben Raspberry Pi).

---

## 12. Parameter-Test

Ermittelt die optimalen Laserparameter für ein neues Material — analog zu LightBurn-Testmustern.

<img width="526" height="679" alt="image" src="https://github.com/user-attachments/assets/1a948f1d-2005-4eea-b081-6df80b0c7b73" />

**Ablauf:**
1. In der Materialbibliothek **🧪 Parameter-Test erzeugen**.
2. Typ wählen: **Gravur** (gefüllte Quadrate) oder **Schnitt** (Konturen).
3. Power-/Speed-Bereich, Anzahl Zeilen (Power) × Spalten (Speed), Feldgröße, Durchläufe pro Feld.
4. **🧪 Testmuster erzeugen** → ein Raster wird zentriert im Arbeitsbereich platziert (Beschriftung am Rand, wird nicht gelasert).
5. **▶ Job Lasern** ausführen.
6. Nach dem Lasern erscheint die **Bewertung**: beste Spalte/Reihe eingeben → Speed/Power werden aufgelöst. Bei zu schwachem Ergebnis **➕ Weiteren Durchlauf lasern** (zählt automatisch hoch).
7. Name eingeben → **💾 Als Material speichern** (mit der aufgelaufenen Durchlaufzahl).

<img width="276" height="266" alt="image" src="https://github.com/user-attachments/assets/b09e6058-4efb-408f-baf2-1102ff0e8c98" />

---

## 13. Projekt speichern & laden

**💾 Projekt speichern (.json):** Speichert **alle** Objekte des Arbeitsbereichs — inklusive importierter **Bilder** (mit Filtern/Clip) und **SVG-Grafiken**, Ebenen-Zuordnung und Arbeitsbereichsgröße. In Chromium/Edge öffnet sich ein **Datei-Dialog zur Speicherort-Wahl** (sonst klassischer Download).

**Projekt laden:** Über den Datei-Dialog eine `.json` wählen. Nur die Benutzerobjekte werden ersetzt; Hilfsobjekte (Raster, Ursprung) bleiben erhalten. Bildfilter werden neu angewendet, die Arbeitsbereichsgröße wird wiederhergestellt. Alte Projektdateien werden ebenfalls geladen.

> ⚠️ **Hinweis:** Linienzug-Bearbeitungsgriffe werden nicht mitgespeichert — geladene Polylinien sind sichtbar und verschiebbar, für punktgenaues Nachbearbeiten ggf. neu zeichnen.

---

## 14. Mehrsprachigkeit

Über das 🌐-Dropdown oben im Arbeitsbereich: **Deutsch, English, Español, 中文**. Die Wahl wird im Browser gespeichert (`localStorage`) und beim nächsten Start automatisch wieder eingestellt. Übersetzt sind die Hauptoberfläche und die Dialoge.

<img width="116" height="145" alt="image" src="https://github.com/user-attachments/assets/a6b57737-7c22-4036-b425-6b9e271fae7c" />

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
| **↑ / ↓** (G-Code-Eingabe) | Durch die Befehls-Historie blättern |

---

## 18. Kamera, Mobil-Bedienung & Wartung

Diese Funktionen sind vor allem für den Betrieb auf einem **Raspberry Pi** gedacht, der fest im Lasercutter verbaut ist.

### 18.1 📷 Kamera-Hintergrundbild

Eine Kamera über dem Arbeitsbereich liefert ein **halbtransparentes Hintergrundbild**, um Objekte passgenau auf ein bereits liegendes Werkstück zu legen. Die Bedienelemente liegen in der **oberen Leiste** des Arbeitsbereichs:

- **Quelle:** **Pi-Kamera (CSI)** über `picamera2` oder **USB-Kamera** (UVC) über OpenCV.
- **📷** nimmt ein Bild auf und legt es **gesperrt** hinter die Objekte (wird nie mitgelasert), **Transparenz**-Regler, **✕** entfernt es.

### 18.2 ⌖ Kamera-Kalibrierung

Damit das Kamerabild **maßgenau** auf dem Bett liegt (Perspektive **und** Weitwinkel-Verzeichnung), kalibrierst du einmalig über den **⌖-Button**:

1. **Physische Marker** an die **8 Positionen** legen: 4 Ecken + 4 Kantenmitten.
2. **Foto aufnehmen** und die Punkte in fester Reihenfolge anklicken (erst 4 Ecken, dann 4 Mitten – gelbe Fadenkreuze helfen).
3. **Speichern** → das Backend entzerrt per **Thin-Plate-Spline** und wendet die Kalibrierung automatisch auf jedes weitere Bild an (gespeichert in `camera_calib.json`).

### 18.3 ⚲ Kantenerkennung → Vektor

Form auf ein Blatt zeichnen / Objekt auflegen, Button **⚲** (Werkzeuge-Panel, neben dem Box-Generator):

1. **📷 Aufnehmen & erkennen** – das (ggf. entzerrte) Bild wird per **Canny + Konturensuche** analysiert, die Vorschau zeigt die Kanten grün.
2. **Live-Regler** (Kanten-Schwellen, Glättung, Min.-Länge, Vereinfachung) anpassen.
3. **Als Vektor übernehmen** → die Konturen werden als **bearbeitbare Schnitt-Objekte** in den Arbeitsbereich eingefügt. Am genauesten mit vorheriger Kalibrierung.

### 18.4 Automatische Verbindung (Raspberry Pi)

Läuft die App auf **Linux/Raspberry Pi** und ist ein **MKS DLC32** per USB angeschlossen, **verbindet sich die App automatisch** damit, sobald die Oberfläche geöffnet wird (Erkennung über die USB-Seriell-Kennung CH340/CH9102/CP2102). So kann das Display am Laser entfallen. Trennst du manuell, wird nicht automatisch wieder verbunden.

### 18.5 ⟳ Software-Update über die Web-UI

Der Button **„⟳ Software aktualisieren"** (Panel ⚙️ Maschine) holt die neueste Version per `git pull` und startet den Dienst neu — **ohne sich am Pi anzumelden**. Voraussetzung ist der systemd-Dienst mit `Restart=always` (im Installer enthalten); bestehende Installationen einmalig per Installer-Neulauf aktualisieren. Ist kein Auto-Neustart möglich, wird das Update geholt und ein manueller Neustart gemeldet (der Server bleibt also nie unten).

### 18.6 📱 Mobile Bedienseite & PWA

Unter **`http://<Pi-IP>:8080/mobile.html`** gibt es eine fingerfreundliche Touch-Oberfläche zum **Positionieren des Kopfes** (Jog-Pad mit Schrittweiten), **Home/Nullpunkt/Unlock**, **Pointer-Laser** und **Pumpe** schalten sowie **Live-Status** — ideal, um den Laser **vor Ort per Handy** ohne Display zu bedienen (Handy und Pi im selben WLAN).

- **„Zum Startbildschirm hinzufügen"** (Android/iOS) öffnet die Seite als **App im Vollbild** (PWA-Manifest + Icon) — kein App-Store nötig.
- Ein Link **„📱 Mobile Bedienseite"** findet sich auch im Maschinen-Panel der Hauptoberfläche.

---

## 19. Fehlerbehebung

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
