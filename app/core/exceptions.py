from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class EntityNotFoundException(BaseAPIException):
    def __init__(self, entity_name: str, identifier: Any = None):
        detail = f"{entity_name} not found"
        if identifier:
            detail += f": {identifier}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class PermissionDeniedException(BaseAPIException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class AuthenticationFailedException(BaseAPIException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class InvalidOperationException(BaseAPIException):
    def __init__(self, detail: str = "Invalid operation"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class DomainRuleViolationException(BaseAPIException):
    """Specific for domain logic violations like State Machine laws"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class DatabaseSchemaMismatchException(BaseAPIException):
    def __init__(self, detail: str = "Database schema is out of date. Run: alembic upgrade head"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
