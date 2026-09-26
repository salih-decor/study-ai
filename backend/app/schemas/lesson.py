from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class LessonCreate(BaseModel):
    subject_id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    display_order: int = 0
    is_published: bool = False
    scheduled_at: Optional[datetime] = None
    # تأكيد النطاق المقصود فقط — لا يُخزّن؛ يجب أن يطابق نطاق المادة المختارة
    level_id: Optional[int] = None
    branch_id: Optional[int] = None


class LessonUpdate(BaseModel):
    subject_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    display_order: Optional[int] = None
    is_published: Optional[bool] = None
    scheduled_at: Optional[datetime] = None
    # تأكيد النطاق المقصود فقط — لا يُخزّن؛ يُتحقق منه عند تغيير subject_id
    level_id: Optional[int] = None
    branch_id: Optional[int] = None


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    subject_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    display_order: int
    is_published: bool
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
