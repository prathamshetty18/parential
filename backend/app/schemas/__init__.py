from app.schemas.auth import (
    ParentLoginRequest,
    ParentRegisterRequest,
    ParentResponse,
    TokenResponse,
)
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentUpdate
from app.schemas.control import ControlResponse, ControlUpdate, ScheduleSchema, TimeSlot
from app.schemas.device import (
    ControlAckRequest,
    ControlAckResponse,
    DevicePairRequest,
    DeviceRegisterResponse,
    DeviceResponse,
)

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
    "DeviceRegisterResponse",
    "DevicePairRequest",
    "DeviceResponse",
    "ControlAckRequest",
    "ControlAckResponse",
    "TimeSlot",
    "ScheduleSchema",
    "ControlUpdate",
    "ControlResponse",
]
