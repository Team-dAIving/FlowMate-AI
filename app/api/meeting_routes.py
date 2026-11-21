import logging
from fastapi import APIRouter
from app.core.exceptions import FlowMateError
from app.schemas.error_schema import ErrorResponse
from app.schemas.meeting_schema import (
    MeetingAnalyzeRequest,
    MeetingAnalyzeResponse
)
from app.services.providers import (
    get_meeting_analyzer,
    ProviderNotReadyError
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai/v1/meetings",
    tags=["Meeting Analyzer"]
)

@router.post(
    "/analyze",
    response_model=MeetingAnalyzeResponse,
    response_model_exclude_unset=True,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)

def analyze_meeting(
    request: MeetingAnalyzeRequest
):

    if request.meetingId != request.transcript.meetingId:

        raise FlowMateError(
            code="MEETING_ID_MISMATCH",
            message="회의 ID가 일치하지 않습니다.",
            status_code=422
        )

    try:

        analyzer = get_meeting_analyzer()

        return analyzer.analyze(request)

    except ProviderNotReadyError as error:

        raise FlowMateError(
            code="PROVIDER_NOT_READY",
            message=str(error),
            status_code=503
        ) from error

    except Exception as error:

        logger.exception("회의록 분석 실패")

        raise FlowMateError(
            code="MEETING_ANALYSIS_FAILED",
            message="회의록 분석에 실패했습니다.",
            status_code=500
        ) from error