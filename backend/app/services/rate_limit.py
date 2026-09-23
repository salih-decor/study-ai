"""حدّ الاستخدام.

- AI: يعتمد على سجل الطلبات في DB (دقيق لكل مستخدم).
- login/register: نافذة منزلقة في الذاكرة لكل IP (تمنع brute-force؛ كافية
  لعملية واحدة — Redis مطلوب لمتعدد العمليات). الحدود من config.
لا يُخزن أي secret هنا — عدّادات فقط.
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from app.models.ai_request_log import AIRequestLog
from app.core.config import settings


_ip_hits: dict[str, deque] = defaultdict(deque)


def _check_ip_window(request: Request, limit_per_minute: int, scope: str) -> None:
    if limit_per_minute <= 0:
        return
    key = f"{scope}:{(request.client.host if request.client else 'unknown')}"
    now = time.monotonic()
    window = _ip_hits[key]
    while window and window[0] <= now - 60:
        window.popleft()
    if len(window) >= limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="طلبات كثيرة جدًا — حاول بعد دقيقة",
        )
    window.append(now)


def check_login_rate_limit(request: Request) -> None:
    _check_ip_window(request, settings.LOGIN_RATE_LIMIT_PER_MINUTE, "login")


def check_register_rate_limit(request: Request) -> None:
    _check_ip_window(request, settings.REGISTER_RATE_LIMIT_PER_MINUTE, "register")


def check_ai_rate_limit(db: Session, user_id: int) -> None:
    limit = settings.AI_RATE_LIMIT_PER_HOUR
    if limit <= 0:
        return
    since = datetime.utcnow() - timedelta(hours=1)
    used = (
        db.query(AIRequestLog)
        .filter(AIRequestLog.user_id == user_id, AIRequestLog.created_at >= since)
        .count()
    )
    if used >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"تجاوزت الحد المسموح ({limit} طلب/ساعة) — حاول لاحقًا",
        )
