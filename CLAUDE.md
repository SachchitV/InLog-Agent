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
- `uv run python server.py` - Start backend only (port 8000)
- `cd frontend && npm run dev` - Start frontend only (port 5173)
- `uv run pytest -v` - Run tests

## Quick Start
```bash
./setup.sh
cp .env.example .env  # Add your ANTHROPIC_API_KEY
./start.sh
# Open http://localhost:5173
```

## Project Structure
```
server.py                  # FastAPI: /upload, /ask, /health + static serving
agent_prompt.md            # System prompt for the log analysis agent
core/
  config.py                # Env loading, paths, logging setup
  models.py                # Pydantic request/response models
  agent.py                 # Claude Agent SDK query logic + prompt building
plugin/
  plugin.json
  skills/
    log-analysis/SKILL.md  # Schema inference + parsing + SQLite
    log-viz/SKILL.md        # Chart generation
frontend/
  src/
    App.jsx                # Landing -> two-pane layout
    components/
      FileDrop.jsx         # Drag-and-drop upload
      FileList.jsx         # Uploaded files sidebar
      ChatPane.jsx         # Chat interface
      SchemaView.jsx       # Schema display in chat
      ChartDisplay.jsx     # Chart images in chat
samples/                   # Sample log files for testing
data/                      # Runtime (gitignored)
  uploads/                 # Uploaded log files
  schemas/                 # Inferred schema JSON
  store.db                 # SQLite database
outputs/                   # Generated chart PNGs (gitignored)
```

## Virtual Environment
This project uses `uv` for dependency management. Run Python commands via `uv run` (e.g. `uv run python server.py`). No manual venv activation needed.

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
