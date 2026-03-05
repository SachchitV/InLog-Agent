#!/usr/bin/env bash
# Start backend and frontend for Inlog Agent

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Check for .env
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Copy .env.example to .env and add your API key."
    exit 1
fi

# Trap to kill background processes on exit
trap 'echo ""; echo "Shutting down..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM

echo "==> Starting backend on http://localhost:8000"
uv run python "$PROJECT_DIR/server.py" &
BACKEND_PID=$!

sleep 1

echo "==> Starting frontend on http://localhost:5173"
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

echo ""
echo "==> Open http://localhost:5173"
echo "==> Press Ctrl+C to stop"
echo ""

# Wait for either process to exit
wait
