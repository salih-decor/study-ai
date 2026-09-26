from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.level import Level
from app.models.branch import Branch
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter()


class LevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class BranchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level_id: int
    name: str


@router.get("", response_model=list[LevelOut])
def list_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """قائمة المستويات — قراءة لأي مستخدم مسجل (طالب أو مشرف)."""
    return db.query(Level).order_by(Level.id).all()


@router.get("/{level_id}/branches", response_model=list[BranchOut])
def list_level_branches(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """شعب مستوى محدد — قراءة لأي مستخدم مسجل (طالب أو مشرف)."""
    level = db.query(Level).filter(Level.id == level_id).first()
    if level is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستوى غير موجود")
    return db.query(Branch).filter(Branch.level_id == level_id).order_by(Branch.id).all()
