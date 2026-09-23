from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.schemas.progress import ProgressOut, ProgressUpdate, SubjectProgressOut
from app.api.deps import get_current_user
from app.models.user import User
from app.services.learning.review_scheduler import register_review_completion


router = APIRouter()


def _visible_lesson_query(db: Session):
    """الدروس التي يحق للطالب رؤيتها: منشورة + مستحقة الموعد + في مادة مفعّلة."""
    return (
        db.query(Lesson)
        .filter(
            Lesson.is_published == True,  # noqa: E712
            ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
        )
        .join(Subject, Lesson.subject_id == Subject.id)
        .filter(Subject.is_active == True)  # noqa: E712
    )


def _get_visible_lesson_or_404(db: Session, lesson_id: int) -> Lesson:
    lesson = _visible_lesson_query(db).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الدرس غير موجود أو غير متاح",
        )
    return lesson


def _get_or_create_progress(db: Session, user_id: int, lesson_id: int) -> LessonProgress:
    progress = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if progress is None:
        progress = LessonProgress(user_id=user_id, lesson_id=lesson_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def _to_out(progress: LessonProgress) -> ProgressOut:
    out = ProgressOut.model_validate(progress)
    out.subject_id = progress.lesson.subject_id if progress.lesson else None
    return out


@router.get("/me", response_model=list[ProgressOut])
def get_my_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == current_user.id)
        .order_by(LessonProgress.updated_at.desc())
        .all()
    )
    return [_to_out(r) for r in records]


@router.get("/lessons/{lesson_id}", response_model=ProgressOut)
def get_lesson_progress(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_visible_lesson_or_404(db, lesson_id)  # التحقق من أحقية الرؤية أولًا
    progress = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == current_user.id, LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="لا يوجد تقدم مسجل لهذا الدرس بعد")
    return _to_out(progress)


@router.post("/lessons/{lesson_id}/complete", response_model=ProgressOut)
def complete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_visible_lesson_or_404(db, lesson_id)  # المسودة/المجدول/المعطّل → 404
    progress = _get_or_create_progress(db, current_user.id, lesson_id)
    now = datetime.utcnow()
    progress.is_completed = True
    progress.completed_at = now
    progress.last_accessed_at = now
    db.commit()
    try:
        register_review_completion(db, current_user.id, lesson_id)  # الإتمام = مراجعة (بلا مساس بـ mastery)
    except Exception:
        db.rollback()
    db.refresh(progress)
    return _to_out(progress)


@router.put("/lessons/{lesson_id}", response_model=ProgressOut)
def update_lesson_progress(
    lesson_id: int,
    progress_in: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_visible_lesson_or_404(db, lesson_id)
    progress = _get_or_create_progress(db, current_user.id, lesson_id)
    data = progress_in.model_dump(exclude_unset=True)
    now = datetime.utcnow()
    if "is_completed" in data:
        progress.is_completed = data["is_completed"]
        progress.completed_at = now if data["is_completed"] else None
    if "last_score" in data:
        progress.last_score = data["last_score"]
    progress.last_accessed_at = now  # أي تحديث = وصول للدرس
    db.commit()
    if data.get("is_completed") is True:
        try:
            register_review_completion(db, current_user.id, lesson_id)
        except Exception:
            db.rollback()
    db.refresh(progress)
    return _to_out(progress)


@router.get("/subjects/{subject_id}", response_model=SubjectProgressOut)
def get_subject_progress(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.is_active == True).first()  # noqa: E712
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
    visible_ids = [lesson_id for (lesson_id,) in _visible_lesson_query(db).filter(Lesson.subject_id == subject_id).with_entities(Lesson.id).all()]
    total = len(visible_ids)
    completed = 0
    if total:
        completed = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == current_user.id,
                LessonProgress.lesson_id.in_(visible_ids),
                LessonProgress.is_completed == True,  # noqa: E712
            )
            .count()
        )
    percentage = round((completed / total) * 100, 1) if total else 0.0
    return SubjectProgressOut(
        subject_id=subject_id,
        total_lessons=total,
        completed_lessons=completed,
        progress_percentage=percentage,
    )
