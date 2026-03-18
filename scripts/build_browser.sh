#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! python3 -m pygbag --help >/dev/null 2>&1; then
  echo "pygbag is not installed in the active Python environment." >&2
  echo 'Install it with: pip install "pygbag>=0.9.3,<1"' >&2
  exit 1
fi

python3 -m pygbag --build --archive --ume_block 0 --width 960 --height 720 --title "Clutch Card Football" "$@" ccf_pygame
