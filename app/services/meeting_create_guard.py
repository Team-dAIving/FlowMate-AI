"""Conservatively promote explicit new-task proposals to CREATE.

Only works when the transcript explicitly describes adding a named task and the
name does not already exist in existingTasks. Every action still needs approval.
"""
from __future__ import annotations

import re
from typing import Any

# Full phrase must contain a specific task name plus an explicit add commitment.
# This is intentionally narrow. The LLM handles other phrasings as NEEDS_REVIEW.
NEW_TASK = re.compile(
    r"(?P<title>[가-힣A-Za-z0-9][가-힣A-Za-z0-9 _+./#-]{1,70}?)"
    r"\s*(?:업무|작업|태스크)?\s*(?:도|를|을)?\s*"
    r"추가(?:하겠습니다|하겠어요|합시다|하죠|하기로\s*했습니다|하기로\s*했어요|해주세요|해\s*주세요|합니다)[.!?\s]*$"
)
NEGATION = re.compile(r"(?:추가하지|추가하지\s*말|추가\s*안|추가는\s*보류|추가를\s*보류|추가하지\s*않)")
UNCERTAIN = re.compile(r"(?:추가할까요|추가하면|추가할지|검토|고려|보류|아직|미정|가능할까요|어떨까요)")


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold().strip()


def _extract_title(text: str) -> str | None:
    """Extract a task name only from supported, affirmative short statements."""
    if NEGATION.search(text) or UNCERTAIN.search(text):
        return None
    # Ignore sentence fragments before the final clause; never invent a title.
    clauses = [part.strip() for part in re.split(r"[.!?]\s*", text.strip()) if part.strip()]
    clause = clauses[-1] if clauses else ""
    match = NEW_TASK.fullmatch(clause)
    if not match:
        return None
    title = match.group("title").strip()
    title = re.sub(r"\s*(?:업무|작업|태스크)$", "", title).strip()
    if len(title) < 3 or len(title) > 70 or _normalize_title(title) in {"업무", "작업", "태스크", "기능"}:
        return None
    return title


def enforce_explicit_task_creates(request: Any, output: dict[str, Any]) -> dict[str, Any]:
    """Promote matching NEEDS_REVIEW items or add missing CREATE proposals.

    Leaves unrelated NEEDS_REVIEW items untouched. Does not alter confirmed
    decisions or write to databases/GitHub. User approval is always required.
    """
    if not isinstance(output, dict) or not isinstance(output.get("actionItems"), list):
        return output
    actions = output["actionItems"]
    existing = {_normalize_title(task.title) for task in request.existingTasks}

    for segment in request.transcript.segments:
        title = _extract_title(segment.text)
        if title is None or _normalize_title(title) in existing:
            continue
        name = _normalize_title(title)
        # If Qwen already proposed the same task with any action type, do not
        # add a duplicate. Only promote NEEDS_REVIEW with shared evidence.
        matching = [a for a in actions if isinstance(a, dict) and (
            _normalize_title(str(a.get("title", ""))) == name
            or (_normalize_title(str(a.get("title", ""))) == _normalize_title(title + " 업무 추가"))
        )]
        if any(a.get("actionType") == "CREATE" for a in matching):
            continue
        if any(a.get("actionType") == "UPDATE" for a in matching):
            continue

        candidate = next((a for a in matching if a.get("actionType") == "NEEDS_REVIEW"
                          and segment.segmentId in a.get("evidenceSegmentIds", [])), None)
        if candidate is not None:
            candidate.update({
                "actionType": "CREATE",
                "title": title,
                "targetTaskId": None,
                "changes": None,
                "assigneeId": None,
                "dueDate": None,
                "requiresReview": True,
                "reason": "회의에서 신규 업무 추가를 명시적으로 언급함",
            })
        elif not matching:
            actions.append({
                "actionType": "CREATE",
                "title": title,
                "description": "",
                "assigneeId": None,
                "dueDate": None,
                "evidenceSegmentIds": [segment.segmentId],
                "requiresReview": True,
                "reason": "회의에서 신규 업무 추가를 명시적으로 언급함",
            })
    return output
