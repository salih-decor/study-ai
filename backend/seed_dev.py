"""Seed للتطوير فقط — ينشئ مستخدم admin وطالب تجريبي إن لم يكونا موجودين.

لا ينشئ أي مواد أو دروس (المحتوى الحقيقي يُدخل عبر لوحة الإدارة).
تشغيل يدوي فقط:  .\\venv\\Scripts\\python.exe seed_dev.py   (من داخل مجلد backend)
ممنوع تشغيله في الإنتاج (يرفض العمل عند APP_ENV=production).
"""

import os
import sys

if os.getenv("APP_ENV", "development").lower() == "production":
    sys.exit("seed_dev مخصص للتطوير فقط — مرفوض في بيئة الإنتاج.")

from app.core.database import SessionLocal, engine, Base
from app.models import user as user_model  # noqa: F401 — تسجيل جدول users
from app.models.user import User, UserRole
from app.core.security import get_password_hash


# كلمات مرور التطوير من البيئة فقط — لا قيم حقيقية في الكود
DEV_ADMIN_PASSWORD = os.getenv("DEV_ADMIN_PASSWORD", "")
DEV_STUDENT_PASSWORD = os.getenv("DEV_STUDENT_PASSWORD", "")

if not DEV_ADMIN_PASSWORD or not DEV_STUDENT_PASSWORD:
    sys.exit("اضبط DEV_ADMIN_PASSWORD وDEV_STUDENT_PASSWORD في backend/.env قبل تشغيل seed_dev.")


Base.metadata.create_all(bind=engine)

DEFAULT_USERS = [
    {"name": "المشرف", "username": "admin", "password": DEV_ADMIN_PASSWORD, "role": UserRole.ADMIN},
    {"name": "طالب تجربة", "username": "student1", "password": DEV_STUDENT_PASSWORD, "role": UserRole.STUDENT},
]

db = SessionLocal()
try:
    for u in DEFAULT_USERS:
        exists = db.query(User).filter(User.username == u["username"]).first()
        if exists:
            print(f"موجود مسبقًا: {u['username']} ({exists.role.value})")
            continue
        db.add(User(
            name=u["name"],
            username=u["username"],
            hashed_password=get_password_hash(u["password"]),
            role=u["role"],
        ))
        print(f"أُنشئ: {u['username']} (لا تُطبع كلمات المرور في السجلات)")
    db.commit()
finally:
    db.close()

print("تم (بيانات تطويرية فقط — غيّر كلمات المرور في الإنتاج).")
