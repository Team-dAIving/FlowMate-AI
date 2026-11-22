from app.services.ollama_meeting_analyzer import OllamaMeetingAnalyzer
from app.services.ollama_provider import OllamaIssueGenerator
import os

from app.config import get_settings
from app.services.issue_generator import IssueGenerator
from app.services.bedrock_issue_generator import BedrockIssueGenerator
from app.services.meeting_analyzer import MeetingAnalyzer
from app.services.stt_service import STTService, stt_service


class ProviderNotReadyError(RuntimeError):
    pass


def get_issue_generator():

    settings = get_settings()

    if settings.ai_mode == "mock":
        return IssueGenerator()

    if settings.ai_mode == "ollama":
        return OllamaIssueGenerator()

    if settings.ai_mode == "aws":

        if not os.getenv("BEDROCK_MODEL_ID"):
            raise ProviderNotReadyError(
                "BEDROCK_MODEL_ID가 설정되지 않았습니다."
            )

        return BedrockIssueGenerator()

    raise ProviderNotReadyError(
        "지원하지 않는 AI_MODE입니다."
    )


def get_stt_service() -> STTService:

    settings = get_settings()

    if settings.ai_mode == "mock":
        return stt_service

    if settings.ai_mode == "ollama":
        from app.services.local_whisper_stt import local_stt_service
        return local_stt_service

    raise ProviderNotReadyError(
        "Amazon Transcribe가 아직 연결되지 않았습니다."
    )


def get_meeting_analyzer() -> MeetingAnalyzer:

    settings = get_settings()

    if settings.ai_mode == "mock":
        return MeetingAnalyzer()

    if settings.ai_mode == "ollama":
        return OllamaMeetingAnalyzer()

    raise ProviderNotReadyError(
        "AWS Meeting Analyzer가 아직 구현되지 않았습니다."
    )
