"""
setup_session.py — Log Analysis Agent Session Initializer

Usage:
    python agent/code/setup_session.py --folder my-session

Creates all session directories and writes initial state files.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


AGENT_ROOT = Path(__file__).parent.parent  # → agent/

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def create_directories(sid: str) -> None:
    """Create all session-specific directories."""
    dirs = [
        AGENT_ROOT / "scripts" / sid,
        AGENT_ROOT / "memory" / sid,
        AGENT_ROOT / "output" / sid,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    log.info("Created %d directories for session '%s'", len(dirs), sid)


def write_state_files(sid: str) -> None:
    """Write initial memory state files."""
    memory_dir = AGENT_ROOT / "memory" / sid
    now = datetime.now(timezone.utc).isoformat()

    # state.json — tracks current workflow position
    state = {
        "session_id": sid,
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
    (memory_dir / "state.json").write_text(json.dumps(state, indent=2))

    # todos.md — workflow checklist
    todos = f"""# Log Analysis — Session: {sid}

## Workflow Checklist

- [ ] Step 0: INIT — verify inputs, check uploaded log files
- [ ] Step 1: INFER SCHEMA — read sample lines, propose schema
- [ ] Step 2: VERIFY SCHEMA — user approves/edits schema *(WAITING)*
- [ ] Step 3: PARSE & LOAD — parse full file, load into SQLite
- [ ] Step 4: VISUALIZE — generate charts, answer questions

Created: {now}
"""
    (memory_dir / "todos.md").write_text(todos)

    # decisions.md — log of key decisions
    decisions = f"""# Decisions Log — Session: {sid}

## [{now[:10]}] Session initialized
**Context:** New log analysis session started
**Session ID:** {sid}
"""
    (memory_dir / "decisions.md").write_text(decisions)

    log.info("Wrote state.json, todos.md, decisions.md for session '%s'", sid)


def write_settings(sid: str) -> None:
    """Write session-scoped .claude/settings.json with folder access restrictions."""
    settings = {
        "permissions": {
            "allow": [
                # Read tools — always allowed
                "Read",
                "Glob",
                "Grep",

                # Write to this session's directories only
                f"Write(scripts/{sid}/**)",
                f"Write(memory/{sid}/**)",
                f"Write(output/{sid}/**)",

                # Write to shared project data
                "Write(../data/schemas/**)",
                "Write(../outputs/**)",

                # Edit same paths
                f"Edit(scripts/{sid}/**)",
                f"Edit(memory/{sid}/**)",
                f"Edit(output/{sid}/**)",
                "Edit(../data/schemas/**)",
                "Edit(../outputs/**)",

                # Bash: run session scripts and setup
                "Bash(python code/setup_session.py *)",
                f"Bash(python scripts/{sid}/**)",
                "Bash(python -c *)",
                "Bash(ls *)",
                "Bash(wc *)",
                "Bash(pwd)",
            ],
            "deny": [
                # Protect read-only directories
                "Write(../data/uploads/**)",
                "Write(code/**)",
                "Write(CLAUDE.md)",
                "Write(.claude/**)",
                "Edit(../data/uploads/**)",
                "Edit(code/**)",
                "Edit(CLAUDE.md)",
                "Edit(.claude/**)",

                # Destructive commands
                "Bash(rm *)",
                "Bash(git *)",
                "Bash(sudo *)",
                "Bash(curl *)",
                "Bash(wget *)",
                "Bash(chmod *)",
                "Bash(chown *)",
                "Bash(kill *)",
            ],
        },
    }

    settings_path = AGENT_ROOT / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2))
    log.info("Wrote session-scoped .claude/settings.json for session '%s'", sid)


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a log analysis agent session")
    parser.add_argument(
        "--folder",
        required=True,
        help="Session folder name (e.g. syslog-2025). Used for all session directories.",
    )
    args = parser.parse_args()

    sid = args.folder.strip()
    if not sid or "/" in sid or "\\" in sid or sid.startswith("."):
        log.error("Invalid folder name '%s'. Use alphanumeric with hyphens only.", sid)
        sys.exit(1)

    log.info("Initializing log analysis session: %s", sid)

    create_directories(sid)
    write_state_files(sid)
    write_settings(sid)

    log.info("Session '%s' initialized successfully", sid)
    log.info("Next: upload log files via web UI or place them in data/uploads/")


if __name__ == "__main__":
    main()
