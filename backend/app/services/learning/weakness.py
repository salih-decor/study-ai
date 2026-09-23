"""إعادة حساب ضعف الدرس + لمس المراجعة.

قواعد الشدة severity (موثقة):
    - mastery is None (بيانات غير كافية) → "none" (لا حكم).
    - mastery >= 80 → "low".
    - mastery >= WEAKNESS_THRESHOLD → "low" (ليس ضعيفًا).
    - mastery < WEAKNESS_THRESHOLD → "medium"، وتُرفع إلى "high" إذا:
        mastery < 40 أو يوجد خطأ متكرر مفتوح في الدرس.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_answer import QuizAnswer
from app.models.weakness import StudentWeakness
from app.core.config import settings
from app.services.learning.mastery import compute_mastery
from app.services.learning.mistakes import open_recurring_count


def lesson_answer_history(db: Session, user_id: int, lesson_id: int) -> list[tuple[bool, datetime]]:
    """كل إجابات الطالب في درس مرتبة من الأقدم للأحدث: (is_correct, at)."""
    rows = (
        db.query(QuizAnswer.is_correct, QuizAttempt.completed_at)
        .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.completed_at != None,  # noqa: E711
            Quiz.lesson_id == lesson_id,
        )
        .order_by(QuizAttempt.completed_at, QuizAnswer.id)
        .all()
    )
    return [(bool(ok), at) for ok, at in rows]


def lesson_attempt_ids(db: Session, user_id: int, lesson_id: int) -> set[int]:
    rows = (
        db.query(QuizAttempt.id)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.completed_at != None,  # noqa: E711
            Quiz.lesson_id == lesson_id,
        )
        .all()
    )
    return {i for (i,) in rows}


def severity_for(mastery: float | None, recurring: int) -> str:
    if mastery is None:
        return "none"
    if mastery >= 80:
        return "low"
    if mastery >= settings.WEAKNESS_THRESHOLD:
        return "low"
    if mastery < 40 or recurring > 0:
        return "high"
    return "medium"


def recompute_lesson_weakness(db: Session, user_id: int, lesson_id: int) -> StudentWeakness | None:
    """إعادة حساب كاملة من الإجابات الفعلية. تُحذف الصف عند انعدام البيانات."""
    history = lesson_answer_history(db, user_id, lesson_id)
    row = (
        db.query(StudentWeakness)
        .filter(
            StudentWeakness.user_id == user_id,
            StudentWeakness.lesson_id == lesson_id,
            StudentWeakness.topic == "lesson",
        )
        .first()
    )
    if not history:
        if row is not None:
            db.delete(row)
            db.commit()
        return None

    results = [ok for ok, _ in history]
    mastery, _confidence, _n = compute_mastery(results)
    wrong_times = [at for ok, at in history if not ok]
    recurring = open_recurring_count(db, user_id, lesson_id)
    now = datetime.utcnow()

    if row is None:
        row = StudentWeakness(user_id=user_id, lesson_id=lesson_id, topic="lesson")
        db.add(row)
    row.mistake_count = sum(1 for ok in results if not ok)
    row.correct_count = sum(1 for ok in results if ok)
    row.attempt_count = len(lesson_attempt_ids(db, user_id, lesson_id))
    row.mastery_score = mastery
    row.last_mistake_at = max(wrong_times) if wrong_times else None
    row.last_reviewed_at = now  # إعادة الحساب تُستدعى عند نشاط تعلمي (إرسال اختبار)
    row.severity = severity_for(mastery, recurring)
    db.commit()
    db.refresh(row)
    return row


def touch_reviewed(db: Session, user_id: int, lesson_id: int) -> None:
    """تسجيل مراجعة عند إتمام درس — لا ينشئ صفًا من لا شيء."""
    row = (
        db.query(StudentWeakness)
        .filter(
            StudentWeakness.user_id == user_id,
            StudentWeakness.lesson_id == lesson_id,
            StudentWeakness.topic == "lesson",
        )
        .first()
    )
    if row is not None:
        row.last_reviewed_at = datetime.utcnow()
        db.commit()
