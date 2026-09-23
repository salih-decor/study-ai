"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { apiFetch, Lesson, Progress, Quiz, ReviewScheduleList, ReviewSchedule } from "@/lib/api";

const FUTURE_ACTIONS = [
  { title: "اختبرني في هذا الدرس", icon: "🧠" },
  { title: "اشرح لي الدرس", icon: "💡" },
  { title: "اختصر الدرس", icon: "✂️" },
  { title: "اسأل عن الدرس", icon: "❓" },
];

export default function LessonDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [completed, setCompleted] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [lessonQuizzes, setLessonQuizzes] = useState<Quiz[] | null>(null);
  const [loadingQuizzes, setLoadingQuizzes] = useState(false);
  const [reviewInfo, setReviewInfo] = useState<ReviewSchedule | null>(null);

  const fmtDT = (iso: string | null) => {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString("ar", { dateStyle: "medium", timeStyle: "short" });
    } catch {
      return iso.slice(0, 16).replace("T", " ");
    }
  };

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    apiFetch<Lesson>(`/api/v1/lessons/${id}`, { cache: "no-store" })
      .then(async (l) => {
        setLesson(l);
        try {
          const sched = await apiFetch<ReviewScheduleList>("/api/v1/learning/review-schedule", { cache: "no-store" });
          const mine = [...sched.today, ...sched.upcoming].find((r) => r.lesson_id === Number(id)) ?? null;
          setReviewInfo(mine);
        } catch {
          // لا جدول مراجعة بعد — طبيعي
        }
        try {
          // تسجيل الوصول للدرس (إنشاء/تحديث last_accessed_at)
          const p = await apiFetch<Progress>(`/api/v1/progress/lessons/${id}`, {
            method: "PUT",
            body: JSON.stringify({}),
          });
          setCompleted(p.is_completed);
        } catch {
          // لا يوجد تقدم بعد — يُنشأ عند الإتمام
        }
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "تعذر تحميل الدرس"))
      .finally(() => setLoading(false));
  }, [id, router]);

  const handleQuizButton = async () => {
    setNotice("");
    setLessonQuizzes(null);
    setLoadingQuizzes(true);
    try {
      const list = await apiFetch<Quiz[]>(`/api/v1/lessons/${id}/quizzes`, { cache: "no-store" });
      if (list.length === 0) {
        setNotice("لا يوجد اختبار لهذا الدرس بعد — سيضيفه المشرف قريبًا 📝");
      } else if (list.length === 1) {
        router.push(`/quizzes/${list[0].id}`);
      } else {
        setLessonQuizzes(list);
      }
    } catch (e: unknown) {
      setNotice(e instanceof Error ? e.message : "تعذر جلب الاختبارات");
    } finally {
      setLoadingQuizzes(false);
    }
  };

  const handleComplete = async () => {
    setCompleting(true);
    try {
      const p = await apiFetch<Progress>(`/api/v1/progress/lessons/${id}/complete`, { method: "POST" });
      setCompleted(p.is_completed);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "تعذر تسجيل الإتمام");
    } finally {
      setCompleting(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500">جاري التحميل...</div>;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-lg text-slate-800">مراجعي الذكي</span>
        </Link>
        <span className="text-sm text-slate-400">صفحة الدرس</span>
      </header>

      <main className="max-w-3xl mx-auto w-full p-6">
        {error && <div className="p-4 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center">{error}</div>}

        {lesson && (
          <>
            <Link
              href={`/subjects/${lesson.subject_id}`}
              className="text-sm font-semibold text-blue-600 hover:underline"
            >
              ← {lesson.subject_name || "المادة"}
            </Link>
            <h1 className="mt-2 text-3xl font-extrabold text-slate-900">{lesson.title}</h1>
            {lesson.description && <p className="mt-2 text-slate-500">{lesson.description}</p>}

            <div className="mt-4">
              {completed ? (
                <div className="p-3.5 text-center font-bold text-emerald-700 bg-emerald-50 rounded-2xl border border-emerald-200">
                  ✓ تم إكمال الدرس
                </div>
              ) : (
                <button
                  onClick={handleComplete}
                  disabled={completing}
                  className="w-full py-3.5 px-4 font-bold text-white bg-emerald-600 rounded-2xl hover:bg-emerald-700 transition shadow-md shadow-emerald-200 disabled:opacity-50"
                >
                  {completing ? "جاري التسجيل..." : "✓ إتمام الدرس"}
                </button>
              )}
            </div>

            <div className="mt-3 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm text-sm">
              {reviewInfo ? (
                <div className="flex flex-wrap gap-x-6 gap-y-1 text-slate-600">
                  <span>🕒 آخر مراجعة: <b>{fmtDT(reviewInfo.last_reviewed_at)}</b></span>
                  <span>🗓️ الموعد القادم: <b>{fmtDT(reviewInfo.due_at)}</b></span>
                  <span>🔁 مرات المراجعة: <b>{reviewInfo.review_count}</b></span>
                </div>
              ) : (
                <p className="text-slate-400 text-center">لا توجد مراجعات مجدولة لهذا الدرس بعد.</p>
              )}
            </div>

            <article className="mt-6 bg-white p-6 sm:p-8 rounded-3xl border border-slate-100 shadow-sm">
              {lesson.content ? (
                <div className="prose prose-slate max-w-none whitespace-pre-wrap leading-relaxed text-slate-800">
                  {lesson.content}
                </div>
              ) : (
                <p className="text-slate-400 text-center py-8">لا يوجد محتوى نصي لهذا الدرس بعد</p>
              )}
            </article>

            <h2 className="mt-8 mb-3 text-lg font-bold text-slate-800">أدوات الذكاء الاصطناعي</h2>
            {notice && (
              <div className="mb-3 p-3 text-sm text-amber-700 bg-amber-50 rounded-xl border border-amber-100 text-center">
                {notice}
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleQuizButton}
                disabled={loadingQuizzes}
                className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition text-center disabled:opacity-50"
              >
                <div className="text-2xl mb-1">🧠</div>
                <div className="font-bold text-sm text-slate-700">اختبرني في هذا الدرس</div>
                <div className="text-[11px] text-blue-500 mt-1 font-semibold">
                  {loadingQuizzes ? "جاري الجلب..." : "ابدأ الاختبار"}
                </div>
              </button>
              {FUTURE_ACTIONS.slice(1).map((a) => (
                <button
                  key={a.title}
                  onClick={() => router.push(`/assistant?lessonId=${id}&action=${a.title === "اشرح لي الدرس" ? "explain" : a.title === "اختصر الدرس" ? "summarize" : "ask"}`)}
                  className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition text-center"
                >
                  <div className="text-2xl mb-1">{a.icon}</div>
                  <div className="font-bold text-sm text-slate-700">{a.title}</div>
                  <div className="text-[11px] text-blue-500 mt-1 font-semibold">بالذكاء الاصطناعي 🤖</div>
                </button>
              ))}
            </div>
            {lessonQuizzes && lessonQuizzes.length > 1 && (
              <div className="mt-3 bg-white p-4 rounded-2xl border border-blue-200 space-y-2">
                <p className="text-sm font-bold text-slate-700">اختر اختبارًا:</p>
                {lessonQuizzes.map((qz) => (
                  <Link
                    key={qz.id}
                    href={`/quizzes/${qz.id}`}
                    className="block px-4 py-3 rounded-xl bg-blue-50 hover:bg-blue-100 transition font-semibold text-blue-800 text-sm"
                  >
                    🧠 {qz.title} • {qz.questions_count} أسئلة
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
