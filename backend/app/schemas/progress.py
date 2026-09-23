from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ProgressUpdate(BaseModel):
    """تحديث التقدم — بدون user_id أو lesson_id (يُستنتجان من JWT والمسار)."""
    is_completed: Optional[bool] = None
    last_score: Optional[float] = None


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    subject_id: Optional[int] = None
    is_completed: bool
    last_score: Optional[float] = None
    completed_at: Optional[datetime] = None
    last_accessed_at: datetime


class SubjectProgressOut(BaseModel):
    subject_id: int
    total_lessons: int
    completed_lessons: int
    progress_percentage: float
