"""Session management: path resolution and session creation.

Merges logic from agent/code/setup_session.py (dir creation, state writing)
and agent/code/skills/lib/session.py (path resolution).
Todos are handled by Claude Code's built-in TodoWrite/TodoRead tools.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from core.config import DATA_DIR, OUTPUTS_DIR, PROJECT_DIR

log = logging.getLogger(__name__)

# Agent folder — the pure Claude Code project
AGENT_DIR = PROJECT_DIR / "agent"


def get_session_paths(session_id: str) -> dict:
    """Return all canonical paths for a given session.

    Every session has three scoped areas:
    - workspace/{sid}/          — agent working memory + scripts
    - data/{sid}/               — uploads, schemas, SQLite DB
    - outputs/{sid}/            — generated chart PNGs
    """

    return {
        # Agent workspace (state, decisions, scripts)
        "workspace":    AGENT_DIR / "workspace" / session_id,
        "scripts":      AGENT_DIR / "workspace" / session_id / "scripts",
        "state":        AGENT_DIR / "workspace" / session_id / "state.json",
        "decisions":    AGENT_DIR / "workspace" / session_id / "decisions.md",

        # Session-scoped data (shared with FastAPI server)
        "uploads_dir":  DATA_DIR / session_id / "uploads",
        "schemas_dir":  DATA_DIR / session_id / "schemas",
        "db_path":      DATA_DIR / session_id / "store.db",

        # Session-scoped outputs
        "outputs_dir":  OUTPUTS_DIR / session_id,

        # Root references
        "agent_root":   AGENT_DIR,
        "project_root": PROJECT_DIR,
    }


def create_session(session_id: str) -> dict:
    """Create all directories and initial state files for a new session.

    Returns the session paths dict (same as get_session_paths).
    """

    paths = get_session_paths(session_id)
    now = datetime.now(timezone.utc).isoformat()

    # Create all session directories
    dirs_to_create = [
        paths["workspace"],
        paths["scripts"],
        paths["uploads_dir"],
        paths["schemas_dir"],
        paths["outputs_dir"],
    ]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

    log.info("Created directories for session '%s'", session_id)

    # Write initial state.json — tracks workflow position
    state = {
        "session_id": session_id,
        "step": 0,
        "step_name": "INIT",
        "status": "awaiting_inputs",
        "created_at": now,
        "updated_at": now,
        "files": {},
        "flags": {
            "schema_approved": False,
            "data_loaded": False,
        },
    }
    paths["state"].write_text(json.dumps(state, indent=2))

    # Write initial decisions.md — records key decisions across the session
    decisions = (
        f"# Decisions Log — Session: {session_id}\n\n"
        f"## [{now[:10]}] Session initialized\n"
        f"**Context:** New log analysis session started\n"
        f"**Session ID:** {session_id}\n"
    )
    paths["decisions"].write_text(decisions)

    log.info("Initialized session '%s'", session_id)
    return paths


def generate_session_id() -> str:
    """Generate a short unique session ID."""
    return uuid.uuid4().hex[:12]
