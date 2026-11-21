import logging
from fastapi import APIRouter, HTTPException
from app.schemas.meeting_schema import (
    MeetingAnalyzeRequest,
    MeetingAnalyzeResponse
)
from app.services.meeting_analyzer import (
    MeetingAnalyzer
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai/v1/meetings",
    tags=["Meeting Analyzer"]
)

@router.post(
    "/analyze",
    response_model=MeetingAnalyzeResponse,
    response_model_exclude_unset=True
)
def analyze_meeting(
    request: MeetingAnalyzeRequest
):

    if request.meetingId != request.transcript.meetingId:
        raise HTTPException(
            status_code=422,
            detail="회의 ID가 일치하지 않습니다."
        )

    try:
        analyzer = MeetingAnalyzer()

        return analyzer.analyze(request)

    except Exception:
        logger.exception("회의록 분석 실패")

        raise HTTPException(
            status_code=500,
            detail="회의록 분석에 실패했습니다."
        )