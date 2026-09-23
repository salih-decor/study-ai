"""تسجيل الأخطاء وحلّها — قواعد حتمية موثقة:

- إجابة خاطئة على سؤال له سجل مفتوح (resolved_at=None): mistake_count+1 وlast_seen_at=الآن.
- إجابة خاطئة بلا سجل (أو سجل محلول): إنشاء/إعادة فتح (resolved_at=None, count+1).
- إجابة صحيحة على سؤال له سجل مفتوح: resolved_at=الآن (حُلّ).
- إجابة صحيحة بلا سجل: لا شيء.
- متكرر (recurring) = سجل مفتوح وmistake_count >= RECURRING_MISTAKE_THRESHOLD.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.mistake import StudentMistake
from app.core.config import settings


def mistake_key_for(question_id: int) -> str:
    return f"question:{question_id}"


def is_recurring(m: StudentMistake) -> bool:
    return m.resolved_at is None and m.mistake_count >= settings.RECURRING_MISTAKE_THRESHOLD


def record_answers(
    db: Session,
    user_id: int,
    lesson_id: int,
    graded: list[tuple[int, bool, datetime]],
) -> None:
    """graded: (question_id, is_correct, at) لإرسال واحد — يُستدعى بعد حفظ الإجابات."""
    for question_id, ok, at in graded:
        key = mistake_key_for(question_id)
        row = (
            db.query(StudentMistake)
            .filter(StudentMistake.user_id == user_id, StudentMistake.mistake_key == key)
            .first()
        )
        if ok:
            if row is not None and row.resolved_at is None:
                row.resolved_at = at
        else:
            if row is None:
                row = StudentMistake(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    question_id=question_id,
                    mistake_key=key,
                    mistake_count=1,
                    first_seen_at=at,
                    last_seen_at=at,
                )
                db.add(row)
            else:
                row.mistake_count += 1
                row.last_seen_at = at
                row.resolved_at = None  # إعادة فتح عند الخطأ مجددًا
    db.commit()


def open_recurring_count(db: Session, user_id: int, lesson_id: int) -> int:
    rows = (
        db.query(StudentMistake)
        .filter(
            StudentMistake.user_id == user_id,
            StudentMistake.lesson_id == lesson_id,
            StudentMistake.resolved_at == None,  # noqa: E711
        )
        .all()
    )
    return sum(1 for r in rows if is_recurring(r))
