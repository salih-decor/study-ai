"""النطاق المركزي (مستوى/شعبة) — مطابقة نصوص المستخدم مع taxonomy دون أي كتابة.

القواعد:
- المطابقة حتمية بعد التطبيع فقط (مساواة تامة) — لا تخمين ولا تقريب.
- الشعبة تُطابق داخل المستوى المطابق فقط.
- أي نقص أو جهالة → (None, None) أي المحتوى العام فقط.
- لا UPDATE ولا تخزين لأي IDs في User.
"""

import re
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.level import Level
from app.models.branch import Branch
from app.models.subject import Subject


def _norm(text: str | None) -> str:
    """تطبيع حتمي يُطبق على الطرفين: مسافات + همزات/تاء مربوطة/ألف مقصورة."""
    t = re.sub(r"\s+", " ", (text or "").strip())
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ة", "ه").replace("ى", "ي")
    return t


# بدائل رقمية/لفظية صريحة ومراجَعة فقط (تُطبق بعد التطبيع) — لا تخمين خارجها
LEVEL_ALIASES: dict[str, str] = {
    "1 ثانوي": "السنة الأولى ثانوي",
    "اولي ثانوي": "السنة الأولى ثانوي",
    "الاولي ثانوي": "السنة الأولى ثانوي",
    "سنه اولي ثانوي": "السنة الأولى ثانوي",
    "2 ثانوي": "السنة الثانية ثانوي",
    "ثانيه ثانوي": "السنة الثانية ثانوي",
    "الثانيه ثانوي": "السنة الثانية ثانوي",
    "سنه ثانيه ثانوي": "السنة الثانية ثانوي",
    "3 ثانوي": "السنة الثالثة ثانوي",
    "ثالثه ثانوي": "السنة الثالثة ثانوي",
    "الثالثه ثانوي": "السنة الثالثة ثانوي",
    "سنه ثالثه ثانوي": "السنة الثالثة ثانوي",
}


# تكافؤ أسماء الشعب (مفاتيح وقيم بصيغة مطبّعة) — الرسمي "علوم تجريبية"،
# و"علوم" مقبولة للتوافق مع النصوص القديمة. يُطبق داخل المستوى المطابق فقط.
BRANCH_ALIASES: dict[str, list[str]] = {
    "علوم": ["علوم تجريبيه"],          # "علوم" ≡ "علوم تجريبية"
    "علوم تجريبيه": ["علوم"],          # "علوم تجريبية" ≡ "علوم"
}


def resolve_user_scope(db: Session, user) -> tuple[int | None, int | None]:
    """إرجاع (level_id, branch_id) المطابقين لنصوص المستخدم — أو (None, None) للعام فقط."""
    level_text = (getattr(user, "level", None) or "").strip()
    branch_text = (getattr(user, "branch", None) or "").strip()
    if not level_text or not branch_text:
        return (None, None)
    norm_level = _norm(level_text)
    level = None
    for lv in db.query(Level).all():
        if _norm(lv.name) == norm_level:
            level = lv
            break
    if level is None:
        canonical = LEVEL_ALIASES.get(norm_level)
        if canonical is None:
            return (None, None)
        level = db.query(Level).filter(Level.name == canonical).first()
        if level is None:
            return (None, None)
    norm_branch = _norm(branch_text)
    candidates = {norm_branch} | {_norm(a) for a in BRANCH_ALIASES.get(norm_branch, [])}
    branch = (
        db.query(Branch)
        .filter(Branch.level_id == level.id)
        .all()
    )
    branch_id = None
    for br in branch:
        if _norm(br.name) in candidates:
            branch_id = br.id
            break
    if branch_id is None:
        return (None, None)
    return (level.id, branch_id)


def apply_subject_scope(query, level_id: int | None, branch_id: int | None):
    """تضييق استعلام يحوي Subject: (NULL أو ==) — و(null,null) تعني العام فقط.

    يجب أن يكون Subject منضمًا (join) في الاستعلام قبل الاستدعاء.
    """
    if level_id is None and branch_id is None:
        return query.filter(Subject.level_id == None, Subject.branch_id == None)  # noqa: E711
    if level_id is not None:
        query = query.filter(or_(Subject.level_id == None, Subject.level_id == level_id))  # noqa: E711
    if branch_id is not None:
        query = query.filter(or_(Subject.branch_id == None, Subject.branch_id == branch_id))  # noqa: E711
    return query


def _is_admin_user(user) -> bool:
    """نفس قاعدة المشرف المستخدمة في الـ endpoints (دور admin فقط يتجاوز النطاق)."""
    role = getattr(user, "role", None)
    value = getattr(role, "value", role)
    return value == "admin" or str(value) == "admin"


def subject_in_scope(subject: Subject | None, level_id: int | None, branch_id: int | None) -> bool:
    """فحص مادة محمّلة: هل تدخل في النطاق؟ (None تعني غير موجودة → خارج النطاق)."""
    if subject is None:
        return False
    if level_id is None and branch_id is None:
        return subject.level_id is None and subject.branch_id is None
    if level_id is not None and subject.level_id is not None and subject.level_id != level_id:
        return False
    if branch_id is not None and subject.branch_id is not None and subject.branch_id != branch_id:
        return False
    return True


def lesson_in_scope(db: Session, user, lesson_id: int) -> bool:
    """هل الدرس داخل نطاق المستخدم؟ المشرف يرى الكل."""
    from app.models.lesson import Lesson

    if _is_admin_user(user):
        return True
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        return False
    subject = db.query(Subject).filter(Subject.id == lesson.subject_id).first()
    level_id, branch_id = resolve_user_scope(db, user)
    return subject_in_scope(subject, level_id, branch_id)


def allowed_lesson_ids(db: Session, user) -> list[int] | None:
    """معرفات الدروس الداخلة في نطاق المستخدم (None = الكل للمشرف) — للترشيح اللاحق."""
    from app.models.lesson import Lesson

    if _is_admin_user(user):
        return None
    level_id, branch_id = resolve_user_scope(db, user)
    q = (
        db.query(Lesson.id)
        .join(Subject, Lesson.subject_id == Subject.id)
        .filter(Subject.is_active == True)  # noqa: E712
    )
    q = apply_subject_scope(q, level_id, branch_id)
    return [lid for (lid,) in q.all()]
