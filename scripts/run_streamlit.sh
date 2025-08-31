#!/usr/bin/env bash
set -euo pipefail

# Simple runner for the SRE Maturity app.
# - Creates/uses a local virtualenv
# - Installs requirements if needed
# - Starts Streamlit bound to 127.0.0.1:8502 by default

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"

VENV_DIR="${VENV_DIR:-$ROOT/.venv}"
PORT="${PORT:-8502}"
ADDRESS="${ADDRESS:-127.0.0.1}"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[+] Creating venv at $VENV_DIR"
  python3 -m venv "$VENV_DIR" || true
fi

# If activate is missing, try recreating with upgrade-deps and bail with hint
if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
  echo "[!] venv activate not found; attempting to recreate with --upgrade-deps"
  python3 -m venv --clear --upgrade-deps "$VENV_DIR" || true
fi

if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
  echo "[!] Could not create a valid virtualenv at $VENV_DIR.\n    Ensure 'python3-venv' is installed (e.g., 'sudo apt-get install -y python3-venv') and rerun." >&2
  exit 1
fi

source "$VENV_DIR/bin/activate"

echo "[+] Ensuring pip/setuptools/wheel are up to date"
python -m pip install --upgrade pip setuptools wheel >/dev/null

echo "[+] Installing requirements"
pip install -r requirements.txt

# Optional Streamlit config for headless/proxy usage
CONF_DIR="$ROOT/.streamlit"
CONF_FILE="$CONF_DIR/config.toml"
if [[ ! -f "$CONF_FILE" ]]; then
  echo "[+] Writing default Streamlit config at $CONF_FILE"
  mkdir -p "$CONF_DIR"
  cat > "$CONF_FILE" <<EOF
server.headless = true
server.address = "${ADDRESS}"
server.port = ${PORT}
server.enableCORS = false
server.enableXsrfProtection = true
EOF
fi

echo "[+] Starting Streamlit on ${ADDRESS}:${PORT}"
exec streamlit run Home.py \
  --server.address "${ADDRESS}" \
  --server.port "${PORT}" \
  --server.headless true
