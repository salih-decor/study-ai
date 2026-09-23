# مراجعي الذكي 🧠

منصة تعليمية تفاعلية (عربية RTL) — Backend بـ FastAPI و Frontend بـ Next.js.

## التشغيل السريع

### 1) Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

- يعمل على: `http://localhost:8000`
- التوثيق التفاعلي: `http://localhost:8000/docs`
- قاعدة البيانات الافتراضية: SQLite (`study_ai.db`) — للتحويل إلى PostgreSQL عدّل `DATABASE_URL` في ملف `.env`.

### 2) Frontend (يتطلب Node.js 18+)

```powershell
cd frontend
npm install
npm run dev
```

- يعمل على: `http://localhost:3000`
- عنوان الـ API يُضبط من `frontend/.env.local` عبر `NEXT_PUBLIC_API_URL`.

## الحسابات

- إنشاء حساب طالب جديد من صفحة `/register`.
- تسجيل الدخول من `/login` ثم التوجيه إلى `/dashboard`.
- endpoint محمي للتجربة: `GET /api/v1/auth/me` مع `Authorization: Bearer <token>`.

## المرحلة 2 — المواد والدروس

- seed التطوير فقط: `.\venv\Scripts\python.exe seed_dev.py` (ينشئ `admin/admin123` و`student1/student123` — بدون أي محتوى وهمي).
- الطالب: `/subjects` ← `/subjects/[id]` ← `/lessons/[id]` (المنشور المستحق فقط).
- الإدارة (Admin فقط): `/admin` — تبويبا المواد والدروس (إضافة/تعديل/حذف/ترتيب/نشر/موعد).

| الطريقة | المسار | الصلاحية |
|---|---|---|
| GET | `/api/v1/subjects` | طالب (المفعّلة) / Admin (الكل) |
| GET | `/api/v1/subjects/{id}` | طالب (المفعّلة) / Admin (الكل) |
| GET | `/api/v1/subjects/{id}/lessons` | طالب (المنشورة المستحقة) / Admin (الكل) |
| POST/PUT/DELETE | `/api/v1/subjects...` | Admin فقط (403 لغيره) |
| GET | `/api/v1/lessons?subject_id=` | طالب (المنشورة المستحقة) / Admin (الكل) |
| GET | `/api/v1/lessons/{id}` | طالب (المنشور المستحق) / Admin (الكل) |
| POST/PUT/DELETE | `/api/v1/lessons...` | Admin فقط (النشر/الإخفاء عبر `is_published` في PUT) |

## المرحلة 3 — التقدم Progress

- جدول `lesson_progress` بقيد فريد `(user_id, lesson_id)` — سجل واحد لكل طالب/درس.
- كل العمليات مشتقة من JWT؛ لا يوجد `user_id` في أي مدخل.
- النسبة = المكتملة من المنشورة المستحقة ÷ إجمالي المنشورة المستحقة (المسودات والمجدولة مستقبلًا خارج الحسبة).

| الطريقة | المسار | الوظيفة |
|---|---|---|
| GET | `/api/v1/progress/me` | كل سجلات الطالب الحالي |
| GET | `/api/v1/progress/lessons/{id}` | تقدم الطالب في درس (404 إن لم يُسجَّل) |
| POST | `/api/v1/progress/lessons/{id}/complete` | إتمام الدرس (المنشور المستحق فقط) |
| PUT | `/api/v1/progress/lessons/{id}` | تحديث/لمس السجل (`last_accessed_at`) |
| GET | `/api/v1/progress/subjects/{id}` | نسبة المادة (total/completed/percentage) |

- الواجهة: نسب حقيقية في `/subjects` والشريط + ✓/○ في `/subjects/[id]` وزر "إتمام الدرس" في `/lessons/[id]` وملخص حقيقي في `/dashboard` (النسبة العامة/المكتملة/المتبقية).

## المرحلة 4 — الاختبارات Quizzes

- جداول: `quizzes` ← `questions` ← (`quiz_attempts` ← `quiz_answers`) مع cascade كامل وقيود فريدة.
- الطالب لا يرى `correct_answer` أبدًا قبل الإرسال (schemas منفصلة `QuestionStudentOut`/`QuestionAdminOut`).
- كل التصحيح في Backend (يُتجاهل أي score من Frontend) + تحديث `LessonProgress.last_score` دون المساس بـ `is_completed`.

