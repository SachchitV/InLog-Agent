#!/usr/bin/env bash
# Setup and startup script for Inlog Agent

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# --- Helper functions ---

setup_backend() {
    echo "==> Setting up Python virtual environment..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    source .venv/bin/activate

    echo "==> Installing Python dependencies..."
    pip install -q -r requirements.txt

    echo "==> Creating runtime directories..."
    mkdir -p data/uploads data/schemas outputs

    echo "==> Backend ready."
}

setup_frontend() {
    echo "==> Installing frontend dependencies..."
    cd "$PROJECT_DIR/frontend"
    npm install --silent
    cd "$PROJECT_DIR"

    echo "==> Frontend ready."
}

start_backend() {
    source "$PROJECT_DIR/.venv/bin/activate"
    echo "==> Starting backend on http://localhost:8000"
    python "$PROJECT_DIR/server.py" &
    BACKEND_PID=$!
}

start_frontend() {
    echo "==> Starting frontend on http://localhost:5173"
    cd "$PROJECT_DIR/frontend"
    npm run dev &
    FRONTEND_PID=$!
    cd "$PROJECT_DIR"
}

# --- Main ---

case "${1:-setup}" in
    setup)
        setup_backend
        setup_frontend
        echo ""
        echo "Setup complete. Next steps:"
        echo "  1. Copy .env.example to .env and add your ANTHROPIC_API_KEY"
        echo "  2. Run: ./setup.sh start"
        ;;

    start)
        # Check for .env
        if [ ! -f ".env" ]; then
            echo "Error: .env file not found. Copy .env.example to .env and add your API key."
            exit 1
        fi

        # Trap to kill background processes on exit
        trap 'echo ""; echo "Shutting down..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM

        start_backend
        sleep 1
        start_frontend

        echo ""
        echo "==> Open http://localhost:5173"
        echo "==> Press Ctrl+C to stop"
        echo ""

        # Wait for either process to exit
        wait
        ;;

    *)
        echo "Usage: ./setup.sh [setup|start]"
        echo "  setup  - Install dependencies (default)"
        echo "  start  - Start backend and frontend"
        exit 1
        ;;
esac
