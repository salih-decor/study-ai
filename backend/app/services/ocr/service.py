"""بنية OCR المستقبلية (جاهزة دون تنفيذ وهمي).

خط السلسلة المخطط:
    Image → OCR → Extracted text → Detect questions
        → Retrieve relevant lessons → AI → Structured answers

كل مرحلة ستكون خدمة مستقلة. حاليًا: التحقق من الملفات + مزود فارغ صادق.
"""

from abc import ABC, abstractmethod
import os


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}


class OcrProvider(ABC):
    @abstractmethod
    def extract_text(self, data: bytes, mime_type: str) -> str | None:
        raise NotImplementedError


class NullOcrProvider(OcrProvider):
    """لا يوجد OCR حقيقي بعد — يعيد None بصدق بدل ادعاء النجاح."""

    NAME = "null"

    def extract_text(self, data: bytes, mime_type: str) -> str | None:
        return None


def get_ocr_provider() -> OcrProvider:
    return NullOcrProvider()


def safe_filename(filename: str | None) -> str:
    """اسم ملف آمن: basename فقط، بلا مسارات."""
    name = os.path.basename(filename or "upload")
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " ")).strip() or "upload"


def validate_image(filename: str | None, mime_type: str | None, size_bytes: int, max_mb: int) -> str | None:
    """ترجع رسالة الخطأ أو None عند الصلاحية."""
    ext = os.path.splitext((filename or "").lower())[1]
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return f"نوع الملف غير مسموح (المسموح: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))})"
    if mime_type and mime_type not in ALLOWED_IMAGE_MIME:
        return "نوع MIME غير مسموح للصور"
    if size_bytes <= 0:
        return "الملف فارغ"
    if size_bytes > max_mb * 1024 * 1024:
        return f"حجم الصورة يتجاوز الحد ({max_mb}MB)"
    return None
