#!/usr/bin/env bash
set -euo pipefail

# Install a systemd service for the SRE Maturity app.
# Usage (as root):
#   ./scripts/install_service.sh [SERVICE_NAME] [USER] [PORT]
# Defaults: SERVICE_NAME=streamlit-assessment, USER=streamlit, PORT=8502

SERVICE_NAME="${1:-streamlit-assessment}"
RUN_USER="${2:-streamlit}"
PORT="${3:-8502}"

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
APP_DIR="$ROOT"
VENV_DIR="$ROOT/.venv"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

id -u "$RUN_USER" >/dev/null 2>&1 || {
  echo "User '$RUN_USER' does not exist. Create it or pass a different user." >&2
  exit 1
}

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "[!] Virtualenv not found at $VENV_DIR. Creating it now..."
  python3 -m venv "$VENV_DIR"
fi

echo "[+] Installing/upgrading dependencies"
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install -r "$ROOT/requirements.txt"

UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
echo "[+] Writing systemd unit to $UNIT_FILE"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=Streamlit - SRE Maturity Assessment (${SERVICE_NAME})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
Environment=PATH=${VENV_DIR}/bin
Environment=HOME=${APP_DIR}
ExecStart=${VENV_DIR}/bin/streamlit run ${APP_DIR}/Home.py --server.address 127.0.0.1 --server.port ${PORT} --server.headless true
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "[+] Reloading systemd and enabling service"
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
systemctl status --no-pager "$SERVICE_NAME" || true

echo "[+] Done. Service name: ${SERVICE_NAME}. Port: ${PORT}."

