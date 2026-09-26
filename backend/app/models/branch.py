from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Branch(Base):
    """الشعبة ضمن مستوى واحد (مثال: آداب تحت أولى ثانوي) — تُدار من Admin فقط."""

    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("level_id", "name", name="uq_branches_level_name"),
    )

    level = relationship("Level", back_populates="branches")
    subjects = relationship("Subject", back_populates="branch")
