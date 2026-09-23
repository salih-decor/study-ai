from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# أنواع المصادر المدعومة حاليًا (قابلة للتوسعة: docx / image لاحقًا)
DOCUMENT_SOURCE_TYPES = ("text", "pdf", "lesson")

# حالات المعالجة
DOCUMENT_STATUSES = ("pending", "processing", "ready", "failed")


class LessonDocument(Base):
    __tablename__ = "lesson_documents"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    source_type = Column(String(20), nullable=False, default="text")
    source_path = Column(String(500), nullable=True)  # اسم الملف الأصلي فقط (لا تُحفظ ملفات على القرص)
    extracted_text = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lesson = relationship("Lesson", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
