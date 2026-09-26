from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class QuizCreate(BaseModel):
    lesson_id: int
    title: str
    description: Optional[str] = None
    is_active: bool = True
    # تأكيد النطاق المقصود فقط — لا يُخزّن؛ يجب أن يطابق نطاق مادة الدرس المختار
    level_id: Optional[int] = None
    branch_id: Optional[int] = None


class QuizUpdate(BaseModel):
    lesson_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    # تأكيد النطاق المقصود فقط — لا يُخزّن؛ يُتحقق منه عند تغيير lesson_id
    level_id: Optional[int] = None
    branch_id: Optional[int] = None


class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    lesson_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    is_active: bool
    questions_count: int = 0
    created_at: datetime
    updated_at: datetime
