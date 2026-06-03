# 🔥 TheBurner — Manual (English)

> Complete feature and process documentation for the web-based laser cutter control.
> **Deutsche Version:** [../de/HANDBUCH.md](../de/HANDBUCH.md)

---

## Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
2. [Installation & Start](#2-installation--start)
3. [Interface Layout](#3-interface-layout)
4. [Left Sidebar — Machine & Control](#4-left-sidebar--machine--control)
5. [Workspace (Canvas)](#5-workspace-canvas)
6. [Right Sidebar — Tools & Layers](#6-right-sidebar--tools--layers)
7. [Drawing Tools in Detail](#7-drawing-tools-in-detail)
8. [Generators](#8-generators)
9. [Edit & Arrange](#9-edit--arrange)
10. [Import & Photo Engraving](#10-import--photo-engraving)
11. [Layers & Materials](#11-layers--materials)
12. [Parameter Test](#12-parameter-test)
13. [Save & Load Project](#13-save--load-project)
14. [Multi-language](#14-multi-language)
15. [Process Flow (Standard Workflow)](#15-process-flow-standard-workflow)
16. [Technical: G-code Generation](#16-technical-g-code-generation)
17. [Keyboard Shortcuts](#17-keyboard-shortcuts)
18. [Troubleshooting](#18-troubleshooting)

---

## 1. Overview & Architecture

TheBurner consists of **two parts**:

| Part | File | Role |
|---|---|---|
| **Backend** | `agent.py` | Python server: serves the UI, talks to the laser, generates G-code, stores materials |
| **Frontend** | `index.html` | Browser UI based on [Fabric.js](http://fabricjs.com/) for drawing and operation |

```
┌────────────────────────┐        WebSocket :8765        ┌────────────────────────┐
│   Browser (index.html) │  ◄──────── Status ──────────  │   agent.py (Python)    │
│                        │  ────────  Commands ───────►  │                        │
│   Fabric.js canvas     │                               │  WebSocket server      │
│   G-code for photo/    │        HTTP :8080             │  HTTP server (UI)      │
│   raster in frontend   │  ◄──── index.html ────────    │  G-code generation     │
└────────────────────────┘                               │  materials.json        │
                                                          └───────────┬────────────┘
                                            USB/COM  or  Wi-Fi (HTTP :8848 + WS :8849)
                                                                      ▼
                                                          ┌────────────────────────┐
                                                          │   GRBL laser cutter    │
                                                          └────────────────────────┘
```

**Concept:** The system is hosted on a small computer (e.g. a Raspberry Pi) **right at the laser cutter**. Anyone on the network simply opens the web page — the material library is then shared by everyone. Running it on a Windows/Linux machine works the same locally.

**Ports:**
- `8080` — HTTP (serves `index.html`)
- `8765` — WebSocket (browser ↔ agent.py)
- `8848`/`8849` — HTTP/WebSocket to the network laser (Wi-Fi mode only)

---

## 2. Installation & Start

```bash
pip install pyserial websockets websocket-client svgelements
python agent.py
```

On start the browser opens automatically at `http://localhost:8080`. On the network: `http://<host-IP>:8080`.

> 📷 **Screenshot:** `docs/images/startup.png` — console after start showing "Agent connected".

---

## 3. Interface Layout

The interface has three areas: **left sidebar** (machine/control), **workspace** (center) and **right sidebar** (tools/layers).

```
┌──────────────┬──────────────────────────────────┬──────────────────┐
│  ⚙️ Machine   │  Workspace   [🌐][⛶ 🔲 1:1][🎯 📍]   │  🛠️ Tools         │
│              │  ┌────────────────────────────┐  │  ▭ ◯ ✒️ T ⭐     │
│  🎛️ Job       │  │      Ruler X              │  │  📦 ▦ │ 🔗 ⛓️‍💥   │
│  Control      │  │ R │                       │  │  ⇤ ↔ ⇥ │ ⤒ ↕ ⤓  │
│              │  │ u │   Canvas               │  │  📥 Import       │
│  🕹️ Control   │  │ l │   (mm grid)           │  │  📐 SVG  🖼️ Image │
│  & Console    │  │ e │                       │  │                  │
│  [Log]        │  │ r │                       │  │  📋 Objects &    │
│              │  │ Y │                       │  │     Layers       │
│              │  └────────────────────────────┘  │  [table]         │
│              │                                  │  ⚙️ Layer params  │
│              │                                  │  💾 Project       │
└──────────────┴──────────────────────────────────┴──────────────────┘
```

> 📷 **Screenshot:** `docs/images/overview.png` — full interface.

**Collapse/expand panels:** Each panel heading (e.g. "🛠️ Tools") has a small arrow **▾/▸**. Clicking it rolls the panel up so only the heading remains. When screen height is low, the whole sidebar scrolls.

**Show/hide sidebars:** The arrow buttons `◀`/`▶` at the edges hide the entire left or right sidebar to make more room for the canvas.

---

## 4. Left Sidebar — Machine & Control

### 4.1 ⚙️ Machine

> 📷 **Screenshot:** `docs/images/panel-machine.png`

| Element | Function |
|---|---|
| 🔴/🟢 status icon | Laser connection state |
| **USB (COM) / Wi-Fi** | Choose connection type |
| **Port + Baud** (USB) | COM port (`🔄` scans available ports) and baud rate (default 115200) |
| **IP + Port** (Wi-Fi) | IP address and port of the network controller |
| **🔌 Connect / 🛑 Disconnect** | Open/close the connection |
| **📡 Data** | Reads machine settings via `$$` (e.g. work area `$130/$131`, max power `$30`, laser mode `$32`) and applies them automatically |
| **📐 Work area** | Width/height in mm — defines the canvas (button `✔️` applies the size) |

### 4.2 🎛️ Job Control

> 📷 **Screenshot:** `docs/images/panel-job.png`

| Element | Function |
|---|---|
| **▶ Run Job** | Builds the G-code from all objects and sends it to the laser. Turns the pump on first (`M8`). |
| **⏹ STOP / ABORT** | Immediately aborts the running job (GRBL soft reset). The pump keeps running for ~10 s afterwards. |
| **Unlock** | Clears a GRBL alarm (`$X`). |
| Progress bar | Shows processing progress in %. |

### 4.3 🕹️ Control & Console

> 📷 **Screenshot:** `docs/images/panel-control.png`

| Element | Function |
|---|---|
| G-code input + `✉️` | Send individual G-code commands directly |
| **Home** | Homing cycle (`$H`) |
| **X0/Y0** | Set current position as origin |
| **Pump ON/OFF** | Toggle extraction/air manually (`M8`/`M9`) |
| **🎯 Graphical Jog Controller** | Opens a round control to jog the axes by mouse click |
| **[Log]** | Console output (commands, responses, errors) |

---

## 5. Workspace (Canvas)

The canvas shows a **mm grid** with rulers. The top bar contains:

| Element | Function |
|---|---|
| 🌐 language dropdown | German / English / Spanish / Chinese (see [Multi-language](#14-multi-language)) |
| **⛶** | Fit all objects (zoom to content) |
| **🔲** | Center on the work area |
| **1:1** | 100% view |
| **🎯** | Move the laser to a clicked point |
| **📍** | Set the origin by clicking |

**Navigation:** mouse wheel = zoom, mouse drag = select/move. The purple marker 📍 shows the origin, the red crosshair the current laser position.

> 📷 **Screenshot:** `docs/images/workspace-toolbar.png` — workspace top bar.

---

## 6. Right Sidebar — Tools & Layers

### 6.1 🛠️ Tools

> 📷 **Screenshot:** `docs/images/panel-tools.png`

The tools are grouped into labeled rows:

| Row | Buttons | Function |
|---|---|---|
| **Draw** | ▭ ◯ ✒️ T ⭐ | Rectangle, circle, polyline, text, shape library |
| **Generators / Grouping** | 📦 ▦ │ 🔗 ⛓️‍💥 | Box generator, grid copy │ group, ungroup |
| **Align** | ⇤ ↔ ⇥ │ ⤒ ↕ ⤓ | Left, center horizontally, right │ top, center vertically, bottom |

### 6.2 📥 Import

| Button | Function |
|---|---|
| **📐 SVG** | Import vector SVG (split into free parts) |
| **🖼️ Image** | Load photo/image (opens photo engraving, see [10.2](#102-photo-engraving)) |

### 6.3 📋 Objects & Layers

Table of all objects. Per row: **Type**, **Action** (dropdown: ✂️ Cut / 🔥 Engrave / 📏 Guide / ❌ Ignore) and a **🗑️ Delete** button.

> 📷 **Screenshot:** `docs/images/panel-objects.png`

### 6.4 ⚙️ Layer Parameters

| Element | Function |
|---|---|
| **📚 Material library** | Opens material management (see [11.2](#112-material-library)) |
| **Processing order** | Engrave first / Cut first / order as in table |
| **✂️ Cut** | Speed, power (%), passes for the cut layer |
| **🔥 Engrave** | Mode (outline / fill / fill+outline), line spacing, speed, power, passes |

### 6.5 💾 Project

Save/load the complete project (see [13](#13-save--load-project)). Located at the very bottom of the right sidebar.

---

## 7. Drawing Tools in Detail

### 7.1 ▭ Rectangle & ◯ Circle

Creates a rectangle or circle on the canvas. Size and position are then changed with the mouse handles or via the **dimension labels** (clicking a displayed dimension opens an input field).

> 📷 **Screenshot:** `docs/images/draw-rect.png` — rectangle with dimensions.

### 7.2 ✒️ Polyline

Click points one after another to draw a polyline. **ESC** finishes.

- **Angle snapping:** snaps to 45° steps when close.
- **Magnet snapping:** near other objects the cursor snaps to endpoints (strong, cyan), intersections (green) or edges (weak, orange). Hold **Alt** to temporarily disable the magnet.
- **Editing:** *single click* on a segment/handle selects it individually (length editable via dimension label, vertex movable via blue handle). *Double click* selects the **entire** polyline for move/rotate/scale.

> 📷 **Screenshot:** `docs/images/polyline-snap.png` — magnet snapping while drawing.

### 7.3 T Text

Opens the text dialog. Enter text, font height and a **TTF/OTF font** (button "📂 Load font"). The text is inserted as a **true vector path** (no bitmap), ready to laser. A live preview shows the laser path.

> 📷 **Screenshot:** `docs/images/dialog-text.png`

### 7.4 ⭐ Shape Library

14 parametric shapes: **star, heart, trapezoid, parallelogram, hexagon, pentagon, octagon, triangle, arrow, cross, barrel, gear, lightning, stadium**. Click a shape, enter parameters, *Insert*. The shape appears centered in the visible area and is immediately editable.

> 📷 **Screenshot:** `docs/images/dialog-shapes.png`

---

## 8. Generators

### 8.1 📦 Box Generator (Finger Joint)

Creates ready-to-cut parts for boxes with **finger/notch joints**.

> 📷 **Screenshot:** `docs/images/dialog-box.png`

**Box types:**

| Type | Description |
|---|---|
| **Rectangle** | Classic box |
| **Trapezoid** | Symmetric taper (hopper/planter) — parameter "top width" |
| **Lectern** | One-sided slope — one wall vertical, one slanted |
| **Parallelogram** | Sheared in X — parameter "top offset" |

**Parameters:** width, depth, height, material thickness, finger width (or fixed "fingers per edge"), part spacing, lid yes/no, group all parts.

**How it works:**
- Tab/slot system: wall fingers protrude and fit into slots of floor/lid and neighboring walls. Corners are always flush (no "dead corners").
- For **trapezoid/parallelogram/lectern**, the fingers of slanted side walls are automatically made deeper (factor `slant/H`) so they engage cleanly despite the angle.
- Dimensions are **outer dimensions**.

### 8.2 ▦ Grid Copy (Array)

Duplicates the current selection in a grid: columns/rows and X/Y spacing.

> 📷 **Screenshot:** `docs/images/dialog-array.png`

---

## 9. Edit & Arrange

### 9.1 🔗 Group / ⛓️‍💥 Ungroup

Combine multiple objects into a group or split them again. Overlapping shapes can be welded into a **compound path** on grouping (true holes via even-odd rule — e.g. for donut shapes).

### 9.2 Align

Select multiple objects (the one clicked **first** is the reference), then choose an align function:

| Button | Function |
|---|---|
| ⇤ / ⇥ | Align left / right |
| ↔ | Center horizontally (same center X) |
| ⤒ / ⤓ | Align top / bottom |
| ↕ | Center vertically (same center Y) |

> 💡 For a defined reference, click the objects **one by one with Shift** (not via a rubber-band box).

> 📷 **Screenshot:** `docs/images/align.png` — before/after.

---

## 10. Import & Photo Engraving

### 10.1 SVG Import

Loads an SVG file and splits it into **free individual parts** that can be edited and assigned layers separately.

### 10.2 Photo Engraving

> 📷 **Screenshot:** `docs/images/dialog-photo.png`

Load a photo via **🖼️ Image** → it is automatically converted to **grayscale** and centered. Select the photo + click **🖼️** again to open the dialog.

**Image adjustment:** brightness, contrast (live preview), invert.

**Crop / fit into shape:** Select the photo **and** a closed shape (rectangle/polygon/polyline) together → "✂️ Fit into shape". Everything outside the shape is not engraved. For pure edge cropping use a rectangle. "Remove clip" undoes it.

**Engraving methods:**

| Method | Description |
|---|---|
| **Grayscale power** | Dark pixels → more power (min…max). Pixels brighter than the white threshold are skipped. |
| **Dithering (B/W)** | Floyd-Steinberg → laser on/off per pixel, constant power. Often the best photo result on wood/paper. |

**Further parameters:** resolution (mm/pixel), speed, power min/max, white threshold. The raster G-code is generated line by line in the frontend (rotation, scaling and clip are handled correctly).

---

## 11. Layers & Materials

### 11.1 Layers (laser mode per object)

In the **Objects & Layers** table, the dropdown sets per object:

| Mode | Meaning |
|---|---|
| ✂️ **Cut** | Vector cut along the contour (red) |
| 🔥 **Engrave** | Outline and/or area fill (blue) |
| 📏 **Guide** | Drawn dashed, **not lasered** — for alignment only. Also acts as a magnet snap target. |
| ❌ **Ignore** | Stays on the canvas but is not lasered |

The parameters (speed/power/passes) apply globally per layer and are set in the **⚙️ Layer Parameters** section.

### 11.2 Material Library

> 📷 **Screenshot:** `docs/images/dialog-material.png`

Table of all materials with cut and engrave parameters (speed/power/passes). Per row:
- **↩ Use** — apply parameters to the main fields
- **✏️ Edit** / **🗑️ Delete**

**Storage:** server-side in `materials.json` next to `agent.py`. This makes the library available to **all clients on the network** (e.g. multiple browsers on the same Raspberry Pi).

---

## 12. Parameter Test

Determines the optimal laser parameters for a new material — similar to LightBurn test patterns.

> 📷 **Screenshot:** `docs/images/dialog-mattest.png`

**Procedure:**
1. In the material library, **🧪 Create parameter test**.
2. Choose type: **Engrave** (filled squares) or **Cut** (outlines).
3. Power/speed range, number of rows (power) × columns (speed), cell size, passes per cell.
4. **🧪 Create test pattern** → a grid is placed centered in the work area (edge labels are not lasered).
5. Run **▶ Run Job**.
6. After lasering, the **evaluation** appears: enter the best column/row → speed/power are resolved. If the result is too weak, **➕ Laser another pass** (counts up automatically).
7. Enter a name → **💾 Save as material** (with the accumulated pass count).

> 📷 **Screenshot:** `docs/images/dialog-eval.png` — evaluation dialog.

---

## 13. Save & Load Project

**💾 Save project (.json):** Saves **all** workspace objects — including imported **images** (with filters/clip) and **SVG** graphics, layer assignment and work-area size. In Chromium/Edge a **file dialog to choose the location** opens (otherwise a classic download).

**Load project:** Choose a `.json` via the file dialog. Only the user objects are replaced; helper objects (grid, origin) stay intact. Image filters are reapplied, the work-area size is restored. Old project files load as well.

> ⚠️ **Note:** Polyline editing handles are not saved — loaded polylines are visible and movable; for point-precise re-editing, redraw if needed.

---

## 14. Multi-language

Via the 🌐 dropdown at the top of the workspace: **German, English, Spanish, Chinese**. The choice is stored in the browser (`localStorage`) and restored automatically on the next start. The main UI and the dialogs are translated.

> 📷 **Screenshot:** `docs/images/language.png` — language dropdown.

---

## 15. Process Flow (Standard Workflow)

```
┌─────────────────────┐
│ 1. Connect          │  ⚙️ Machine → USB/Wi-Fi → 🔌 Connect → 📡 Data
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. Work area        │  Set width/height (or automatically from $130/$131)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. Origin           │  Jog laser (🎯), set position as X0/Y0 or 📍
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 4. Create objects   │  Draw / import / box / photo / text …
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 5. Layers & params  │  Choose cut/engrave per object,
│                     │  apply material from library (📚)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ (optional) Material │  🧪 Parameter test for an unknown material
│  test               │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 6. Run Job          │  ▶ → Pump ON (M8) → engrave first, then cut
│                     │  → progress → pump 10 s after-run
└─────────────────────┘
```

**Processing order:** the default is "engrave, then cut" — sensible, because after cutting the workpiece might come loose.

---

## 16. Technical: G-code Generation

The job is sent to `agent.py` as a "mixed job". The backend builds a G-code list with header `M8 G21 G90 M5`:

| Job item | Generation |
|---|---|
| **Vector** (cut/outline) | `generate_gcode_from_svg()` — follows the contour, curves are split into short line segments |
| **Raster** (engrave fill, material test) | `generate_raster_gcode()` — line-by-line fill |
| **raw** (photo) | Pre-generated lines from the frontend (grayscale/dithering) |

- **Power:** percent → S value via the machine max power (`$30`). 100% ≙ `S1000` at `$30=1000`.
- **Passes:** the object is queued multiple times.
- **Flow control:** for **network lasers** the server waits for `ok` after each command (prevents "modal group violation" caused by sending too fast over Wi-Fi). For USB, the GRBL buffer is filled via byte counting.
- **Pump:** `M8` at the start, `M9` with a ~10 s after-run on job end/abort.

---

## 17. Keyboard Shortcuts

| Key | Function |
|---|---|
| **ESC** | Finish polyline drawing |
| **Del / Delete** | Delete selected objects |
| **Alt** (hold) | Temporarily disable magnet snapping while drawing |
| **Double click** (polyline) | Select the entire polyline |

---

## 18. Troubleshooting

| Problem | Cause / Solution |
|---|---|
| **`error: Gcode modal group violation`** | Usually sending too fast over Wi-Fi (solved by `ok` flow control) **or** a stored GRBL startup block. Check with `$$`, clear `$N0=` and `$N1=` if needed. |
| **`error: Expected GCode command letter`** | A `$` command was sent to the G-code parser — `$$`/`$H` etc. only work via the proper interface depending on the controller. |
| **Pump keeps running after a test job** | The pass counter increases on every "Run Job" while test cells are on the canvas — delete the test cells before a normal job. |
| **Material library empty on another device** | `materials.json` lives on the host. With its own instance, each device has its own file. |
| **No "choose location" dialog** | Only Chromium/Edge support the File System Access API; otherwise a classic download. |
| **`$30` ≠ 1000** | Then 100% corresponds to a different S value; the system adopts `$30` automatically as max power. |

---

> 📷 **Note on screenshots:** Places marked "📷 Screenshot" reference images in `docs/images/`. A guide on which captures make sense is in [docs/images/README.md](../images/README.md).
