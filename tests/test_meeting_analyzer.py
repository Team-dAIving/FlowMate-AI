from datetime import date
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.meeting_schema import (
    MeetingAnalyzeRequest,
    MeetingAnalyzeResponse,
    ActionItem,
    ExistingTask,
    Decision
)
from app.services.meeting_analyzer import (
    MeetingAnalyzer
)
from app.services.action_validator import (
    validate_action_items
)
from app.schemas.stt_schema import (
    TranscriptionRequest
)
from app.services.stt_service import STTService


client = TestClient(app)


@pytest.fixture
def analyzer():
    return MeetingAnalyzer()


@pytest.fixture
def valid_request():

    stt = STTService()

    stt_result = stt.start_transcription(
        TranscriptionRequest(
            meetingId=301,
            bucket="flowmate-meetings",
            objectKey="meetings/301/audio.wav",
            language="ko-KR"
        )
    )

    return MeetingAnalyzeRequest(
        meetingId=301,
        projectId=101,
        meetingDate=date(2026, 11, 20),
        transcript=stt_result.transcript,
        members=[
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
        existingTasks=[
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
    )

def test_analyze_meeting(analyzer, valid_request):

    result = analyzer.analyze(valid_request)

    assert result.meetingId == 301
    assert result.projectId == 101
    assert len(result.topics) == 3
    assert len(result.actionItems) == 2
    assert result.summary

def test_update_action(analyzer, valid_request):

    result = analyzer.analyze(valid_request)

    action = next(
        item
        for item in result.actionItems
        if item.actionType == "UPDATE"
    )

    assert action.targetTaskId == 502
    assert action.title == "DB 설계"
    assert action.requiresReview is True
    assert action.evidenceSegmentIds == ["seg_002"]

def test_create_action(analyzer, valid_request):

    result = analyzer.analyze(valid_request)

    action = next(
        item
        for item in result.actionItems
        if item.actionType == "CREATE"
    )

    assert action.title == "로그인 API 테스트"
    assert action.targetTaskId is None
    assert action.assigneeId is None
    assert action.dueDate is None
    assert action.evidenceSegmentIds == ["seg_003"]

def test_relative_date(analyzer, valid_request):

    valid_request.meetingDate = date(
        2026, 11, 21
    )

    result = analyzer.analyze(valid_request)

    action = next(
        item
        for item in result.actionItems
        if item.actionType == "UPDATE"
    )

    assert action.changes.dueDate == date(
        2026, 11, 23
    )

def test_missing_existing_task(
    analyzer, valid_request
):

    valid_request.existingTasks = []

    result = analyzer.analyze(valid_request)

    assert any(
        item.actionType == "NEEDS_REVIEW"
        for item in result.actionItems
    )

def test_prevent_duplicate_task(
    analyzer, valid_request
):

    valid_request.existingTasks.append(
        ExistingTask(
            taskId=503,
            title="로그인 API 테스트"
        )
    )

    result = analyzer.analyze(valid_request)

    assert not any(
        item.actionType == "CREATE"
        and item.title == "로그인 API 테스트"
        for item in result.actionItems
    )
    
def test_invalid_assignee(
    analyzer, valid_request
):

    result = analyzer.analyze(valid_request)

    result.actionItems[0].assigneeId = 999

    with pytest.raises(
        ValueError,
        match="존재하지 않는 담당자"
    ):
        validate_action_items(
            valid_request, result
        )

def test_invalid_target_task(
    analyzer, valid_request
):

    result = analyzer.analyze(valid_request)

    result.actionItems[0].targetTaskId = 999

    with pytest.raises(
        ValueError,
        match="존재하지 않는 변경 대상"
    ):
        validate_action_items(
            valid_request, result
        )

def test_invalid_evidence(
    analyzer, valid_request
):

    result = analyzer.analyze(valid_request)

    result.actionItems[0].evidenceSegmentIds = [
        "invalid_segment"
    ]

    with pytest.raises(
        ValueError,
        match="존재하지 않는 발언 ID"
    ):
        validate_action_items(
            valid_request, result
        )

def test_missing_evidence(
    analyzer, valid_request
):

    result = analyzer.analyze(valid_request)

    result.actionItems[0].evidenceSegmentIds = []

    with pytest.raises(
        ValueError,
        match="원문 근거가 없습니다"
    ):
        validate_action_items(
            valid_request, result
        )

def test_duplicate_action(
    analyzer, valid_request
):

    result = analyzer.analyze(valid_request)

    result.actionItems.append(
        result.actionItems[0].model_copy(
            deep=True
        )
    )

    with pytest.raises(
        ValueError,
        match="중복된 업무 제안"
    ):
        validate_action_items(
            valid_request, result
        )

def test_meeting_api(valid_request):

    response = client.post(
        "/ai/v1/meetings/analyze",
        json=valid_request.model_dump(
            mode="json"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meetingId"] == 301
    assert len(data["actionItems"]) == 2

def test_meeting_id_mismatch(valid_request):

    payload = valid_request.model_dump(
        mode="json"
    )

    payload["transcript"]["meetingId"] = 999

    response = client.post(
        "/ai/v1/meetings/analyze",
        json=payload
    )

    assert response.status_code == 422

def test_update_changes_only(valid_request):

    response = client.post(
        "/ai/v1/meetings/analyze",
        json=valid_request.model_dump(
            mode="json"
        )
    )

    assert response.status_code == 200

    action = next(
        item
        for item in response.json()["actionItems"]
        if item["actionType"] == "UPDATE"
    )

    assert action["changes"] == {
        "dueDate": "2026-11-23"
    }

def test_decision_without_evidence(
    analyzer, valid_request
):

    result = analyzer.analyze(valid_request)

    result.decisions.append(
        Decision(
            content="프로젝트 개발 완료",
            evidenceSegmentIds=[]
        )
    )

    with pytest.raises(
        ValueError,
        match="결정 사항의 근거가 없습니다"
    ):
        validate_action_items(
            valid_request, result
        )