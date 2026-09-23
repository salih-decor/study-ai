from fastapi import APIRouter
from app.api.v1.endpoints import auth, subjects, lessons, progress, quizzes, questions, attempts
from app.api.v1.endpoints import documents, ai, image_analysis, learning


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["المصادقة (Authentication)"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["المواد الدراسية (Subjects)"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["الدروس (Lessons)"])
api_router.include_router(progress.router, prefix="/progress", tags=["التقدم (Progress)"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["الاختبارات (Quizzes)"])
api_router.include_router(questions.router, prefix="/questions", tags=["الأسئلة (Questions)"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["المحاولات (Attempts)"])
api_router.include_router(documents.router, prefix="/documents", tags=["المستندات (Documents)"])
api_router.include_router(ai.router, prefix="/ai", tags=["المساعد الذكي (AI)"])
api_router.include_router(image_analysis.router, prefix="/image-analysis", tags=["تحليل الصور (OCR)"])
api_router.include_router(learning.router, prefix="/learning", tags=["ملف التعلم (Learning)"])
