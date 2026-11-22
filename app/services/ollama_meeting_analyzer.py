"""Qwen3/Ollama implementation of the existing FlowMate meeting analysis contract.

No database or GitHub writes. Outputs are validated review proposals only.
"""
from __future__ import annotations
from app.services.meeting_create_guard import enforce_explicit_task_creates
from app.services.meeting_update_guard import enforce_explicit_due_date_updates

import json
import logging
import os
import re
from urllib.request import Request, urlopen

from app.schemas.meeting_schema import MeetingAnalyzeRequest, MeetingAnalyzeResponse
from app.services.action_validator import validate_action_items

logger = logging.getLogger(__name__)


class OllamaMeetingAnalyzer:
    def analyze(self, request: MeetingAnalyzeRequest) -> MeetingAnalyzeResponse:
        # Empty transcripts must not hallucinate meetings or tasks.
        if not request.transcript.segments:
            return MeetingAnalyzeResponse(
                meetingId=request.meetingId,
                projectId=request.projectId,
                summary="분석할 회의 발언이 없습니다.",
                topics=[], decisions=[], unresolvedItems=[], actionItems=[],
            )

        system = """/no_think
당신은 팀 협업 회의록 분석 AI입니다. 반드시 한국어로 작성하세요.
제공된 transcript.segments만 사실의 근거로 사용하세요.
출력은 JSON 객체 하나뿐이며, 최상위 키는 반드시 meetingId, projectId,
summary, topics, decisions, unresolvedItems, actionItems 입니다.

중요한 규칙:
- 회의에서 명시적으로 확정된 결정만 decisions에 포함하세요. 단순 제안/추측은 제외하세요.
- 업무 생성/수정은 절대 실행하지 마세요. actionItems는 제안이며 requiresReview는 반드시 true입니다.
- CREATE: 기존 existingTasks에 없는 새로운 업무일 때만 사용하세요.
  targetTaskId와 changes는 null 또는 생략하세요.
- UPDATE: existingTasks에 실제 있는 taskId만 targetTaskId로 지정하세요.
  changes에는 실제로 변경할 필드만 넣고, 변경하지 않는 필드는 생략하세요.
  구체적인 값이 언급되지 않았으면 임의로 날짜/담당자 등을 만들지 마세요.
- NEEDS_REVIEW: 미확정 사항이나 기존 업무 확인이 필요한 경우에 사용하세요.
- actionItems의 evidenceSegmentIds는 실제 해당 제안을 뒷받침하는 segmentId 1개 이상이어야 합니다.
- decisions의 evidenceSegmentIds도 실제 확정 발언의 segmentId 1개 이상이어야 합니다.
- assigneeId는 members의 userId 또는 null이어야 합니다.
- 상대 날짜는 meetingDate를 기준으로 해석하세요. 불확실하면 기한을 지정하지 말고 unresolvedItems에 적으세요.
- actionItems에서 추론만으로 업무를 생성하지 마세요.
- 동일한 업무를 중복 제안하지 마세요. 논의 사항이 없으면 빈 배열을 반환하세요.
- 요약/주제는 실제 발언만 반영하세요. 내부 추론이나 코드블록을 출력하지 마세요.
"""
        model_payload = {
            "model": os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": request.model_dump_json(exclude_none=True)},
            ],
            "stream": False,
            "think": False,
            "format": MeetingAnalyzeResponse.model_json_schema(),
            "options": {"temperature": 0.1, "num_predict": 4500},
        }
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11435").rstrip("/")
        http_request = Request(
            f"{base_url}/api/chat",
            data=json.dumps(model_payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=240) as response:
                envelope = json.load(response)
            raw = envelope["message"]["content"].strip()
            raw = re.sub(r"(?s)^.*?</think>\s*", "", raw).strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
            raw = re.sub(r"\s*```$", "", raw).strip()
            output = json.loads(raw)

            # IDs are controlled by BE's request, never by the model.
            output["meetingId"] = request.meetingId
            output["projectId"] = request.projectId

            # The current API is proposal-only; require human approval.
            for action in output.get("actionItems", []):
                action["requiresReview"] = True
                if action.get("actionType") == "UPDATE" and isinstance(action.get("changes"), dict):
                    # Nullable fields are used in the response schema. Nulls mean
                    # unspecified, not a deliberate instruction to clear a field.
                    action["changes"] = {
                        k: v for k, v in action["changes"].items() if v is not None
                    }
                    if not action["changes"]:
                        raise ValueError("UPDATE에 유효한 변경 내용이 없습니다.")

            output = enforce_explicit_due_date_updates(request, output)
            output = enforce_explicit_task_creates(request, output)
            validated = MeetingAnalyzeResponse.model_validate(output)
            return validate_action_items(request, validated)
        except Exception as exc:
            logger.exception("Ollama 회의록 분석 또는 JSON 검증 실패")
            raise RuntimeError("Qwen 회의록 분석에 실패했습니다.") from exc
