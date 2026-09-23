from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.question import Question, QUESTION_TYPES
from app.schemas.question import QuestionUpdate, QuestionAdminOut
from app.api.deps import require_admin
from app.models.user import User


router = APIRouter()


@router.put("/{question_id}", response_model=QuestionAdminOut)
def update_question(
    question_id: int,
    q_in: QuestionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="السؤال غير موجود")
    data = q_in.model_dump(exclude_unset=True)
    if "question_type" in data and data["question_type"] not in QUESTION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="نوع السؤال غير مدعوم")
    for field, value in data.items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return QuestionAdminOut.model_validate(question)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="السؤال غير موجود")
    db.delete(question)
    db.commit()
    return None
