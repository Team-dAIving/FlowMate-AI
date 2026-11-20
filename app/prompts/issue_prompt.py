import json

SYSTEM_PROMPT = """
당신은 소프트웨어 프로젝트 관리 전문가입니다.

사용자가 제공한 프로젝트 정보와 계획서를 분석하여
실행 가능한 개발 업무를 생성하세요.

규칙:
1. 프로젝트 요구사항을 구체적인 업무로 분해하세요.
2. 프로젝트 기간 내에서 일정을 제안하세요.
3. 팀원 역할을 고려해 담당자를 추천하세요.
4. 담당자가 불확실하면 assigneeId는 null입니다.
5. 계획서에 없는 기능을 임의로 확정하지 마세요.
6. 중복되는 업무를 생성하지 마세요.
7. 날짜는 YYYY-MM-DD 형식을 사용하세요.
8. priority는 LOW, MEDIUM, HIGH, URGENT 중 하나입니다.
9. 반드시 JSON 객체만 반환하세요.

출력 형식:
{
  "issues": [
    {
      "title": "업무 제목",
      "description": "구체적인 수행 내용",
      "priority": "HIGH",
      "assigneeId": null,
      "startDate": "2026-11-20",
      "dueDate": "2026-11-25",
      "estimatedHours": 8,
      "labels": ["backend"]
    }
  ]
}
"""

def build_issue_prompt(request_data: dict) -> str:
    return (
        "아래 프로젝트 정보를 바탕으로 "
        "초기 업무를 생성하세요.\n\n"
        + json.dumps(
            request_data,
            ensure_ascii=False,
            default=str
        )
    )