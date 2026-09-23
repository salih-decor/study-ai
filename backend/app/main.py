from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, cors_origin_list, is_production
from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.models import user, subject, lesson, progress, quiz, question, quiz_attempt, quiz_answer  # noqa: F401
from app.models import lesson_document, document_chunk, ai_request_log  # noqa: F401,E501
from app.models import weakness, mistake  # noqa: F401
from app.models import review_schedule  # noqa: F401


# حراس الإنتاج: يفشل الإقلاع بدل العمل بإعدادات غير آمنة
if is_production():
    if settings.JWT_SECRET_KEY == "secret_key_for_dev" or len(settings.JWT_SECRET_KEY) < 32:
        raise RuntimeError("JWT_SECRET_KEY غير صالح للإنتاج: ضع مفتاحًا طويلًا عشوائيًا في البيئة")
    origins = cors_origin_list()
    if not origins or "*" in origins:
        raise RuntimeError("CORS_ORIGINS غير صالح للإنتاج: حدد دومينات الواجهة صراحة (ممنوع '*')")


# إنشاء الجداول عند التشغيل — Development fallback فقط.
# في الإنتاج تُدار التغييرات عبر Alembic (backend/alembic/)، ولا يُنفَّذ create_all
# أبدًا في بيئة production (الحماية أسفل: إذا وجد جدولًا ناقصًا يفشل Alembic بدل
# إنشائه تلقائيًا، وهو السلوك المطلوب للإنتاج).
if not is_production():
    Base.metadata.create_all(bind=engine)


# الوثائق التفاعلية: للتطوير فقط (مخفية دائمًا في الإنتاج).
_docs_enabled = settings.ENABLE_DOCS and not is_production()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API منصة مراجعي الذكي للتعليم التفاعلي",
    version="1.0.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "مرحباً بك في السيرفر الخلفي لمنصة مراجعي الذكي 🚀",
        "docs": "/docs"
    }
