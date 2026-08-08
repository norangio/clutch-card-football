#!/usr/bin/env bash
# Run the whole local stack: FastAPI on :8000, Vite on :5173.
# Vite proxies /api to the backend, so the app stays same-origin.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ ! -x .venv/bin/python ]]; then
  echo "→ Creating .venv"
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements-api.txt -r requirements-desktop.txt
fi
[[ -d web/node_modules ]] || (echo "→ Installing web deps"; npm install --prefix web)

.venv/bin/python -m uvicorn web_api.app:app --port 8000 --log-level warning &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

echo "→ API   http://localhost:8000"
echo "→ Game  http://localhost:5173   (append ?mock=1 to run without the API)"
npm run dev --prefix web
