"""خط الفهرسة: document → extract → clean → chunk → index.

المستخرجات المدعومة الآن: TXT + PDF. تُضاف DOCX/الصور لاحقًا دون إعادة تصميم.
"""

import io
from sqlalchemy.orm import Session
from app.models.lesson import Lesson
from app.models.lesson_document import LessonDocument
from app.models.document_chunk import DocumentChunk
from app.services.rag.chunker import chunk_text


def decode_txt(data: bytes) -> str:
    for encoding in ("utf-8", "windows-1256", "utf-8-sig"):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def extract_pdf_text(data: bytes) -> tuple[str, list[int]]:
    """يرجع (النص الكامل، أرقام الصفحات الحقيقية فقط — لا تُخترع أبدًا)."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    texts: list[str] = []
    pages: list[int] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            t = (page.extract_text() or "").strip()
        except Exception:
            t = ""
        if t:
            texts.append(t)
            pages.append(i)
    return "\n\n".join(texts), pages


def extract_text(source_type: str, data: bytes) -> tuple[str, dict]:
    """استخراج النص + metadata حقيقية (صفحة PDF فقط عندما تكون متوفرة فعلًا)."""
    if source_type == "pdf":
        text, pages = extract_pdf_text(data)
        meta = {"pages": pages} if pages else {}
        return text, meta
    return decode_txt(data), {}


def index_document(db: Session, document: LessonDocument) -> int:
    """فهرسة مستند: حذف المقاطع القديمة، تقطيع، تخزين. يرجع عدد المقاطع."""
    document.status = "processing"
    db.commit()
    try:
        chunks = chunk_text(document.extracted_text or "")
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        for idx, content in enumerate(chunks):
            db.add(DocumentChunk(
                document_id=document.id,
                lesson_id=document.lesson_id,
                chunk_index=idx,
                content=content,
                chunk_metadata={
                    "source_title": document.title,
                    "origin": document.source_type,
                    "order": idx,
                },
            ))
        document.status = "ready" if chunks else "failed"
        db.commit()
        return len(chunks)
    except Exception:
        db.rollback()
        document.status = "failed"
        db.commit()
        return 0


def sync_lesson_content(db: Session, lesson: Lesson) -> LessonDocument | None:
    """مزامنة محتوى الدرس نفسه كمستند RAG (source_type='lesson')."""
    db.query(LessonDocument).filter(
        LessonDocument.lesson_id == lesson.id,
        LessonDocument.source_type == "lesson",
    ).delete(synchronize_session=False)
    content = (lesson.content or "").strip()
    if not content:
        db.commit()
        return None
    doc = LessonDocument(
        lesson_id=lesson.id,
        title=f"محتوى الدرس: {lesson.title}",
        source_type="lesson",
        extracted_text=content,
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    index_document(db, doc)
    return doc
