import logging
from fastapi import APIRouter, HTTPException
from app.schemas.issue_schema import (
    IssueGenerateRequest,
    IssueGenerateResponse
)
from app.services.issue_generator import IssueGenerator

router = APIRouter(
    prefix="/ai/v1/projects",
    tags=["AI Issue Generator"]
)

logger = logging.getLogger(__name__)

@router.post(
    "/generate-issues",
    response_model=IssueGenerateResponse
)
def generate_issues(request: IssueGenerateRequest):
    try:
        generator = IssueGenerator()
        return generator.generate(request)

    except Exception:
        logger.exception("AI 이슈 생성 오류")

        raise HTTPException(
            status_code=500,
            detail="AI 이슈 생성에 실패했습니다."
        )