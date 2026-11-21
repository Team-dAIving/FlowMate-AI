from typing import Literal
from pydantic import BaseModel, Field

class TranscriptionRequest(BaseModel):
    meetingId: int = Field(gt=0)
    bucket: str = Field(min_length=1)
    objectKey: str = Field(min_length=1)
    language: Literal["ko-KR"] = "ko-KR"

class TranscriptSegment(BaseModel):
    segmentId: str
    speakerId: str | None = None
    startMs: int = Field(ge=0)
    endMs: int = Field(ge=0)
    text: str

class Transcript(BaseModel):
    meetingId: int
    language: str
    fullText: str
    segments: list[TranscriptSegment]

class TranscriptionResponse(BaseModel):
    meetingId: int
    jobId: str

    status: Literal[
        "QUEUED",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED"
    ]

    transcript: Transcript | None = None
    failureReason: str | None = None