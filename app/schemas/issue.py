from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from app.models.issue import IssueStatus

ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}

class IssueBase(BaseModel):
    title: str = Field(..., min_length=1, example="Fix login bug", title="Issue Title")
    description: str = Field(..., example="Login page returns 500 status code", title="Issue Description")
    severity: str = Field("low", example="low", title="Severity Level")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in ALLOWED_SEVERITIES:
            raise ValueError(f"Severity must be one of {sorted(ALLOWED_SEVERITIES)}")
        return v

class IssueCreate(IssueBase):
    project_id: int = Field(..., gt=0, example=1, title="ID of the Project")
    assignee_id: Optional[int] = Field(None, gt=0, example=2, title="ID of the Assignee")

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[IssueStatus] = None # Logic will handle transitions
    assignee_id: Optional[int] = None

    @field_validator("severity")
    @classmethod
    def validate_update_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ALLOWED_SEVERITIES:
            raise ValueError(f"Severity must be one of {sorted(ALLOWED_SEVERITIES)}")
        return v

class IssueResponse(IssueBase):
    id: int
    status: IssueStatus
    project_id: int
    reporter_id: int
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
