from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EntryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: Optional[str] = Field(default=None, max_length=50)

    estimated_min: int = Field(ge=1, le=24 * 60)
    actual_min: int = Field(ge=1, le=24 * 60)

    difficulty: int = Field(ge=1, le=5)
    mood: int = Field(ge=1, le=5)
    distractions: int = Field(ge=0, le=5)

    notes: Optional[str] = None


class EntryOut(EntryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True