"""Pytest configuration: shared fixtures for the entire test suite."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Prevent claude-agent-sdk from refusing to launch inside a Claude Code session
os.environ.pop("CLAUDECODE", None)

from server import app

# Relative to this file: tests/fixtures/app_server.log
SAMPLE_LOG = Path(__file__).parent / "fixtures" / "app_server.log"


@pytest.fixture(scope="session")
def client():
    """Shared TestClient instance reused across all tests in the session."""
    return TestClient(app)


@pytest.fixture(scope="session")
def sample_log() -> bytes:
    """Raw bytes of the canonical sample log file used across tests."""
    return SAMPLE_LOG.read_bytes()
