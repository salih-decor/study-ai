from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.lesson import Lesson
from app.models.lesson_document import LessonDocument, DOCUMENT_SOURCE_TYPES
from app.models.document_chunk import DocumentChunk
from app.schemas.document import DocumentTextCreate, DocumentOut
from app.api.deps import require_admin
from app.models.user import User
from app.services.rag.indexer import index_document, extract_text, decode_txt
from app.services.ocr.service import safe_filename
import os


router = APIRouter()

ALLOWED_DOC_EXTENSIONS = {".txt": "text", ".pdf": "pdf"}
ALLOWED_DOC_MIME = {"text/plain": "text", "application/pdf": "pdf", "application/octet-stream": None}


def _doc_to_out(db: Session, doc: LessonDocument) -> DocumentOut:
    out = DocumentOut.model_validate(doc)
    out.lesson_title = doc.lesson.title if doc.lesson else None
    out.chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    return out


def _get_doc_or_404(db: Session, document_id: int) -> LessonDocument:
    doc = db.query(LessonDocument).filter(LessonDocument.id == document_id).first()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستند غير موجود")
    return doc


def _create_and_index(
    db: Session,
    lesson_id: int,
    title: str,
    source_type: str,
    extracted_text: str,
    source_path: str | None = None,
) -> LessonDocument:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الدرس غير موجود")
    if source_type not in DOCUMENT_SOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="نوع المصدر غير مدعوم")
    if not (extracted_text or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="لا يوجد نص قابل للفهرسة")
    doc = LessonDocument(
        lesson_id=lesson_id,
        title=title,
        source_type=source_type,
        source_path=source_path,
        extracted_text=extracted_text,
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    index_document(db, doc)
    db.refresh(doc)
    return doc


@router.post("/text", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_text_document(
    doc_in: DocumentTextCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doc = _create_and_index(db, doc_in.lesson_id, doc_in.title, "text", doc_in.content)
    return _doc_to_out(db, doc)


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    lesson_id: int = Form(...),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = await file.read()
    max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
    if len(data) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الملف فارغ")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"حجم الملف يتجاوز الحد ({settings.UPLOAD_MAX_MB}MB)",
        )
    filename = safe_filename(file.filename)
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"نوع الملف غير مسموح (المسموح: {', '.join(sorted(ALLOWED_DOC_EXTENSIONS))})",
        )
    if file.content_type and file.content_type not in ALLOWED_DOC_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="نوع MIME غير مسموح")
    source_type = ALLOWED_DOC_EXTENSIONS[ext]
    try:
        if source_type == "pdf":
            extracted, _meta = extract_text("pdf", data)
        else:
            extracted = decode_txt(data)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="تعذر استخراج النص من الملف")
    if not extracted.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="تعذر استخراج أي نص من الملف")
    doc = _create_and_index(db, lesson_id, title or filename, source_type, extracted, source_path=filename)
    return _doc_to_out(db, doc)


@router.post("/{document_id}/process", response_model=DocumentOut)
def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doc = _get_doc_or_404(db, document_id)
    index_document(db, doc)
    db.refresh(doc)
    return _doc_to_out(db, doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doc = _get_doc_or_404(db, document_id)
    if doc.source_type == "lesson":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="مستند محتوى الدرس يُدار من صفحة الدرس (عدّل محتوى الدرس نفسه)",
        )
    db.delete(doc)
    db.commit()
    return None
