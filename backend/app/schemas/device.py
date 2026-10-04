from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DeviceRegisterResponse(BaseModel):
    device_id: uuid.UUID
    pairing_token: str
    device_secret: str


class DevicePairRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pairing_token: str
    child_id: uuid.UUID


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    child_id: Optional[uuid.UUID] = None
    status: str
    last_seen: Optional[datetime] = None
    created_at: datetime


class ControlAckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    control_version: int = Field(..., ge=1)


class ControlAckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    device_id: uuid.UUID
    control_version: int
    acked_at: datetime
