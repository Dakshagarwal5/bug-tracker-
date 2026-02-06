from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    key: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    key: Optional[str] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None

class ProjectResponse(ProjectBase):
    id: int
    is_archived: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
