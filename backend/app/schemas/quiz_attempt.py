from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class QuizAnswerCreate(BaseModel):
    """إجابة واحدة من الطالب — بدون أي درجة (كل الحساب في Backend)."""
    question_id: int
    answer: Optional[str] = None


class QuizAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quiz_id: int
    score: float
    total_points: float
    percentage: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    answers_count: int = 0


class QuizAnswerResultOut(BaseModel):
    question_id: int
    question_text: str
    question_type: str
    your_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    points_earned: float
    points: float
    explanation: Optional[str] = None


class QuizResultOut(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    score: float
    total_points: float
    percentage: float
    correct_count: int
    wrong_count: int
    completed_at: Optional[datetime] = None
    answers: list[QuizAnswerResultOut] = []
