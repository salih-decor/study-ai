from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class StudentMistake(Base):
    """خطأ طالب في سؤال محدد عبر المحاولات (المفتاح = السؤال نفسه، لا مفاهيم مخترعة)."""

    __tablename__ = "student_mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True)
    mistake_key = Column(String(100), nullable=False)  # مثال: question:12
    mistake_count = Column(Integer, default=1, nullable=False)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # يُضبط عند الإجابة الصحيحة لاحقًا

    __table_args__ = (
        UniqueConstraint("user_id", "mistake_key", name="uq_mistake_user_key"),
    )

    user = relationship("User", back_populates="mistakes")
    lesson = relationship("Lesson", back_populates="mistakes")
