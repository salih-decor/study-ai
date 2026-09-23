from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.lesson_document import LessonDocument
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonOut
from app.schemas.quiz import QuizOut
from app.schemas.document import DocumentOut
from app.api.v1.endpoints.quizzes import _quiz_to_out
from app.services.rag.indexer import sync_lesson_content
from app.api.deps import get_current_user, require_admin
from app.models.user import User


router = APIRouter()


def _is_admin(user: User) -> bool:
    return user.role == "admin" or str(getattr(user.role, "value", user.role)) == "admin"


def _lesson_query_for(db: Session, user: User):
    """استعلام الدروس حسب صلاحية المستخدم (الطالب: المنشورة المستحقة في مواد مفعّلة فقط)."""
    q = db.query(Lesson)
    if not _is_admin(user):
        q = q.filter(
            Lesson.is_published == True,  # noqa: E712
            ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
        ).join(Subject, Lesson.subject_id == Subject.id).filter(Subject.is_active == True)  # noqa: E712
    return q


def _to_lesson_out(lesson: Lesson) -> LessonOut:
    out = LessonOut.model_validate(lesson)
    out.subject_name = lesson.subject.name if lesson.subject else None
    return out


@router.get("", response_model=list[LessonOut])
def list_lessons(
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = _lesson_query_for(db, current_user)
    if subject_id is not None:
        q = q.filter(Lesson.subject_id == subject_id)
    lessons = q.order_by(Lesson.display_order, Lesson.id).all()
    return [_to_lesson_out(lesson) for lesson in lessons]


@router.get("/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lesson = _lesson_query_for(db, current_user).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
    return _to_lesson_out(lesson)


@router.post("", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
def create_lesson(
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    subject = db.query(Subject).filter(Subject.id == lesson_in.subject_id).first()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
    lesson = Lesson(**lesson_in.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    sync_lesson_content(db, lesson)  # فهرسة محتوى الدرس في RAG
    return _to_lesson_out(lesson)


@router.put("/{lesson_id}", response_model=LessonOut)
def update_lesson(
    lesson_id: int,
    lesson_in: LessonUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
    data = lesson_in.model_dump(exclude_unset=True)
    if "subject_id" in data:
        subject = db.query(Subject).filter(Subject.id == data["subject_id"]).first()
        if subject is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
    for field, value in data.items():
        setattr(lesson, field, value)
    db.commit()
    db.refresh(lesson)
    if "content" in data:
        sync_lesson_content(db, lesson)  # إعادة فهرسة محتوى الدرس
    return _to_lesson_out(lesson)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
    db.delete(lesson)
    db.commit()
    return None


@router.get("/{lesson_id}/quizzes", response_model=list[QuizOut])
def lesson_quizzes(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """اختبارات درس — الطالب يرى المفعّلة في الدروس المرئية فقط، والمشرف يرى الكل."""
    if _is_admin(current_user):
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
        quizzes = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).order_by(Quiz.id).all()
    else:
        lesson = _lesson_query_for(db, current_user).filter(Lesson.id == lesson_id).first()
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
        quizzes = (
            db.query(Quiz)
            .filter(Quiz.lesson_id == lesson_id, Quiz.is_active == True)  # noqa: E712
            .order_by(Quiz.id)
            .all()
        )
    return [_quiz_to_out(db, q) for q in quizzes]


def _doc_to_out(db: Session, doc: LessonDocument) -> DocumentOut:
    from app.models.document_chunk import DocumentChunk

    out = DocumentOut.model_validate(doc)
    out.lesson_title = doc.lesson.title if doc.lesson else None
    out.chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    return out


@router.get("/{lesson_id}/documents", response_model=list[DocumentOut])
def lesson_documents(
    lesson_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """مستندات درس — للمشرف فقط (الطالب لا يراها إطلاقًا)."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
    docs = (
        db.query(LessonDocument)
        .filter(LessonDocument.lesson_id == lesson_id)
        .order_by(LessonDocument.id)
        .all()
    )
    return [_doc_to_out(db, d) for d in docs]
