"""Local faster-whisper STT provider, preserving FlowMate TranscriptionResponse."""
from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.schemas.stt_schema import (
    Transcript,
    TranscriptSegment,
    TranscriptionRequest,
    TranscriptionResponse,
)

logger = logging.getLogger(__name__)
ALLOWED_AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".mp4", ".flac", ".ogg", ".webm"}


class LocalWhisperSTT:
    def __init__(self, audio_dir: str | Path | None = None):
        self.audio_dir = Path(audio_dir or os.getenv("STT_AUDIO_DIR", ".local_audio")).resolve()
        self._jobs: dict[str, TranscriptionResponse] = {}
        self._lock = Lock()
        self._model_lock = Lock()
        self._model = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="flowmate-stt")

    def _resolve_local_audio(self, request: TranscriptionRequest) -> Path:
        if request.bucket != "local":
            raise ValueError("로컬 STT에서는 bucket='local'만 지원합니다.")
        relative = Path(request.objectKey)
        if relative.is_absolute() or any(part in ("..", ".") for part in relative.parts):
            raise ValueError("유효하지 않은 objectKey입니다.")
        path = (self.audio_dir / relative).resolve()
        if not path.is_relative_to(self.audio_dir):
            raise ValueError("오디오 경로가 허용된 폴더 밖에 있습니다.")
        if path.suffix.lower() not in ALLOWED_AUDIO_SUFFIXES:
            raise ValueError("지원하지 않는 음성 파일 형식입니다.")
        if not path.is_file():
            raise FileNotFoundError("음성 파일을 찾을 수 없습니다.")
        if not path.stat().st_size:
            raise ValueError("빈 음성 파일입니다.")
        return path

    def _get_model(self):
        if self._model is None:
            # Import only when a local job starts, so mock tests do not require Whisper.
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                os.getenv("WHISPER_MODEL", "small"),
                device=os.getenv("WHISPER_DEVICE", "cpu"),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
            )
        return self._model

    def _transcribe(self, path: Path, meeting_id: int, language: str) -> Transcript:
        # One worker + lock avoids concurrent work on the same model instance.
        with self._model_lock:
            segments, _ = self._get_model().transcribe(
                str(path), language="ko", beam_size=5, vad_filter=True
            )
            items = [
                TranscriptSegment(
                    segmentId=f"seg_{index:03d}",
                    speakerId=None,  # Whisper is not speaker diarization.
                    startMs=max(0, round(segment.start * 1000)),
                    endMs=max(0, round(segment.end * 1000)),
                    text=segment.text.strip(),
                )
                for index, segment in enumerate(segments, start=1)
                if segment.text.strip()
            ]
        return Transcript(
            meetingId=meeting_id,
            language=language,
            fullText="\n".join(segment.text for segment in items),
            segments=items,
        )

    def start_transcription(
        self, request: TranscriptionRequest, *, delete_when_done: bool = False
    ) -> TranscriptionResponse:
        path = self._resolve_local_audio(request)
        job_id = f"fm-{request.meetingId}-{uuid4().hex[:12]}"
        queued = TranscriptionResponse(
            meetingId=request.meetingId, jobId=job_id, status="QUEUED", transcript=None
        )
        with self._lock:
            self._jobs[job_id] = queued
        self._executor.submit(
            self._run_job, job_id, path, request.meetingId,
            request.language, delete_when_done
        )
        return queued

    def _run_job(
        self, job_id: str, path: Path, meeting_id: int,
        language: str, delete_when_done: bool
    ) -> None:
        with self._lock:
            self._jobs[job_id] = TranscriptionResponse(
                meetingId=meeting_id, jobId=job_id, status="IN_PROGRESS"
            )
        try:
            transcript = self._transcribe(path, meeting_id, language)
            result = TranscriptionResponse(
                meetingId=meeting_id, jobId=job_id,
                status="COMPLETED", transcript=transcript
            )
        except Exception:
            logger.exception("Whisper STT failed: jobId=%s", job_id)
            result = TranscriptionResponse(
                meetingId=meeting_id, jobId=job_id, status="FAILED",
                failureReason="음성 인식에 실패했습니다. 서버 로그를 확인하세요."
            )
        finally:
            if delete_when_done:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    logger.exception("Could not delete temporary audio")
        with self._lock:
            self._jobs[job_id] = result

    def get_transcription(self, job_id: str) -> TranscriptionResponse | None:
        with self._lock:
            return self._jobs.get(job_id)

    def start_uploaded_file(self, meeting_id: int, filename: str, stream) -> TranscriptionResponse:
        if meeting_id <= 0:
            raise ValueError("meetingId는 양수여야 합니다.")
        suffix = Path(filename or "").suffix.lower()
        if suffix not in ALLOWED_AUDIO_SUFFIXES:
            raise ValueError("지원하지 않는 음성 파일 형식입니다.")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        object_key = f"upload-{uuid4().hex}{suffix}"
        target = self.audio_dir / object_key
        max_bytes = int(os.getenv("STT_MAX_UPLOAD_MB", "50")) * 1024 * 1024
        size = 0
        try:
            # x+b prevents overwriting and does not trust the uploaded filename.
            with target.open("xb") as out:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("음성 파일이 허용 용량을 초과했습니다.")
                    out.write(chunk)
            if size == 0:
                raise ValueError("빈 음성 파일입니다.")
            request = TranscriptionRequest(
                meetingId=meeting_id, bucket="local", objectKey=object_key,
                language="ko-KR"
            )
            return self.start_transcription(request, delete_when_done=True)
        except Exception:
            target.unlink(missing_ok=True)
            raise


local_stt_service = LocalWhisperSTT()
