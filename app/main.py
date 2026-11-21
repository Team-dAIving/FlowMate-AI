from fastapi import FastAPI
from app.api.issue_routes import router as issue_router
from app.api.document_routes import router as document_router
from app.api.stt_routes import router as stt_router
from app.api.meeting_routes import router as meeting_router

app = FastAPI(
    title="FlowMate AI Server",
    version="1.0.0"
)

app.include_router(issue_router)
app.include_router(document_router)
app.include_router(stt_router)
app.include_router(meeting_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "flowmate-ai"
    }