| الطريقة | المسار | الصلاحية |
|---|---|---|
| GET | `/api/v1/quizzes` | Admin (الكل) |
| POST/PUT/DELETE | `/api/v1/quizzes...` | Admin |
| POST/PUT/DELETE | `/api/v1/quizzes/{id}/questions` + `/api/v1/questions/{id}` | Admin |
| GET | `/api/v1/quizzes/{id}` | طالب (بدون إجابات) / Admin (كاملة) |
| GET | `/api/v1/lessons/{id}/quizzes` | طالب (المفعّلة) / Admin (الكل) |
| POST | `/api/v1/quizzes/{id}/attempts` | بدء محاولة (مالكها = صاحب JWT) |
| GET | `/api/v1/quizzes/{id}/attempts/me` | محاولاتي |
| POST | `/api/v1/attempts/{id}/submit` | إرسال مرة واحدة (إعادة الإرسال ← 400) |
| GET | `/api/v1/attempts/{id}/result` | النتيجة + الشرح (المالك فقط) |

- الواجهة: `/quizzes/[id]` (مقدمة ← أسئلة بتنقل ومؤشر ← نتيجة + مراجعة + إعادة) وزر "اختبرني" مفعّل في صفحة الدرس وتبويب "إدارة الاختبارات" في `/admin`.

## المرحلة 5 — AI + RAG + تجهيز OCR

- المزود الافتراضي `mock` (بلا مفاتيح)؛ المزود الحقيقي عبر `AI_PROVIDER=openai-compatible` + `AI_API_KEY` + `AI_BASE_URL` في `.env` فقط.
- طبقات: `services/ai` (provider/service) • `services/rag` (chunker/retriever/indexer — SimpleRetriever يعمل مع SQLite، والواجهة جاهزة لـ pgvector) • `services/ocr` (تحقق + مزود فارغ صادق) • حدّ استخدام `AI_RATE_LIMIT_PER_HOUR` من سجل الطلبات.
- محتوى الدرس يُفهرس تلقائيًا كمستند RAG عند إنشائه/تعديله.

| الطريقة | المسار | الصلاحية |
|---|---|---|
| POST | `/api/v1/documents/text` + `/documents/upload` (TXT/PDF) | Admin |
| GET | `/api/v1/lessons/{id}/documents` | Admin |
| POST / DELETE | `/api/v1/documents/{id}/process` + `/documents/{id}` | Admin |
| POST | `/api/v1/ai/ask` (ask/explain/summarize + `grounded` + مصادر) | طالب (المرئي فقط) |
| GET | `/api/v1/ai/status` (بلا أسرار) | مسجّل |
| POST | `/api/v1/image-analysis` (تحقق صارم؛ OCR الحقيقي لاحقًا) | مسجّل |

- الواجهة: `/assistant` (تشغيل تلقائي للشرح/التلخيص من صفحة الدرس) + أزرار الدرس الثلاثة مفعّلة + تبويب "مستندات RAG" في `/admin` + بطاقة "اسأل مساعدي".

## المرحلة 6 — ملف التعلم (Weakness + خطة مراجعة)

- الحساب حتمي وقابل للتفسير (لا AI في تحديد الضعف). المعادلة:
  `mastery = 100 × Σ(wᵢ·rᵢ) / Σwᵢ` بأوزان حداثة خطية (wᵢ=i)، والثقة `min(n/6, 1)`، ولا حكم تحت `WEAKNESS_MIN_ATTEMPTS`.
- الأولوية: `(100-mastery) + min(15×متكررة, 30) + حداثة(10) + قِدم مراجعة(10)` — محصورة 100.
- القواعد: الخطأ twice = متكرر • الإجابة الصحيحة لاحقًا = محلول (يُعاد فتحه عند الخطأ) • الإتمام/إرسال اختبار = مراجعة (`last_reviewed_at`).

