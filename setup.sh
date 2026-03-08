#!/usr/bin/env bash
# Install all dependencies for Inlog Agent

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Installing Python dependencies..."
(cd "$PROJECT_DIR/backend" && uv sync)

echo "==> Creating runtime directories..."
mkdir -p "$PROJECT_DIR/backend/data" "$PROJECT_DIR/backend/outputs"

echo "==> Installing frontend dependencies..."
(cd "$PROJECT_DIR/frontend" && npm install --silent)

echo ""
echo "Setup complete. Next steps:"
echo "  1. Copy .env.example to .env and add your ANTHROPIC_API_KEY"
echo "  2. Run: ./start.sh"
