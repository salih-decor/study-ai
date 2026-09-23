from sqlalchemy import Column, Integer, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("lesson_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, nullable=False, index=True)  # denormalized لتسريع الترشيح
    chunk_index = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)
    # معلومات إضافية: {source_title, origin, page?} — لا تُخترع أرقام صفحات أبدًا
    chunk_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("LessonDocument", back_populates="chunks")

    document = relationship("LessonDocument", back_populates="chunks")
