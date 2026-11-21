from datetime import timedelta
from app.schemas.meeting_schema import (
    MeetingAnalyzeRequest,
    MeetingAnalyzeResponse,
    ActionItem,
    TaskChanges
)
from app.services.action_validator import (
    validate_action_items
)

class MeetingAnalyzer:

    def analyze(
        self,
        request: MeetingAnalyzeRequest
    ) -> MeetingAnalyzeResponse:

        segments = request.transcript.segments

        actions = []
        topics = []

        next_monday = request.meetingDate + timedelta(
            days=7 - request.meetingDate.weekday()
        )

        db_task = next(
            (
                task
                for task in request.existingTasks
                if task.title.strip() == "DB 설계"
            ),
            None
        )

        for segment in segments:

            text = segment.text

            if "로그인 API" in text and "금요일" in text:
                topics.append("로그인 API 개발 일정")

            if (
                "DB 설계" in text
                and "변경합시다" in text
                and "다음 주 월요일" in text
            ):

                topics.append("DB 설계 일정 변경")

                if db_task is not None:

                    actions.append(
                        ActionItem(
                            actionType="UPDATE",
                            targetTaskId=db_task.taskId,
                            title=db_task.title,
                            changes=TaskChanges(
                                dueDate=next_monday
                            ),
                            evidenceSegmentIds=[
                                segment.segmentId
                            ],
                            requiresReview=True,
                            reason="회의에서 마감일 변경을 제안함"
                        )
                    )

                else:
                    actions.append(
                        ActionItem(
                            actionType="NEEDS_REVIEW",
                            title="DB 설계",
                            evidenceSegmentIds=[
                                segment.segmentId
                            ],
                            requiresReview=True,
                            reason="기존 업무를 찾을 수 없음"
                        )
                    )

            if (
                "로그인 API 테스트" in text
                and "추가하겠습니다" in text
            ):

                topics.append("로그인 API 테스트 추가")

                test_task = next(
                    (
                        task
                        for task in request.existingTasks
                        if task.title.strip() == "로그인 API 테스트"
                    ),
                    None
                )

                if test_task is None:

                    actions.append(
                        ActionItem(
                            actionType="CREATE",
                            title="로그인 API 테스트",
                            description="로그인 API 기능 테스트 수행",
                            assigneeId=None,
                            dueDate=None,
                            evidenceSegmentIds=[
                                segment.segmentId
                            ],
                            requiresReview=True,
                            reason="회의에서 신규 업무 추가를 언급함"
                        )
                    )

        topics = list(dict.fromkeys(topics))

        summary = (
            ", ".join(topics) + "에 대해 논의했습니다."
            if topics
            else "현재 Mock에서 분석 가능한 주제가 없습니다."
        )

        response = MeetingAnalyzeResponse(
            meetingId=request.meetingId,
            projectId=request.projectId,
            summary=summary,
            topics=topics,
            decisions=[],
            unresolvedItems=[
                "업무 변경 및 추가에 대한 최종 승인 필요"
            ] if actions else [],
            actionItems=actions
        )

        return validate_action_items(
            request,
            response
        )