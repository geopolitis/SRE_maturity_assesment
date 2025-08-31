#!/usr/bin/env bash
set -euo pipefail

# Clone this repo into a target directory and start Streamlit.
# Usage:
#   ./scripts/clone_and_run.sh [TARGET_DIR] [PORT] [ADDRESS]
# Defaults:
#   TARGET_DIR=/opt/assessment-app/app
#   PORT=8502
#   ADDRESS=127.0.0.1

REPO_URL="https://github.com/geopolitis/SRE_maturity_assesment.git"
TARGET_DIR="${1:-/opt/assessment-app/app}"
PORT="${2:-8502}"
ADDRESS="${3:-127.0.0.1}"

sudo mkdir -p "$(dirname "$TARGET_DIR")"
if [[ -d "$TARGET_DIR/.git" ]]; then
  echo "[+] Repo exists at $TARGET_DIR, pulling latest..."
  sudo git -C "$TARGET_DIR" pull --ff-only
else
  echo "[+] Cloning into $TARGET_DIR"
  sudo git clone "$REPO_URL" "$TARGET_DIR"
fi

echo "[+] Launching app from $TARGET_DIR on ${ADDRESS}:${PORT}"
cd "$TARGET_DIR"
chmod +x "$TARGET_DIR"/scripts/*.sh || true
PORT="$PORT" ADDRESS="$ADDRESS" bash ./scripts/run_streamlit.sh
