"""Session management: path resolution and session creation.

Todos are handled by Claude Code's built-in TodoWrite/TodoRead tools.
"""

import logging
import uuid

from core.config import DATA_DIR, OUTPUTS_DIR, PROJECT_DIR

log = logging.getLogger(__name__)

# Agent folder — the pure Claude Code project
AGENT_DIR = PROJECT_DIR / "agent"


def get_session_paths(session_id: str) -> dict:
    """Return all canonical paths for a given session without touching the filesystem.

    Every session spans three scoped areas:
    - ``agent/workspace/{sid}/`` — agent scripts directory
    - ``backend/data/{sid}/``    — uploads, schemas, SQLite DB
    - ``backend/outputs/{sid}/`` — generated chart PNGs

    Args:
        session_id: The unique session identifier (12-char hex).

    Returns:
        dict: Mapping of logical names to ``pathlib.Path`` objects:
            ``workspace``, ``scripts``, ``uploads_dir``, ``schemas_dir``,
            ``db_path``, ``outputs_dir``, ``agent_root``, ``project_root``.
    """

    return {
        # Agent workspace (scripts only — state derived from filesystem)
        "workspace":    AGENT_DIR / "workspace" / session_id,
        "scripts":      AGENT_DIR / "workspace" / session_id / "scripts",

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
    """Create all directories for a new session and return their paths.

    Idempotent — safe to call if directories already exist. No state files are
    written; session progress is inferred from filesystem artifacts (schema
    JSON, SQLite DB, chart PNGs). Todos are managed by the agent via Claude
    Code's built-in TodoWrite/TodoRead tools.

    Args:
        session_id: The unique session identifier (12-char hex).

    Returns:
        dict: Same mapping returned by ``get_session_paths``, with all
            directories guaranteed to exist.
    """

    paths = get_session_paths(session_id)

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

    log.info("Created session '%s'", session_id)
    return paths


def generate_session_id() -> str:
    """Generate a short unique session ID.

    Returns:
        str: A 12-character lowercase hex string derived from a UUID4.
    """
    return uuid.uuid4().hex[:12]
