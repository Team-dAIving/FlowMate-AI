from pathlib import Path
from zipfile import BadZipFile
from fastapi import APIRouter, UploadFile, File
from starlette.concurrency import run_in_threadpool
from pypdf.errors import PdfReadError
from docx.opc.exceptions import PackageNotFoundError
from app.core.exceptions import FlowMateError
from app.schemas.error_schema import ErrorResponse
from app.services.document_parser import (
    extract_text,
    MAX_FILE_SIZE
)

router = APIRouter(
    prefix="/ai/v1/documents",
    tags=["Document Parser"]
)

@router.post(
    "/extract",
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)

async def extract_document(
    file: UploadFile = File(...)
):

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:

            raise FlowMateError(
                code="FILE_TOO_LARGE",
                message="파일 크기는 10MB 이하여야 합니다.",
                status_code=413
            )

        filename = file.filename or ""

        extension = Path(filename).suffix.lower()

        if extension not in {".txt", ".pdf", ".docx"}:

            raise FlowMateError(
                code="UNSUPPORTED_FILE_TYPE",
                message="지원하지 않는 파일 형식입니다.",
                status_code=400
            )

        text = await run_in_threadpool(
            extract_text,
            filename,
            content
        )

        return {
            "filename": filename,
            "text": text,
            "length": len(text)
        }

    except (
        UnicodeDecodeError,
        PdfReadError,
        BadZipFile,
        PackageNotFoundError
    ) as error:

        raise FlowMateError(
            code="DOCUMENT_PARSE_FAILED",
            message="문서가 손상되었거나 읽을 수 없습니다.",
            status_code=400
        ) from error

    except ValueError as error:

        code = (
            "EMPTY_DOCUMENT"
            if str(error) == "추출 가능한 텍스트가 없습니다."
            else "DOCUMENT_PARSE_FAILED"
        )

        raise FlowMateError(
            code=code,
            message="추출 가능한 텍스트가 없습니다."
            if code == "EMPTY_DOCUMENT"
            else "문서를 처리할 수 없습니다.",
            status_code=400
        ) from error

    finally:
        await file.close()