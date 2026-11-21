from fastapi import APIRouter, HTTPException
from app.schemas.stt_schema import (
    TranscriptionRequest,
    TranscriptionResponse
)
from app.services.providers import (
    get_stt_service,
    ProviderNotReadyError
)

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

    try:

        service = get_stt_service()

        return service.start_transcription(
            request
        )

    except ProviderNotReadyError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

@router.get(
    "/{jobId}",
    response_model=TranscriptionResponse
)
def get_transcription(jobId: str):

    try:

        service = get_stt_service()

        result = service.get_transcription(
            jobId
        )

    except ProviderNotReadyError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="STT 작업을 찾을 수 없습니다."
        )

    return result