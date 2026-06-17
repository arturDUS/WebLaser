#!/usr/bin/env bash
#
# WebLaser – Installationsskript für Raspberry Pi
# ------------------------------------------------
# Lädt WebLaser von GitHub, richtet eine Python-Umgebung ein und installiert
# einen systemd-Dienst, der bei jedem Start des Raspberry automatisch läuft.
# Danach ist die Oberfläche im Netzwerk per http://<Pi-IP>:8080 erreichbar.
#
# Aufruf (als normaler Benutzer, NICHT als root):
#   bash install_raspberry.sh
# oder direkt:
#   curl -fsSL https://raw.githubusercontent.com/arturDUS/WebLaser/main/install_raspberry.sh | bash
#
set -euo pipefail

REPO_URL="https://github.com/arturDUS/WebLaser.git"
INSTALL_DIR="${HOME}/WebLaser"
SERVICE_NAME="weblaser"
RUN_USER="$(whoami)"

if [ "$(id -u)" = "0" ]; then
  echo "Bitte NICHT als root ausführen – starte das Skript als normaler Benutzer (z. B. 'pi')."
  echo "Das Skript nutzt 'sudo' selbst, wo es nötig ist."
  exit 1
fi

echo "=================================================="
echo "  WebLaser – Installation auf dem Raspberry Pi"
echo "  Zielordner : ${INSTALL_DIR}"
echo "  Dienst     : ${SERVICE_NAME}.service (Benutzer ${RUN_USER})"
echo "=================================================="

echo "==> [1/6] Systempakete installieren (Python, git, venv, Kamera) ..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
# Kamera (optionales Hintergrundbild im WebLaser):
#  - python3-picamera2 -> CSI/Pi-Kamera (libcamera)
#  - python3-opencv     -> USB-Kamera (UVC)
# Beides sind System-Pakete -> per apt + venv mit --system-site-packages.
sudo apt-get install -y python3-picamera2 || echo "Hinweis: python3-picamera2 nicht installiert (CSI-Kamera optional)."
sudo apt-get install -y python3-opencv    || echo "Hinweis: python3-opencv nicht installiert (USB-Kamera optional)."

echo "==> [2/6] WebLaser von GitHub holen/aktualisieren ..."
if [ -d "${INSTALL_DIR}/.git" ]; then
  git -C "${INSTALL_DIR}" pull --ff-only
else
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

echo "==> [3/6] Python-Umgebung (venv) einrichten ..."
# --system-site-packages: damit das per apt installierte picamera2 (Kamera)
# in der venv sichtbar ist. Wirkt auch beim erneuten Ausfuehren auf bestehende venvs.
python3 -m venv --system-site-packages "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install pyserial websockets websocket-client svgelements

echo "==> [4/6] Zugriff auf USB-Seriell (Gruppe 'dialout') gewähren ..."
sudo usermod -aG dialout "${RUN_USER}" || true

echo "==> [5/6] systemd-Dienst einrichten ..."
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" >/dev/null <<EOF
[Unit]
Description=WebLaser – Web-basierte Lasercutter-Steuerung
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/agent.py
# Restart=always: erlaubt das Update über die Web-UI (Agent beendet sich sauber,
# systemd startet ihn mit der neuen Version neu – kein sudo/Login nötig).
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "==> [6/6] Dienst aktivieren und starten ..."
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
sudo systemctl restart "${SERVICE_NAME}.service"

IP_ADDR="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "=================================================="
echo "  ✅ Fertig! WebLaser läuft jetzt und startet automatisch beim Booten."
echo ""
echo "  Aufruf im Browser (von jedem Gerät im Netzwerk):"
echo "      http://${IP_ADDR:-<Pi-IP>}:8080"
echo ""
echo "  Nützliche Befehle:"
echo "      sudo systemctl status ${SERVICE_NAME}     # Status ansehen"
echo "      sudo systemctl restart ${SERVICE_NAME}    # neu starten"
echo "      journalctl -u ${SERVICE_NAME} -f          # Live-Log"
echo ""
echo "  Hinweis: Für USB-Laser ggf. einmal neu anmelden/booten,"
echo "  damit die 'dialout'-Gruppenrechte wirksam werden."
echo "=================================================="
