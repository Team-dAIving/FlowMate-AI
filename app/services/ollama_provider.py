"""Ollama/Qwen issue generator using the existing FlowMate request/response contract."""
from __future__ import annotations

import json
import logging
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.schemas.issue_schema import IssueGenerateRequest, IssueGenerateResponse
from app.services.issue_validator import validate_issues

logger = logging.getLogger(__name__)


class OllamaIssueGenerator:
    """Never returns model thinking or Ollama metadata to the backend."""

    def generate(self, request: IssueGenerateRequest) -> IssueGenerateResponse:
        start = request.project.startDate
        end = request.project.endDate
        allowed_ids = [m.userId for m in request.members]
        system = (
            "당신은 소프트웨어 프로젝트 관리 AI입니다. 프로젝트 계획을 실행 가능한 GitHub 이슈 초안으로 분해하세요. "
            "한국어로 작성하세요. 최종 JSON 객체만 출력하세요. Markdown, 설명, 추론은 금지합니다. "
            '최상위 형식은 반드시 {"issues": [...]} 입니다. 이슈는 2~5개 작성하세요. '
            "각 이슈 필드: title(문자열), description(문자열), "
            "priority(LOW|MEDIUM|HIGH|URGENT), assigneeId(허용된 userId 또는 null), "
            "startDate(YYYY-MM-DD), dueDate(YYYY-MM-DD), "
            "estimatedHours(양수 또는 null), labels(문자열 배열). "
            f"프로젝트 일정은 {start.isoformat()}부터 {end.isoformat()}까지입니다. "
            "모든 이슈 일정은 프로젝트 기간 안에 있어야 하며 startDate <= dueDate여야 합니다. "
            f"사용 가능한 담당자 userId: {allowed_ids}. 해당 팀원이 적합하지 않으면 null을 지정하세요. "
            "이슈 제목은 중복되지 않아야 합니다. 사실을 임의로 만들어 단정하지 마세요. "
            "DB 저장과 GitHub 이슈 생성은 하지 마세요."
        )
        payload = {
            "model": os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            "messages": [
                {"role": "system", "content": "/no_think\n" + system},
                {"role": "user", "content": request.model_dump_json()},
            ],
            "stream": False,
            "think": False,
            "format": IssueGenerateResponse.model_json_schema(),
            "options": {"temperature": 0.2, "num_predict": 2600},
        }
        base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11435").rstrip("/")
        http_request = Request(
            f"{base}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=180) as response:
                envelope = json.load(response)
            content = envelope["message"]["content"].strip()
            # Some Qwen/Ollama versions put <think> content inside the main string.
            content = re.sub(r"(?s)^.*?</think>\s*", "", content).strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.I)
                content = re.sub(r"\s*```$", "", content).strip()
            output = json.loads(content)
            validated = IssueGenerateResponse.model_validate(output)
            return validate_issues(request, validated)
        except (HTTPError, URLError, TimeoutError, OSError, KeyError, TypeError, ValueError) as exc:
            logger.exception("Ollama request or JSON parsing failed")
            raise RuntimeError("Ollama 호출 또는 응답 처리에 실패했습니다.") from exc
        # Validation errors are deliberately allowed to bubble up to the existing
        # FlowMateError -> AI_GENERATION_FAILED handler, never returning bad JSON.
