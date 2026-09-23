from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional
from datetime import datetime


QuestionType = Literal["multiple_choice", "true_false", "short_answer"]


class QuestionCreate(BaseModel):
    question_text: str
    question_type: QuestionType = "multiple_choice"
    options: Optional[list[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    points: float = 1.0
    display_order: int = 0


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[list[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    points: Optional[float] = None
    display_order: Optional[int] = None


class _QuestionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quiz_id: int
    question_text: str
    question_type: str
    options: Optional[list[str]] = None
    points: float
    display_order: int


class QuestionStudentOut(_QuestionBase):
    """ما يراه الطالب — بدون correct_answer وبدون explanation."""
    pass


class QuestionAdminOut(_QuestionBase):
    """ما يراه المشرف فقط — يتضمن الإجابة والشرح."""
    correct_answer: str
    explanation: Optional[str] = None
