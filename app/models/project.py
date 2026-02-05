from typing import List
from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Project(Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False) # Soft delete
    
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="projects_owned")
    issues = relationship("Issue", back_populates="project", cascade="all, delete") # If project is hard deleted
