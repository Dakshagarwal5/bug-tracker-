from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, issues, comments, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
