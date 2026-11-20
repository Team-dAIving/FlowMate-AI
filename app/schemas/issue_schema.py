from datetime import date
from typing import Literal
from pydantic import BaseModel, Field

class ProjectInfo(BaseModel):
    title: str
    description: str
    startDate: date
    endDate: date
    techStack: list[str] = Field(default_factory=list)

class TeamMember(BaseModel):
    userId: int
    name: str
    role: str

class IssueGenerateRequest(BaseModel):
    project: ProjectInfo
    planText: str
    members: list[TeamMember]

class IssueDraft(BaseModel):
    title: str
    description: str
    priority: Literal[
        "LOW", "MEDIUM", "HIGH", "URGENT"
    ]
    assigneeId: int | None = None
    startDate: date
    dueDate: date
    estimatedHours: float | None = None
    labels: list[str] = Field(default_factory=list)

class IssueGenerateResponse(BaseModel):
    issues: list[IssueDraft]