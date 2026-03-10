#!/usr/bin/env bash
# Run on the VPS to deploy the latest clutch-card-football code from GitHub.
# Usage: bash /opt/clutch-card-football/deploy/server-deploy.sh [branch]
set -euo pipefail

APP_DIR="/opt/clutch-card-football"
SERVICE="clutch-card-football"
BRANCH="${1:-main}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "This script must run as root." >&2
  exit 1
fi

if [[ ! "$BRANCH" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  echo "Invalid branch name: $BRANCH" >&2
  exit 1
fi

echo "→ Deploying clutch-card-football branch: $BRANCH"
cd "$APP_DIR"

echo "→ Fetching latest code from GitHub..."
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if ! command -v python3 >/dev/null 2>&1; then
  echo "→ Installing Python runtime..."
  apt-get update
  apt-get install -y python3 python3-venv python3-pip
fi

echo "→ Installing Python dependencies..."
python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q pygbag

echo "→ Building browser bundle with pygbag..."
rm -rf ccf_pygame/build/web
mkdir -p ccf_pygame/build/web ccf_pygame/build/web-cache
venv/bin/python -m pygbag --build ccf_pygame

if [[ ! -f ccf_pygame/build/web/index.html ]]; then
  echo "Browser build failed: missing ccf_pygame/build/web/index.html" >&2
  exit 1
fi

echo "→ Updating systemd service..."
cp deploy/clutch-card-football.service /etc/systemd/system/clutch-card-football.service
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null 2>&1 || true

echo "→ Restarting service..."
systemctl restart "$SERVICE"

echo "✓ VPS deploy complete"
