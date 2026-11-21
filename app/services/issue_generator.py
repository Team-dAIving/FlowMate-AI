from app.schemas.issue_schema import (
    IssueGenerateRequest,
    IssueGenerateResponse,
    IssueDraft
)

from app.services.issue_validator import validate_issues

class IssueGenerator:

    def generate(
        self,
        request: IssueGenerateRequest
    ) -> IssueGenerateResponse:

        start = request.project.startDate
        end = request.project.endDate

        response = IssueGenerateResponse(
            issues=[
                IssueDraft(
                    title="프로젝트 요구사항 분석",
                    description="프로젝트의 주요 기능과 요구사항을 정리합니다.",
                    priority="HIGH",
                    assigneeId=None,
                    startDate=start,
                    dueDate=end,
                    estimatedHours=5,
                    labels=["planning"]
                ),
                IssueDraft(
                    title="데이터베이스 설계",
                    description="프로젝트에 필요한 엔티티와 ERD를 설계합니다.",
                    priority="HIGH",
                    assigneeId=None,
                    startDate=start,
                    dueDate=end,
                    estimatedHours=8,
                    labels=["backend", "database"]
                )
            ]
        )

        return validate_issues(request, response)