from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.consent import ConsentCreate, ConsentResponse


class ChildCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(..., ge=1, le=18)
    grade: str = Field(..., min_length=1, max_length=100)
    curriculum: str = Field(..., min_length=1, max_length=255)
    language: str = Field("English", min_length=1, max_length=50)
    consent: ConsentCreate


class ChildUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    age: Optional[int] = Field(None, ge=1, le=18)
    grade: Optional[str] = Field(None, min_length=1, max_length=100)
    curriculum: Optional[str] = Field(None, min_length=1, max_length=255)
    language: Optional[str] = Field(None, min_length=1, max_length=50)


class ChildResponse(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID
    name: str
    age: int
    grade: str
    curriculum: str
    language: str
    created_at: datetime
    consent: Optional[ConsentResponse] = None

    model_config = ConfigDict(from_attributes=True)
