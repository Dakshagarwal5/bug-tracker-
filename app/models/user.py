import enum
from sqlalchemy import String, Boolean, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    # Using Argon2 hashes, which are long strings
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    # kept for backward compatibility with existing checks; maintained in sync with role
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    projects_owned = relationship("Project", back_populates="owner")
    issues_reported = relationship("Issue", back_populates="reporter", foreign_keys="Issue.reporter_id")
    issues_assigned = relationship("Issue", back_populates="assignee", foreign_keys="Issue.assignee_id")
    comments = relationship("Comment", back_populates="author")

    @property
    def is_superuser(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_admin
