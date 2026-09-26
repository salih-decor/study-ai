from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.models.level import Level
from app.models.branch import Branch
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectOut
from app.schemas.lesson import LessonOut
from app.api.v1.endpoints.lessons import _lesson_query_for, _to_lesson_out
from app.api.deps import get_current_user, require_admin
from app.models.user import User


router = APIRouter()


def _visible_lessons_count(db: Session, subject_id: int, is_admin: bool) -> int:
    """عدد الدروس الظاهرة لصاحب الطلب (الكل للـAdmin، المنشورة المستحقة فقط للطالب)."""
    q = db.query(Lesson).filter(Lesson.subject_id == subject_id)
    if not is_admin:
        q = q.filter(
            Lesson.is_published == True,  # noqa: E712
            ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
        )
    return q.count()


def _to_out(db: Session, subject: Subject, is_admin: bool) -> SubjectOut:
    out = SubjectOut.model_validate(subject)
    out.lessons_count = _visible_lessons_count(db, subject.id, is_admin)
    return out


def _validate_subject_scope(
    db: Session, level_id: int | None, branch_id: int | None
) -> tuple[int | None, int | None]:
    """التحقق من نطاق المادة: عام (NULL) أو مستوى فقط أو مستوى+شعبة — مع منع شعبة من مستوى مختلف."""
    if branch_id is not None:
        branch = db.query(Branch).filter(Branch.id == branch_id).first()
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الشعبة غير موجودة")
        if level_id is None:
            level_id = branch.level_id
        elif branch.level_id != level_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الشعبة لا تنتمي إلى المستوى المحدد")
    elif level_id is not None:
        level = db.query(Level).filter(Level.id == level_id).first()
        if level is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستوى غير موجود")
    return level_id, branch_id


@router.get("", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin = current_user.role == "admin" or str(getattr(current_user.role, "value", current_user.role)) == "admin"
    q = db.query(Subject)
    if not is_admin:
        q = q.filter(Subject.is_active == True)  # noqa: E712
    subjects = q.order_by(Subject.display_order, Subject.id).all()
    return [_to_out(db, s, is_admin) for s in subjects]


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin = current_user.role == "admin" or str(getattr(current_user.role, "value", current_user.role)) == "admin"
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None or (not is_admin and not subject.is_active):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
    return _to_out(db, subject, is_admin)


@router.get("/{subject_id}/lessons", response_model=list[LessonOut])
def list_subject_lessons(subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin = current_user.role == "admin" or str(getattr(current_user.role, "value", current_user.role)) == "admin"
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None or (not is_admin and not subject.is_active):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
    lessons = _lesson_query_for(db, current_user).filter(Lesson.subject_id == subject_id).order_by(
        Lesson.display_order, Lesson.id
    ).all()
    return [_to_lesson_out(l) for l in lessons]


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject_in: SubjectCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = subject_in.model_dump()
    data["level_id"], data["branch_id"] = _validate_subject_scope(db, data.get("level_id"), data.get("branch_id"))
    subject = Subject(**data)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return _to_out(db, subject, True)


@router.put("/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: int,
    subject_in: SubjectUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
    data = subject_in.model_dump(exclude_unset=True)
    eff_level = data.get("level_id", subject.level_id)
    eff_branch = data.get("branch_id", subject.branch_id)
    data["level_id"], data["branch_id"] = _validate_subject_scope(db, eff_level, eff_branch)
    for field, value in data.items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return _to_out(db, subject, True)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
    db.delete(subject)  # الدروس المرتبطة تُحذف تلقائيًا (cascade)
    db.commit()
    return None
