import logging
from fastapi import APIRouter
from app.core.exceptions import FlowMateError
from app.schemas.error_schema import ErrorResponse
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
    response_model=IssueGenerateResponse,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)

def generate_issues(request: IssueGenerateRequest):

    if request.project.startDate > request.project.endDate:

        raise FlowMateError(
            code="INVALID_PROJECT_DATES",
            message="프로젝트 시작일이 종료일보다 늦습니다.",
            status_code=422
        )

    try:

        generator = get_issue_generator()

        return generator.generate(request)

    except ProviderNotReadyError as error:

        raise FlowMateError(
            code="PROVIDER_NOT_READY",
            message=str(error),
            status_code=503
        ) from error

    except Exception as error:

        logger.exception("AI 이슈 생성 오류")

        raise FlowMateError(
            code="AI_GENERATION_FAILED",
            message="AI 이슈 생성에 실패했습니다.",
            status_code=500
        ) from error