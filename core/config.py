"""Server configuration: env loading, logging, paths."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# CORS allowed origins (comma-separated in env, defaults to local dev)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# Runtime directories (server-owned)
UPLOADS_DIR = PROJECT_DIR / "data" / "uploads"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

