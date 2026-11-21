from app.schemas.issue_schema import (
    IssueGenerateRequest,
    IssueGenerateResponse
)

def validate_issues(
    request: IssueGenerateRequest,
    response: IssueGenerateResponse
) -> IssueGenerateResponse:

    valid_ids = {m.userId for m in request.members}
    seen_titles = set()

    if request.project.startDate > request.project.endDate:
        raise ValueError(
            "프로젝트 시작일이 종료일보다 늦습니다."
        )

    for issue in response.issues:

        if issue.assigneeId is not None:
            if issue.assigneeId not in valid_ids:
                raise ValueError(
                    f"존재하지 않는 담당자 ID: {issue.assigneeId}"
                )

        if issue.startDate > issue.dueDate:
            raise ValueError(
                f"업무 시작일이 마감일보다 늦습니다: {issue.title}"
            )

        if (
            issue.startDate < request.project.startDate
            or issue.dueDate > request.project.endDate
        ):
            raise ValueError(
                f"프로젝트 기간을 벗어난 업무: {issue.title}"
            )

        normalized_title = " ".join(
            issue.title.lower().split()
        )

        if normalized_title in seen_titles:
            raise ValueError(
                f"중복 업무: {issue.title}"
            )

        seen_titles.add(normalized_title)

    return response