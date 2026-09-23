from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class WeaknessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    lesson_title: Optional[str] = None
    topic: str
    attempt_count: int
    correct_count: int
    mistake_count: int
    mastery_score: Optional[float] = None
    confidence: float = 0.0
    sample_size: int = 0
    severity: str
    last_mistake_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None


class MistakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    lesson_title: Optional[str] = None
    question_id: Optional[int] = None
    question_text: Optional[str] = None
    mistake_key: str
    mistake_count: int
    is_recurring: bool = False
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: Optional[datetime] = None


class WeakLessonOut(BaseModel):
    lesson_id: int
    lesson_title: str
    subject_id: Optional[int] = None
    mastery_score: float
    severity: str
    confidence: float = 0.0
    sample_size: int = 0


class RecurringMistakeOut(BaseModel):
    lesson_id: int
    lesson_title: str
    question_id: Optional[int] = None
    question_text: Optional[str] = None
    mistake_count: int
    last_seen_at: datetime


class RecentAttemptOut(BaseModel):
    quiz_id: int
    quiz_title: str
    percentage: float
    completed_at: Optional[datetime] = None


class ProfileOut(BaseModel):
    overall_mastery: Optional[float] = None
    lessons_completed: int = 0
    quizzes_completed: int = 0
    weak_lessons: list[WeakLessonOut] = []
    recurring_mistakes: list[RecurringMistakeOut] = []
    recent_performance: list[RecentAttemptOut] = []


class ReviewItemOut(BaseModel):
    lesson_id: int
    lesson_title: str
    subject_id: Optional[int] = None
    quiz_id: Optional[int] = None
    kind: str
    reason: str
    priority: float
    mastery: float
    due_at: Optional[datetime] = None
    review_count: int = 0
    last_reviewed_at: Optional[datetime] = None


class ReviewPlanOut(BaseModel):
    date: str
    items: list[ReviewItemOut] = []


class ReviewScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    lesson_title: Optional[str] = None
    subject_id: Optional[int] = None
    quiz_id: Optional[int] = None
    due_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
    review_count: int
    interval_days: int
    priority: float
    status: str


class ReviewScheduleListOut(BaseModel):
    today: list[ReviewScheduleOut] = []
    upcoming: list[ReviewScheduleOut] = []
