import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_settings_cache():

    get_settings.cache_clear()

    yield

    get_settings.cache_clear()

def assert_error(response, status, code):

    assert response.status_code == status

    data = response.json()

    assert data["success"] is False
    assert data["error"]["code"] == code

    assert isinstance(
        data["error"]["message"],
        str
    )

    assert data["error"]["message"]

def test_job_not_found():

    response = client.get(
        "/ai/v1/transcriptions/invalid-job-id"
    )

    assert_error(
        response, 404, "JOB_NOT_FOUND"
    )

def test_invalid_request():

    response = client.post(
        "/ai/v1/transcriptions",
        json={
            "meetingId": -1,
            "bucket": "flowmate-meetings",
            "objectKey": "audio.wav"
        }
    )

    assert_error(
        response, 422, "VALIDATION_ERROR"
    )

def test_invalid_project_dates():

    response = client.post(
        "/ai/v1/projects/generate-issues",
        json={
            "project": {
                "title": "FlowMate",
                "description": "AI 협업 서비스",
                "startDate": "2026-12-20",
                "endDate": "2026-11-20"
            },
            "planText": "프로젝트 관리",
            "members": []
        }
    )

    assert_error(
        response, 422, "INVALID_PROJECT_DATES"
    )
    
def test_unsupported_file():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "image.png",
                b"invalid data",
                "image/png"
            )
        }
    )

    assert_error(
        response, 400, "UNSUPPORTED_FILE_TYPE"
    )

def test_empty_document():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain"
            )
        }
    )

    assert_error(
        response, 400, "EMPTY_DOCUMENT"
    )

def test_corrupted_pdf():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "invalid.pdf",
                b"This is not a PDF",
                "application/pdf"
            )
        }
    )

    assert_error(
        response, 400, "DOCUMENT_PARSE_FAILED"
    )

def test_corrupted_docx():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "invalid.docx",
                b"Invalid Word file",
                "application/octet-stream"
            )
        }
    )

    assert_error(
        response, 400, "DOCUMENT_PARSE_FAILED"
    )

def test_file_too_large():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "large.txt",
                b"a" * (10 * 1024 * 1024 + 1),
                "text/plain"
            )
        }
    )

    assert_error(
        response, 413, "FILE_TOO_LARGE"
    )
    
def test_provider_not_ready(monkeypatch):

    monkeypatch.setenv("AI_MODE", "aws")
    get_settings.cache_clear()

    response = client.post(
        "/ai/v1/transcriptions",
        json={
            "meetingId": 301,
            "bucket": "flowmate-meetings",
            "objectKey": "audio.wav"
        }
    )

    assert_error(
        response, 503, "PROVIDER_NOT_READY"
    )

def test_unknown_endpoint():

    response = client.get(
        "/ai/v1/unknown-endpoint"
    )

    assert_error(
        response, 404, "NOT_FOUND"
    )