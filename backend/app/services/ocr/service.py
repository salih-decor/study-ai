"""بنية OCR المستقبلية (جاهزة دون تنفيذ وهمي).

خط السلسلة المخطط:
    Image → OCR → Extracted text → Detect questions
        → Retrieve relevant lessons → AI → Structured answers

كل مرحلة ستكون خدمة مستقلة. حاليًا: التحقق من الملفات + مزود فارغ صادق.
"""

from abc import ABC, abstractmethod
import json
import os
import sys
import urllib.request
import urllib.error
from app.core.config import settings


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


class OpenAIVisionProvider(OcrProvider):
    """مزود رؤية عبر OpenAI-compatible API — يرسل الصورة كـ base64."""

    NAME = "openai-vision"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def extract_text(self, data: bytes, mime_type: str) -> str | None:
        import base64
        b64 = base64.b64encode(data).decode("utf-8")
        mime = mime_type or "image/png"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "استخرج النص من هذه الصورة فقط. لا تشرح، فقط اكتب النص."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            "max_tokens": 1000,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                # User-Agent عادي بدل توقيع Python-urllib الافتراضي
                # (توقيعات البوتات تُحظر من حماية Cloudflare — خطأ 1010)
                "User-Agent": "study-ai/1.0",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"[DEBUG OCR] HTTP {exc.code}: {body[:200]}", file=sys.stderr)
            return None
        except Exception as exc:
            print(f"[DEBUG OCR] {type(exc).__name__}: {exc}", file=sys.stderr)
            return None


    def extract_questions(self, data: bytes, mime_type: str) -> list[dict] | None:
        """استخراج الأسئلة مع الخيارات والحل المباشر دفعة واحدة (JSON منظم، بحد أقصى 10)."""
        import base64
        b64 = base64.b64encode(data).decode("utf-8")
        mime = mime_type or "image/png"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            "استخرج جميع الأسئلة الموجودة في هذه الصورة (بحد أقصى 10 أسئلة) "
                            "واستخرج خيارات كل سؤال إن وجدت وحل كل سؤال مباشرة مع شرح مختصر. "
                            "أعد JSON فقط بهذا الشكل تمامًا وبدون أي شرح خارج JSON: "
                            '{"questions": [{"question_text": "...", "options": ["..."], '
                            '"direct_answer": "...", "explanation": "..."}]}'
                        )},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            "max_tokens": 4000,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                # User-Agent عادي بدل توقيع Python-urllib الافتراضي
                # (توقيعات البوتات تُحظر من حماية Cloudflare — خطأ 1010)
                "User-Agent": "study-ai/1.0",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:]
            parsed = json.loads(content.strip())
            items = parsed.get("questions", []) if isinstance(parsed, dict) else []
            return [it for it in items if isinstance(it, dict) and it.get("question_text")][:10]
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"[DEBUG OCR] HTTP {exc.code}: {body[:200]}", file=sys.stderr)
            return None
        except Exception as exc:
            print(f"[DEBUG OCR] {type(exc).__name__}: {exc}", file=sys.stderr)
            return None


def get_ocr_provider() -> OcrProvider:
    """إرجاع مزود OCR حقيقي إذا كانت الإعدادات متوفرة، وإلا NullOcrProvider."""
    if (
        settings.AI_PROVIDER == "openai-compatible"
        and settings.AI_API_KEY
        and settings.AI_BASE_URL
        and settings.AI_VISION_MODEL
    ):
        return OpenAIVisionProvider(
            base_url=settings.AI_BASE_URL,
            api_key=settings.AI_API_KEY,
            model=settings.AI_VISION_MODEL,
        )
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
