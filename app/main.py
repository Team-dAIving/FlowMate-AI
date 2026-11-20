from fastapi import FastAPI
from app.api.issue_routes import router as issue_router


app = FastAPI(
    title="FlowMate AI Server",
    version="1.0.0"
)

app.include_router(issue_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "flowmate-ai"
    }