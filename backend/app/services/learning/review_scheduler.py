"""جدولة المراجعة — deterministic بسيط (ليست SM-2/FSRS).

القواعد (موثقة):
- الفاصل من الشدة الحالية: high→1d / medium→2d / low→4d / mastered(none أو ≥80)→7d.
- التخرج: mastery ≥ REVIEW_MASTERED_MASTERY وثقة ≥ REVIEW_MASTERED_CONFIDENCE
  → status=completed وdue_at=None (لا مواعيد).
- الإتمام الصريح ("أكملت المراجعة"): count+1 وlast_reviewed=الآن وفاصل جديد —
  دون أي مساس بـ mastery أو الدرجات.
- إرسال اختبار: يعيد الجدولة (last_reviewed=الآن، فاصل جديد) دون count+1.
- إتمام درس (Progress): يعامَل كإتمام مراجعة (حدث حقيقي).
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.weakness import StudentWeakness
from app.models.review_schedule import StudentReviewSchedule
from app.core.config import settings
from app.services.learning.weakness import touch_reviewed


def interval_for_severity(severity: str) -> int:
    return {
        "high": settings.REVIEW_INTERVAL_HIGH_DAYS,
        "medium": settings.REVIEW_INTERVAL_MEDIUM_DAYS,
        "low": settings.REVIEW_INTERVAL_LOW_DAYS,
    }.get(severity, settings.REVIEW_INTERVAL_MASTERED_DAYS)


def _weakness_of(db: Session, user_id: int, lesson_id: int) -> StudentWeakness | None:
    return (
        db.query(StudentWeakness)
        .filter(
            StudentWeakness.user_id == user_id,
            StudentWeakness.lesson_id == lesson_id,
            StudentWeakness.topic == "lesson",
        )
        .first()
    )


def _plan_priority_for(db: Session, user_id: int, lesson_id: int, mastery: float | None) -> float:
    from app.services.learning.review_plan import build_review_plan

    for item in build_review_plan(db, user_id, limit=1000):
        if item["lesson_id"] == lesson_id:
            return float(item["priority"])
    base = (100.0 - mastery) if mastery is not None else 50.0
    return round(max(0.0, min(base, 100.0)), 1)


def _is_mastered(mastery: float | None, confidence: float) -> bool:
    return (
        mastery is not None
        and mastery >= settings.REVIEW_MASTERED_MASTERY
        and confidence >= settings.REVIEW_MASTERED_CONFIDENCE
    )


def _confidence_of(row: StudentWeakness | None) -> float:
    if row is None:
        return 0.0
    total = (row.correct_count or 0) + (row.mistake_count or 0)
    return round(min(total / 6.0, 1.0), 2)


def ensure_schedule(db: Session, user_id: int, lesson_id: int) -> StudentReviewSchedule:
    row = (
        db.query(StudentReviewSchedule)
        .filter(
            StudentReviewSchedule.user_id == user_id,
            StudentReviewSchedule.lesson_id == lesson_id,
        )
        .first()
    )
    if row is None:
        row = StudentReviewSchedule(user_id=user_id, lesson_id=lesson_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def reschedule_after_quiz(db: Session, user_id: int, lesson_id: int) -> StudentReviewSchedule:
    """يُستدعى بعد إرسال اختبار — يعيد الحساب دون زيادة العداد."""
    row = ensure_schedule(db, user_id, lesson_id)
    now = datetime.utcnow()
    weak = _weakness_of(db, user_id, lesson_id)
    mastery = float(weak.mastery_score) if weak and weak.mastery_score is not None else None
    severity = weak.severity if weak else "none"
    row.last_reviewed_at = now
    row.interval_days = interval_for_severity(severity)
    if _is_mastered(mastery, _confidence_of(weak)):
        row.status = "completed"
        row.due_at = None
    else:
        row.status = "pending"
        row.due_at = now + timedelta(days=row.interval_days)
    row.priority = _plan_priority_for(db, user_id, lesson_id, mastery)
    db.commit()
    db.refresh(row)
    return row


def register_review_completion(db: Session, user_id: int, lesson_id: int) -> StudentReviewSchedule:
    """حدث 'أكملت المراجعة' (زر صريح أو إتمام درس): count+1 وفاصل جديد، بلا مساس بـ mastery."""
    row = ensure_schedule(db, user_id, lesson_id)
    now = datetime.utcnow()
    weak = _weakness_of(db, user_id, lesson_id)
    mastery = float(weak.mastery_score) if weak and weak.mastery_score is not None else None
    severity = weak.severity if weak else "none"
    row.review_count = (row.review_count or 0) + 1
    row.last_reviewed_at = now
    row.interval_days = interval_for_severity(severity)
    if _is_mastered(mastery, _confidence_of(weak)):
        row.status = "completed"
        row.due_at = None
    else:
        row.status = "pending"
        row.due_at = now + timedelta(days=row.interval_days)
    row.priority = _plan_priority_for(db, user_id, lesson_id, mastery)
    db.commit()
    touch_reviewed(db, user_id, lesson_id)  # مزامنة last_reviewed في ملف الضعف
    db.refresh(row)
    return row


def get_today(db: Session, user_id: int) -> list[StudentReviewSchedule]:
    now = datetime.utcnow()
    return (
        db.query(StudentReviewSchedule)
        .filter(
            StudentReviewSchedule.user_id == user_id,
            StudentReviewSchedule.status == "pending",
            StudentReviewSchedule.due_at != None,  # noqa: E711
            StudentReviewSchedule.due_at <= now,
        )
        .order_by(StudentReviewSchedule.priority.desc())
        .all()
    )


def get_upcoming(db: Session, user_id: int) -> list[StudentReviewSchedule]:
    now = datetime.utcnow()
    return (
        db.query(StudentReviewSchedule)
        .filter(
            StudentReviewSchedule.user_id == user_id,
            StudentReviewSchedule.status == "pending",
            StudentReviewSchedule.due_at != None,  # noqa: E711
            StudentReviewSchedule.due_at > now,
        )
        .order_by(StudentReviewSchedule.due_at.asc())
        .all()
    )
