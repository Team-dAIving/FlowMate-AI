from app.schemas.meeting_schema import (
    MeetingAnalyzeRequest,
    MeetingAnalyzeResponse
)

def validate_action_items(
    request: MeetingAnalyzeRequest,
    response: MeetingAnalyzeResponse
) -> MeetingAnalyzeResponse:

    if request.transcript.meetingId != request.meetingId:
        raise ValueError("회의 ID가 일치하지 않습니다.")

    if response.meetingId != request.meetingId:
        raise ValueError("응답 회의 ID가 일치하지 않습니다.")

    if response.projectId != request.projectId:
        raise ValueError("프로젝트 ID가 일치하지 않습니다.")

    valid_member_ids = {
        member.userId for member in request.members
    }

    existing_tasks = {
        task.taskId: task
        for task in request.existingTasks
    }

    valid_segment_ids = {
        segment.segmentId
        for segment in request.transcript.segments
    }

    seen_actions = set()

    for item in response.actionItems:

        if item.assigneeId is not None:
            if item.assigneeId not in valid_member_ids:
                raise ValueError("존재하지 않는 담당자입니다.")

        if not item.evidenceSegmentIds:
            raise ValueError("업무 제안에 원문 근거가 없습니다.")

        for segment_id in item.evidenceSegmentIds:
            if segment_id not in valid_segment_ids:
                raise ValueError("존재하지 않는 발언 ID입니다.")

        if item.actionType == "CREATE":

            if item.targetTaskId is not None:
                raise ValueError(
                    "CREATE에는 targetTaskId가 없어야 합니다."
                )

            if item.changes is not None:
                raise ValueError(
                    "CREATE에는 changes가 없어야 합니다."
                )

        elif item.actionType == "UPDATE":

            if item.targetTaskId not in existing_tasks:
                raise ValueError(
                    "존재하지 않는 변경 대상 업무입니다."
                )

            if item.changes is None:
                raise ValueError("업무 변경 내용이 없습니다.")

            changes = item.changes.model_dump(
                exclude_unset=True
            )

            if not changes:
                raise ValueError("업무 변경 내용이 비어 있습니다.")

            changed_assignee = changes.get("assigneeId")

            if changed_assignee is not None:
                if changed_assignee not in valid_member_ids:
                    raise ValueError(
                        "존재하지 않는 변경 담당자입니다."
                    )

            old_task = existing_tasks[item.targetTaskId]

            start = changes.get(
                "startDate", old_task.startDate
            )

            end = changes.get(
                "dueDate", old_task.dueDate
            )

            if start and end and start > end:
                raise ValueError(
                    "변경된 업무의 날짜가 올바르지 않습니다."
                )

        elif item.actionType == "NEEDS_REVIEW":

            if not item.requiresReview:
                raise ValueError("사용자 검토가 필요합니다.")

        action_key = (
            item.actionType,
            item.targetTaskId,
            " ".join(item.title.lower().split())
        )

        if action_key in seen_actions:
            raise ValueError("중복된 업무 제안입니다.")

        seen_actions.add(action_key)

    for decision in response.decisions:

        if not decision.evidenceSegmentIds:
            raise ValueError("결정 사항의 근거가 없습니다.")

        for segment_id in decision.evidenceSegmentIds:
            if segment_id not in valid_segment_ids:
                raise ValueError("잘못된 결정 사항 근거입니다.")

    return response