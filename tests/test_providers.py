import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings
from app.services.providers import (
    get_issue_generator,
    get_stt_service,
    get_meeting_analyzer,
    ProviderNotReadyError
)
from app.services.issue_generator import IssueGenerator
from app.services.stt_service import STTService
from app.services.meeting_analyzer import MeetingAnalyzer

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

def test_mock_mode(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    assert get_settings().ai_mode == "mock"

def test_mock_issue_generator(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    assert isinstance(
        get_issue_generator(),
        IssueGenerator
    )

def test_mock_stt_service(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    assert isinstance(
        get_stt_service(),
        STTService
    )

def test_mock_meeting_analyzer(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    assert isinstance(
        get_meeting_analyzer(),
        MeetingAnalyzer
    )

def test_stt_service_singleton(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    assert get_stt_service() is get_stt_service()

@pytest.mark.parametrize(
    "provider",
    [
        get_issue_generator,
        get_stt_service,
        get_meeting_analyzer
    ]
)
def test_aws_provider_not_ready(
    monkeypatch,
    provider
):
    monkeypatch.setenv("AI_MODE", "aws")

    with pytest.raises(ProviderNotReadyError):
        provider()

def test_health_mode(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "mock"

def test_aws_api_not_ready(monkeypatch):
    monkeypatch.setenv("AI_MODE", "aws")

    response = client.post(
        "/ai/v1/transcriptions",
        json={
            "meetingId": 301,
            "bucket": "flowmate-meetings",
            "objectKey": "meetings/301/audio.wav",
            "language": "ko-KR"
        }
    )

    assert response.status_code == 503