from fastapi import APIRouter, HTTPException
from app.schemas.stt_schema import (
    TranscriptionRequest,
    TranscriptionResponse
)
from app.services.stt_service import stt_service

router = APIRouter(
    prefix="/ai/v1/transcriptions",
    tags=["STT"]
)

@router.post(
    "",
    response_model=TranscriptionResponse
)
def start_transcription(
    request: TranscriptionRequest
):
    return stt_service.start_transcription(
        request
    )

@router.get(
    "/{jobId}",
    response_model=TranscriptionResponse
)
def get_transcription(jobId: str):

    result = stt_service.get_transcription(
        jobId
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="STT 작업을 찾을 수 없습니다."
        )

    return result