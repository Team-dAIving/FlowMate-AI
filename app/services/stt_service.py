from uuid import uuid4
from threading import Lock
from app.schemas.stt_schema import (
    TranscriptionRequest,
    TranscriptionResponse,
    Transcript,
    TranscriptSegment
)

class STTService:

    def __init__(self):
        self.jobs = {}
        self.lock = Lock()

    def start_transcription(
        self,
        request: TranscriptionRequest
    ) -> TranscriptionResponse:

        job_id = (
            f"fm-{request.meetingId}-"
            f"{uuid4().hex[:12]}"
        )

        segments = [
            TranscriptSegment(
                segmentId="seg_001",
                speakerId="spk_0",
                startMs=0,
                endMs=5000,
                text=(
                    "로그인 API는 이번 주 "
                    "금요일까지 완료하겠습니다."
                )
            ),
            TranscriptSegment(
                segmentId="seg_002",
                speakerId="spk_1",
                startMs=5000,
                endMs=10000,
                text=(
                    "DB 설계 마감일은 "
                    "다음 주 월요일로 변경합시다."
                )
            ),
            TranscriptSegment(
                segmentId="seg_003",
                speakerId="spk_2",
                startMs=10000,
                endMs=15000,
                text=(
                    "로그인 API 테스트 업무를 "
                    "추가하겠습니다."
                )
            )
        ]

        transcript = Transcript(
            meetingId=request.meetingId,
            language=request.language,
            fullText="\n".join(
                segment.text
                for segment in segments
            ),
            segments=segments
        )

        result = TranscriptionResponse(
            meetingId=request.meetingId,
            jobId=job_id,
            status="COMPLETED",
            transcript=transcript
        )

        with self.lock:
            self.jobs[job_id] = result

        return result

    def get_transcription(
        self,
        job_id: str
    ) -> TranscriptionResponse | None:

        with self.lock:
            return self.jobs.get(job_id)

stt_service = STTService()