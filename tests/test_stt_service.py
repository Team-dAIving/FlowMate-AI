import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.stt_schema import (
    TranscriptionRequest
)
from app.services.stt_service import STTService

client = TestClient(app)

@pytest.fixture
def service():
    return STTService()

@pytest.fixture
def valid_request():
    return TranscriptionRequest(
        meetingId=301,
        bucket="flowmate-meetings",
        objectKey="meetings/301/audio.wav",
        language="ko-KR"
    )

def test_start_transcription(service, valid_request):
    result = service.start_transcription(
        valid_request
    )

    assert result.status == "COMPLETED"
    assert result.meetingId == 301
    assert result.transcript is not None

def test_unique_job_id(service, valid_request):
    first = service.start_transcription(
        valid_request
    )

    second = service.start_transcription(
        valid_request
    )

    assert first.jobId != second.jobId

def test_transcript_content(service, valid_request):
    result = service.start_transcription(
        valid_request
    )

    transcript = result.transcript

    assert transcript.language == "ko-KR"
    assert transcript.meetingId == 301
    assert len(transcript.segments) == 3
    assert "로그인 API" in transcript.fullText

    assert transcript.fullText == "\n".join(
        segment.text
        for segment in transcript.segments
    )

def test_segment_timestamps(service, valid_request):
    result = service.start_transcription(
        valid_request
    )

    for segment in result.transcript.segments:
        assert segment.startMs >= 0
        assert segment.endMs > segment.startMs

def test_get_transcription(service, valid_request):
    created = service.start_transcription(
        valid_request
    )

    retrieved = service.get_transcription(
        created.jobId
    )

    assert retrieved == created

def test_unknown_job(service):
    result = service.get_transcription(
        "invalid-job-id"
    )

    assert result is None

def test_stt_api():
    response = client.post(
        "/ai/v1/transcriptions",
        json={
            "meetingId": 301,
            "bucket": "flowmate-meetings",
            "objectKey": "meetings/301/audio.wav",
            "language": "ko-KR"
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "COMPLETED"

    query_response = client.get(
        f"/ai/v1/transcriptions/{data['jobId']}"
    )

    assert query_response.status_code == 200
    assert query_response.json() == data

def test_unknown_job_api():
    response = client.get(
        "/ai/v1/transcriptions/invalid-job-id"
    )

    assert response.status_code == 404

def test_invalid_meeting_id_api():
    response = client.post(
        "/ai/v1/transcriptions",
        json={
            "meetingId": -1,
            "bucket": "flowmate-meetings",
            "objectKey": "meetings/audio.wav",
            "language": "ko-KR"
        }
    )

    assert response.status_code == 422