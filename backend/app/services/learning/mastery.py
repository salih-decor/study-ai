"""حساب الإتقان mastery — حتمي وقابل للتفسير (لا AI هنا).

المعادلة (موثقة):
    - الإجابات مرتبة من الأقدم إلى الأحدث: r_1 .. r_n (True=صحيحة).
    - الوزن الخطي بالحداثة: w_i = i (الأحدث وزن أكبر).
    - mastery = 100 * Σ(w_i * r_i) / Σ(w_i)، مقربًا لمنزلة واحدة.
    - الثقة: confidence = min(n / 6, 1.0) — تقدير مبكر عند عينات قليلة.
    - إذا كان n < WEAKNESS_MIN_ATTEMPTS → mastery = None (لا حكم — لا نسم الطالب ضعيفًا).

النتيجة دائمًا بين 0 و100.
"""

from app.core.config import settings


def compute_mastery(results: list[bool]) -> tuple[float | None, float, int]:
    """يرجع (mastery أو None, confidence, sample_size). المدخل من الأقدم للأحدث."""
    n = len(results)
    if n < settings.WEAKNESS_MIN_ATTEMPTS:
        return None, round(min(n / 6.0, 1.0), 2), n
    total_w = n * (n + 1) / 2.0
    earned = sum((i + 1) * (1.0 if ok else 0.0) for i, ok in enumerate(results))
    mastery = round((earned / total_w) * 100.0, 1) if total_w else 0.0
    mastery = max(0.0, min(100.0, mastery))
    return mastery, round(min(n / 6.0, 1.0), 2), n
