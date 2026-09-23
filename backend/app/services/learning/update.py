"""منسّق تحديث بيانات التعلم بعد إرسال اختبار.

المسار: Submit → (النتيجة محفوظة) → last_score → mistakes → weakness → mastery.
يُستدعى بعد commit النتيجة، وأي خطأ هنا لا يكسر الدرجة (try/except في الـ endpoint).
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.services.learning.mistakes import record_answers
from app.services.learning.weakness import recompute_lesson_weakness
from app.services.learning.review_scheduler import reschedule_after_quiz


def update_learning_data(
    db: Session,
    user_id: int,
    lesson_id: int,
    graded: list[tuple[int, bool]],
) -> None:
    """graded: [(question_id, is_correct)] للإرسال الحالي."""
    now = datetime.utcnow()
    record_answers(db, user_id, lesson_id, [(qid, ok, now) for qid, ok in graded])
    recompute_lesson_weakness(db, user_id, lesson_id)
    reschedule_after_quiz(db, user_id, lesson_id)
