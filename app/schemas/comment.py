from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime

class CommentBase(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("Comment content cannot be empty")
        if len(text) > 2000:
            raise ValueError("Comment content too long (max 2000 characters)")
        return text

class CommentCreate(CommentBase):
    issue_id: int

class CommentResponse(CommentBase):
    id: int
    issue_id: int
    author_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
