from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel
from app.config import get_settings
from app.core.exception_handlers import (
    register_exception_handlers
)
from app.api.issue_routes import router as issue_router
from app.api.document_routes import router as document_router
from app.api.stt_routes import router as stt_router
from app.api.meeting_routes import router as meeting_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)

register_exception_handlers(app)

app.include_router(issue_router)
app.include_router(document_router)
app.include_router(stt_router)
app.include_router(meeting_router)
class HealthResponse(BaseModel):

    status: Literal["ok"] = "ok"
    service: Literal["flowmate-ai"] = "flowmate-ai"
    mode: Literal["mock", "aws", "ollama"] = "mock"

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"]
)
def health_check():

    current_settings = get_settings()

    return HealthResponse(
        status="ok",
        service="flowmate-ai",
        mode=current_settings.ai_mode
    )