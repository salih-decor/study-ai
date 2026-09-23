"""طبقة الاسترجاع — واجهة مستقلة تسمح لاحقًا بـ pgvector دون تغيير الـ API."""

from abc import ABC, abstractmethod
import re
from sqlalchemy.orm import Session
from app.models.document_chunk import DocumentChunk
from app.core.config import settings


AR_STOPWORDS = {
    "من", "في", "على", "إلى", "عن", "ما", "هل", "هو", "هي", "هذا", "هذه",
    "التي", "الذي", "أن", "إن", "كان", "مع", "أو", "ثم", "كما", "لا", "لم",
    "لن", "قد", "كل", "بعد", "قبل", "عند", "غير", "إذا", "لكن", "بل", "حتى",
    "أي", "تم", "يتم", "بين", "كيف", "لماذا", "ماذا", "أين", "متى",
}


def tokenize(text: str) -> list[str]:
    # كلمات فقط (بدون ترقيم): [^\W_] يستبعد علامات مثل ؟ . ، — يعمل مع العربية عبر UNICODE
    tokens = re.findall(r"[^\W_]+", text or "", re.UNICODE)
    return [t for t in tokens if len(t) > 1 and t not in AR_STOPWORDS]


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        db: Session,
        query: str,
        lesson_ids: list[int] | None,
        top_k: int | None = None,
    ) -> list[DocumentChunk]:
        """استرجاع أفضل المقاطع. lesson_ids=None تعني كل الدروس (للمشرف)."""
        raise NotImplementedError


class SimpleRetriever(BaseRetriever):
    """استرجاع تطويري يعمل مع SQLite: تطابق الكلمات المرجّح بالتكرار."""

    NAME = "simple"

    def retrieve(self, db, query, lesson_ids, top_k=None) -> list[DocumentChunk]:
        k = top_k or settings.RAG_TOP_K
        tokens = tokenize(query)
        if not tokens:
            return []
        q = db.query(DocumentChunk)
        if lesson_ids is not None:
            if not lesson_ids:
                return []
            q = q.filter(DocumentChunk.lesson_id.in_(lesson_ids))
        scored: list[tuple[int, DocumentChunk]] = []
        for chunk in q.order_by(DocumentChunk.lesson_id, DocumentChunk.chunk_index).all():
            content = chunk.content or ""
            score = sum(content.count(tok) for tok in set(tokens))
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].chunk_index))
        return [chunk for _, chunk in scored[:k]]


def get_retriever() -> BaseRetriever:
    return SimpleRetriever()
