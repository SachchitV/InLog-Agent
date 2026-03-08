# Inlog-Agent

## Project Overview
AI-assisted log structuring and visualization tool. Users upload timestamped text logs via a React frontend. A Claude agent (via `claude-agent-sdk`) reads the log, infers the best schema, creates SQLite tables, parses the file, and generates charts.

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, Claude Agent SDK
- **Frontend**: React 18, Vite
- **Data**: SQLite, pandas, matplotlib

## Common Commands
- `./setup.sh` - Install all dependencies
- `./start.sh` - Start backend + frontend together
- `cd backend && uv run python server.py` - Start backend only (port 8000)
- `cd frontend && npm run dev` - Start frontend only (port 5173)
- `cd backend && uv run pytest -v` - Run tests

## Quick Start
```bash
./setup.sh
cp .env.example .env  # Add your ANTHROPIC_API_KEY
./start.sh
# Open http://localhost:5173
```

## Project Structure
```
backend/
  server.py                # FastAPI: /upload, /ask, /health + static serving
  core/
    config.py              # Env loading, paths, logging setup
    models.py              # Pydantic request/response models
  agent/                   # Claude Agent SDK package
    code/
      agent.py             # Agent query logic + prompt building
      skills/              # Skill implementations
  tests/                   # pytest test suite
  sample_logs/             # Sample log files for testing
  data/                    # Runtime (gitignored)
    uploads/               # Uploaded log files
    schemas/               # Inferred schema JSON
    store.db               # SQLite database
  outputs/                 # Generated chart PNGs (gitignored)
  pyproject.toml           # Python dependencies
frontend/
  src/
    App.jsx                # Landing -> two-pane layout
    components/
      FileDrop.jsx         # Drag-and-drop upload
      FileList.jsx         # Uploaded files sidebar
      ChatPane.jsx         # Chat interface
      SchemaView.jsx       # Schema display in chat
      ChartDisplay.jsx     # Chart images in chat
.env                       # API keys (gitignored)
.env.example               # Template for .env
```

## Virtual Environment
This project uses `uv` for dependency management. The `.venv` lives at `backend/.venv`. All `uv run` commands must be run from `backend/`. No manual venv activation needed.

---

# Coding Guidelines

## Incremental Development
- **40-50 lines max per step**: Break tasks into small chunks
- **One change at a time**: Complete each step before moving on

## Code Quality
- **Comments**:
  - Function docstrings: Explain both the logic (what it does) and intention (why it exists)
  - Inline comments: Use one-liner comments at regular intervals for easy readability
- **Spacing**: Blank lines between logical blocks

## Logging
- Use `logging.getLogger(__name__)` in every module — never `print()`

## Error Handling
- **Avoid try-except**: Do not use unless absolutely necessary
- Let errors propagate naturally for easier debugging

## Repository Etiquette
- **Main branch**: `main`
- **Commit messages**: Descriptive, include what and why
