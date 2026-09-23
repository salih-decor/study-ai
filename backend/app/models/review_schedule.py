from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# حالات الجدولة: pending (نشط) | completed (مُتقن ومستقر — متخرج) | paused (موقوف مؤقتًا)
REVIEW_STATUSES = ("pending", "completed", "paused")


class StudentReviewSchedule(Base):
    """جدول مراجعة طالب لدرس — يُبنى من الأحداث الحقيقية فقط (لا صفوف بلا بيانات)."""

    __tablename__ = "student_review_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    due_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_count = Column(Integer, default=0, nullable=False)
    interval_days = Column(Integer, default=1, nullable=False)
    priority = Column(Float, default=0.0, nullable=False)  # لقطة من معادلة الخطة
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_review_user_lesson"),
    )

    user = relationship("User", back_populates="review_schedules")
    lesson = relationship("Lesson", back_populates="review_schedules")
