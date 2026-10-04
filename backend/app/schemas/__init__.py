from app.schemas.auth import (
    ParentLoginRequest,
    ParentRegisterRequest,
    ParentResponse,
    TokenResponse,
)
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentUpdate

__all__ = [
    "ParentRegisterRequest",
    "ParentLoginRequest",
    "TokenResponse",
    "ParentResponse",
    "ConsentCreate",
    "ConsentUpdate",
    "ConsentResponse",
    "ChildCreate",
    "ChildUpdate",
    "ChildResponse",
]
