from functools import lru_cache
from typing import Literal
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)

class Settings(BaseSettings):

    app_name: str = "FlowMate AI Server"

    ai_mode: Literal["mock", "aws"] = "mock"

    aws_region: str = "ap-northeast-2"

    bedrock_model_id: str | None = None

    s3_bucket_name: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()