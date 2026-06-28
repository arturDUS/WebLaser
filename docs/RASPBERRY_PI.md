# 🍓 WebLaser auf dem Raspberry Pi / on Raspberry Pi

> 🇩🇪 [Deutsch](#-deutsch) · 🇬🇧 [English](#-english)

---

<a id="-deutsch"></a>
## 🇩🇪 Deutsch

Diese Anleitung installiert WebLaser so auf einem Raspberry Pi, dass es **bei jedem Start automatisch läuft** und im Netzwerk per **`http://<Pi-IP>:8080`** von jedem Browser erreichbar ist.

### Voraussetzungen
- Raspberry Pi (Pi 3 / 4 / 5 / Zero 2 W) mit **Raspberry Pi OS** (Bookworm)
- Netzwerk (LAN oder WLAN) eingerichtet
- Der Laser hängt entweder per **USB** am Pi oder ist per **WLAN/FluidNC** im selben Netz

### Schnellinstallation (eine Zeile)

Auf dem Pi (Terminal oder per SSH) als normaler Benutzer (`pi`):

```bash
curl -fsSL https://raw.githubusercontent.com/arturDUS/WebLaser/main/install_raspberry.sh | bash
```

Das Skript erledigt automatisch:
1. Systempakete installieren (Python, git, venv)
2. WebLaser von GitHub holen → `~/WebLaser`
3. Python-Umgebung + Abhängigkeiten einrichten
4. USB-Seriell-Rechte (`dialout`) freischalten
5. `systemd`-Dienst `weblaser` einrichten → **Autostart beim Booten**
6. Dienst starten

Am Ende zeigt es die Aufruf-Adresse, z. B. `http://192.168.178.50:8080`.

> **Alternative (manuell):**
> ```bash
> git clone https://github.com/arturDUS/WebLaser.git
> cd WebLaser
> bash install_raspberry.sh
> ```

### Aufrufen
Auf einem **beliebigen Gerät im selben Netzwerk** den Browser öffnen:

```
http://<Pi-IP>:8080
```

Die Pi-IP findest du mit `hostname -I` auf dem Pi.

### Verwaltung

```bash
sudo systemctl status weblaser      # Läuft der Dienst?
sudo systemctl restart weblaser     # Neu starten
sudo systemctl stop weblaser        # Stoppen
journalctl -u weblaser -f           # Live-Log ansehen
```

### Aktualisieren (neue Version von GitHub)

```bash
cd ~/WebLaser && git pull && sudo systemctl restart weblaser
```
(oder einfach das Installationsskript erneut ausführen — es aktualisiert vorhandene Installationen.)

### Deinstallieren

```bash
sudo systemctl disable --now weblaser
sudo rm /etc/systemd/system/weblaser.service
sudo systemctl daemon-reload
rm -rf ~/WebLaser
```

### Tipps
- **Feste IP empfehlenswert:** Damit sich die Aufruf-Adresse nicht ändert, im Router eine **feste IP** für den Pi vergeben (DHCP-Reservierung).
- **USB-Laser:** Nach der Erstinstallation einmal **neu booten**, damit die `dialout`-Gruppenrechte greifen.
- **FluidNC per WLAN:** In der Oberfläche unter ⚙️ Maschine → WLAN → IP des FluidNC eingeben → Modus „Auto-Erkennung".
- **Materialbibliothek:** Wird auf dem Pi in `~/WebLaser/materials.json` gespeichert und ist so für **alle** Nutzer im Netzwerk gemeinsam verfügbar.
- **MKS DLC32 per USB:** Wird automatisch erkannt und verbunden, sobald die Oberfläche geöffnet wird (kein manuelles Verbinden nötig).
- **Software-Update:** über den Button **„⟳ Software aktualisieren"** (Panel ⚙️ Maschine) — kein SSH/Login am Pi nötig.

### 🖥️ Optionales OLED-Display (128×64, SSD1306, I2C)

Ein kleines OLED zeigt direkt am Pi einen **QR-Code zur Mobilseite**, die **Browser-Adresse** (Hostname/IP) und den **System-Status** (Verbindung, Position, Leistung, Kamera). Der Installer installiert die Bibliotheken (`luma.oled`, `qrcode`) und aktiviert I2C.

- **Anschluss:** `VCC→3.3V`, `GND→GND`, `SDA→GPIO2 (Pin 3)`, `SCL→GPIO3 (Pin 5)` — I2C-Adresse **0x3C**.
- **Optionaler Taster** zum Weiterschalten: `GPIO17 (Pin 11)` gegen GND.
- Nach dem Anschließen einmal **neu booten**. Einstellungen (Adresse, Taster-Pin, Wechselzeit) stehen in `agent.py`; für ein **1,3″-SH1106** dort `ssd1306` → `sh1106` ändern.

---

<a id="-english"></a>
## 🇬🇧 English

This guide installs WebLaser on a Raspberry Pi so it **starts automatically on every boot** and is reachable on the network from any browser via **`http://<Pi-IP>:8080`**.

### Requirements
- Raspberry Pi (Pi 3 / 4 / 5 / Zero 2 W) with **Raspberry Pi OS** (Bookworm)
- Network (LAN or Wi-Fi) configured
- The laser is connected to the Pi via **USB**, or reachable via **Wi-Fi/FluidNC** on the same network

### One-line install

On the Pi (terminal or via SSH) as a normal user (`pi`):

```bash
curl -fsSL https://raw.githubusercontent.com/arturDUS/WebLaser/main/install_raspberry.sh | bash
```

The script automatically:
1. installs system packages (Python, git, venv)
2. fetches WebLaser from GitHub → `~/WebLaser`
3. sets up a Python environment + dependencies
4. grants USB serial access (`dialout`)
5. creates the `systemd` service `weblaser` → **autostart on boot**
6. starts the service

At the end it prints the access URL, e.g. `http://192.168.178.50:8080`.

> **Alternative (manual):**
> ```bash
> git clone https://github.com/arturDUS/WebLaser.git
> cd WebLaser
> bash install_raspberry.sh
> ```

### Access
On **any device on the same network**, open the browser:

```
http://<Pi-IP>:8080
```

Find the Pi's IP with `hostname -I` on the Pi.

### Management

```bash
sudo systemctl status weblaser      # Is the service running?
sudo systemctl restart weblaser     # Restart
sudo systemctl stop weblaser        # Stop
journalctl -u weblaser -f           # Live log
```

### Update (new version from GitHub)

```bash
cd ~/WebLaser && git pull && sudo systemctl restart weblaser
```
(or just re-run the install script — it updates an existing installation.)

### Uninstall

```bash
sudo systemctl disable --now weblaser
sudo rm /etc/systemd/system/weblaser.service
sudo systemctl daemon-reload
rm -rf ~/WebLaser
```

### Tips
- **Static IP recommended:** assign a **static IP** for the Pi in your router (DHCP reservation) so the URL never changes.
- **USB laser:** after the first install, **reboot once** so the `dialout` group permissions take effect.
- **FluidNC via Wi-Fi:** in the UI under ⚙️ Machine → Wi-Fi → enter the FluidNC IP → mode "Auto-detect".
- **Material library:** stored on the Pi in `~/WebLaser/materials.json`, so it is shared by **all** users on the network.
- **MKS DLC32 via USB:** detected and connected automatically as soon as the UI is opened (no manual connect needed).
- **Software update:** via the **"⟳ Update software"** button (⚙️ Machine panel) — no SSH/login to the Pi required.

### 🖥️ Optional OLED display (128×64, SSD1306, I2C)

A small OLED shows, right at the Pi, a **QR code to the mobile page**, the **browser address** (hostname/IP) and the **system status** (connection, position, power, camera). The installer installs the libraries (`luma.oled`, `qrcode`) and enables I2C.

- **Wiring:** `VCC→3.3V`, `GND→GND`, `SDA→GPIO2 (pin 3)`, `SCL→GPIO3 (pin 5)` — I2C address **0x3C**.
- **Optional button** to cycle screens: `GPIO17 (pin 11)` to GND.
- After connecting, **reboot once**. Settings (address, button pin, cycle time) are in `agent.py`; for a **1.3″ SH1106** change `ssd1306` → `sh1106` in `oled_worker`.
