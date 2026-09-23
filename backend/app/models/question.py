from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# أنواع الأسئلة المدعومة (قابلة للتوسعة: essay لاحقًا)
QUESTION_TYPES = ("multiple_choice", "true_false", "short_answer")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), nullable=False, default="multiple_choice")
    options = Column(JSON, nullable=True)  # قائمة اختيارات (لـ multiple_choice / true_false)
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    points = Column(Float, default=1.0, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")
