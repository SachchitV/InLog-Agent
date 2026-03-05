#!/usr/bin/env bash
# Install all dependencies for Inlog Agent

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "==> Installing Python dependencies..."
uv sync

echo "==> Creating runtime directories..."
mkdir -p data/uploads data/schemas outputs

echo "==> Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend"
npm install --silent
cd "$PROJECT_DIR"

echo ""
echo "Setup complete. Next steps:"
echo "  1. Copy .env.example to .env and add your ANTHROPIC_API_KEY"
echo "  2. Run: ./start.sh"
