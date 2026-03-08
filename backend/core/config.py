"""Server configuration: env loading, logging, paths."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ directory (parent of core/)
PROJECT_DIR = Path(__file__).resolve().parent.parent
# Project root is one level above backend/
ROOT_DIR = PROJECT_DIR.parent
load_dotenv(ROOT_DIR / ".env")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# CORS allowed origins (comma-separated in env, defaults to local dev)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# Base directories — session subdirs created dynamically by core.session
DATA_DIR = PROJECT_DIR / "data"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

