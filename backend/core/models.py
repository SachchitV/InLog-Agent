"""Pydantic request/response models for API endpoints."""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response returned by POST /upload.

    Attributes:
        file_id: Randomly generated 12-char hex ID assigned to the uploaded file.
        filename: Original filename as sent by the client (for display only).
        session_id: Randomly generated 12-char hex ID for the new session.
    """

    file_id: str
    filename: str
    session_id: str


class AskRequest(BaseModel):
    """Request body for POST /ask.

    Attributes:
        session_id: Session ID returned by a prior POST /upload call.
        file_id: File ID returned by a prior POST /upload call.
        question: Free-text question or instruction from the user.
    """

    session_id: str
    file_id: str
    question: str


class AskResponse(BaseModel):
    """Response returned by POST /ask.

    Attributes:
        answer: Text response from the Claude agent.
        files: Relative paths of chart PNGs written to ``outputs/{sid}/``
            during this turn (empty list if no charts were generated).
        todos: Final todo-list snapshot from the agent's last ``TodoWrite``
            call, each item being a dict with ``content`` and ``status`` keys.
            Empty list if the agent did not use TodoWrite.
        cost_usd: Total Anthropic API cost for this agent turn in USD.
            ``None`` if the SDK did not report a cost.
        num_turns: Number of agentic turns taken.
            ``None`` if the SDK did not report turn count.
    """

    answer: str
    files: list[str]
    todos: list[dict] = []
    cost_usd: float | None = None
    num_turns: int | None = None


class HealthResponse(BaseModel):
    """Response returned by GET /health.

    Attributes:
        status: Always ``"ok"`` while the server is running.
    """

    status: str
