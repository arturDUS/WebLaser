import asyncio
import http.server
import io
import json
import os
import re
import serial
import serial.tools.list_ports
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
import websocket
import websockets
from collections import deque
from svgelements import SVG, Path, Shape, Move, QuadraticBezier, CubicBezier, Arc

# --- KONFIGURATION ---
RX_BUFFER_SIZE = 128
STATUS_RE = re.compile(r'<([^|]+)\|.*?MPos:([^,]+),([^,|]+)')

# Materialbibliothek wird als JSON-Datei neben diesem Skript gespeichert,
# damit sie für alle Clients im Netzwerk (z. B. am Raspberry Pi) verfügbar ist.
MATERIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials.json")

def load_materials_file():
    """Liest die Materialbibliothek aus der JSON-Datei (leere Liste, falls nicht vorhanden)."""
    try:
        if os.path.exists(MATERIALS_FILE):
            with open(MATERIALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Material-Datei Lesefehler: {e}")
    return []

def save_materials_file(mats):
    """Schreibt die komplette Materialbibliothek in die JSON-Datei."""
    try:
        with open(MATERIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(mats, f, ensure_ascii=False, indent=2)
        print(f"Materialbibliothek gespeichert ({len(mats)} Einträge) → {MATERIALS_FILE}")
        return True
    except Exception as e:
        print(f"Material-Datei Schreibfehler: {e}")
        return False

# --- KAMERA (Raspberry Pi, CSI über picamera2/libcamera) ---
_picam = None  # Picamera2-Instanz (einmal initialisiert, dann offen gehalten)

def capture_camera_jpeg():
    """Nimmt ein Standbild der Pi-Kamera auf und gibt es als Base64-JPEG zurück.
    Lazy-Import von picamera2: läuft die App ohne Kamera (z. B. auf Windows),
    wird hier eine klare Fehlermeldung ausgelöst, ohne den Start zu blockieren."""
    global _picam
    import base64
    try:
        from picamera2 import Picamera2
    except Exception:
        raise RuntimeError("picamera2 nicht verfügbar. Auf dem Raspberry Pi installieren: "
                           "sudo apt install -y python3-picamera2 (und venv mit --system-site-packages).")
    if _picam is None:
        _picam = Picamera2()
        cfg = _picam.create_still_configuration(main={"size": (1640, 1232)})
        _picam.configure(cfg)
        _picam.start()
        time.sleep(2)  # Belichtung/Weißabgleich beim ersten Start einpendeln lassen
    buf = io.BytesIO()
    _picam.capture_file(buf, format="jpeg")
    return base64.b64encode(buf.getvalue()).decode("ascii")

def capture_usb_jpeg(index=0, width=2048, height=1536):
    """Nimmt ein Standbild einer USB-Kamera (UVC) über OpenCV auf -> Base64-JPEG.
    Lazy-Import von cv2, damit die App ohne OpenCV/Kamera weiter läuft."""
    import base64
    try:
        import cv2
    except Exception:
        raise RuntimeError("OpenCV (cv2) nicht verfügbar. Auf dem Raspberry Pi: "
                           "sudo apt install -y python3-opencv (Windows: pip install opencv-python).")
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_V4L2
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)   # Fallback ohne explizites Backend
    if not cap.isOpened():
        raise RuntimeError(f"USB-Kamera (Index {index}) konnte nicht geöffnet werden.")
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        frame = None
        for _ in range(8):              # ein paar Frames für Auto-Belichtung
            ok, f = cap.read()
            if ok:
                frame = f
        if frame is None:
            raise RuntimeError("Kein Bild von der USB-Kamera erhalten.")
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            raise RuntimeError("JPEG-Encodierung der USB-Kamera fehlgeschlagen.")
        return base64.b64encode(buf.tobytes()).decode("ascii")
    finally:
        cap.release()

# --- GLOBALE VARIABLEN ---
laser_serial = None
connected_websocket = None
job_queue = deque()
unacked_lengths = deque()
bytes_in_buffer = 0
stop_thread = False
total_job_lines = 0
completed_job_lines = 0
last_progress_percent = -1
active_connections = 0
current_transport = "USB"      # "USB" | "Telnet" | "ESP3D-WebUI" – aktive Verbindungsart
firmware_detected = None       # z. B. "FluidNC v3.7" / "Grbl 1.1f" (per $I/Banner erkannt)

class NetworkLaser:
    """
    Hybrid-Kommunikation für ESP3D/Makerbase Controller (z. B. Grbl_ESP32):
    - Hört über WebSockets (Port 8849) zu (Zuhören/Status).
    - Spricht über HTTP GET Requests (Port 8848) (Befehle).
    """
    IS_NETWORK = True
    def __init__(self, ip, ws_port=8849, http_port=8848, timeout=0.1):
        self.ip = ip
        self.http_port = http_port
        
        # 1. Das Ohr: WebSocket Verbindung für den Datenstrom (Status, OK, etc.)
        url = f"ws://{ip}:{ws_port}/"
        try:
            # Subprotokoll 'arduino' wird oft von ESP3D erwartet
            self.ws = websocket.create_connection(url, timeout=2.0, subprotocols=["arduino"])
        except:
            self.ws = websocket.create_connection(url, timeout=2.0)
            
        # Socket-Timeout für den Lese-Vorgang setzen
        self.ws.sock.settimeout(timeout) 
        self.is_open = True
        self.last_poll = time.time()
        print(f"DEBUG: Laser verbunden! Hört auf {ws_port} (WS), Spricht auf {http_port} (HTTP)")

    def write(self, data):
        """Sendet Befehle via HTTP GET (Port 8848)."""
        if not self.is_open:
            return

        try:
            payload = data.decode('utf-8') if isinstance(data, bytes) else data
            # Kommentare entfernen (alles ab ';') und trimmen
            payload = payload.split(';')[0].strip()
            if not payload:
                return

            encoded_cmd = urllib.parse.quote(payload)
            url = f"http://{self.ip}:{self.http_port}/command?commandText={encoded_cmd}&PAGEID=0"
            urllib.request.urlopen(url, timeout=1.0)
            print(f"DEBUG SEND (HTTP): {payload}")

        except Exception as e:
            print("HTTP Sende-Fehler:", e)

    @property
    def in_waiting(self):
        """Gibt an, ob Daten im WebSocket-Puffer liegen."""
        return 1 if self.is_open else 0

    def readline(self):
        """Liest Daten aus dem WebSocket (Port 8849)."""
        if not self.is_open:
            return b""

        # Automatischer Status-Ping via HTTP
        now = time.time()
        if now - self.last_poll > 1.0:
            self.last_poll = now
            try:
                # Ping-Befehl per HTTP senden
                url = f"http://{self.ip}:{self.http_port}/command?commandText=%3F&PAGEID=0"
                urllib.request.urlopen(url, timeout=0.5)
            except:
                pass

        try:
            # WebSocket-Nachricht empfangen
            line = self.ws.recv()
            
            if isinstance(line, str):
                if line == "": 
                    return b""
                    
                # ESP3D/Makerbase Protokoll-Spam filtern
                if line.startswith("PING:") or "CURRENT_ID:" in line or "ACTIVE_ID:" in line:
                    return b""
                    
                print(f"DEBUG RECV (WS): {line.strip()}") 
                return line.encode('utf-8') + b'\n'
                
            return line + b'\n'
            
        except websocket.WebSocketTimeoutException:
            return b""
        except Exception as e:
            if "timed out" in str(e).lower():
                return b""
            print("WS Lese-Fehler:", e)
            self.is_open = False
            return b""

    def close(self):
        """Schließt die Verbindung."""
        self.is_open = False
        try:
            self.ws.close()
            print("DEBUG: Netzwerkverbindung getrennt.")
        except:
            pass


class TelnetLaser:
    """
    Roher TCP/Telnet-Stream zu FluidNC (Standard-Port 23).
    Verhält sich wie eine serielle Schnittstelle: G-Code-Zeilen + '\\n' senden,
    '?' / 0x18 als Realtime-Bytes, Antworten zeilenweise lesen.
    """
    IS_NETWORK = True
    def __init__(self, ip, port=23, timeout=0.1):
        self.ip = ip
        self.port = port
        self.sock = socket.create_connection((ip, port), timeout=3.0)
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # kleine Befehle sofort senden
        except Exception:
            pass
        self.sock.settimeout(timeout)
        self._buf = b""      # bereinigte Textbytes (für Zeilen)
        self._raw = b""      # noch nicht IAC-verarbeitete Rohbytes
        self.is_open = True
        print(f"DEBUG: FluidNC-Telnet verbunden mit {ip}:{port}")

    def _process_iac(self):
        """Telnet-IAC-Aushandlung verarbeiten: Optionen höflich ablehnen, Steuerbytes entfernen."""
        IAC, DONT, DO, WONT, WILL, SB, SE = 255, 254, 253, 252, 251, 250, 240
        raw = self._raw
        n = len(raw)
        i = 0
        clean = bytearray()
        resp = bytearray()
        while i < n:
            b = raw[i]
            if b != IAC:
                clean.append(b); i += 1; continue
            if i + 1 >= n:
                break                                   # unvollständige IAC am Ende
            c = raw[i + 1]
            if c == IAC:
                clean.append(IAC); i += 2; continue     # escaped 0xFF = literal
            if c in (DO, DONT, WILL, WONT):
                if i + 2 >= n:
                    break
                opt = raw[i + 2]
                if c == DO:     resp += bytes([IAC, WONT, opt])   # jede Option ablehnen
                elif c == WILL: resp += bytes([IAC, DONT, opt])
                i += 3; continue
            if c == SB:
                j = i + 2                               # Subnegotiation bis IAC SE überspringen
                while j + 1 < n and not (raw[j] == IAC and raw[j + 1] == SE):
                    j += 1
                if j + 1 >= n:
                    break
                i = j + 2; continue
            i += 2; continue                            # sonstige 2-Byte-Kommandos
        self._raw = raw[i:]                             # Rest (inkl. unvollständiger IAC) behalten
        if resp:
            try:
                self.sock.sendall(bytes(resp))
                print(f"DEBUG TELNET IAC-Antwort gesendet ({len(resp)} Bytes)")
            except Exception:
                pass
        self._buf += bytes(clean)

    def write(self, data):
        if not self.is_open:
            return
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            self.sock.sendall(data)   # Bytes exakt wie übergeben (Realtime '?'/0x18 ohne Newline)
        except Exception as e:
            print("Telnet Sende-Fehler:", e)
            self.is_open = False

    @property
    def in_waiting(self):
        return 1 if self.is_open else 0

    def _pop_line(self):
        """Extrahiert eine Zeile aus dem Puffer; akzeptiert \\n, \\r ODER \\r\\n als Ende."""
        idx = -1
        for k, ch in enumerate(self._buf):
            if ch == 0x0A or ch == 0x0D:   # \n oder \r
                idx = k
                break
        if idx == -1:
            return None
        line = self._buf[:idx]
        # \r\n als Paar gemeinsam konsumieren
        if self._buf[idx:idx+2] == b"\r\n":
            self._buf = self._buf[idx+2:]
        else:
            self._buf = self._buf[idx+1:]
        return line + b"\n"

    def readline(self):
        """Liefert genau eine vollständige Zeile (mit '\\n') oder b'' bei Timeout."""
        if not self.is_open:
            return b""
        line = self._pop_line()
        if line is not None:
            return line
        try:
            chunk = self.sock.recv(2048)
            if chunk == b"":
                self.is_open = False     # Gegenseite hat geschlossen
                return b""
            self._raw += chunk
            self._process_iac()          # IAC-Steuerbytes verarbeiten/entfernen
        except socket.timeout:
            return b""
        except Exception as e:
            if "timed out" in str(e).lower():
                return b""
            print("Telnet Lese-Fehler:", e)
            self.is_open = False
            return b""
        line = self._pop_line()
        return line if line is not None else b""

    def close(self):
        self.is_open = False
        try:
            self.sock.close()
            print("DEBUG: Telnet-Verbindung getrennt.")
        except:
            pass


def connect_network_laser(ip, mode, ws_port, http_port):
    """
    Stellt eine Netzwerkverbindung her und erkennt den Transport automatisch.
    mode: 'auto' | 'telnet' | 'webui'.  Liefert (laser, transport_name).
    """
    # FluidNC-Telnet (Port 23) zuerst probieren (bei 'auto' und 'telnet')
    if mode in ('auto', 'telnet'):
        try:
            laser = TelnetLaser(ip, 23)
            return laser, "Telnet"
        except Exception as e:
            print(f"DEBUG: Telnet (Port 23) nicht erreichbar: {e}")
            if mode == 'telnet':
                raise   # explizit gewünscht → Fehler durchreichen
    # Fallback / explizit: ESP3D-WebUI (Grbl_ESP32)
    laser = NetworkLaser(ip, ws_port, http_port)
    return laser, "ESP3D-WebUI"


def _detect_firmware(line_str, loop):
    """Erkennt FluidNC vs. Grbl aus Banner-/$I-Zeilen und meldet es einmalig ans Frontend."""
    global firmware_detected
    if firmware_detected:
        return
    name = None
    if 'FluidNC' in line_str:
        m = re.search(r'FluidNC\s+v?([0-9][0-9.]*)', line_str)
        name = "FluidNC" + (f" v{m.group(1)}" if m else "")
    elif line_str.startswith('Grbl') or line_str.startswith('[VER:'):
        m = re.search(r'Grbl\s+v?([0-9][0-9.]*[a-z]?)', line_str)
        if not m:
            m = re.search(r'\[VER:([0-9][0-9.]*[a-z]?)', line_str)
        name = "Grbl" + (f" {m.group(1)}" if m else "")
    if name:
        firmware_detected = name
        print(f"DEBUG: Firmware erkannt: {name} über {current_transport}")
        if connected_websocket:
            asyncio.run_coroutine_threadsafe(
                connected_websocket.send(json.dumps({
                    "type": "firmware", "name": name, "transport": current_transport})), loop)


def get_base_path():
    """ 
    Erkennt, ob das Programm als .exe läuft (sys.frozen) 
    oder als normales Python-Skript.
    """
    if getattr(sys, 'frozen', False):
        # Wenn es eine .exe ist, nutze den temporären Entpack-Ordner von PyInstaller
        return sys._MEIPASS
    else:
        # Wenn es normal gestartet wird, nutze den Ordner des Skripts
        return os.path.dirname(os.path.abspath(__file__))

def start_webserver():
    port = 8080
    web_dir = get_base_path()
    os.chdir(web_dir)
    
    # Ein eigener, "stummer" Handler. Er überschreibt die Log-Funktion 
    # und tut einfach gar nichts (pass), anstatt in die Konsole zu schreiben!
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass 
            
    with http.server.ThreadingHTTPServer(("", port), QuietHandler) as httpd:
        try:
            print(f"🌐 Web-Oberfläche erreichbar unter: http://127.0.0.1:{port}")
        except:
            pass # Falls print ohne Konsole crasht, ignorieren wir das auch
            
        httpd.serve_forever()

def open_browser_app_mode():
    time.sleep(0.5)
    url = "http://127.0.0.1:8080"
    
    try:
        if sys.platform == "win32":
            # WINDOWS: Versucht Chrome, dann Edge
            command = f'start chrome --app={url} || start msedge --app={url}'
            subprocess.run(command, shell=True)
            
        elif sys.platform.startswith("linux"):
            # LINUX: Sucht nach gängigen Chromium-Derivaten
            browsers = ['google-chrome', 'chromium-browser', 'chromium', 'brave-browser']
            app_cmd = None
            
            for b in browsers:
                if shutil.which(b):  # Prüft, ob der Browser im System installiert ist
                    app_cmd = [b, f'--app={url}']
                    break
            
            if app_cmd:
                # Popen blockiert den Python-Thread nicht
                subprocess.Popen(app_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print("Kein Chromium-Browser unter Linux gefunden. Nutze Fallback.")
                webbrowser.open(url)
                
        elif sys.platform == "darwin":
            # MAC OS
            command = f'open -n -a "Google Chrome" --args --app={url}'
            subprocess.run(command, shell=True)
            
        else:
            # Unbekanntes System
            webbrowser.open(url)
            
        print("Frontend gestartet.")
        
    except Exception as e:
        print(f"App-Modus fehlgeschlagen, nutze Standard-Browser: {e}")
        webbrowser.open(url)

# --- HILFSFUNKTIONEN ---
def generate_raster_gcode(x, y, w, h, power, speed, step=0.3):
    """Füllt ein Rechteck zeilenweise mit G-Code (Raster-Gravur)"""
    lines = [f"G0 X{x:.2f} Y{y:.2f}", f"M4 S{power}"]
    curr_y = y
    while curr_y < y + h:
        lines.append(f"G1 X{x+w:.2f} Y{curr_y:.2f} F{speed}")
        curr_y += step
        if curr_y < y + h:
            lines.append(f"G1 X{x:.2f} Y{curr_y:.2f} F{speed}")
            curr_y += step
    lines.append("M5")
    return lines

def generate_material_test_gcode(start_x, start_y, rows, cols, power_start, power_step, feed_start, feed_step):
    gcode = ["; --- START MATERIAL TEST ---"]
    
    for r in range(rows):
        current_power = power_start + (r * power_step)
        for c in range(cols):
            current_feed = feed_start + (c * feed_step)
            x_pos = start_x + (c * 15) # 15mm Abstand pro Kästchen
            y_pos = start_y + (r * 15)
            
            # Quadrat für diesen Testpunkt zeichnen
            gcode.append(f"G0 X{x_pos} Y{y_pos}")
            gcode.append(f"M4 S{current_power}")
            gcode.append(f"G1 X{x_pos+10} Y{y_pos} F{current_feed}") # Linie
            gcode.append(f"G1 X{x_pos+10} Y{y_pos+10}")
            gcode.append(f"G1 X{x_pos} Y{y_pos+10}")
            gcode.append(f"G1 X{x_pos} Y{y_pos}")
            gcode.append("M5")
            
    gcode.append("; --- END MATERIAL TEST ---")
    return gcode


def generate_gcode_from_svg(svg_string, feedrate, power, canvas_height, origin_x=0, origin_y=0, engrave_mode="line", line_interval=0.1):
    svg = SVG.parse(io.StringIO(svg_string))
    segments = []      # Sammelt alle Wände des Objekts für die Flächenberechnung
    outline_cmds = []  # Der normale Umriss-Code

    # 1. Wir zerlegen das SVG in reine, gerade Geometrie (Linien/Wände)
    def process_element(elem):
        if isinstance(elem, (Path, Shape)):
            path = Path(elem)
            path.reify()
            for subpath in path.as_subpaths():
                last_x = None
                last_y = None
                for segment in subpath:
                    if isinstance(segment, Move):
                        x = segment.end.x - origin_x
                        y = (canvas_height - segment.end.y) - origin_y
                        outline_cmds.append("M5")
                        outline_cmds.append(f"G0 X{x:.2f} Y{y:.2f}")
                        outline_cmds.append(f"M4 S{power}")
                        last_x, last_y = x, y
                    elif getattr(segment, 'end', None) is not None:
                        # Fallback für Kurven (werden in kleine Geraden zerlegt)
                        steps = 1
                        if isinstance(segment, (QuadraticBezier, CubicBezier, Arc)):
                            steps = max(int(segment.length() / 0.5), 3)
                            
                        for i in range(1, steps + 1):
                            pt = segment.point(i / steps) if steps > 1 else segment.end
                            x = pt.x - origin_x
                            y = (canvas_height - pt.y) - origin_y
                            if last_x is not None:
                                segments.append((last_x, last_y, x, y))
                                outline_cmds.append(f"G1 X{x:.2f} Y{y:.2f} F{feedrate}")
                            last_x, last_y = x, y
        elif hasattr(elem, '__iter__'):
            for child in elem:
                process_element(child)

    process_element(svg)
    cmds = []

    # 2. FLÄCHE BERECHNEN (Ray-Casting Algorithmus)
    if engrave_mode in ["fill", "fill_line"] and segments:
        min_y = min(min(s[1], s[3]) for s in segments)
        max_y = max(max(s[1], s[3]) for s in segments)
        
        y = min_y
        direction = 1 # 1 = Rechts, -1 = Links (Zick-Zack Füllung)
        
        while y <= max_y:
            intersects = []
            for (x1, y1, x2, y2) in segments:
                # Prüfen, ob unser Laserstrahl (y) diese Wand trifft
                if (y1 <= y and y2 > y) or (y2 <= y and y1 > y):
                    # Mathematischer Schnittpunkt X
                    x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                    intersects.append(x)
            
            intersects.sort()
            
            # Wir fassen immer 2 Schnittpunkte als eine Laser-Linie zusammen (Even-Odd-Rule)
            lines_to_draw = []
            for i in range(0, len(intersects)-1, 2):
                lines_to_draw.append((intersects[i], intersects[i+1]))
                
            # Zick-Zack Richtung umkehren
            if direction == -1:
                lines_to_draw.reverse()
                
            for (start_x, end_x) in lines_to_draw:
                if direction == 1:
                    cmds.append("M5")
                    cmds.append(f"G0 X{start_x:.2f} Y{y:.2f}")
                    cmds.append(f"M4 S{power}")
                    cmds.append(f"G1 X{end_x:.2f} Y{y:.2f} F{feedrate}")
                else:
                    cmds.append("M5")
                    cmds.append(f"G0 X{end_x:.2f} Y{y:.2f}")
                    cmds.append(f"M4 S{power}")
                    cmds.append(f"G1 X{start_x:.2f} Y{y:.2f} F{feedrate}")
                    
            y += line_interval
            direction *= -1

    # 3. UMRISS HINZUFÜGEN (Falls gewünscht oder reiner Schneide-Layer)
    if engrave_mode in ["line", "fill_line"]:
        cmds.extend(outline_cmds)

    cmds.append("M5")
    return cmds


# --- SERIAL WORKER ---
def serial_worker(loop):
    global laser_serial, connected_websocket, stop_thread, bytes_in_buffer, total_job_lines, completed_job_lines, last_progress_percent

    print("DEBUG: Serial Worker gestartet.")
    last_poll_time = time.time()
    recent_cmds   = deque(maxlen=5)   # letzte Befehle für Fehler-Diagnose
    # Netzwerk-Flusskontrolle: nach jedem gesendeten Befehl auf 'ok' warten,
    # bevor der nächste gesendet wird.  Verhindert, dass GRBL-ESP32 unter
    # WiFi-Last zwei Befehle in einem Parsing-Zyklus zusammenfasst.
    net_waiting_ok = False
    net_ok_timeout = 0.0           # Zeitstempel, nach dem wir ohne ok weitermachen
    
    while not stop_thread:
        # laser_serial ist jetzt entweder ein pyserial-Objekt ODER unsere NetworkLaser-Klasse
        if laser_serial and laser_serial.is_open:
            try:
                # 1. Daten vom Laser lesen (Funktioniert für USB & Netzwerk)
                line = laser_serial.readline()
                if line:
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    if line_str:
                        _detect_firmware(line_str, loop)   # FluidNC/Grbl aus Banner/$I erkennen
                        # Status-Polls (<...>)
                        if line_str.startswith('<'):
                            match = STATUS_RE.search(line_str)
                            if match and connected_websocket:
                                s_val = 0.0
                                if "|FS:" in line_str:
                                    try:
                                        parts = line_str.split("|FS:")[1].split(">")[0].split("|")[0].split(",")
                                        if len(parts) > 1: s_val = float(parts[1])
                                    except: pass
                                elif "|S:" in line_str:
                                    try:
                                        s_val = float(line_str.split("|S:")[1].split(">")[0].split("|")[0])
                                    except: pass

                                asyncio.run_coroutine_threadsafe(
                                    connected_websocket.send(json.dumps({
                                        "type": "status", 
                                        "state": match.group(1), 
                                        "x": float(match.group(2)), 
                                        "y": float(match.group(3)),
                                        "s": s_val
                                    })), loop)
                        # OK / Fehler-Meldungen
                        elif line_str.startswith('ok'):
                            net_waiting_ok = False          # Nächsten Befehl freigeben
                            if unacked_lengths:
                                bytes_in_buffer -= unacked_lengths.popleft()
                            completed_job_lines += 1
                            if total_job_lines > 0 and connected_websocket:
                                percent = int((completed_job_lines / total_job_lines) * 100)
                                if percent != last_progress_percent:
                                    asyncio.run_coroutine_threadsafe(
                                        connected_websocket.send(json.dumps({"type": "progress", "percent": percent})), loop)
                                    last_progress_percent = percent
                                # Job fertig: alle Befehle abgearbeitet, Queue leer
                                if completed_job_lines >= total_job_lines and not job_queue:
                                    asyncio.run_coroutine_threadsafe(
                                        connected_websocket.send(json.dumps({"type": "job_done"})), loop)
                                    total_job_lines = 0
                                    completed_job_lines = 0
                                    last_progress_percent = -1
                        elif line_str.lower().startswith('error') or line_str.lower().startswith('alarm'):
                            net_waiting_ok = False          # Bei Fehler/Alarm ebenfalls freigeben
                            print(f"LASER FEHLER: {line_str} | Letzte Befehle: {list(recent_cmds)}")
                            if connected_websocket:
                                asyncio.run_coroutine_threadsafe(
                                    connected_websocket.send(json.dumps({"type": "error", "msg": line_str})), loop)
                        else:
                            if connected_websocket:
                                asyncio.run_coroutine_threadsafe(
                                    connected_websocket.send(json.dumps({"type": "response", "msg": line_str})), loop)

                # 2. Polling (Fragezeichen senden)
                current_time = time.time()
                if current_time - last_poll_time > 1.0:
                    laser_serial.write(b'?')
                    last_poll_time = current_time

                # 3. Queue abarbeiten
                is_net = getattr(laser_serial, 'IS_NETWORK', False)   # NetworkLaser ODER TelnetLaser
                # Netzwerk: nur senden wenn GRBL das letzte 'ok' geschickt hat
                # (oder ein Timeout von 3 s überschritten wurde als Fallback)
                ok_to_send = (not is_net) or (not net_waiting_ok) or (time.time() > net_ok_timeout)
                if job_queue and ok_to_send:
                    cmd = job_queue.popleft()
                    recent_cmds.append(cmd)
                    if is_net:
                        net_waiting_ok = True
                        net_ok_timeout = time.time() + 3.0
                    else:
                        unacked_lengths.append(len(cmd) + 1)
                        bytes_in_buffer += len(cmd) + 1
                    laser_serial.write((cmd + '\n').encode('utf-8'))
                    time.sleep(0.02)
                
            except Exception as e:
                print(f"DEBUG: Serial Worker Fehler: {e}")
                time.sleep(1)
        else:
            time.sleep(0.5)

# --- WEBSOCKET HANDLER ---
async def handle_client(websocket, path=None):
    global laser_serial, connected_websocket, stop_thread, total_job_lines, completed_job_lines, last_progress_percent, bytes_in_buffer, unacked_lengths
    global active_connections
    active_connections += 1
    connected_websocket = websocket
    loop = asyncio.get_event_loop()
    
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "connect":
                try:
                    conn_type = data.get("connType", "usb")
                    global current_transport, firmware_detected
                    firmware_detected = None   # bei jeder neuen Verbindung zurücksetzen

                    if conn_type == "net":
                        ip = data.get("ip")
                        net_mode = data.get("netMode", "auto")        # auto | telnet | webui
                        ws_port = int(data.get("netPort", 8849))      # ESP3D-WebUI-Port (Fallback)
                        # Transport automatisch erkennen (FluidNC-Telnet 23 zuerst)
                        laser_serial, current_transport = connect_network_laser(ip, net_mode, ws_port, 8848)
                    else:
                        # USB / serielle Verbindung
                        current_transport = "USB"
                        com_port = data.get("port")
                        baud = int(data.get("baudrate", 115200))
                        laser_serial = serial.Serial(com_port, baud, timeout=0.1)

                    stop_thread = False
                    threading.Thread(target=serial_worker, args=(loop,), daemon=True).start()
                    await websocket.send(json.dumps({"type": "info", "msg": f"Verbunden ({conn_type})"}))
                    # Transport sofort melden; $I löst die Firmware-Erkennung aus
                    await websocket.send(json.dumps({"type": "conn_info", "transport": current_transport, "connType": conn_type}))
                    job_queue.append('$I')
                except Exception as e:
                    await websocket.send(json.dumps({"type": "error", "msg": str(e)}))
            
            elif action == "get_ports":
                # Scannt das System nach verfügbaren COM/USB Ports
                ports = [port.device for port in serial.tools.list_ports.comports()]
                print(f"DEBUG: Gefundene Ports: {ports}")
                await websocket.send(json.dumps({"type": "ports_list", "ports": ports}))

            elif action == "capture_camera":
                # Standbild der Kamera aufnehmen (blockierend → in Thread auslagern).
                # source: "csi" (Pi-Kamera/picamera2) oder "usb" (UVC/OpenCV).
                source = data.get("source", "csi")
                try:
                    loop = asyncio.get_running_loop()
                    if source == "usb":
                        idx = int(data.get("device", 0))
                        b64 = await loop.run_in_executor(None, capture_usb_jpeg, idx)
                    else:
                        b64 = await loop.run_in_executor(None, capture_camera_jpeg)
                    await websocket.send(json.dumps({"type": "camera_photo",
                                                     "data": "data:image/jpeg;base64," + b64}))
                    print(f"DEBUG: Kamerabild ({source}) aufgenommen und gesendet.")
                except Exception as e:
                    print(f"DEBUG: Kamera-Fehler ({source}): {e}")
                    await websocket.send(json.dumps({"type": "camera_error", "msg": str(e)}))

            elif action == "disconnect":
                print("DEBUG: Trenne Laser-Verbindung...")
                stop_thread = True  # Stoppt die 200ms-Statusabfragen
                if laser_serial and laser_serial.is_open:
                    laser_serial.close()  # Schließt den USB/COM-Port physisch
                    
                await websocket.send(json.dumps({"type": "info", "msg": "USB-Verbindung erfolgreich getrennt."}))
                # Optional: Status direkt rot schalten
                await websocket.send(json.dumps({"type": "status", "state": "Disconnected", "x": 0, "y": 0}))

            elif action == "run_mixed_job":
                job_list = data.get("job", [])
                print(f"DEBUG: Empfange Job mit {len(job_list)} Objekten") # <--- WICHTIG!
                feedrate = data.get("feedrate", 1000)
                power = data.get("power", 800)
                height = data.get("height", 600)
                ox, oy = data.get("originX", 0), data.get("originY", 0)
                relative = data.get("relative", False)

                gcode = ["; --- START MIXED JOB ---", "M8", "G21", "G90", "M5"]
                # Relativ-Modus: die aktuelle (manuell angefahrene) Laserposition wird
                # zum Referenzpunkt (0/0). Die Job-Koordinaten sind bereits relativ zum
                # Referenzpunkt erzeugt (originX/Y = Referenzpunkt).
                if relative:
                    gcode.append("G92 X0 Y0")
                    print("DEBUG: Relativ-Modus aktiv -> G92 X0 Y0 (aktuelle Position = Referenzpunkt)")
                for item in job_list:
                    print(f"DEBUG: Verarbeite Item Typ: {item.get('type')}") # <--- WICHTIG!
                    item_type = item.get("type")
                    if item_type == "raw":
                        # Vorgenerierte G-Code-Zeilen (z. B. Foto-Gravur aus dem Frontend)
                        gcode.extend(item.get("lines", []))
                    elif item_type == "raster":
                        # Lade das 'data' Paket vom Frontend
                        d = item.get("data", {})
                        
                        # Hole die genauen Koordinaten und Werte (mit Fallback-Werten zur Sicherheit)
                        box_x = d.get("x", ox)
                        box_y = d.get("y", oy)
                        box_w = d.get("width", 25)
                        box_h = d.get("height", 25)
                        box_power = d.get("power", power)
                        box_speed = d.get("speed", feedrate)
                        
                        # Rufe die Raster-Funktion mit den echten Box-Daten auf
                        gcode.extend(generate_raster_gcode(box_x, box_y, box_w, box_h, box_power, box_speed))
                    else:
                        svg_part = item.get("svg", "")
                        
                        # Wir holen Speed, Power und Ebenen-Infos direkt aus dem JSON-Objekt
                        item_speed = item.get("speed", feedrate)
                        item_power = item.get("power", power)
                        layer_mode = item.get("layer", "cut")
                        pass_num = item.get("pass", 1)
                        total_passes = item.get("totalPasses", 1)

                        engrave_mode = item.get("engraveMode", "line")
                        line_interval = item.get("lineInterval", 0.1)
                        
                        # Eine Info-Zeile für das Terminal
                        print(f"DEBUG: Ebene '{layer_mode}' (Durchlauf {pass_num}/{total_passes}) - Speed: F{item_speed}, Power: S{item_power}")
                        
                        # Wir schreiben einen schönen Kommentar in die G-Code Datei zur Übersicht
                        gcode.append(f"\n; --- Objekt-Ebene: {layer_mode} | Durchlauf: {pass_num}/{total_passes} | S{item_power} F{item_speed} ---")
                        
                        # Wir übergeben jetzt item_speed und item_power an die Generierungs-Funktion!
                        gcode.extend(generate_gcode_from_svg(svg_part, item_speed, item_power, height, ox, oy, engrave_mode, line_interval))

                gcode.append("M5")
                # Relativ-Modus: temporären G92-Offset wieder aufheben, damit die
                # normale (absolute) Nullung (G10 L20 / G54) unverändert bleibt.
                if relative:
                    gcode.append("G92.1")

                # Filtere leere Zeilen und Zeilen ohne Buchstaben-Kommando
                final_gcode = []
                for line in gcode:
                    line = line.strip()
                    # Prüfe, ob die Zeile Buchstaben enthält (G, M, X, Y, S, F...)
                    if line and any(c.isalpha() for c in line):
                        final_gcode.append(line)

                total_job_lines = len(final_gcode)
                completed_job_lines = 0
                last_progress_percent = -1
                # job_queue.clear()
                # Jetzt die gefilterte Liste in die Queue:
                job_queue.extend(final_gcode)
                await websocket.send(json.dumps({"type": "info", "msg": f"Job geladen: {total_job_lines} Zeilen."}))
                print(f"DEBUG: QUEUE BEFÜLLT. Anzahl Elemente in Queue: {len(job_queue)}")

            elif action == "abort_job":
                print("DEBUG: ABBRUCH-SIGNAL EMPFANGEN!")
                
                # 1. Queue sofort leeren, damit nichts Neues mehr gesendet wird
                job_queue.clear()
                
                # 2. Puffer- und Fortschritts-Zähler zurücksetzen
                total_job_lines = 0
                completed_job_lines = 0
                last_progress_percent = -1
                unacked_lengths.clear()
                bytes_in_buffer = 0

                # 3. Hardware sofort stoppen (Soft-Reset für GRBL)
                if laser_serial and laser_serial.is_open:
                    try:
                        # \x18 ist der GRBL Soft-Reset (bricht alles sofort ab)
                        laser_serial.write(b'\x18')
                        time.sleep(0.1) # Dem Controller kurz Zeit geben
                        # Sicherstellen, dass der Laser aus ist
                        laser_serial.write(b'M5\n')
                    except Exception as e:
                        print(f"DEBUG: Fehler beim Senden des Abbruchs: {e}")
                
                await websocket.send(json.dumps({"type": "error", "msg": "JOB ABGEBROCHEN!"}))
                # Setze den Fortschrittsbalken im Frontend auf 0
                await websocket.send(json.dumps({"type": "progress", "percent": 0}))

            elif action == "send_gcode":
                cmd = data.get("command")
                print(f"DEBUG: Empfange G-Code: {cmd}") # <--- DAS HIER MUSS ERSCHEINEN
                job_queue.append(cmd)
                print(f"DEBUG: Aktuelle Job-Queue Länge: {len(job_queue)}")

            elif action == "get_materials":
                # Materialbibliothek aus der Datei laden und an diesen Client senden
                mats = load_materials_file()
                await websocket.send(json.dumps({"type": "materials", "data": mats}))

            elif action == "save_materials":
                # Komplette Bibliothek vom Client speichern (Datei wird überschrieben)
                mats = data.get("materials", [])
                ok = save_materials_file(mats)
                await websocket.send(json.dumps({"type": "materials_saved", "ok": ok}))

    finally:
        # Dieser Block wird GARANTIERT ausgeführt, wenn der Browser
        # geschlossen wird oder die Verbindung abreißt.
        active_connections -= 1
        
        if active_connections == 0:
            # Wenn der letzte Browser zu ist, starte den Countdown
            asyncio.create_task(shutdown_timer())



async def shutdown_timer():
    # 2 Sekunden Toleranz, falls der User die Seite nur mit F5 neu lädt
    await asyncio.sleep(2) 
    
    global active_connections
    if active_connections == 0:
        # os._exit(0) ist ein "harter" Befehl. Er killt sofort den Webserver, 
        # den WebSocket und beendet die .exe restlos, ohne auf Threads zu warten.
        os._exit(0)

async def main():
    # 1. Den HTTP-Webserver als Hintergrund-Prozess (Daemon) starten
    threading.Thread(target=start_webserver, daemon=True).start()

    # 2. NEU: Das Frontend vollautomatisch als "Desktop-App" öffnen
    threading.Thread(target=open_browser_app_mode, daemon=True).start()
    
    # 3. Den WebSocket Server für die Laser-Befehle starten
    print("Starte WebSocket Server auf Port 8765...")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())