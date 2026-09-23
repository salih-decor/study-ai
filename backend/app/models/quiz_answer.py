from sqlalchemy import Column, Integer, Text, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer = Column(Text, nullable=True)  # إجابة الطالب النصية (تحفظ دائمًا لتحليل نقاط الضعف لاحقًا)
    is_correct = Column(Boolean, default=False, nullable=False)  # تُحسب في Backend فقط
    points_earned = Column(Float, default=0.0, nullable=False)    # تُحسب في Backend فقط
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_answer_attempt_question"),
    )

    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")
