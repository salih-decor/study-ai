"""خطة المراجعة الذكية — ترتيب رقمي مفسَّر (لا أوصاف غامضة).

معادلة الأولوية (موثقة، كل حد من config أو ثابت مسمى):
    base      = 100 - mastery                      (ضعف الإتقان)
    recurring = min(15 * open_recurring, 30)        (تكرار الأخطاء)
    recent    = 10 إذا آخر خطأ خلال 7 أيام وإلا 0   (حداثة الخطأ)
    stale     = 10 إذا لم تُراجع أبدًا أو منذ > 14 يومًا وإلا 0
    overdue   = 15 إذا حان موعد المراجعة المجدولة وإلا 0
    priority  = round(min(base + recurring + recent + stale + overdue, 100), 1)

يدخل الخطة: mastery < WEAKNESS_THRESHOLD أو أخطاء متكررة مفتوحة.
اللغة تعليمية إيجابية — لا كلمة "ضعيف" للطالب.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.weakness import StudentWeakness
from app.models.review_schedule import StudentReviewSchedule
from app.core.config import settings
from app.services.learning.mistakes import open_recurring_count

REVIEW_STALE_DAYS = 14
RECENT_MISTAKE_DAYS = 7
OVERDUE_BONUS = 15


def reason_for(mastery: float, recurring: int, overdue: bool = False, stale: bool = False) -> str:
    parts = ["يحتاج هذا الدرس إلى مراجعة إضافية."]
    if mastery < settings.WEAKNESS_THRESHOLD:
        parts.append(f"مستوى الإتقان منخفض ({mastery}%).")
    if recurring > 0:
        parts.append("ظهر لديك خطأ متكرر في أسئلته.")
    if overdue:
        parts.append("حان موعد المراجعة.")
    if stale:
        parts.append("لم تتم مراجعة الدرس منذ فترة.")
    return " ".join(parts)


def build_review_plan(db: Session, user_id: int, limit: int | None = None) -> list[dict]:
    max_items = limit or settings.REVIEW_PLAN_MAX_ITEMS
    rows = (
        db.query(StudentWeakness)
        .filter(
            StudentWeakness.user_id == user_id,
            StudentWeakness.mastery_score != None,  # noqa: E711
        )
        .all()
    )
    now = datetime.utcnow()
    items: list[dict] = []
    for row in rows:
        mastery = float(row.mastery_score)
        recurring = open_recurring_count(db, user_id, row.lesson_id)
        if mastery >= settings.WEAKNESS_THRESHOLD and recurring == 0:
            continue
        recent = (
            10
            if row.last_mistake_at is not None and (now - row.last_mistake_at) <= timedelta(days=RECENT_MISTAKE_DAYS)
            else 0
        )
        stale = (
            10
            if row.last_reviewed_at is None or (now - row.last_reviewed_at) > timedelta(days=REVIEW_STALE_DAYS)
            else 0
        )
        sched = (
            db.query(StudentReviewSchedule)
            .filter(
                StudentReviewSchedule.user_id == user_id,
                StudentReviewSchedule.lesson_id == row.lesson_id,
                StudentReviewSchedule.status == "pending",
            )
            .first()
        )
        overdue = bool(sched is not None and sched.due_at is not None and sched.due_at <= now)
        overdue_bonus = OVERDUE_BONUS if overdue else 0
        priority = round(min((100 - mastery) + min(15 * recurring, 30) + recent + stale + overdue_bonus, 100), 1)
        lesson = db.query(Lesson).filter(Lesson.id == row.lesson_id).first()
        if lesson is None:
            continue
        quiz = (
            db.query(Quiz)
            .filter(Quiz.lesson_id == row.lesson_id, Quiz.is_active == True)  # noqa: E712
            .order_by(Quiz.id)
            .first()
        )
        kind = "fix_mistake" if recurring > 0 else ("retry_quiz" if quiz else "review_lesson")
        items.append({
            "lesson_id": row.lesson_id,
            "lesson_title": lesson.title,
            "subject_id": lesson.subject_id,
            "quiz_id": quiz.id if quiz else None,
            "kind": kind,
            "reason": reason_for(mastery, recurring, overdue, stale > 0),
            "priority": priority,
            "mastery": mastery,
            "due_at": sched.due_at if sched else None,
            "review_count": sched.review_count if sched else 0,
            "last_reviewed_at": sched.last_reviewed_at if sched else None,
        })
    items.sort(key=lambda x: -x["priority"])
    return items[:max_items]
