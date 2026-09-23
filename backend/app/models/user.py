from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)

    # تفاصيل خاصة بالطالب
    level = Column(String(100), nullable=True)     # المستوى الدراسي (مثال: 3 ثانوي)
    branch = Column(String(100), nullable=True)    # الشعبة (مثال: علوم تجريبية / آداب وفلسفة)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    progress_records = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    ai_request_logs = relationship("AIRequestLog", back_populates="user", cascade="all, delete-orphan")
    weaknesses = relationship("StudentWeakness", back_populates="user", cascade="all, delete-orphan")
    mistakes = relationship("StudentMistake", back_populates="user", cascade="all, delete-orphan")
    review_schedules = relationship("StudentReviewSchedule", back_populates="user", cascade="all, delete-orphan")
