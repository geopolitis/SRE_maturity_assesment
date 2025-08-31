#!/usr/bin/env bash
set -euo pipefail

# Clone this repo into a target directory and install a systemd service.
# Usage (as root):
#   ./scripts/clone_and_install_service.sh [TARGET_DIR] [SERVICE_NAME] [USER] [PORT]
# Defaults:
#   TARGET_DIR=/opt/assessment-app/app
#   SERVICE_NAME=streamlit-assessment
#   USER=streamlit
#   PORT=8502

REPO_URL="https://github.com/geopolitis/SRE_maturity_assesment.git"
TARGET_DIR="${1:-/opt/assessment-app/app}"
SERVICE_NAME="${2:-streamlit-assessment}"
RUN_USER="${3:-streamlit}"
PORT="${4:-8502}"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

mkdir -p "$(dirname "$TARGET_DIR")"
if [[ -d "$TARGET_DIR/.git" ]]; then
  echo "[+] Repo exists at $TARGET_DIR, pulling latest..."
  git -C "$TARGET_DIR" pull --ff-only
else
  echo "[+] Cloning into $TARGET_DIR"
  git clone "$REPO_URL" "$TARGET_DIR"
fi

chown -R "$RUN_USER":"$RUN_USER" "$TARGET_DIR" || true

cd "$TARGET_DIR"
# Ensure scripts are executable and runnable
chmod +x "$TARGET_DIR"/scripts/*.sh || true

# Prewarm venv and dependencies as the run user (ignores run failure)
sudo -u "$RUN_USER" bash -lc "VENV_DIR='$TARGET_DIR/.venv' PORT='$PORT' ADDRESS='127.0.0.1' bash ./scripts/run_streamlit.sh || true"

# Install the systemd service (as root)
bash ./scripts/install_service.sh "$SERVICE_NAME" "$RUN_USER" "$PORT"

systemctl status --no-pager "$SERVICE_NAME" || true

echo "[+] Done. Service: $SERVICE_NAME, App dir: $TARGET_DIR, Port: $PORT"
