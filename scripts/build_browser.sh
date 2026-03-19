#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$ROOT_DIR/.venv-build/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv-build/bin/python"
fi

if ! "$PYTHON_BIN" -c "import pygbag" >/dev/null 2>&1; then
  echo "pygbag is not installed in the active Python environment." >&2
  echo "Install it with: $PYTHON_BIN -m pip install \"pygbag>=0.9.3,<1>\"" >&2
  exit 1
fi

"$PYTHON_BIN" -m pygbag --build --archive --ume_block 0 --width 960 --height 720 --title "Clutch Card Football" "$@" ccf_pygame

"$PYTHON_BIN" "$ROOT_DIR/scripts/postprocess_browser_build.py"
