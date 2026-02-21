"""Pydantic request/response models for API endpoints."""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: str
    filename: str


class AskRequest(BaseModel):
    question: str
    file_id: str


class AskResponse(BaseModel):
    answer: str
    files: list[str]
    cost_usd: float | None = None
    num_turns: int | None = None
