#!/usr/bin/env bash
# Run on the VPS to deploy the latest clutch-card-football code from GitHub.
# Usage: bash /opt/clutch-card-football/deploy/server-deploy.sh [branch]
set -euo pipefail

APP_DIR="/opt/clutch-card-football"
BRANCH="${1:-main}"
BROWSER_BUILD_CMD=(venv/bin/python -m pygbag --build --archive --ume_block 0 --width 960 --height 720 --title "Clutch Card Football" ccf_pygame)

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

echo "→ Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv python3-pip

echo "→ Installing Python dependencies..."
python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements-desktop.txt "pygbag>=0.9.3,<1"

echo "→ Building browser bundle..."
"${BROWSER_BUILD_CMD[@]}"

# pygbag hardcodes fb_ar to 1.77 (1280/720); fix to 1.33 (960/720)
sed -i 's/fb_ar   :  1\.77/fb_ar   :  1.33/' "$APP_DIR/ccf_pygame/build/web/index.html"

echo "→ Preparing static asset permissions..."
chown -R www-data:www-data "$APP_DIR/ccf_pygame/build"
find "$APP_DIR/ccf_pygame/build" -type d -exec chmod 755 {} +
find "$APP_DIR/ccf_pygame/build" -type f -exec chmod 644 {} +

echo "→ Disabling legacy launcher service..."
systemctl disable --now clutch-card-football >/dev/null 2>&1 || true

echo "✓ VPS deploy complete"
