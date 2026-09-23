from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_answer import QuizAnswer
from app.models.progress import LessonProgress
from app.schemas.quiz_attempt import QuizAnswerCreate, QuizAttemptOut, QuizAnswerResultOut, QuizResultOut
from app.api.deps import get_current_user
from app.models.user import User
from app.services.learning.update import update_learning_data


router = APIRouter()

TRUE_SET = {"صح", "صحيح", "true", "t", "1", "نعم", "yes", "y"}
FALSE_SET = {"خطأ", "خطا", "خاطئ", "false", "f", "0", "لا", "no", "n"}


def _norm(value) -> str:
    return str(value or "").strip().casefold()


def _grade(question: Question, student_answer) -> bool:
    """تصحيح سؤال واحد في Backend — لا يُوثق بأي حساب من Frontend."""
    given = _norm(student_answer)
    correct = _norm(question.correct_answer)
    if not given:
        return False
    if question.question_type == "true_false":
        given_bool = True if given in TRUE_SET else (False if given in FALSE_SET else None)
        correct_bool = True if correct in TRUE_SET else (False if correct in FALSE_SET else None)
        if given_bool is not None and correct_bool is not None:
            return given_bool == correct_bool
        return given == correct
    # multiple_choice / short_answer (ومستقبلًا essay يُصحح يدويًا/بالذكاء الاصطناعي)
    return given == correct


def _get_owned_attempt_or_403(db: Session, attempt_id: int, user_id: int) -> QuizAttempt:
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المحاولة غير موجودة")
    if attempt.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه المحاولة تخص طالبًا آخر")
    return attempt


def _build_result(db: Session, attempt: QuizAttempt) -> QuizResultOut:
    questions = (
        db.query(Question)
        .filter(Question.quiz_id == attempt.quiz_id)
        .order_by(Question.display_order, Question.id)
        .all()
    )
    by_qid = {a.question_id: a for a in attempt.answers}
    answers_out = []
    correct_count = 0
    for q in questions:
        a = by_qid.get(q.id)
        is_ok = bool(a and a.is_correct)
        correct_count += 1 if is_ok else 0
        answers_out.append(QuizAnswerResultOut(
            question_id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            your_answer=a.answer if a else None,
            correct_answer=q.correct_answer,
            is_correct=is_ok,
            points_earned=a.points_earned if a else 0.0,
            points=q.points,
            explanation=q.explanation,
        ))
    return QuizResultOut(
        attempt_id=attempt.id,
        quiz_id=attempt.quiz_id,
        quiz_title=attempt.quiz.title if attempt.quiz else "",
        score=attempt.score,
        total_points=attempt.total_points,
        percentage=attempt.percentage,
        correct_count=correct_count,
        wrong_count=len(questions) - correct_count,
        completed_at=attempt.completed_at,
        answers=answers_out,
    )


@router.post("/{attempt_id}/submit", response_model=QuizResultOut)
def submit_attempt(
    attempt_id: int,
    answers_in: list[QuizAnswerCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_owned_attempt_or_403(db, attempt_id, current_user.id)
    if attempt.completed_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="تم إرسال هذه المحاولة مسبقًا")
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id, Quiz.is_active == True).first()  # noqa: E712
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الاختبار غير فعال حاليًا")

    quiz_questions = {q.id: q for q in db.query(Question).filter(Question.quiz_id == quiz.id).all()}
    if not quiz_questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الاختبار بلا أسئلة")

    seen: set[int] = set()
    score = 0.0
    total = 0.0
    graded: list[tuple[int, bool]] = []
    for item in answers_in:
        q = quiz_questions.get(item.question_id)
        if q is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"السؤال {item.question_id} لا ينتمي إلى هذا الاختبار",
            )
        if item.question_id in seen:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="إجابة مكررة لنفس السؤال")
        seen.add(item.question_id)
        ok = _grade(q, item.answer)
        graded.append((q.id, ok))
        earned = float(q.points) if ok else 0.0
        score += earned
        total += float(q.points)
        db.add(QuizAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            answer=item.answer,
            is_correct=ok,
            points_earned=earned,
        ))
    # الأسئلة غير المُجاب عنها تُحسب خاطئة (صفر) لكن تدخل في المجموع
    for qid, q in quiz_questions.items():
        if qid not in seen:
            total += float(q.points)
            graded.append((qid, False))
            db.add(QuizAnswer(attempt_id=attempt.id, question_id=qid, answer=None, is_correct=False, points_earned=0.0))

    now = datetime.utcnow()
    attempt.score = round(score, 2)
    attempt.total_points = round(total, 2)
    attempt.percentage = round((score / total) * 100, 1) if total else 0.0
    attempt.completed_at = now
    db.commit()

    # تحديث last_score في تقدم الدرس (دون المساس بـ is_completed)
    progress = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == current_user.id, LessonProgress.lesson_id == quiz.lesson_id)
        .first()
    )
    if progress is None:
        progress = LessonProgress(user_id=current_user.id, lesson_id=quiz.lesson_id)
        db.add(progress)
    progress.last_score = attempt.percentage
    progress.last_accessed_at = now
    db.commit()

    # تحديث بيانات التعلم (ضعف/أخطاء/إتقان) — خطأ هنا لا يكسر الدرجة المحفوظة
    try:
        update_learning_data(db, current_user.id, quiz.lesson_id, graded)
    except Exception:
        db.rollback()

    db.refresh(attempt)
    return _build_result(db, attempt)


@router.get("/{attempt_id}/result", response_model=QuizResultOut)
def get_result(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_owned_attempt_or_403(db, attempt_id, current_user.id)
    if attempt.completed_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="لم يتم إرسال هذه المحاولة بعد")
    return _build_result(db, attempt)


@router.get("/{attempt_id}", response_model=QuizAttemptOut)
def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_owned_attempt_or_403(db, attempt_id, current_user.id)
    out = QuizAttemptOut.model_validate(attempt)
    out.answers_count = len(attempt.answers)
    return out
