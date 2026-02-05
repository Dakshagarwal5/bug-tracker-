from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import TimestampMixin

class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    issue = relationship("Issue", back_populates="comments")
    author = relationship("User", back_populates="comments")
