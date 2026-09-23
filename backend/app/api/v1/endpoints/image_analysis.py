from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings
from app.services.ocr.service import get_ocr_provider, validate_image, safe_filename


router = APIRouter()


@router.post("", response_model=None)
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """تحليل صورة — التحقق الكامل الآن، وOCR الحقيقي لاحقًا (لا ادعاءات كاذبة)."""
    data = await file.read()
    error = validate_image(file.filename, file.content_type, len(data), settings.UPLOAD_MAX_MB)
    if error:
        code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "يتجاوز الحد" in error else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=error)

    # لا تُحفظ الملفات ولا تُنفَّذ — تُعالج في الذاكرة فقط
    extracted = get_ocr_provider().extract_text(data, file.content_type or "")
    if extracted is None:
        return {
            "ocr_available": False,
            "extracted_text": None,
            "filename": safe_filename(file.filename),
            "message": "خدمة OCR غير مفعّلة بعد — تم قبول الصورة والتحقق منها، وسيُضاف الاستخراج النصي في مرحلة لاحقة.",
        }
    return {
        "ocr_available": True,
        "extracted_text": extracted,
        "filename": safe_filename(file.filename),
        "message": "تم استخراج النص من الصورة.",
    }
