"""Integration test: full user journey through the real Claude Agent SDK.

Upload → infer schema → confirm & parse → charts generated.

Uses rfnd_flight_telemetry.csv (ArduPilot rangefinder sensor log — CSV with
timestamps, sparse numeric columns, ~3MB / ~60k rows at 50ms intervals).

Run:
    cd backend && uv run pytest tests/agent/test_agent_flow.py -v -s --log-cli-level=INFO

Requires ANTHROPIC_API_KEY in the environment.
"""

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path

import pytest

os.environ.pop("CLAUDECODE", None)

from core.session import create_session, generate_session_id
from core.agent import run_agent

log = logging.getLogger(__name__)

SAMPLE_LOG = Path(__file__).resolve().parent.parent / "fixtures" / "rfnd_flight_telemetry.csv"


def _run(coro):
    """Run an async coroutine synchronously in a fresh event loop.

    Used to call async agent functions from synchronous pytest test functions
    without requiring pytest-asyncio.

    Args:
        coro: An awaitable coroutine object to execute.

    Returns:
        Whatever the coroutine returns.

    Raises:
        Any exception raised by the coroutine is propagated as-is.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.mark.integration
def test_full_user_journey():
    """Simulate the complete user journey against the live Claude Agent SDK.

    Covers the two-turn interaction:
      1. Upload a log file and request schema inference.
      2. Confirm the schema and request parsing + chart generation.

    Assertions:
      - Agent returns a non-empty answer for both turns.
      - Schema JSON is written to ``schemas/{file_id}.json`` with at least one table.
      - SQLite database is created at ``store.db``.
      - At least one chart PNG is written to ``outputs/{sid}/``.

    Raises:
        AssertionError: If any of the above artifacts are missing or malformed.
        Exception: Any unhandled SDK or network error propagates from ``run_agent``.
    """

    session_id = generate_session_id()
    file_id = "flight_telemetry"
    paths = create_session(session_id)

    # --- Upload: copy fixture into session (mirrors what POST /upload does) ---
    dest = paths["uploads_dir"] / f"{file_id}.log"
    shutil.copy2(SAMPLE_LOG, dest)
    log.info("Uploaded %s (%d bytes) into session %s", dest.name, dest.stat().st_size, session_id)

    # --- Step 1: User uploads file, frontend auto-sends initial analysis request ---
    result = _run(run_agent(
        session_id, file_id,
        "Analyze the log file. Read the file, infer the schema, "
        "and show me the proposed table structure.",
    ))
    log.info("Infer: turns=%s, cost=$%s, answer=%d chars", result["num_turns"], result["cost_usd"], len(result["answer"]))
    assert result["answer"], "Empty answer from schema inference"

    schema_path = paths["schemas_dir"] / f"{file_id}.json"
    assert schema_path.exists(), f"Agent did not write schema to {schema_path}"
    schema = json.loads(schema_path.read_text())

    # Agent may write "tables" (array), "table" (object), or flat with "columns"
    if "tables" in schema:
        tables = schema["tables"]
    elif "table" in schema:
        tables = [schema["table"]]
    elif "columns" in schema:
        tables = [{"name": schema.get("table_name", "unknown"), "columns": schema["columns"]}]
    else:
        tables = []
    assert len(tables) > 0, f"No tables found in schema keys: {list(schema.keys())}"
    log.info("Schema tables: %s", [t.get("name") for t in tables])

    # --- Step 2: User confirms schema, agent parses + generates charts ---
    result = _run(run_agent(
        session_id, file_id,
        "Looks good, parse it and generate charts.",
    ))
    log.info("Confirm: turns=%s, cost=$%s, answer=%d chars", result["num_turns"], result["cost_usd"], len(result["answer"]))
    assert result["answer"], "Empty answer from confirm step"

    # DB should exist with data
    assert paths["db_path"].exists(), f"SQLite DB not created at {paths['db_path']}"

    # At least one chart should have been generated
    charts = list(paths["outputs_dir"].glob("*.png"))
    log.info("Charts: %s", [c.name for c in charts])
    assert len(charts) > 0, f"No charts in {paths['outputs_dir']}"

    log.info("Session artifacts preserved at: data/%s/ and outputs/%s/", session_id, session_id)
