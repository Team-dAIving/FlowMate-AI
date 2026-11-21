from io import BytesIO
import pytest
from docx import Document
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):

    monkeypatch.setenv("AI_MODE", "mock")
    get_settings.cache_clear()

    yield

    get_settings.cache_clear()

@pytest.fixture
def project_request():

    return {
        "project": {
            "title": "FlowMate",
            "description": "AI 기반 협업 관리 서비스",
            "startDate": "2026-11-20",
            "endDate": "2026-12-20",
            "techStack": [
                "React",
                "Spring Boot",
                "FastAPI"
            ]
        },
        "planText": "",
        "members": [
            {
                "userId": 1,
                "name": "팀원 A",
                "role": "BACKEND"
            },
            {
                "userId": 2,
                "name": "팀원 B",
                "role": "FRONTEND"
            },
            {
                "userId": 3,
                "name": "팀원 C",
                "role": "AI"
            }
        ]
    }

def run_project_pipeline(
    filename,
    content,
    content_type,
    project_request
):

    document_response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                filename,
                content,
                content_type
            )
        }
    )

    assert document_response.status_code == 200

    extracted = document_response.json()

    assert extracted["text"]
    assert extracted["length"] > 0

    project_request["planText"] = extracted["text"]

    issue_response = client.post(
        "/ai/v1/projects/generate-issues",
        json=project_request
    )

    assert issue_response.status_code == 200

    result = issue_response.json()

    assert len(result["issues"]) > 0

    return result

def test_txt_to_issue_pipeline(project_request):

    content = (
        "FlowMate 프로젝트 계획서\n"
        "AI 기반 협업 관리 서비스 개발\n"
        "로그인, 팀 관리, AI 회의록 구현"
    ).encode("utf-8")

    result = run_project_pipeline(
        "plan.txt",
        content,
        "text/plain",
        project_request
    )

    assert "issues" in result
    
def test_pdf_to_issue_pipeline(project_request):

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.drawString(
        100, 750,
        "Project: FlowMate"
    )

    pdf.drawString(
        100, 730,
        "AI Collaboration Service"
    )

    pdf.save()

    result = run_project_pipeline(
        "plan.pdf",
        buffer.getvalue(),
        "application/pdf",
        project_request
    )

    assert "issues" in result

def test_docx_to_issue_pipeline(project_request):

    buffer = BytesIO()

    document = Document()

    document.add_heading(
        "FlowMate 프로젝트",
        level=1
    )

    document.add_paragraph(
        "AI 기반 프로젝트 업무 관리 서비스"
    )

    document.add_paragraph(
        "회의록 분석 및 GitHub Issue 연동"
    )

    document.save(buffer)

    result = run_project_pipeline(
        "plan.docx",
        buffer.getvalue(),
        (
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
        project_request
    )

    assert "issues" in result

def test_invalid_document_pipeline():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "invalid.pdf",
                b"Invalid PDF content",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400

    assert response.json()["error"]["code"] == (
        "DOCUMENT_PARSE_FAILED"
    )

@pytest.fixture
def meeting_request():

    stt_response = client.post(
        "/ai/v1/transcriptions",
        json={
            "meetingId": 301,
            "bucket": "flowmate-meetings",
            "objectKey": "meetings/301/audio.wav",
            "language": "ko-KR"
        }
    )

    assert stt_response.status_code == 200

    stt_result = stt_response.json()

    job_id = stt_result["jobId"]

    query_response = client.get(
        f"/ai/v1/transcriptions/{job_id}"
    )

    assert query_response.status_code == 200

    query_result = query_response.json()

    assert query_result["status"] == "COMPLETED"
    assert query_result == stt_result

    return {
        "meetingId": 301,
        "projectId": 101,
        "meetingDate": "2026-11-20",
        "transcript": query_result["transcript"],
        "members": [
            {
                "userId": 1,
                "name": "팀원 A",
                "role": "BACKEND"
            },
            {
                "userId": 2,
                "name": "팀원 B",
                "role": "FRONTEND"
            },
            {
                "userId": 3,
                "name": "팀원 C",
                "role": "AI"
            }
        ],
        "existingTasks": [
            {
                "taskId": 501,
                "title": "로그인 API 개발",
                "assigneeId": 1,
                "dueDate": "2026-11-20"
            },
            {
                "taskId": 502,
                "title": "DB 설계",
                "assigneeId": 1,
                "dueDate": "2026-11-21"
            }
        ]
    }

def run_meeting_pipeline(meeting_request):

    response = client.post(
        "/ai/v1/meetings/analyze",
        json=meeting_request
    )

    assert response.status_code == 200

    return response.json()

def test_stt_to_meeting_pipeline(meeting_request):

    result = run_meeting_pipeline(
        meeting_request
    )

    assert result["meetingId"] == 301
    assert result["projectId"] == 101

    assert result["summary"]

    action_types = {
        action["actionType"]
        for action in result["actionItems"]
    }

    assert "CREATE" in action_types
    assert "UPDATE" in action_types

def test_pipeline_target_task(meeting_request):

    result = run_meeting_pipeline(
        meeting_request
    )

    valid_task_ids = {
        task["taskId"]
        for task in meeting_request["existingTasks"]
    }

    for action in result["actionItems"]:

        if action["actionType"] == "UPDATE":

            assert action["targetTaskId"] in (
                valid_task_ids
            )

        elif action["actionType"] == "CREATE":

            assert action.get("targetTaskId") is None

def test_pipeline_update_fields(meeting_request):

    result = run_meeting_pipeline(
        meeting_request
    )

    update = next(
        action
        for action in result["actionItems"]
        if action["actionType"] == "UPDATE"
    )

    assert update["targetTaskId"] == 502

    assert update["changes"] == {
        "dueDate": "2026-11-23"
    }

def test_pipeline_evidence(meeting_request):

    result = run_meeting_pipeline(
        meeting_request
    )

    valid_segment_ids = {
        segment["segmentId"]
        for segment in
        meeting_request["transcript"]["segments"]
    }

    for action in result["actionItems"]:

        assert action["evidenceSegmentIds"]

        for segment_id in action["evidenceSegmentIds"]:

            assert segment_id in valid_segment_ids

        assert action["requiresReview"] is True

def test_pipeline_duplicate_task(meeting_request):

    meeting_request["existingTasks"].append(
        {
            "taskId": 503,
            "title": "로그인 API 테스트"
        }
    )

    result = run_meeting_pipeline(
        meeting_request
    )

    assert not any(
        action["actionType"] == "CREATE"
        and action["title"] == "로그인 API 테스트"
        for action in result["actionItems"]
    )

def test_pipeline_meeting_id_mismatch(
    meeting_request
):

    meeting_request["meetingId"] = 999

    response = client.post(
        "/ai/v1/meetings/analyze",
        json=meeting_request
    )

    assert response.status_code == 422

    assert response.json()["error"]["code"] == (
        "MEETING_ID_MISMATCH"
    )