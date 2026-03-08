#!/usr/bin/env bash
set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

[ -f "$PROJECT_DIR/.env" ] || { echo "Error: .env not found. Copy .env.example and add your API key."; exit 1; }

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM

echo "==> Starting backend on http://localhost:8000"
(cd "$PROJECT_DIR/backend" && uv run python server.py) &
BACKEND_PID=$!

sleep 1

echo "==> Starting frontend on http://localhost:5173"
(cd "$PROJECT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "==> Open http://localhost:5173"
echo "==> Press Ctrl+C to stop"
echo ""

wait
