from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class StudentWeakness(Base):
    """ملخص ضعف طالب في درس (مستوى الدرس فقط — لا مواضيع مخترعة)."""

    __tablename__ = "student_weaknesses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, default="lesson")
    mistake_count = Column(Integer, default=0, nullable=False)   # إجابات خاطئة
    attempt_count = Column(Integer, default=0, nullable=False)   # محاولات مكتملة متميزة
    correct_count = Column(Integer, default=0, nullable=False)   # إجابات صحيحة
    mastery_score = Column(Float, nullable=True)  # None = بيانات غير كافية (لا حكم)
    last_mistake_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    severity = Column(String(20), nullable=False, default="none")  # none | low | medium | high
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", "topic", name="uq_weakness_user_lesson_topic"),
    )

    user = relationship("User", back_populates="weaknesses")
    lesson = relationship("Lesson", back_populates="weaknesses")
