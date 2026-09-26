from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.core.config import settings
from app.services.ocr.service import get_ocr_provider, validate_image, safe_filename
from app.services.rag.retriever import get_retriever
from app.services.ai.service import get_ai_service
from app.services.rate_limit import check_ai_rate_limit
from app.services.scoping import apply_subject_scope, resolve_user_scope, subject_in_scope


router = APIRouter()


def _resolve_lesson_scope(
    db: Session, user: User, lesson_id: int | None, subject_id: int | None
) -> list[int] | None:
    """نطاق الدروس المرئية للطالب (None = الكل للمشرف)."""
    admin = user.role == "admin" or str(getattr(user.role, "value", user.role)) == "admin"
    base = (
        db.query(Lesson)
        .join(Subject, Lesson.subject_id == Subject.id)
        .filter(Subject.is_active == True)  # noqa: E712
    )
    if not admin:
        base = base.filter(
            Lesson.is_published == True,  # noqa: E712
            ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
        )
    if lesson_id is not None:
        lesson = base.filter(Lesson.id == lesson_id).first()
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود أو غير متاح")
        if not admin:
            subj = db.query(Subject).filter(Subject.id == lesson.subject_id).first()
            scope_level, scope_branch = resolve_user_scope(db, user)
            if not subject_in_scope(subj, scope_level, scope_branch):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود أو غير متاح")
        return [lesson_id]
    if subject_id is not None:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if subject is None or (not admin and not subject.is_active):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
        if not admin:
            scope_level, scope_branch = resolve_user_scope(db, user)
            if not subject_in_scope(subject, scope_level, scope_branch):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
        return [lid for (lid,) in base.filter(Lesson.subject_id == subject_id).with_entities(Lesson.id).all()]
    if admin:
        return None
    scope_level, scope_branch = resolve_user_scope(db, user)
    base = apply_subject_scope(base, scope_level, scope_branch)
    return [lid for (lid,) in base.with_entities(Lesson.id).all()]


@router.post("", response_model=None)
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """تحليل صورة — التحقق الكامل الآن، وOCR الحقيقي لاحقًا (لا ادعاءات كاذبة)."""
    data = await file.read()
    error = validate_image(file.filename, file.content_type, len(data), settings.UPLOAD_MAX_MB)
    if error:
        code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "يتجاوز الحد" in error else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=error)

    # لا تُحفظ الملفات ولا تُنفَّذ — تُعالج في الذاكرة فقط
    extracted = get_ocr_provider().extract_text(data, file.content_type or "")
    if extracted is None:
        return {
            "ocr_available": False,
            "extracted_text": None,
            "filename": safe_filename(file.filename),
            "message": "خدمة OCR غير مفعّلة بعد — تم قبول الصورة والتحقق منها، وسيُضاف الاستخراج النصي في مرحلة لاحقة.",
        }
    return {
        "ocr_available": True,
        "extracted_text": extracted,
        "filename": safe_filename(file.filename),
        "message": "تم استخراج النص من الصورة.",
    }


@router.post("/solve", response_model=None)
async def solve_image_questions(
    file: UploadFile = File(...),
    subject_id: int | None = Form(None),
    lesson_id: int | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """الصورة → استخراج الأسئلة وحلها → تأكيد بسياق الدروس — بلا أي كتابة في قاعدة البيانات."""
    data = await file.read()
    error = validate_image(file.filename, file.content_type, len(data), settings.UPLOAD_MAX_MB)
    if error:
        code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "يتجاوز الحد" in error else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=error)

    check_ai_rate_limit(db, current_user.id)
    lesson_ids = _resolve_lesson_scope(db, current_user, lesson_id, subject_id)

    provider = get_ocr_provider()
    if not hasattr(provider, "extract_questions"):
        return {
            "questions": [],
            "message": "خدمة OCR غير مفعّلة بعد — تم قبول الصورة والتحقق منها، وسيُضاف الاستخراج النصي في مرحلة لاحقة.",
        }
    raw_items = provider.extract_questions(data, file.content_type or "")
    if not raw_items:
        return {
            "questions": [],
            "message": "تعذر استخراج الأسئلة من الصورة — تأكد من وضوح الصورة وحاول مجددًا.",
        }

    service = get_ai_service()
    questions: list[dict] = []
    for raw in raw_items[:10]:
        try:
            q_text = str(raw.get("question_text") or "").strip()
            if not q_text:
                continue
            options = raw.get("options") if isinstance(raw.get("options"), list) else None
            direct = str(raw.get("direct_answer") or "")
            expl = str(raw.get("explanation") or "")
            correct, lesson_id_found = direct, None
            chunks = get_retriever().retrieve(db, q_text, lesson_ids)
            if chunks:
                lesson_id_found = chunks[0].lesson_id
                try:
                    correct, expl = service.confirm_answer(
                        q_text, direct, [c.content for c in chunks])
                except (RuntimeError, ValueError):
                    pass
            questions.append({
                "question_text": q_text,
                "options": options,
                "correct_answer": correct,
                "explanation": expl,
                "lesson_id": lesson_id_found,
            })
        except Exception:
            continue
    return {"questions": questions}
