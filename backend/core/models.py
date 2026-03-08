"""Pydantic request/response models for API endpoints."""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    session_id: str


class AskRequest(BaseModel):
    session_id: str
    file_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    files: list[str]
    cost_usd: float | None = None
    num_turns: int | None = None


class HealthResponse(BaseModel):
    status: str
