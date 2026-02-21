# Inlog Agent

AI-assisted log structuring and visualization tool. Upload a timestamped text log, and a Claude agent infers the schema, parses the file into SQLite, and generates charts — all through a chat interface.

## How It Works

1. Drop a log file on the landing page
2. The agent reads a sample, infers the schema, and proposes a table structure
3. Review the schema in chat — request changes or confirm
4. Agent parses the full file, stores it in SQLite, and generates overview charts
5. Continue chatting to ask questions, refine, or create more visualizations

## Setup

```bash
# Clone and enter the project
cd inlog-agent

# Run the setup script (creates venv, installs deps, etc.)
./setup.sh

# Add your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## Running

```bash
# Start both backend and frontend
./setup.sh start

# Or start them separately:

# Backend (terminal 1)
source .venv/bin/activate
python server.py

# Frontend (terminal 2)
cd frontend && npm run dev
```

Open http://localhost:5173 in your browser.

## Project Structure

```
server.py                  # FastAPI server: /upload, /ask, /health
agent_prompt.md            # System prompt for the Claude agent
core/
  config.py                # Env loading, paths, logging
  models.py                # Pydantic request/response models
  agent.py                 # Claude Agent SDK query logic
plugin/
  plugin.json
  skills/
    log-analysis/SKILL.md  # Schema inference + parsing skill
    log-viz/SKILL.md        # Chart generation skill
frontend/
  src/
    App.jsx                # Landing -> two-pane layout
    components/
      FileDrop.jsx         # Drag-and-drop upload
      FileList.jsx         # Uploaded files sidebar
      ChatPane.jsx         # Chat interface
      SchemaView.jsx       # Schema table display
      ChartDisplay.jsx     # Chart image display
samples/                   # Sample log files for testing
data/                      # Runtime (gitignored)
  uploads/                 # Uploaded log files
  schemas/                 # Inferred schema JSON
  store.db                 # SQLite database
outputs/                   # Generated chart PNGs (gitignored)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Upload a log file. Returns `{ file_id, filename }` |
| `POST` | `/ask` | Send a question with `{ question, file_id }`. Returns `{ answer, files, cost_usd, num_turns }` |
| `GET` | `/health` | Health check |
| `GET` | `/outputs/{file}` | Serves generated chart images |

## Sample Logs

Two sample files are included in `samples/` for testing:

- **`app_server.log`** — Application server log (88 lines): timestamps, levels, service sources, key=value pairs
- **`web_access.log`** — Apache combined access log (62 lines): IPs, users, HTTP methods, status codes, user agents
