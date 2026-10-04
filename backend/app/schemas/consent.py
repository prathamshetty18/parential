from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ConsentCreate(BaseModel):
    method: str = Field(..., min_length=1)
    voice: bool
    expression: bool
    store_reasoning: bool
    model_improvement: bool


class ConsentUpdate(BaseModel):
    method: Optional[str] = Field(None, min_length=1)
    voice: Optional[bool] = None
    expression: Optional[bool] = None
    store_reasoning: Optional[bool] = None
    model_improvement: Optional[bool] = None


class ConsentResponse(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID
    child_id: uuid.UUID
    method: str
    consented_at: datetime
    voice: bool
    expression: bool
    store_reasoning: bool
    model_improvement: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
