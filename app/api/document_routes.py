from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.concurrency import run_in_threadpool
from app.services.document_parser import (
    extract_text,
    MAX_FILE_SIZE
)

router = APIRouter(
    prefix="/ai/v1/documents",
    tags=["Document Parser"]
)

@router.post("/extract")
async def extract_document(file: UploadFile = File(...)):

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="파일 크기는 10MB 이하여야 합니다."
            )

        text = await run_in_threadpool(
            extract_text,
            file.filename or "",
            content
        )

        return {
            "filename": file.filename,
            "text": text,
            "length": len(text)
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    finally:
        await file.close()