import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.models.ai_request_log import AIRequestLog
from app.schemas.ai import AskRequest, AskResponse, SourceOut
from app.api.deps import get_current_user
from app.api.v1.endpoints.quizzes import _lesson_visible_to_student
from app.models.user import User
from app.services.rag.retriever import get_retriever
from app.services.ai.service import get_ai_service
from app.services.rate_limit import check_ai_rate_limit


router = APIRouter()
@router.get("/diagnose")
def diagnose():
    import os
    from app.core.config import settings

    return {
        "OS_AI_MODEL": os.environ.get("AI_MODEL", "NOT_SET"),
        "SETTINGS_AI_MODEL": settings.AI_MODEL,
        "OS_AI_VISION_MODEL": os.environ.get("AI_VISION_MODEL", "NOT_SET"),
        "SETTINGS_AI_VISION_MODEL": settings.AI_VISION_MODEL,
        "OS_AI_PROVIDER": os.environ.get("AI_PROVIDER", "NOT_SET"),
        "SETTINGS_AI_PROVIDER": settings.AI_PROVIDER,
        "OS_AI_BASE_URL_SET": bool(os.environ.get("AI_BASE_URL")),
        "SETTINGS_AI_BASE_URL_SET": bool(settings.AI_BASE_URL),
        "CWD": os.getcwd(),
    }

ACTION_QUESTIONS = {
    "explain": "اشرح لي هذا الدرس بالتفصيل",
    "summarize": "اختصر هذا الدرس في نقاط رئيسية",
}


def _is_admin(user: User) -> bool:
    return user.role == "admin" or str(getattr(user.role, "value", user.role)) == "admin"


def _resolve_scope(db: Session, user: User, lesson_id, subject_id) -> list[int] | None:
    """يرجع lesson_ids المسموحة (None = الكل للمشرف). يتحقق من الصلاحيات أو يرفع 404."""
    admin = _is_admin(user)
    if lesson_id is not None:
        if admin:
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            if lesson is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
        else:
            lesson = _lesson_visible_to_student(db, lesson_id)
            if lesson is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود أو غير متاح")
        return [lesson_id]
    if subject_id is not None:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if subject is None or (not admin and not subject.is_active):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المادة غير موجودة")
        q = db.query(Lesson.id).filter(Lesson.subject_id == subject_id)
        if not admin:
            from datetime import datetime
            q = q.filter(
                Lesson.is_published == True,  # noqa: E712
                ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
            )
        return [lid for (lid,) in q.all()]
    if admin:
        return None
    from datetime import datetime
    rows = (
        db.query(Lesson.id)
        .filter(
            Lesson.is_published == True,  # noqa: E712
            ((Lesson.scheduled_at == None) | (Lesson.scheduled_at <= datetime.utcnow())),  # noqa: E711
        )
        .join(Subject, Lesson.subject_id == Subject.id)
        .filter(Subject.is_active == True)  # noqa: E712
        .all()
    )
    return [lid for (lid,) in rows]


@router.post("/ask", response_model=AskResponse)
def ask_ai(
    req: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="السؤال فارغ")
    if len(question) > settings.AI_MAX_QUESTION_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"السؤال طويل جدًا (الحد {settings.AI_MAX_QUESTION_CHARS} حرف)",
        )
    if req.action in ("explain", "summarize") and req.lesson_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الشرح والتلخيص يتطلبان تحديد الدرس")

    check_ai_rate_limit(db, current_user.id)
    lesson_ids = _resolve_scope(db, current_user, req.lesson_id, req.subject_id)

    effective_question = question or ACTION_QUESTIONS.get(req.action, question)
    if req.action in ACTION_QUESTIONS and not question:
        effective_question = ACTION_QUESTIONS[req.action]

    chunks = get_retriever().retrieve(db, effective_question, lesson_ids, settings.RAG_TOP_K)
    if req.action in ("explain", "summarize") and req.lesson_id is not None:
        # الشرح/التلخيص سياقه الدرس كله، لا كلمات السؤال
        from app.models.document_chunk import DocumentChunk

        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.lesson_id == req.lesson_id)
            .order_by(DocumentChunk.chunk_index)
            .limit(12)
            .all()
        )
    sources = [
        SourceOut(
            document_id=c.document_id,
            chunk_id=c.id,
            title=(c.chunk_metadata or {}).get("source_title") or (c.document.title if c.document else "مستند"),
        )
        for c in chunks
    ]
    context_blocks = [c.content for c in chunks]

    service = get_ai_service()
    t0 = time.perf_counter()
    try:
        answer, grounded = service.answer(
            effective_question, context_blocks, req.action, getattr(current_user, "level", None),
        )
        success = True
    except RuntimeError:
        success = False
        answer, grounded = "", False
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    db.add(AIRequestLog(
        user_id=current_user.id,
        lesson_id=req.lesson_id,
        request_type=req.action,
        success=success,
        response_time_ms=elapsed_ms,
    ))
    db.commit()

    if not success:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="تعذر الاتصال بخدمة الذكاء الاصطناعي حاليًا")
    return AskResponse(answer=answer, sources=sources, grounded=grounded)


@router.get("/status")
def ai_status(current_user: User = Depends(get_current_user)):
    """حالة خدمة AI (بلا أسرار) — تُستخدم لاحقًا في لوحة الإدارة."""
    service = get_ai_service()
    return {
        "provider": "mock" if service.is_mock else settings.AI_PROVIDER,
        "model": settings.AI_MODEL,
        "mock_mode": service.is_mock,
    }
