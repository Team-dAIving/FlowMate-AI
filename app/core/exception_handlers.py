import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import (
    HTTPException as StarletteHTTPException
)
from app.core.exceptions import FlowMateError
from app.schemas.error_schema import (
    ErrorResponse,
    ErrorDetail
)

logger = logging.getLogger(__name__)

def create_error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict | None = None
) -> JSONResponse:

    response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
        headers=headers
    )

async def flowmate_error_handler(
    request: Request,
    exc: FlowMateError
):
    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message
    )

async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
):
    return create_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="요청 데이터 형식이 올바르지 않습니다."
    )

async def http_error_handler(
    request: Request,
    exc: StarletteHTTPException
):

    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        413: "FILE_TOO_LARGE",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }

    return create_error_response(
        status_code=exc.status_code,
        code=error_codes.get(
            exc.status_code,
            "HTTP_ERROR"
        ),
        message=str(exc.detail),
        headers=exc.headers
    )

async def unexpected_error_handler(
    request: Request,
    exc: Exception
):

    logger.error(
        "Unexpected server error",
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__
        )
    )

    return create_error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="서버 내부 오류가 발생했습니다."
    )

def register_exception_handlers(app: FastAPI):

    app.add_exception_handler(
        FlowMateError,
        flowmate_error_handler
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler
    )

    app.add_exception_handler(
        StarletteHTTPException,
        http_error_handler
    )

    app.add_exception_handler(
        Exception,
        unexpected_error_handler
    )