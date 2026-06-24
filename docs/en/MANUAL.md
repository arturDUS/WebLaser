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
18. [Camera, Mobile Control & Maintenance](#18-camera-mobile-control--maintenance)
19. [Troubleshooting](#19-troubleshooting)

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

<img width="2218" height="1367" alt="image" src="https://github.com/user-attachments/assets/374ef1c0-805c-476e-a56a-7c069fd1bae1" />

**Collapse/expand panels:** Each panel heading (e.g. "🛠️ Tools") has a small arrow **▾/▸**. Clicking it rolls the panel up so only the heading remains. When screen height is low, the whole sidebar scrolls.

**Show/hide sidebars:** The arrow buttons `◀`/`▶` at the edges hide the entire left or right sidebar to make more room for the canvas.

---

## 4. Left Sidebar — Machine & Control

### 4.1 ⚙️ Machine

<img width="322" height="315" alt="image" src="https://github.com/user-attachments/assets/9c4f2d5f-fef3-4dcf-8bdf-18ff35a3d375" />

| Element | Function |
|---|---|
| 🔴/🟢 status icon | Laser connection state |
| **USB (COM) / Wi-Fi** | Choose connection type |
| **Port + Baud** (USB) | COM port (`🔄` scans available ports) and baud rate (default 115200) |
| **IP + Port** (Wi-Fi) | IP address and port of the network controller |
| **Mode** (Wi-Fi) | **Auto-detect** (recommended), **Telnet** (FluidNC, port 23) or **WebUI** (ESP3D / Grbl_ESP32). With "Auto" the server tries Telnet first and falls back to WebUI. |
| **🔌 Connect / 🛑 Disconnect** | Open/close the connection |
| **📡 Data** | Reads machine settings via `$$` (e.g. work area `$130/$131`, max power `$30`, laser mode `$32`) and applies them automatically |

> 📐 **Work-area size:** the width/height (mm) input fields are now in the **top bar of the workspace** (see [section 5](#5-workspace-canvas)).

> 🔎 **Firmware detection:** On connect the system automatically detects the firmware (**FluidNC** or **Grbl/Grbl_ESP32**) and the transport, and reports it in the log (e.g. "Connected: FluidNC via Telnet"). FluidNC v4 over Wi-Fi is addressed via **Telnet**.

### 4.2 🎛️ Job Control

<img width="323" height="183" alt="image" src="https://github.com/user-attachments/assets/bf8c4a51-b1a5-4c51-befc-e70e46203fb9" />

| Element | Function |
|---|---|
| **▶ Run Job** | Builds the G-code from all objects and sends it to the laser. Turns the pump on first (`M8`). |
| **⏹ STOP / ABORT** | Immediately aborts the running job (GRBL soft reset). The pump keeps running for ~10 s afterwards. |
| **Unlock** | Clears a GRBL alarm (`$X`). |
| Progress bar | Shows processing progress in %. |
| **📌 Relative mode** (toggle) | Lasers the job **relative to the current, manually positioned laser head** instead of at absolute coordinates (see below). |

#### 4.2.1 📌 Relative Mode

Instead of lasering an object at fixed machine coordinates, the job can be lasered **relative** to the spot you have just moved the laser head to. Ideal for placing a motif precisely onto a workpiece that is already in place.

1. **Turn on the "Relative mode" toggle.**
2. **📌 Set reference point:** click in the work area — the cursor **snaps magnetically to corners** (or click freely). An **orange diamond marker** shows the point; its value appears in the status line. *Without* a reference point, "Run Job" refuses to start.
3. **🔦 Pointer laser** (optional): turn on the laser at **minimal power** as a visible dot and move the head manually to where the reference point should sit. The pointer laser turns off automatically **on the next click** or **after 2 minutes**.
4. **▶ Run Job** — the object is lasered so that the reference point lands **exactly at the current head position**.

> ⚙️ **Technical:** in relative mode the reference point becomes the coordinate origin; the backend emits `G92 X0 Y0` at the start (current position = 0/0) and `G92.1` at the end (clear the offset). Your normal zero (`X0/Y0` button, `G10 L20`) stays **untouched**.
>
> 🔦 **Pointer laser:** with laser mode active (`$32=1`) the laser will not fire while stationary — therefore `$32` is briefly set to `0` and restored on switch-off. Power ≈ 1 % of `$30`.

### 4.3 🕹️ Control & Console

<img width="321" height="768" alt="image" src="https://github.com/user-attachments/assets/cbc98bf1-17f1-439f-96ed-c1ea0b4ef5ae" />

| Element | Function |
|---|---|
| G-code input + `✉️` | Send individual G-code commands directly. **Terminal-style command history:** use **↑/↓** to scroll through recently sent commands. The history survives a program restart (`localStorage`, max. 50 entries). |
| **Home** | Homing cycle (`$H`) |
| **X0/Y0** | Set current position as origin |
| **Pump ON/OFF** | Toggle extraction/air manually (`M8`/`M9`) |
| **🎯 Graphical Jog Controller** | Opens a round control to jog the axes by mouse click |
| **[Log]** | Console output (commands, responses, errors) |

<img width="406" height="499" alt="image" src="https://github.com/user-attachments/assets/71a49623-fc1b-4061-aa7d-d092aa35159f" />

---

## 5. Workspace (Canvas)

The canvas shows a **mm grid** with rulers. The top bar contains:

| Element | Function |
|---|---|
| **📐 Width × Height + ✔️** | Set the **work-area size** in mm (button `✔️` applies it) — moved here from the machine panel |
| 🌐 language dropdown | German / English / Spanish / Chinese (see [Multi-language](#14-multi-language)) |
| **⛶** | Fit all objects (zoom to content) |
| **🔲** | Center on the work area |
| **1:1** | 100% view |
| **🎯** | Move the laser to a clicked point |
| **📍** | Set the origin by clicking |

**Navigation:** mouse wheel = zoom, mouse drag = select/move. The purple marker 📍 shows the origin, the red crosshair the current laser position.

> ⚠️ **Laser-radiation warning:** while a job is running (or the pointer laser is active) a clearly visible warning floats over the top of the workspace.

<img width="1489" height="46" alt="image" src="https://github.com/user-attachments/assets/f34e3e27-8aad-4c5f-ad5d-6429de5869e0" />
<img width="1486" height="110" alt="image" src="https://github.com/user-attachments/assets/4f40818b-ff59-415b-b4c6-085e59f5ed55" />

---

## 6. Right Sidebar — Tools & Layers

### 6.1 🛠️ Tools

<img width="320" height="338" alt="image" src="https://github.com/user-attachments/assets/74f286c7-d6c7-4c30-8da9-eb9b644d8344" />

The tools are grouped into labeled rows (all icons are monochrome/single-color):

| Row | Buttons | Function |
|---|---|---|
| **Draw** | ⬉ │ ▭ ◯ ∠ T ★ | **Select/move** │ rectangle, circle, polyline, text, shape library |
| **Generators / Grouping** | ▣ ▦ │ ⛓ ⛓̸ | Box generator, grid copy │ group, ungroup |
| **Align** | ⇤ ↔ ⇥ │ ⤒ ↕ ⤓ | Left, center horizontally, right │ top, center vertically, bottom |

**Pointer vs. draw mode:** the **⬉ Select tool** is the default mode for selecting objects and moving vertices. **∠ Polyline** switches to draw mode. The **currently active tool is highlighted** in the toolbar (blue border/background). In draw mode objects are not "grabbed", so a polyline can be started **directly on another line or corner**. ESC or a click on **⬉** ends draw mode.

### 6.2 📥 Import

| Button | Function |
|---|---|
| **📐 SVG** | Import vector SVG (split into free parts) |
| **🖼️ Image** | Load photo/image (opens photo engraving, see [10.2](#102-photo-engraving)) |

### 6.3 📋 Objects & Layers

Table of all objects. Per row: **Type**, **Action** (dropdown: ✂️ Cut / 🔥 Engrave / 📏 Guide / ❌ Ignore) and a **🗑️ Delete** button.

<img width="323" height="772" alt="image" src="https://github.com/user-attachments/assets/72caf641-78a8-4706-b2d6-615805254336" />

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

Creates a rectangle or circle on the canvas. Size and position are then changed with the mouse handles or via the **dimension labels** (clicking a displayed dimension opens an input field). When an object is **rotated**, the dimension lines rotate with it and run along the rotated edges.

<img width="653" height="339" alt="image" src="https://github.com/user-attachments/assets/56e50461-ca31-4894-854a-97456539cede" />

### 7.2 ✒️ Polyline

Click points one after another to draw a polyline. **ESC** finishes. Even the **first point** snaps magnetically to other objects/corners, and the polyline can be **started directly on another line** (see pointer/draw mode in [6.1](#61--tools)).

- **Angle snapping:** snaps to 45° steps when close.
- **Magnet snapping:** near other objects the cursor snaps to endpoints (strong, cyan), intersections (green) or edges (weak, orange). Hold **Alt** to temporarily disable the magnet.
- **Alignment-line snap:** hovering over a corner remembers it as a reference. When you then place a point in its horizontal or vertical **alignment**, that axis snaps and a **light-blue dashed guide line** shows the alignment. It disappears when you leave the alignment zone.
- **Live dimensions while drawing:** while placing a line's end point, a small label at the cursor shows **length (mm) and angle**. For the **first** segment the angle is **relative to the work-area Y axis** (0° = up, 90° = right); for every **further** segment the **interior angle to the previous line** (180° = straight on, 90° = right angle).
- **Editing:** *single click* on a segment/handle selects it individually (length editable via dimension label, vertex movable via handle). *Double click* selects the **entire** polyline for move/rotate/scale. The vertex handles are drawn as small, unfilled squares.
- **Move vertices with magnet:** dragging a vertex also snaps magnetically — to other objects **and to the other vertices/edges of the same polyline**. While dragging, the label shows the length(s) of the affected segments live and (for a middle vertex) the angle between them.
- **Connect (merge) vertices:** if you release a vertex while it is snapped onto another vertex, the two are **permanently linked**. Moving the shared point afterwards moves **all** affected lines (e.g. to couple two polylines or close a loop). *Note:* links apply to the current session and are not saved with the project.

<img width="305" height="246" alt="image" src="https://github.com/user-attachments/assets/0c9629c7-ba8f-4952-a89e-edc0c6cc9335" />

### 7.3 T Text

Opens the text dialog. Enter text, font height and a **TTF/OTF font** (button "📂 Load font"). The text is inserted as a **true vector path** (no bitmap), ready to laser. A live preview shows the laser path.

<img width="405" height="415" alt="image" src="https://github.com/user-attachments/assets/158db16e-7675-4559-a180-93927951fb23" />

### 7.4 ★ Shape Library

14 parametric shapes: **star, heart, trapezoid, parallelogram, hexagon, pentagon, octagon, triangle, arrow, cross, barrel, gear, lightning, stadium**. Click a shape, enter parameters, *Insert*. The shape appears centered in the visible area and is immediately editable.

<img width="606" height="413" alt="image" src="https://github.com/user-attachments/assets/8220430b-0928-442e-b7d6-c2abef1c1772" />

---

## 8. Generators

### 8.1 ▣ Box Generator (Finger Joint)

Creates ready-to-cut parts for boxes with **finger/notch joints**.

<img width="487" height="660" alt="image" src="https://github.com/user-attachments/assets/af261e83-f060-43fc-9b87-1ad1332aa294" />

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

<img width="462" height="600" alt="image" src="https://github.com/user-attachments/assets/f5fe886e-7ae8-4daa-b43a-c62ab99757cd" />

---

## 9. Edit & Arrange

### 9.1 ⛓ Group / ⛓̸ Ungroup

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

<img width="690" height="384" alt="image" src="https://github.com/user-attachments/assets/a73917bd-961c-4c2d-bfba-bed56b86300a" />
<img width="715" height="260" alt="image" src="https://github.com/user-attachments/assets/06d604fc-cdb7-4ad6-bc3a-bb2176d15775" />

---

## 10. Import & Photo Engraving

### 10.1 SVG Import

Loads an SVG file and splits it into **free individual parts** that can be edited and assigned layers separately.

### 10.2 Photo Engraving

<img width="505" height="710" alt="image" src="https://github.com/user-attachments/assets/bf03efa2-4cf7-4f11-b95c-e6121fd68638" />

Load a photo via **🖼️ Image** → it is automatically converted to **grayscale** and centered. Select the photo + click **🖼️** again to open the dialog.

**Image adjustment:** brightness, contrast (live preview), invert.

**Crop / fit into shape:** Select the photo **and** a closed shape (rectangle/polygon/polyline) together → "✂️ Fit into shape". Everything outside the shape is not engraved. For pure edge cropping use a rectangle. "Remove clip" undoes it.

**Engraving methods:**

| Method | Description |
|---|---|
| **Grayscale power** | Dark pixels → more power (min…max). Pixels brighter than the white threshold are skipped. |
| **Dithering (B/W)** | Floyd-Steinberg → laser on/off per pixel, constant power. Often the best photo result on wood/paper. |

**Further parameters:** resolution (mm/pixel), speed, power min/max, white threshold. The raster G-code is generated line by line in the frontend (rotation, scaling and clip are handled correctly).
<img width="620" height="626" alt="image" src="https://github.com/user-attachments/assets/cd54e8e8-1f29-472d-87de-1a6d48ec2209" />

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

<img width="767" height="489" alt="image" src="https://github.com/user-attachments/assets/28537746-dade-4e36-9aee-031781d809a5" />

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

<img width="530" height="681" alt="image" src="https://github.com/user-attachments/assets/2fe51785-7853-4910-823a-0e54b854dcbc" />
<img width="205" height="200" alt="image" src="https://github.com/user-attachments/assets/58e4366e-7248-4204-a882-d2daf2341e0a" />

---

## 13. Save & Load Project

**💾 Save project (.json):** Saves **all** workspace objects — including imported **images** (with filters/clip) and **SVG** graphics, layer assignment and work-area size. In Chromium/Edge a **file dialog to choose the location** opens (otherwise a classic download).

**Load project:** Choose a `.json` via the file dialog. Only the user objects are replaced; helper objects (grid, origin) stay intact. Image filters are reapplied, the work-area size is restored. Old project files load as well.

> ⚠️ **Note:** Polyline editing handles are not saved — loaded polylines are visible and movable; for point-precise re-editing, redraw if needed.

---

## 14. Multi-language

Via the 🌐 dropdown at the top of the workspace: **German, English, Spanish, Chinese**. The choice is stored in the browser (`localStorage`) and restored automatically on the next start. The main UI and the dialogs are translated.

<img width="116" height="146" alt="image" src="https://github.com/user-attachments/assets/c0f92a2e-8338-4474-9f31-c9c77870eb15" />

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
| **↑ / ↓** (G-code input) | Scroll through the command history |

---

## 18. Camera, Mobile Control & Maintenance

These features are aimed mainly at running on a **Raspberry Pi** built into the laser cutter.

### 18.1 📷 Camera Background Image

A camera above the work area provides a **semi-transparent background image** to place objects precisely onto a workpiece that is already in position. The controls are in the **top bar** of the workspace:

- **Source:** **Pi camera (CSI)** via `picamera2` or **USB camera** (UVC) via OpenCV.
- **📷** captures an image and places it **locked** behind the objects (never lasered), a **transparency** slider, **✕** removes it.

### 18.2 ⌖ Camera Calibration

So the camera image sits **dimensionally accurate** on the bed (perspective **and** wide-angle distortion), calibrate once via the **⌖ button**:

1. Place **physical markers** at the **8 positions**: 4 corners + 4 edge midpoints.
2. **Capture a photo** and click the points in a fixed order (4 corners first, then 4 midpoints – yellow crosshairs help).
3. **Save** → the backend rectifies via **Thin-Plate-Spline** and applies the calibration automatically to every further image (stored in `camera_calib.json`).

### 18.3 ⚲ Edge Detection → Vector

Draw a shape on a sheet / place an object, then the **⚲ button** (Tools panel, next to the box generator):

1. **📷 Capture & detect** – the (rectified) image is analysed via **Canny + contour finding**, the preview shows the edges in green.
2. Adjust the **live sliders** (edge thresholds, smoothing, min. length, simplify).
3. **Apply as vector** → the contours are inserted as **editable cut objects**. Most accurate with prior calibration.

### 18.4 Automatic Connection (Raspberry Pi)

When the app runs on **Linux/Raspberry Pi** and an **MKS DLC32** is connected via USB, the app **connects to it automatically** as soon as the UI is opened (detected via the USB-serial chip CH340/CH9102/CP2102). This lets you drop the display at the laser. If you disconnect manually, it won't auto-reconnect.

### 18.5 ⟳ Software Update via the Web UI

The **"⟳ Update software"** button (⚙️ Machine panel) fetches the latest version via `git pull` and restarts the service — **without logging into the Pi**. It requires the systemd service with `Restart=always` (included in the installer); update existing installs once by re-running the installer. If an auto-restart isn't possible, the update is fetched and a manual restart is reported (so the server is never left down).

### 18.6 📱 Mobile Control Page & PWA

At **`http://<Pi-IP>:8080/mobile.html`** there is a touch-friendly UI to **position the head** (jog pad with step sizes), trigger **Home/Origin/Unlock**, toggle the **pointer laser** and **pump**, and see the **live status** — ideal for operating the laser **on-site from a phone** without a display (phone and Pi on the same Wi-Fi).

- **"Add to Home Screen"** (Android/iOS) opens the page as a **full-screen app** (PWA manifest + icon) — no app store needed.
- A link **"📱 Mobile control page"** is also available in the machine panel of the main UI.

---

## 19. Troubleshooting

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
