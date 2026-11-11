#!/usr/bin/env bash
# One-command setup and launch for Linux.
#   ./run.sh                 # real Moonshine Tiny (downloads weights from Hugging Face on first run)
#   MOONSHINE_STUB=1 ./run.sh  # fake engine, for testing the UI without downloading anything
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
echo "Open http://${HOST}:${PORT} in your browser (Chrome or Firefox)."
exec python -m uvicorn server:app --host "$HOST" --port "$PORT"
