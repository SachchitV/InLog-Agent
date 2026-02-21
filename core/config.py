"""Application configuration: env loading, logging, paths, and agent prompt."""

import logging
import os
import sys
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
log = logging.getLogger("inlog-agent")

# Validate API key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    log.error("ANTHROPIC_API_KEY is not set.")
    log.error("Create a .env file with ANTHROPIC_API_KEY=sk-ant-... or export it.")
    sys.exit(1)

log.info(
    "ANTHROPIC_API_KEY loaded (%s...%s)",
    ANTHROPIC_API_KEY[:7],
    ANTHROPIC_API_KEY[-4:],
)

# Runtime directories
UPLOADS_DIR = PROJECT_DIR / "data" / "uploads"
SCHEMAS_DIR = PROJECT_DIR / "data" / "schemas"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Agent system prompt
AGENT_PROMPT = (PROJECT_DIR / "agent_prompt.md").read_text()
log.info("Agent prompt loaded (%d chars)", len(AGENT_PROMPT))
