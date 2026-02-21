#!/usr/bin/env python3
"""FastAPI server exposing the log analysis agent via Claude Agent SDK."""

import logging
import uuid

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import UPLOADS_DIR, OUTPUTS_DIR
from core.models import UploadResponse, AskRequest, AskResponse
from core.agent import run_agent

log = logging.getLogger("inlog-agent")

app = FastAPI(title="Inlog Agent", version="0.1.0")

# CORS for local frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated chart images
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile):
    """Accept a log file upload, save it, and return a file_id."""

    file_id = uuid.uuid4().hex[:12]
    dest = UPLOADS_DIR / f"{file_id}.log"

    # Save uploaded file
    content = await file.read()
    dest.write_bytes(content)

    log.info("Uploaded file '%s' as %s (%d bytes)", file.filename, file_id, len(content))
    return UploadResponse(file_id=file_id, filename=file.filename)


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """Send a question to the Claude agent with file context."""

    result = await run_agent(request.file_id, request.question)
    return AskResponse(**result)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    log.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
