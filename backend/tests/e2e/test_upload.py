"""E2E tests for POST /upload endpoint."""

import pytest

from core.config import UPLOADS_DIR


@pytest.mark.smoke
def test_upload(client, sample_log):
    """POST /upload with a real log file saves it and returns correct metadata."""
    resp = client.post(
        "/upload",
        files={"file": ("app_server.log", sample_log, "text/plain")},
    )

    # Endpoint must accept the upload
    assert resp.status_code == 200

    # Response must be JSON
    assert "application/json" in resp.headers["content-type"]

    data = resp.json()

    # Response must contain a non-empty file_id string
    assert "file_id" in data
    assert isinstance(data["file_id"], str)
    assert len(data["file_id"]) > 0

    # Filename echoed back must match what was sent
    assert data["filename"] == "app_server.log"

    # File must be written to disk with exact content
    saved = UPLOADS_DIR / f"{data['file_id']}.log"
    assert saved.exists()
    assert saved.read_bytes() == sample_log


@pytest.mark.smoke
def test_upload_empty_file(client):
    """POST /upload with an empty file still succeeds and writes a zero-byte file."""
    resp = client.post(
        "/upload",
        files={"file": ("empty.log", b"", "text/plain")},
    )

    # Server must accept empty uploads without erroring
    assert resp.status_code == 200

    data = resp.json()

    # A file_id must still be assigned
    assert data["file_id"]

    # Zero-byte file must exist on disk
    saved = UPLOADS_DIR / f"{data['file_id']}.log"
    assert saved.exists()
    assert saved.read_bytes() == b""


@pytest.mark.smoke
def test_upload_missing_file_field(client):
    """POST /upload with no file field returns 422 Unprocessable Entity."""
    resp = client.post("/upload")

    # FastAPI must reject the request when the required file field is absent
    assert resp.status_code == 422


@pytest.mark.smoke
def test_upload_long_filename(client, sample_log):
    """POST /upload with a very long filename echoes it back correctly."""
    long_name = "a" * 200 + ".log"
    resp = client.post(
        "/upload",
        files={"file": (long_name, sample_log, "text/plain")},
    )

    # Upload must succeed regardless of filename length
    assert resp.status_code == 200

    # Filename must be preserved exactly as sent
    assert resp.json()["filename"] == long_name


@pytest.mark.smoke
def test_upload_non_text_content(client):
    """POST /upload accepts arbitrary bytes — content type is not enforced server-side."""
    binary_content = bytes(range(256))
    resp = client.post(
        "/upload",
        files={"file": ("binary.log", binary_content, "application/octet-stream")},
    )

    # Server must accept any content without validation
    assert resp.status_code == 200

    data = resp.json()

    # Binary content must be stored without corruption
    saved = UPLOADS_DIR / f"{data['file_id']}.log"
    assert saved.read_bytes() == binary_content
