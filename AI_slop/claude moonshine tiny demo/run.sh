#!/usr/bin/env bash
# One-command setup and launch for Linux.
#   ./run.sh                   # real Moonshine Tiny (downloads weights from Hugging Face on first run)
#   MOONSHINE_STUB=1 ./run.sh  # fake engine, for testing the UI without downloading the model
set -euo pipefail
cd "$(dirname "$0")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
MODE="real Moonshine Tiny"
[ "${MOONSHINE_STUB:-}" = "1" ] && MODE="stub (fake transcripts, no model download)"

echo "==> Moonshine Tiny demo: $MODE"
echo "==> Step 1/3: creating Python environment in .venv (first run only)"
if [ ! -f .venv/bin/activate ]; then
  rm -rf .venv
  python3 -m venv .venv || { echo "ERROR: could not create a venv. On Debian/Ubuntu run: sudo apt install python3-venv"; exit 1; }
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Step 2/3: installing packages (first run can take a few minutes; pip output is shown below)"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Step 3/3: starting server"
echo "    Open http://${HOST}:${PORT} in Chrome or Firefox. Press Ctrl+C to stop."
exec python -m uvicorn server:app --host "$HOST" --port "$PORT"
