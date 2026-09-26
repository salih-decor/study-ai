from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.question import Question, QUESTION_TYPES
from app.models.quiz_attempt import QuizAttempt
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizOut
from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionStudentOut, QuestionAdminOut,
)
from app.schemas.quiz_attempt import QuizAttemptOut
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.services.scoping import apply_subject_scope, resolve_user_scope


router = APIRouter()


def _is_admin(user: User) -> bool:
    return user.role == "admin" or str(getattr(user.role, "value", user.role)) == "admin"


def _lesson_visible_to_student(db: Session, lesson_id: int) -> Lesson | None:
    """الدرس كما يراه الطالب: منشور + مستحق + في مادة مفعّلة."""
    return (
        db.query(Lesson)
        .filter(
            Lesson.id == lesson_id,
            Lesson.is_published == True,  # noqa: E712
            ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
        )
        .join(Subject, Lesson.subject_id == Subject.id)
        .filter(Subject.is_active == True)  # noqa: E712
        .first()
    )


def _quiz_to_out(db: Session, quiz: Quiz) -> QuizOut:
    out = QuizOut.model_validate(quiz)
    out.lesson_title = quiz.lesson.title if quiz.lesson else None
    out.questions_count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
    return out


def _assert_lesson_scope(
    db: Session, lesson: Lesson, level_id: int | None, branch_id: int | None
) -> None:
    """رفض الربط المتقاطع: تأكيد النطاق المرسل يجب أن يطابق نطاق مادة الدرس (400 عند التعارض)."""
    subject = db.query(Subject).filter(Subject.id == lesson.subject_id).first()
    if subject is None:
        return
    if level_id is not None and subject.level_id is not None and subject.level_id != level_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الدرس لا ينتمي إلى المستوى المحدد")
    if branch_id is not None and subject.branch_id is not None and subject.branch_id != branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الدرس لا ينتمي إلى الشعبة المحددة")


def _get_quiz_for_admin(db: Session, quiz_id: int) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الاختبار غير موجود")
    return quiz


def _get_quiz_for_student(db: Session, quiz_id: int, user: User) -> Quiz:
    level_id, branch_id = resolve_user_scope(db, user)
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.is_active == True)  # noqa: E712
        .join(Lesson, Quiz.lesson_id == Lesson.id)
        .filter(
            Lesson.is_published == True,  # noqa: E712
            ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
        )
        .join(Subject, Lesson.subject_id == Subject.id)
        .filter(Subject.is_active == True)  # noqa: E712
    )
    quiz = apply_subject_scope(quiz, level_id, branch_id).first()
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الاختبار غير موجود أو غير متاح")
    return quiz


# ---------------- Admin: CRUD quizzes ----------------

@router.get("", response_model=list[QuizOut])
def list_all_quizzes(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quizzes = db.query(Quiz).order_by(Quiz.lesson_id, Quiz.id).all()
    return [_quiz_to_out(db, q) for q in quizzes]


@router.post("", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz_in: QuizCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    lesson = db.query(Lesson).filter(Lesson.id == quiz_in.lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
    data = quiz_in.model_dump()
    level_id = data.pop("level_id", None)
    branch_id = data.pop("branch_id", None)
    _assert_lesson_scope(db, lesson, level_id, branch_id)
    quiz = Quiz(**data)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return _quiz_to_out(db, quiz)


@router.put("/{quiz_id}", response_model=QuizOut)
def update_quiz(
    quiz_id: int,
    quiz_in: QuizUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = _get_quiz_for_admin(db, quiz_id)
    data = quiz_in.model_dump(exclude_unset=True)
    level_id = data.pop("level_id", None)
    branch_id = data.pop("branch_id", None)
    if "lesson_id" in data:
        lesson = db.query(Lesson).filter(Lesson.id == data["lesson_id"]).first()
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
        _assert_lesson_scope(db, lesson, level_id, branch_id)
    for field, value in data.items():
        setattr(quiz, field, value)
    db.commit()
    db.refresh(quiz)
    return _quiz_to_out(db, quiz)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = _get_quiz_for_admin(db, quiz_id)
    db.delete(quiz)  # الأسئلة والمحاولات والإجابات تُحذف cascade
    db.commit()
    return None


# ---------------- Admin: questions ----------------

@router.post("/{quiz_id}/questions", response_model=QuestionAdminOut, status_code=status.HTTP_201_CREATED)
def create_question(
    quiz_id: int,
    q_in: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = _get_quiz_for_admin(db, quiz_id)
    if q_in.question_type not in QUESTION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="نوع السؤال غير مدعوم")
    question = Question(quiz_id=quiz.id, **q_in.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return QuestionAdminOut.model_validate(question)


@router.get("/{quiz_id}", response_model=None)
def get_quiz_detail(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """تفاصيل الاختبار — المشرف يرى الإجابات، الطالب لا يراها أبدًا."""
    if _is_admin(current_user):
        quiz = _get_quiz_for_admin(db, quiz_id)
        questions = (
            db.query(Question)
            .filter(Question.quiz_id == quiz.id)
            .order_by(Question.display_order, Question.id)
            .all()
        )
        detail = _quiz_to_out(db, quiz).model_dump()
        detail["questions"] = [QuestionAdminOut.model_validate(q).model_dump() for q in questions]
        return detail
    quiz = _get_quiz_for_student(db, quiz_id, current_user)
    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz.id)
        .order_by(Question.display_order, Question.id)
        .all()
    )
    detail = _quiz_to_out(db, quiz).model_dump()
    detail["questions"] = [QuestionStudentOut.model_validate(q).model_dump() for q in questions]
    return detail


# ---------------- Student: attempts ----------------

@router.post("/{quiz_id}/attempts", response_model=QuizAttemptOut, status_code=status.HTTP_201_CREATED)
def start_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = _quiz_to_out(db, _get_quiz_for_student(db, quiz_id, current_user))  # تحقق الإتاحة أولًا
    attempt = QuizAttempt(quiz_id=quiz.id, user_id=current_user.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    out = QuizAttemptOut.model_validate(attempt)
    out.answers_count = 0
    return out


@router.get("/{quiz_id}/attempts/me", response_model=list[QuizAttemptOut])
def my_attempts(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الاختبار غير موجود")
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.started_at.desc())
        .all()
    )
    result = []
    for a in attempts:
        out = QuizAttemptOut.model_validate(a)
        out.answers_count = len(a.answers)
        result.append(out)
    return result