| الطريقة | المسار |
|---|---|
| GET | `/api/v1/learning/profile` (الإتقان العام + الضعف + المتكرر + الأخير) |
| GET | `/api/v1/learning/weaknesses` • `/learning/mistakes` (خاصة بالمالك فقط) |
| GET | `/api/v1/learning/review-plan` (`{date, items[]}` بأولوية رقمية) |
| GET | `/api/v1/learning/admin/overview` (مجمع فقط — Admin) |

- الواجهة: `/progress` (إتقان/مكتمل/أخير/مراجعة/متكرر — كله حقيقي) + قسم "خطة اليوم 🎯" في `/dashboard` (فارغ ← رسالة عدم كفاية البيانات، لا توصيات وهمية).

## المرحلة 7 — جدولة المراجعة

- جدول `student_review_schedules` بقيد فريد (user/lesson) وحالات pending/completed/paused.
- الفاصل من الشدة: high→1d / medium→2d / low→4d / mastered→7d (كلها في `.env`).
- التخرج: mastery≥90 وثقة≥0.8 ← completed بلا موعد. الإتمام الصريح/إتمام الدرس/إرسال اختبار = أحداث مراجعة (count+1 للصريح فقط، ولا مساس بـ mastery أبدًا).

| الطريقة | المسار |
|---|---|
| GET | `/api/v1/learning/review-schedule` (اليوم + القادمة) |
| GET | `/api/v1/learning/review-schedule/today` |
| POST | `/api/v1/learning/review-schedule/{lesson_id}/complete` |

- الخطة تدمج الجدولة: موعد مستحق +15 مع سبب "حان موعد المراجعة."، وعناصرها تحمل due_at/review_count.
- الواجهة: قسما "مراجعات اليوم" (مع زر ✓ أكملت المراجعة) و"المراجعات القادمة" في `/progress`.

## المرحلة 8 — تدقيق الإكمال والتصليب

- كل البطاقات تقود لصفحات حقيقية (الميت منها موسوم "قريبًا" وغير قابل للنقر).
- صفحة الدرس تعرض حالة المراجعة (آخر/قادم/العدد) + الإكمال + الاختبارات + أدوات RAG.
- الثقة (confidence) ظاهرة بجانب كل ضعف؛ التقدير المبكر موسوم صراحة.
- المساعد يميز بصريًا الإجابة المستندة (شارة خضراء + مصادر) من غير المستندة.
- الإدارة: شريط نظرة عامة من `admin/overview` (مجمع فقط) + منع الطلبات المكررة في كل نماذج الحفظ.
- الأمان: لا أسرار في الكود/الردود، المفاتيح من البيئة، الرفع مُتحقق منه، ولا تنفيذ لملفات.

## المرحلة 9 — Production Checklist

- [ ] انسخ `backend/.env.example` إلى `backend/.env` واملأ القيم (لا تضع أسرارًا في git — `.env` و`.env.*` مُتجاهلة).
- [ ] `APP_ENV=production` + `JWT_SECRET_KEY` طويل عشوائي (64+ حرف) — الإقلاع يفشل بدونه.
- [ ] `CORS_ORIGINS` = دومين الواجهة فقط (ممنوع `*` — الإقلاع يفشل معه).
- [ ] `DATABASE_URL` → PostgreSQL للإنتاج (`postgresql://USER:PASSWORD@HOST:5432/study_ai`)؛ SQLite للتطوير فقط.
- [ ] الترحيلات: `alembic upgrade head` في الإنتاج (create_all للتطوير فقط) — راجع `backend/alembic/`.
- [ ] `NEXT_PUBLIC_API_URL` في `frontend/.env.local` = رابط الـ backend الإنتاجي.
- [ ] `AI_API_KEY` + `AI_BASE_URL` للإنتاج (وإلا يعمل MockProvider) — لا تظهر المفاتيح في أي response.
- [ ] `UPLOAD_MAX_MB` والحدود (`LOGIN/REGISTER/AI RATE_LIMIT`) حسب الحاجة.
- [ ] HTTPS أمام الـ backend (reverse proxy) + نسخ احتياطي دوري لقاعدة البيانات + مراقبة سجلات uvicorn.
- [ ] `seed_dev.py` مرفوض في الإنتاج تلقائيًا — أنشئ حساب المشرف الأول يدويًا عبر API/DB.
- [ ] الوثائق التفاعلية (`/docs`) مخفية تلقائيًا في الإنتاج.
