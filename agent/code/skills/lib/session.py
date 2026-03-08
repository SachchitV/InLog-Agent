"""
session.py — Shared path resolver for log analysis agent skill modules.

Usage:
    from code.skills.lib.session import get_session_paths
    paths = get_session_paths("my-session")
    print(paths["scripts"])
"""

from pathlib import Path


def get_session_paths(session_id: str) -> dict[str, Path]:
    """
    Returns a dict of all canonical paths for a given session.

    The agent_root is resolved relative to this file's location:
      code/skills/lib/session.py → agent/
    """
    agent_root = Path(__file__).parent.parent.parent.parent  # → agent/
    project_root = agent_root.parent  # → inlog-agent/

    return {
        # Session-scoped directories (agent writes here)
        "scripts":       agent_root / "scripts" / session_id,
        "memory":        agent_root / "memory" / session_id,
        "output":        agent_root / "output" / session_id,

        # Memory files
        "state":         agent_root / "memory" / session_id / "state.json",
        "todos":         agent_root / "memory" / session_id / "todos.md",
        "decisions":     agent_root / "memory" / session_id / "decisions.md",

        # Project-level data directories (shared with FastAPI server)
        "uploads_dir":   project_root / "data" / "uploads",
        "schemas_dir":   project_root / "data" / "schemas",
        "db_path":       project_root / "data" / "store.db",
        "outputs_dir":   project_root / "outputs",

        # Root references
        "agent_root":    agent_root,
        "project_root":  project_root,
    }
