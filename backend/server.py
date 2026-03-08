#!/usr/bin/env python3
"""FastAPI server exposing the log analysis agent via Claude Agent SDK."""

import logging
import uuid

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import OUTPUTS_DIR, ALLOWED_ORIGINS
from core.models import UploadResponse, AskRequest, AskResponse, HealthResponse
from core.session import create_session, get_session_paths, generate_session_id
import core.agent as _agent

log = logging.getLogger("inlog-agent")

app = FastAPI(title="Inlog Agent", version="0.1.0")

# CORS for local frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated chart images (subdirs served recursively: /outputs/{sid}/chart.png)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile):
    """Accept a log file upload, auto-create a session, and save the file."""

    # Auto-create a new session for each upload
    session_id = generate_session_id()
    paths = create_session(session_id)

    file_id = uuid.uuid4().hex[:12]
    dest = paths["uploads_dir"] / f"{file_id}.log"

    # Save uploaded file to session-scoped directory
    content = await file.read()
    dest.write_bytes(content)

    log.info(
        "Uploaded file '%s' as %s in session %s (%d bytes)",
        file.filename, file_id, session_id, len(content),
    )
    return UploadResponse(file_id=file_id, filename=file.filename, session_id=session_id)


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """Send a question to the Claude agent with session and file context."""

    result = await _agent.run_agent(request.session_id, request.file_id, request.question)
    return AskResponse(**result)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


if __name__ == "__main__":
    import uvicorn

    log.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
