import logging
from fastapi import APIRouter, HTTPException
from app.schemas.issue_schema import (
    IssueGenerateRequest,
    IssueGenerateResponse
)

from app.services.providers import (
    get_issue_generator,
    ProviderNotReadyError
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai/v1/projects",
    tags=["AI Issue Generator"]
)

@router.post(
    "/generate-issues",
    response_model=IssueGenerateResponse
)
def generate_issues(
    request: IssueGenerateRequest
):

    if request.project.startDate > request.project.endDate:
        raise HTTPException(
            status_code=422,
            detail="프로젝트 시작일이 종료일보다 늦습니다."
        )

    try:

        generator = get_issue_generator()

        return generator.generate(request)

    except ProviderNotReadyError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    except Exception:
        logger.exception("AI 이슈 생성 오류")

        raise HTTPException(
            status_code=500,
            detail="AI 이슈 생성에 실패했습니다."
        )