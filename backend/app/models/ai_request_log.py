from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AIRequestLog(Base):
    """سجل استخدام AI للإحصائيات — بلا كلمات مرور أو tokens أو مفاتيح."""

    __tablename__ = "ai_request_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, nullable=True, index=True)
    request_type = Column(String(30), nullable=False, default="ask")  # ask | explain | summarize | image
    success = Column(Boolean, default=True, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="ai_request_logs")
