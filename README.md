# Inlog Agent

AI-assisted log structuring and visualization tool. Upload a timestamped text log, and a Claude agent infers the schema, parses the file into SQLite, and generates charts — all through a chat interface.

## How It Works

1. Drop a log file on the landing page
2. The agent reads a sample, infers the schema, and proposes a table structure
3. Review the schema in chat — request changes or confirm
4. Agent parses the full file, stores it in SQLite, and generates overview charts
5. Continue chatting to ask questions, refine, or create more visualizations

## Quick Start (Docker)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows, Mac, Linux):

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

docker compose up
```

Open http://localhost:5173 in your browser.

## Manual Setup

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and Node.js 18+.

```bash
./setup.sh

cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

./start.sh
```

Open http://localhost:5173 in your browser.

## Project Structure

```
backend/
  server.py                # FastAPI server: /upload, /ask, /health
  core/
    config.py              # Env loading, paths, logging
    models.py              # Pydantic request/response models
  agent/                   # Claude Agent SDK package
    code/
      agent.py             # Agent query logic
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
      SchemaView.jsx       # Schema table display
      ChartDisplay.jsx     # Chart image display
.env                       # API keys (gitignored)
.env.example               # Template for .env
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Upload a log file. Returns `{ file_id, filename }` |
| `POST` | `/ask` | Send a question with `{ question, file_id }`. Returns `{ answer, files, cost_usd, num_turns }` |
| `GET` | `/health` | Health check |
| `GET` | `/outputs/{file}` | Serves generated chart images |

## Sample Logs

Two sample files are included in `sample_logs/` for testing:

- **`app_server.log`** — Application server log (88 lines): timestamps, levels, service sources, key=value pairs
- **`web_access.log`** — Apache combined access log (62 lines): IPs, users, HTTP methods, status codes, user agents
