from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.quiz_attempt import QuizAttempt
from app.models.progress import LessonProgress
from app.models.weakness import StudentWeakness
from app.models.mistake import StudentMistake
from app.models.review_schedule import StudentReviewSchedule
from app.schemas.learning import (
    WeaknessOut, MistakeOut, ProfileOut, WeakLessonOut,
    RecurringMistakeOut, RecentAttemptOut, ReviewPlanOut, ReviewItemOut,
    ReviewScheduleOut, ReviewScheduleListOut,
)
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.services.scoping import allowed_lesson_ids, lesson_in_scope
from app.services.learning.mistakes import is_recurring
from app.services.learning.review_plan import build_review_plan
from app.services.learning.review_scheduler import (
    get_today, get_upcoming, register_review_completion,
)


router = APIRouter()


def _lesson_title(db: Session, lesson_id: int) -> str:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    return lesson.title if lesson else ""


def _weakness_to_out(db: Session, row: StudentWeakness) -> WeaknessOut:
    out = WeaknessOut.model_validate(row)
    out.lesson_title = _lesson_title(db, row.lesson_id)
    total = row.correct_count + row.mistake_count
    out.confidence = round(min(total / 6.0, 1.0), 2)
    out.sample_size = total
    return out


def _mistake_to_out(db: Session, row: StudentMistake) -> MistakeOut:
    out = MistakeOut.model_validate(row)
    out.lesson_title = _lesson_title(db, row.lesson_id)
    out.is_recurring = is_recurring(row)
    if row.question_id is not None:
        q = db.query(Question).filter(Question.id == row.question_id).first()
        out.question_text = q.question_text if q else None
    return out


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    weaknesses = (
        db.query(StudentWeakness)
        .filter(
            StudentWeakness.user_id == current_user.id,
            StudentWeakness.mastery_score != None,  # noqa: E711
        )
        .all()
    )
    masteries = [float(w.mastery_score) for w in weaknesses]
    overall = round(sum(masteries) / len(masteries), 1) if masteries else None

    weak_lessons = []
    for w in weaknesses:
        if w.severity in ("medium", "high"):
            lesson = db.query(Lesson).filter(Lesson.id == w.lesson_id).first()
            sample = (w.correct_count or 0) + (w.mistake_count or 0)
            weak_lessons.append(WeakLessonOut(
                lesson_id=w.lesson_id,
                lesson_title=lesson.title if lesson else "",
                subject_id=lesson.subject_id if lesson else None,
                mastery_score=float(w.mastery_score),
                severity=w.severity,
                confidence=round(min(sample / 6.0, 1.0), 2),
                sample_size=sample,
            ))

    open_mistakes = (
        db.query(StudentMistake)
        .filter(
            StudentMistake.user_id == current_user.id,
            StudentMistake.resolved_at == None,  # noqa: E711
        )
        .order_by(StudentMistake.mistake_count.desc(), StudentMistake.last_seen_at.desc())
        .all()
    )
    recurring = []
    for m in open_mistakes:
        if not is_recurring(m):
            continue
        lesson = db.query(Lesson).filter(Lesson.id == m.lesson_id).first()
        qtext = None
        if m.question_id is not None:
            q = db.query(Question).filter(Question.id == m.question_id).first()
            qtext = q.question_text if q else None
        recurring.append(RecurringMistakeOut(
            lesson_id=m.lesson_id,
            lesson_title=lesson.title if lesson else "",
            question_id=m.question_id,
            question_text=qtext,
            mistake_count=m.mistake_count,
            last_seen_at=m.last_seen_at,
        ))

    recent = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.completed_at != None,  # noqa: E711
        )
        .order_by(QuizAttempt.completed_at.desc())
        .limit(5)
        .all()
    )
    recent_out = []
    for a in recent:
        quiz = db.query(Quiz).filter(Quiz.id == a.quiz_id).first()
        recent_out.append(RecentAttemptOut(
            quiz_id=a.quiz_id,
            quiz_title=quiz.title if quiz else "",
            percentage=a.percentage,
            completed_at=a.completed_at,
        ))

    lessons_completed = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == current_user.id, LessonProgress.is_completed == True)  # noqa: E712
        .count()
    )
    quizzes_completed = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id, QuizAttempt.completed_at != None)  # noqa: E711
        .count()
    )
    return ProfileOut(
        overall_mastery=overall,
        lessons_completed=lessons_completed,
        quizzes_completed=quizzes_completed,
        weak_lessons=weak_lessons,
        recurring_mistakes=recurring,
        recent_performance=recent_out,
    )


@router.get("/weaknesses", response_model=list[WeaknessOut])
def get_weaknesses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(StudentWeakness)
        .filter(StudentWeakness.user_id == current_user.id)
        .order_by(StudentWeakness.updated_at.desc())
        .all()
    )
    allowed = allowed_lesson_ids(db, current_user)
    if allowed is not None:
        rows = [r for r in rows if r.lesson_id in allowed]
    return [_weakness_to_out(db, r) for r in rows]


