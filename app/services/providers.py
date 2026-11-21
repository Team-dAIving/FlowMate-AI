from app.config import get_settings
from app.services.issue_generator import (
    IssueGenerator
)
from app.services.meeting_analyzer import (
    MeetingAnalyzer
)
from app.services.stt_service import (
    STTService,
    stt_service
)

class ProviderNotReadyError(RuntimeError):
    pass

def get_issue_generator() -> IssueGenerator:

    settings = get_settings()

    if settings.ai_mode == "mock":
        return IssueGenerator()

    raise ProviderNotReadyError(
        "AWS Issue Generator가 아직 구현되지 않았습니다."
    )

def get_stt_service() -> STTService:

    settings = get_settings()

    if settings.ai_mode == "mock":
        return stt_service

    raise ProviderNotReadyError(
        "Amazon Transcribe가 아직 연결되지 않았습니다."
    )

def get_meeting_analyzer() -> MeetingAnalyzer:

    settings = get_settings()

    if settings.ai_mode == "mock":
        return MeetingAnalyzer()

    raise ProviderNotReadyError(
        "AWS Meeting Analyzer가 아직 구현되지 않았습니다."
    )