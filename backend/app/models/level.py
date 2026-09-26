from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Level(Base):
    """المستوى الدراسي (مثال: أولى ثانوي) — تُدار قيمه من Admin فقط."""

    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    branches = relationship("Branch", back_populates="level", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="level")
