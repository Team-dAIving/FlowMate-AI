"""Conservative post-processing for explicit deadline-change proposals.

Only promotes a statement to UPDATE if it names an existing task, explicitly
requests a deadline change, and includes an unambiguous supported date phrase.
Does not modify DB/GitHub and never turns proposals into decisions.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

WEEKDAYS = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}
PROPOSAL = re.compile(r"(?:변경합시다|바꿉시다|미룹시다|변경하(?:죠|면)|바꾸(?:죠|면)|제안(?:합니)?다)")
CONFIRMED = re.compile(r"(?:확정(?:했|합니|됐|되었)|결정(?:했|합니|됐|되었)|합의(?:했|됐|되었)|하기로\s*했)")
DEADLINE = re.compile(r"(?:마감|기한|완료\s*예정|due\s*date)", re.I)
CHANGE = re.compile(r"(?:변경|바꾸|미루|연기|조정)")
NEGATED = re.compile(r"(?:변경하지|바꾸지|미루지|연기하지|변경은\s*없|변경\s*안)")


def resolve_date(text: str, meeting_date: date) -> date | None:
    """Only dates with an explicit, unambiguous referent are supported."""
    match = re.search(r"(이번\s*주|다음\s*주)\s*([월화수목금토일])요일", text)
    if match:
        monday_this_week = meeting_date - timedelta(days=meeting_date.weekday())
        week_offset = 7 if "다음" in match.group(1) else 0
        return monday_this_week + timedelta(days=week_offset + WEEKDAYS[match.group(2)])
    match = re.search(r"(?<!\d)(20\d{2})[-./년\s]+(\d{1,2})[-./월\s]+(\d{1,2})일?(?!\d)", text)
    if match:
        try:
            return date(*map(int, match.groups()))
        except ValueError:
            return None
    return None


def enforce_explicit_due_date_updates(request: Any, output: dict[str, Any]) -> dict[str, Any]:
    """Supplement *missing* UPDATE actions and remove unconfirmed decisions.

    A model-produced non-empty, conflicting UPDATE is NOT overwritten; its
    correctness must be evaluated separately by the user.
    """
    if not isinstance(output, dict):
        return output
    actions = output.get("actionItems")
    if not isinstance(actions, list):
        return output

    tasks = sorted(request.existingTasks, key=lambda t: len(t.title.strip()), reverse=True)
    evidence_by_id = {seg.segmentId: seg.text for seg in request.transcript.segments}
    decisions = output.get("decisions", [])
    if isinstance(decisions, list):
        output["decisions"] = [
            d for d in decisions
            if not (
                isinstance(d, dict)
                and d.get("evidenceSegmentIds")
                and any(
                    PROPOSAL.search(evidence_by_id.get(seg_id, ""))
                    and not CONFIRMED.search(evidence_by_id.get(seg_id, ""))
                    for seg_id in d["evidenceSegmentIds"]
                )
            )
        ]

    for segment in request.transcript.segments:
        text = segment.text.strip()
        if not (DEADLINE.search(text) and CHANGE.search(text)) or NEGATED.search(text):
            continue
        due_date = resolve_date(text, request.meetingDate)
        if due_date is None:
            continue
        task = next((task for task in tasks if task.title.strip() in text), None)
        if task is None:
            continue

        existing_update = next((action for action in actions if isinstance(action, dict)
                                and action.get("actionType") == "UPDATE"
                                and action.get("targetTaskId") == task.taskId), None)
        if existing_update is not None:
            # Preserve an existing model proposal; avoid duplicating an UPDATE.
            continue

        actions.append({
            "actionType": "UPDATE",
            "targetTaskId": task.taskId,
            "title": task.title,
            "changes": {"dueDate": due_date.isoformat()},
            "evidenceSegmentIds": [segment.segmentId],
            "requiresReview": True,
            "reason": "원문에서 기존 업무 마감일 변경을 명시적으로 제안함",
        })
        if not CONFIRMED.search(text):
            unresolved = output.setdefault("unresolvedItems", [])
            notice = f"{task.title} 마감일 변경 제안 - 승인 필요"
            if isinstance(unresolved, list) and notice not in unresolved:
                unresolved.append(notice)
    return output
