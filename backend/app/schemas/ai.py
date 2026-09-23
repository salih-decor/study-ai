from pydantic import BaseModel
from typing import Literal, Optional


class AskRequest(BaseModel):
    question: str
    lesson_id: Optional[int] = None
    subject_id: Optional[int] = None
    action: Literal["ask", "explain", "summarize"] = "ask"


class SourceOut(BaseModel):
    document_id: int
    chunk_id: int
    title: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut] = []
    grounded: bool
