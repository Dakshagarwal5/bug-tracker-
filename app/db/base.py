from app.db.base_class import Base

# Import ALL models here so SQLAlchemy knows about them
from app.models.user import User
from app.models.project import Project
from app.models.issue import Issue
from app.models.comment import Comment
