"""E2E tests for POST /ask endpoint."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_query_mock(answer: str = "Analysis complete.", cost: float = 0.002, turns: int = 2):
    """Return an async generator function that simulates a claude_agent_sdk query response.

    Yields one AssistantMessage followed by a ResultMessage — matching the
    real SDK stream so run_agent's message-processing logic is fully exercised.
    """
    async def _fake_query(*args, **kwargs):
        yield AssistantMessage(
            content=[TextBlock(text=answer)],
            model="claude-sonnet-4-6",
        )
        yield ResultMessage(
            subtype="result",
            duration_ms=500,
            duration_api_ms=400,
            is_error=False,
            num_turns=turns,
            session_id="test-session",
            total_cost_usd=cost,
            result=answer,
        )

    return _fake_query


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_ask(client, sample_log):
    """POST /ask returns a well-formed AskResponse, exercising real run_agent logic."""
    upload = client.post(
        "/upload",
        files={"file": ("app_server.log", sample_log, "text/plain")},
    )
    upload_data = upload.json()
    file_id = upload_data["file_id"]
    session_id = upload_data["session_id"]

    with patch("core.agent.query", new=_make_query_mock()):
        resp = client.post("/ask", json={"session_id": session_id, "file_id": file_id, "question": "Summarise errors."})

    # Endpoint must respond successfully
    assert resp.status_code == 200

    # Response must be JSON
    assert "application/json" in resp.headers["content-type"]

    data = resp.json()

    # All AskResponse fields must be present
    assert "answer" in data
    assert "files" in data
    assert "cost_usd" in data
    assert "num_turns" in data

    # Answer must be a non-empty string matching what the mock returned
    assert data["answer"] == "Analysis complete."

    # files must be a list (empty because mock didn't call Write to outputs/)
    assert isinstance(data["files"], list)

    # Cost and turns must reflect mock values
    assert data["cost_usd"] == 0.002
    assert data["num_turns"] == 2


@pytest.mark.smoke
def test_ask_prompt_contains_file_id_and_question(client, sample_log):
    """The prompt forwarded to query must embed the file_id and the user's question."""
    upload = client.post(
        "/upload",
        files={"file": ("app_server.log", sample_log, "text/plain")},
    )
    upload_data = upload.json()
    file_id = upload_data["file_id"]
    session_id = upload_data["session_id"]
    question = "How many errors occurred?"

    captured: dict = {}

    async def _capturing_query(*args, **kwargs):
        # Capture the prompt kwarg passed by run_agent
        captured["prompt"] = kwargs.get("prompt", args[0] if args else "")
        yield AssistantMessage(content=[TextBlock(text="ok")], model="claude-sonnet-4-6")
        yield ResultMessage(
            subtype="result", duration_ms=100, duration_api_ms=90,
            is_error=False, num_turns=1, session_id="s", result="ok",
        )

    with patch("core.agent.query", new=_capturing_query):
        client.post("/ask", json={"session_id": session_id, "file_id": file_id, "question": question})

    # file_id must appear in the prompt so the agent knows which log to read
    assert file_id in captured["prompt"]

    # The user's question must be passed through unchanged
    assert question in captured["prompt"]


@pytest.mark.smoke
def test_ask_missing_fields(client):
    """POST /ask with an empty body returns 422 Unprocessable Entity."""
    resp = client.post("/ask", json={})

    # FastAPI must reject incomplete request bodies
    assert resp.status_code == 422


@pytest.mark.smoke
def test_ask_missing_question(client):
    """POST /ask with file_id but no question returns 422."""
    resp = client.post("/ask", json={"file_id": "abc123"})

    # question is a required field — must be rejected
    assert resp.status_code == 422


@pytest.mark.smoke
def test_ask_missing_file_id(client):
    """POST /ask with question but no file_id returns 422."""
    resp = client.post("/ask", json={"question": "What happened?"})

    # file_id is a required field — must be rejected
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Integration test (skipped by default — run with: pytest -m integration)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_ask_end_to_end(client, sample_log):
    """Full flow: upload → infer schema → confirm → assert charts generated."""

    # Step 1: upload the sample log (auto-creates session)
    upload_resp = client.post(
        "/upload",
        files={"file": ("app_server.log", sample_log, "text/plain")},
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    file_id = upload_data["file_id"]
    session_id = upload_data["session_id"]
    log.info("Uploaded file_id=%s in session=%s", file_id, session_id)

    # Session-scoped paths for assertions
    backend_dir = Path(__file__).resolve().parent.parent.parent
    schemas_dir = backend_dir / "data" / session_id / "schemas"
    outputs_dir = backend_dir / "outputs" / session_id

    # Step 2: ask the agent to infer a schema
    infer_resp = client.post(
        "/ask",
        json={"session_id": session_id, "file_id": file_id, "question": "Analyse this log file."},
    )
    assert infer_resp.status_code == 200
    infer_data = infer_resp.json()

    # Agent must return a non-empty answer and create a schema file
    assert infer_data["answer"], "Agent returned empty answer on schema inference"
    assert (schemas_dir / f"{file_id}.json").exists(), "Schema file was not created"
    log.info("Schema inferred: turns=%s cost=$%s", infer_data["num_turns"], infer_data["cost_usd"])

    # Step 3: confirm schema — triggers parsing + chart generation
    confirm_resp = client.post(
        "/ask",
        json={"session_id": session_id, "file_id": file_id, "question": "Looks good, parse it and generate charts."},
    )
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()

    # Agent must return a non-empty answer after confirmation
    assert confirm_data["answer"], "Agent returned empty answer on confirm"
    log.info("Parsed + visualised: turns=%s cost=$%s", confirm_data["num_turns"], confirm_data["cost_usd"])

    # At least one chart PNG must have been written to outputs/{session_id}/
    chart_files = list(outputs_dir.glob("*.png"))
    assert len(chart_files) > 0, f"No chart PNGs found in {outputs_dir}"
    log.info("Generated %d chart(s): %s", len(chart_files), [f.name for f in chart_files])
