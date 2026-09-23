import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "مراجعي الذكي"
    API_V1_STR: str = "/api/v1"

    # البيئة: development | production (تغيّر السلوك دون تغيير الكود)
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./study_ai.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret_key_for_dev")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # كلمات مرور seed التطوير (تُقرأ من البيئة في seed_dev.py فقط).
    # أُعلن عنها هنا لأنها منصوصة في .env.example؛ وإلا ترفضها pydantic-settings
    # كمدخلات زائدة (extra_forbidden) عند قراءة .env وتفشل Settings() حتى في التطوير.
    DEV_ADMIN_PASSWORD: str = os.getenv("DEV_ADMIN_PASSWORD", "")
    DEV_STUDENT_PASSWORD: str = os.getenv("DEV_STUDENT_PASSWORD", "")

    # CORS: قائمة مفصولة بفواصل (لا "*" في الإنتاج — يُرفض عند الإقلاع)
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    ENABLE_DOCS: bool = os.getenv("ENABLE_DOCS", "true").lower() == "true"

    # حماية brute-force (ذاكرة محلية — كافية لعملية واحدة؛ Redis لمتعدد العمليات)
    LOGIN_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("LOGIN_RATE_LIMIT_PER_MINUTE", "30"))
    REGISTER_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("REGISTER_RATE_LIMIT_PER_MINUTE", "10"))

    # AI provider (keys تبقى في البيئة فقط — لا توضع في الكود أبدًا)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")  # mock | openai-compatible
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "")
    AI_MAX_QUESTION_CHARS: int = int(os.getenv("AI_MAX_QUESTION_CHARS", "2000"))
    AI_RATE_LIMIT_PER_HOUR: int = int(os.getenv("AI_RATE_LIMIT_PER_HOUR", "30"))

    # RAG
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

    # الرفع
    UPLOAD_MAX_MB: int = int(os.getenv("UPLOAD_MAX_MB", "5"))

    # التعلم (عتبات الضعف — كلها هنا، لا قيم مخفية في الكود)
    WEAKNESS_MIN_ATTEMPTS: int = int(os.getenv("WEAKNESS_MIN_ATTEMPTS", "2"))
    WEAKNESS_THRESHOLD: float = float(os.getenv("WEAKNESS_THRESHOLD", "60.0"))
    RECURRING_MISTAKE_THRESHOLD: int = int(os.getenv("RECURRING_MISTAKE_THRESHOLD", "2"))
    REVIEW_PLAN_MAX_ITEMS: int = int(os.getenv("REVIEW_PLAN_MAX_ITEMS", "6"))

    # جدولة المراجعة (أيام الفاصل حسب الشدة — قابلة للتهيئة، ليست SM-2)
    REVIEW_INTERVAL_HIGH_DAYS: int = int(os.getenv("REVIEW_INTERVAL_HIGH_DAYS", "1"))
    REVIEW_INTERVAL_MEDIUM_DAYS: int = int(os.getenv("REVIEW_INTERVAL_MEDIUM_DAYS", "2"))
    REVIEW_INTERVAL_LOW_DAYS: int = int(os.getenv("REVIEW_INTERVAL_LOW_DAYS", "4"))
    REVIEW_INTERVAL_MASTERED_DAYS: int = int(os.getenv("REVIEW_INTERVAL_MASTERED_DAYS", "7"))
    REVIEW_MASTERED_MASTERY: float = float(os.getenv("REVIEW_MASTERED_MASTERY", "90.0"))
    REVIEW_MASTERED_CONFIDENCE: float = float(os.getenv("REVIEW_MASTERED_CONFIDENCE", "0.8"))


settings = Settings()


def cors_origin_list() -> list[str]:
    return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]


def is_production() -> bool:
    return settings.APP_ENV.lower() == "production"
