from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # موعد النشر المجدول (اختياري)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subject = relationship("Subject", back_populates="lessons")
    progress_records = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")
    documents = relationship("LessonDocument", back_populates="lesson", cascade="all, delete-orphan")
    weaknesses = relationship("StudentWeakness", back_populates="lesson", cascade="all, delete-orphan")
    mistakes = relationship("StudentMistake", back_populates="lesson", cascade="all, delete-orphan")
    review_schedules = relationship("StudentReviewSchedule", back_populates="lesson", cascade="all, delete-orphan")
