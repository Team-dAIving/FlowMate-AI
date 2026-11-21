
from datetime import date
import pytest
from app.schemas.issue_schema import (
    IssueGenerateRequest,
    IssueGenerateResponse,
    IssueDraft
)
from app.services.issue_validator import validate_issues

@pytest.fixture
def valid_request():
    return IssueGenerateRequest(
        project={
            "title": "FlowMate",
            "description": "AI 협업 관리 서비스",
            "startDate": "2026-11-20",
            "endDate": "2026-12-20",
            "techStack": ["React", "Spring Boot"]
        },
        planText="AI 기반 프로젝트 관리 서비스 개발",
        members=[
            {
                "userId": 1,
                "name": "팀원 A",
                "role": "BACKEND"
            },
            {
                "userId": 2,
                "name": "팀원 B",
                "role": "AI"
            }
        ]
    )

@pytest.fixture
def valid_issue():
    return IssueDraft(
        title="데이터베이스 설계",
        description="ERD 및 DB 테이블 설계",
        priority="HIGH",
        assigneeId=1,
        startDate=date(2026, 11, 21),
        dueDate=date(2026, 11, 25),
        estimatedHours=8,
        labels=["backend"]
    )

def test_valid_issue(valid_request, valid_issue):
    response = IssueGenerateResponse(
        issues=[valid_issue]
    )

    result = validate_issues(
        valid_request,
        response
    )

    assert len(result.issues) == 1
    assert result.issues[0].assigneeId == 1

def test_invalid_project_dates(
    valid_request, valid_issue
):
    valid_request.project.startDate = date(
        2026, 12, 25
    )

    response = IssueGenerateResponse(
        issues=[valid_issue]
    )

    with pytest.raises(
        ValueError,
        match="프로젝트 시작일"
    ):
        validate_issues(valid_request, response)

def test_invalid_assignee(
    valid_request, valid_issue
):
    valid_issue.assigneeId = 999

    response = IssueGenerateResponse(
        issues=[valid_issue]
    )

    with pytest.raises(
        ValueError,
        match="존재하지 않는 담당자"
    ):
        validate_issues(valid_request, response)

def test_invalid_task_dates(
    valid_request, valid_issue
):
    valid_issue.startDate = date(2026, 11, 30)
    valid_issue.dueDate = date(2026, 11, 25)

    response = IssueGenerateResponse(
        issues=[valid_issue]
    )

    with pytest.raises(
        ValueError,
        match="업무 시작일"
    ):
        validate_issues(valid_request, response)

def test_task_outside_project_period(
    valid_request, valid_issue
):
    valid_issue.dueDate = date(2026, 12, 30)

    response = IssueGenerateResponse(
        issues=[valid_issue]
    )

    with pytest.raises(
        ValueError,
        match="프로젝트 기간을 벗어난"
    ):
        validate_issues(valid_request, response)

def test_duplicate_issue(
    valid_request, valid_issue
):
    duplicate = valid_issue.model_copy(deep=True)

    response = IssueGenerateResponse(
        issues=[valid_issue, duplicate]
    )

    with pytest.raises(
        ValueError,
        match="중복 업무"
    ):
        validate_issues(valid_request, response)

def test_unassigned_issue(
    valid_request, valid_issue
):
    valid_issue.assigneeId = None

    response = IssueGenerateResponse(
        issues=[valid_issue]
    )

    result = validate_issues(
        valid_request,
        response
    )

    assert result.issues[0].assigneeId is None