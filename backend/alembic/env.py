"""Alembic env — يقرأ الرابط من إعدادات المشروع، والـ metadata من كل الموديلات."""

import os
import sys
from logging.config import fileConfig

# مجلد backend على المسار دائمًا (يعمل من أي مكان استدعاء)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.core.database import Base
# تسجيل كل الموديلات (نفس قائمة main.py — يجب تحديثها مع أي موديل جديد)
from app.models import user, subject, lesson, progress, quiz, question, quiz_attempt, quiz_answer  # noqa: F401
from app.models import lesson_document, document_chunk, ai_request_log  # noqa: F401,E501
from app.models import weakness, mistake  # noqa: F401
from app.models import review_schedule  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# الرابط من البيئة دائمًا (لا يُكتب في alembic.ini للإنتاج)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # ضروري لـ SQLite عند ALTER مستقبلًا
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
