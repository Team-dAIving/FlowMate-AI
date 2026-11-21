from datetime import date
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.stt_schema import Transcript
from app.schemas.issue_schema import TeamMember

class ExistingTask(BaseModel):
    taskId: int = Field(gt=0)
    title: str = Field(min_length=1)
    description: str = ""
    assigneeId: int | None = None
    startDate: date | None = None
    dueDate: date | None = None

    priority: Literal[
        "LOW", "MEDIUM", "HIGH", "URGENT"
    ] = "MEDIUM"

    status: Literal[
        "TODO",
        "IN_PROGRESS",
        "IN_REVIEW",
        "DONE",
        "BLOCKED"
    ] = "TODO"

class MeetingAnalyzeRequest(BaseModel):
    meetingId: int = Field(gt=0)
    projectId: int = Field(gt=0)
    meetingDate: date
    transcript: Transcript
    members: list[TeamMember]
    existingTasks: list[ExistingTask]

class Decision(BaseModel):
    content: str

    evidenceSegmentIds: list[str] = Field(
        default_factory=list
    )

class TaskChanges(BaseModel):
    title: str | None = None
    description: str | None = None
    assigneeId: int | None = None
    startDate: date | None = None
    dueDate: date | None = None

    priority: Literal[
        "LOW", "MEDIUM", "HIGH", "URGENT"
    ] | None = None

class ActionItem(BaseModel):
    actionType: Literal[
        "CREATE",
        "UPDATE",
        "NEEDS_REVIEW"
    ]

    targetTaskId: int | None = None

    title: str = Field(min_length=1)
    description: str = ""

    assigneeId: int | None = None
    dueDate: date | None = None

    changes: TaskChanges | None = None

    evidenceSegmentIds: list[str] = Field(
        default_factory=list
    )

    requiresReview: bool = True

    reason: str = ""

class MeetingAnalyzeResponse(BaseModel):
    meetingId: int
    projectId: int
    summary: str

    topics: list[str] = Field(
        default_factory=list
    )

    decisions: list[Decision] = Field(
        default_factory=list
    )

    unresolvedItems: list[str] = Field(
        default_factory=list
    )

    actionItems: list[ActionItem] = Field(
        default_factory=list
    )