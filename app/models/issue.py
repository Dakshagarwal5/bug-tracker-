import enum
from sqlalchemy import String, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import TimestampMixin

class IssueStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

class Issue(TimestampMixin, Base):
    __tablename__ = "issues"

    title: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IssueStatus] = mapped_column(Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False)
    severity: Mapped[str] = mapped_column(String, default="low") # low, medium, high, critical
    
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    project = relationship("Project", back_populates="issues")
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="issues_reported")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="issues_assigned")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")
