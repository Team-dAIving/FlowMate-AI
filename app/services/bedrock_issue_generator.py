import json
import re

from app.schemas.issue_schema import (
    IssueGenerateRequest,
    IssueGenerateResponse,
)
from app.services.bedrock_service import BedrockService
from app.services.issue_validator import validate_issues


class BedrockIssueGenerator:
    def generate(
        self,
        request: IssueGenerateRequest
    ) -> IssueGenerateResponse:

        system_prompt = """
당신은 소프트웨어 프로젝트 관리 AI입니다.
프로젝트 계획을 실행 가능한 GitHub 이슈 초안으로 분해하세요.

규칙:
1. 최종 JSON 객체만 출력하세요. Markdown과 설명은 금지합니다.
2. 최상위 키는 반드시 "issues"입니다.
3. 각 이슈에는 다음 필드가 있어야 합니다.
   title, description, priority, assigneeId,
   startDate, dueDate, estimatedHours, labels
4. priority는 LOW, MEDIUM, HIGH, URGENT 중 하나입니다.
5. assigneeId는 제공된 팀원의 userId 또는 null입니다.
6. 날짜는 YYYY-MM-DD 형식입니다.
7. 모든 일정은 프로젝트 시작일과 종료일 사이여야 합니다.
8. estimatedHours는 양수 또는 null입니다.
9. 실제 DB 저장이나 GitHub 생성은 수행하지 마세요.
10. 프로젝트 정보에 없는 사실을 확정적으로 만들지 마세요.
11. 내부 추론 과정은 출력하지 마세요.
12. 프로젝트 규모에 맞춰 3~6개 이슈를 작성하세요.
"""

        user_prompt = (
            "아래 프로젝트 정보를 바탕으로 이슈 초안을 생성하세요.\n\n"
            + json.dumps(
                request.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2
            )
            + '\n\n반환 형식: {"issues": [...]}'
        )

        raw_text = BedrockService().generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # 모델이 코드 블록을 붙이는 경우 제거
        cleaned = raw_text.strip()
        cleaned = re.sub(
            r"(?s)^.*?</think>\s*",
            "",
            cleaned
        ).strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        ).strip()

        # JSON 구조 및 각 필드 타입 검증
        response = IssueGenerateResponse.model_validate_json(cleaned)

        # 기존 프로젝트 일정·팀원 검증 재사용
        return validate_issues(request, response)
