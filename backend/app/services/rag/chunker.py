"""تقسيم النصوص إلى مقاطع — يدعم العربية (تقسيم عند حدود الكلمات)."""

import re
from app.core.config import settings


def clean_text(text: str) -> str:
    """تنظيف: توحيد الفراغات وإزالة الزوائد دون المساس بالكلمات."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    # فواصل الجمل العربية والأجنبية + الأسطر
    parts = re.split(r"(?<=[.!?؟…])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """تقسيم النص إلى مقاطع مرتبة (chunk_index = الترتيب)."""
    size = chunk_size or settings.RAG_CHUNK_SIZE
    ov = overlap or settings.RAG_CHUNK_OVERLAP
    cleaned = clean_text(text or "")
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]

    sentences = _split_sentences(cleaned)
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        candidate = f"{current} {sent}".strip() if current else sent
        if len(candidate) <= size:
            current = candidate
        else:
            if current:
                chunks.append(current)
                # overlap من نهاية المقطع عند حد كلمة
                tail = current[-ov:] if ov > 0 else ""
                cut = tail.find(" ")
                current = (tail[cut + 1:] + " " + sent).strip() if cut != -1 else sent
            else:
                # جملة واحدة أطول من الحد: قصّ صلب عند حد كلمة
                while len(sent) > size:
                    cut_at = sent.rfind(" ", 0, size)
                    cut_at = cut_at if cut_at > 0 else size
                    chunks.append(sent[:cut_at].strip())
                    sent = sent[cut_at:].strip()
                current = sent
    if current:
        chunks.append(current)
    return chunks
