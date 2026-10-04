from datetime import datetime
from typing import Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TimeSlot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    @model_validator(mode="after")
    def validate_start_before_end(self):
        if self.start >= self.end:
            raise ValueError("TimeSlot start time must be strictly before end time")
        return self


class ScheduleSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mon: Optional[List[TimeSlot]] = None
    tue: Optional[List[TimeSlot]] = None
    wed: Optional[List[TimeSlot]] = None
    thu: Optional[List[TimeSlot]] = None
    fri: Optional[List[TimeSlot]] = None
    sat: Optional[List[TimeSlot]] = None
    sun: Optional[List[TimeSlot]] = None


class ControlUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    daily_limit_minutes: Optional[int] = Field(None, ge=0, le=1440)
    tries_before_reveal: Optional[int] = Field(None, ge=1, le=3)
    probe_mode: Optional[Literal["voice", "tap", "both"]] = None
    schedule: Optional[ScheduleSchema] = None
    subjects_allowed: Optional[List[str]] = None
    content_level: Optional[str] = None
    paused: Optional[bool] = None
    frustration_guard: Optional[bool] = None


class ControlResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    child_id: uuid.UUID
    version: int
    daily_limit_minutes: int
    schedule: Optional[dict] = None
    paused: bool
    subjects_allowed: Optional[list] = None
    content_level: Optional[str] = None
    tries_before_reveal: int
    probe_mode: str
    frustration_guard: bool
    sync_status: Literal["applied", "pending", "no_device"] = "no_device"
    created_at: datetime
