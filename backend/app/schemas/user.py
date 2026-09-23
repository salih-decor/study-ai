from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


# بيانات إنشاء حساب طالب جديد
class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    level: Optional[str] = None
    branch: Optional[str] = None


# ما يتم إرجاعه للعميل (User Response)
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    role: str
    level: Optional[str] = None
    branch: Optional[str] = None
    is_active: bool
    created_at: datetime


# نموذج الـ Token
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
