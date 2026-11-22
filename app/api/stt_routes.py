from fastapi import APIRouter
from app.core.exceptions import FlowMateError
from app.schemas.error_schema import ErrorResponse
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
    response_model=TranscriptionResponse,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
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

        raise FlowMateError(
            code="PROVIDER_NOT_READY",
            message=str(error),
            status_code=503
        ) from error

@router.get(
    "/{jobId}",
    response_model=TranscriptionResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)

def get_transcription(jobId: str):

    try:

        service = get_stt_service()

        result = service.get_transcription(
            jobId
        )

    except ProviderNotReadyError as error:

        raise FlowMateError(
            code="PROVIDER_NOT_READY",
            message=str(error),
            status_code=503
        ) from error

    if result is None:

        raise FlowMateError(
            code="JOB_NOT_FOUND",
            message="STT 작업을 찾을 수 없습니다.",
            status_code=404
        )

    return result

# --- Local Whisper upload endpoint (addition; existing JSON endpoint unchanged) ---
from fastapi import File, Form, UploadFile

@router.post("/upload", response_model=TranscriptionResponse,
             responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
def upload_transcription(
    meetingId: int = Form(..., gt=0),
    file: UploadFile = File(...),
):
    try:
        service = get_stt_service()
        if not hasattr(service, "start_uploaded_file"):
            raise ProviderNotReadyError("파일 업로드 STT는 AI_MODE=ollama에서만 지원합니다.")
        return service.start_uploaded_file(meetingId, file.filename or "", file.file)
    except ProviderNotReadyError as error:
        raise FlowMateError(code="PROVIDER_NOT_READY", message=str(error), status_code=503) from error
    except (ValueError, FileNotFoundError) as error:
        raise FlowMateError(code="INVALID_AUDIO_FILE", message=str(error), status_code=422) from error
    finally:
        file.file.close()