@router.get("/mistakes", response_model=list[MistakeOut])
def get_mistakes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(StudentMistake)
        .filter(StudentMistake.user_id == current_user.id)
        .order_by(StudentMistake.resolved_at.asc(), StudentMistake.mistake_count.desc())
        .all()
    )
    allowed = allowed_lesson_ids(db, current_user)
    if allowed is not None:
        rows = [r for r in rows if r.lesson_id in allowed]
    return [_mistake_to_out(db, r) for r in rows]


@router.get("/review-plan", response_model=ReviewPlanOut)
def get_review_plan(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = build_review_plan(db, current_user.id)
    allowed = allowed_lesson_ids(db, current_user)
    if allowed is not None:
        items = [it for it in items if it.get("lesson_id") in allowed]
    return ReviewPlanOut(
        date=datetime.utcnow().date().isoformat(),
        items=[ReviewItemOut(**item) for item in items],
    )


def _schedule_to_out(db: Session, row: StudentReviewSchedule) -> ReviewScheduleOut:
    out = ReviewScheduleOut.model_validate(row)
    lesson = db.query(Lesson).filter(Lesson.id == row.lesson_id).first()
    out.lesson_title = lesson.title if lesson else ""
    out.subject_id = lesson.subject_id if lesson else None
    quiz = (
        db.query(Quiz)
        .filter(Quiz.lesson_id == row.lesson_id, Quiz.is_active == True)  # noqa: E712
        .order_by(Quiz.id)
        .first()
    )
    out.quiz_id = quiz.id if quiz else None
    return out


@router.get("/review-schedule", response_model=ReviewScheduleListOut)
def get_review_schedule(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    allowed = allowed_lesson_ids(db, current_user)
    today = get_today(db, current_user.id)
    upcoming = get_upcoming(db, current_user.id)
    if allowed is not None:
        today = [r for r in today if r.lesson_id in allowed]
        upcoming = [r for r in upcoming if r.lesson_id in allowed]
    return ReviewScheduleListOut(
        today=[_schedule_to_out(db, r) for r in today],
        upcoming=[_schedule_to_out(db, r) for r in upcoming],
    )


@router.get("/review-schedule/today", response_model=ReviewScheduleListOut)
def get_review_schedule_today(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = get_today(db, current_user.id)
    allowed = allowed_lesson_ids(db, current_user)
    if allowed is not None:
        today = [r for r in today if r.lesson_id in allowed]
    return ReviewScheduleListOut(
        today=[_schedule_to_out(db, r) for r in today],
        upcoming=[],
    )


@router.post("/review-schedule/{lesson_id}/complete", response_model=ReviewScheduleOut)
def complete_review_schedule(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(StudentReviewSchedule)
        .filter(
            StudentReviewSchedule.user_id == current_user.id,
            StudentReviewSchedule.lesson_id == lesson_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="لا يوجد جدول مراجعة لهذا الدرس")
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="هذه المراجعة ليست بانتظار الإكمال")
    if not lesson_in_scope(db, current_user, lesson_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود أو غير متاح")
    return _schedule_to_out(db, register_review_completion(db, current_user.id, lesson_id))


@router.get("/admin/overview")
def admin_overview(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """أساس إحصائيات الإدارة (مجمعة فقط — بلا بيانات فردية لطالب)."""
    lessons_stats = []
    for lesson in db.query(Lesson).order_by(Lesson.id).all():
        quiz_ids = [q.id for q in db.query(Quiz).filter(Quiz.lesson_id == lesson.id).all()]
        attempts = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id.in_(quiz_ids),
                QuizAttempt.completed_at != None,  # noqa: E711
            )
            .all() if quiz_ids else []
        )
        avg_pct = round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else None
        mistakes = (
            db.query(StudentMistake)
            .filter(StudentMistake.lesson_id == lesson.id, StudentMistake.resolved_at == None)  # noqa: E711
            .count()
        )
        lessons_stats.append({
            "lesson_id": lesson.id,
            "title": lesson.title,
            "attempts": len(attempts),
            "avg_percentage": avg_pct,
            "open_mistakes": mistakes,
        })
    from app.models.subject import Subject
    from app.models.question import Question
    totals = {
        "subjects": db.query(Subject).count(),
        "lessons": db.query(Lesson).count(),
        "quizzes": db.query(Quiz).count(),
        "questions": db.query(Question).count(),
        "users": db.query(User).count(),
        "completed_attempts": db.query(QuizAttempt).filter(QuizAttempt.completed_at != None).count(),  # noqa: E711
    }
    return {"totals": totals, "lessons": lessons_stats}
