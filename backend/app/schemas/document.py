from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class DocumentTextCreate(BaseModel):
    lesson_id: int
    title: str
    content: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    lesson_title: Optional[str] = None
    title: str
    source_type: str
    source_path: Optional[str] = None
    status: str
    chunks_count: int = 0
    created_at: datetime
    updated_at: datetime
