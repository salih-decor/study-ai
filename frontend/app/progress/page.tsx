"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, LearningProfile, Mistake, ReviewScheduleList, ReviewSchedule } from "@/lib/api";
import CollapsibleSection from "@/components/CollapsibleSection";

export default function ProgressPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<LearningProfile | null>(null);
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [schedule, setSchedule] = useState<ReviewScheduleList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [completingId, setCompletingId] = useState<number | null>(null);

  const loadData = async () => {
    const [p, m, s] = await Promise.all([
      apiFetch<LearningProfile>("/api/v1/learning/profile", { cache: "no-store" }),
      apiFetch<Mistake[]>("/api/v1/learning/mistakes", { cache: "no-store" }).catch(() => [] as Mistake[]),
      apiFetch<ReviewScheduleList>("/api/v1/learning/review-schedule", { cache: "no-store" }).catch(
        () => ({ today: [], upcoming: [] } as ReviewScheduleList)
      ),
    ]);
    setProfile(p);
    setMistakes(m);
    setSchedule(s);
  };

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    loadData()
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "تعذر تحميل التقدم"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  const completeReview = async (lessonId: number) => {
    setCompletingId(lessonId);
    try {
      await apiFetch(`/api/v1/learning/review-schedule/${lessonId}/complete`, { method: "POST" });
      await loadData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "تعذر تسجيل المراجعة");
    } finally {
      setCompletingId(null);
    }
  };

  const fmtDate = (iso: string | null) => {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString("ar", { dateStyle: "medium", timeStyle: "short" });
    } catch {
      return iso.slice(0, 16).replace("T", " ");
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500">جاري التحميل...</div>;

  const openMistakes = mistakes.filter((m) => !m.resolved_at);
  const resolvedCount = mistakes.filter((m) => m.resolved_at).length;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-2xl">📊</span>
          <span className="font-bold text-lg text-slate-800">تقدمي</span>
        </Link>
        <Link href="/dashboard" className="text-sm font-semibold text-blue-600 hover:underline">← لوحتي</Link>
      </header>

      <main className="max-w-5xl mx-auto w-full p-6 space-y-6">
        {error && <div className="p-4 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center">{error}</div>}

        {/* الإتقان العام */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl p-8 text-white shadow-xl shadow-blue-200/50 text-center">
          {profile?.overall_mastery === null || profile?.overall_mastery === undefined ? (
            <>
              <h1 className="text-2xl font-extrabold">لا توجد بيانات كافية بعد 📊</h1>
              <p className="mt-2 text-blue-100">أكمل بعض الدروس والاختبارات حتى نتمكن من حساب مستوى إتقانك الحقيقي.</p>
            </>
          ) : (
            <>
              <h1 className="text-5xl font-extrabold">{profile.overall_mastery}%</h1>
              <p className="mt-2 text-blue-100">متوسط الإتقان العام (من بياناتك الفعلية)</p>
            </>
          )}
          <div className="mt-4 flex justify-center gap-6 text-sm">
            <span>📚 الدروس المكتملة: <b>{profile?.lessons_completed ?? 0}</b></span>
            <span>🧠 الاختبارات المكتملة: <b>{profile?.quizzes_completed ?? 0}</b></span>
          </div>
        </div>

        {/* مراجعات اليوم */}
        <CollapsibleSection
          title="🎯 مراجعات اليوم"
          emptyText={(schedule?.today.length ?? 0) === 0 ? "لا توجد مراجعات مستحقة اليوم. أحسنت! 🎉" : undefined}
        >
          <div className="space-y-3">
            {schedule?.today.map((r: ReviewSchedule) => (
              <div key={r.lesson_id} className="px-4 py-3 bg-blue-50/60 rounded-2xl border border-blue-100 flex flex-wrap items-center gap-3">
                <div className="flex-1 min-w-40">
                  <Link href={`/lessons/${r.lesson_id}`} className="font-bold text-sm text-slate-800 hover:underline">
                    📚 {r.lesson_title}
                  </Link>
                  <p className="text-xs text-slate-500 mt-1">
                    آخر مراجعة: {fmtDate(r.last_reviewed_at)} • مرات المراجعة: {r.review_count} • الأولوية: {r.priority}
                  </p>
                </div>
                <button
                  onClick={() => completeReview(r.lesson_id)}
                  disabled={completingId === r.lesson_id}
                  className="px-4 py-2 text-sm font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 transition disabled:opacity-50"
                >
                  {completingId === r.lesson_id ? "جاري التسجيل..." : "✓ أكملت المراجعة"}
                </button>
              </div>
            ))}
          </div>
        </CollapsibleSection>

        {/* المراجعات القادمة */}
        <CollapsibleSection
          title="🗓️ المراجعات القادمة"
          emptyText={(schedule?.upcoming.length ?? 0) === 0 ? "لا توجد مراجعات مجدولة قادمة." : undefined}
        >
          <div className="space-y-2">
            {schedule?.upcoming.map((r: ReviewSchedule) => (
              <div key={r.lesson_id} className="flex items-center justify-between px-4 py-3 bg-slate-50 rounded-2xl border border-slate-100">
                <Link href={`/lessons/${r.lesson_id}`} className="font-semibold text-sm text-slate-700 hover:underline">
                  📖 {r.lesson_title}
                </Link>
                <span className="text-xs text-slate-500">الموعد: {fmtDate(r.due_at)}</span>
              </div>
            ))}
          </div>
        </CollapsibleSection>

        {/* الأداء الأخير */}
        <CollapsibleSection
          title="⚡ الأداء الأخير"
          emptyText={(profile?.recent_performance.length ?? 0) === 0 ? "لم تكمل أي اختبار بعد — 0 بيانات حقيقية، وليست تجريبية." : undefined}
        >
          <div className="space-y-2">
            {profile?.recent_performance.map((r, i) => (
              <div key={i} className="flex items-center justify-between px-4 py-3 bg-slate-50 rounded-2xl border border-slate-100">
                <span className="font-semibold text-sm text-slate-700">{r.quiz_title}</span>
                <span className={`font-extrabold ${r.percentage >= 60 ? "text-emerald-600" : "text-amber-600"}`}>{r.percentage}%</span>
              </div>
            ))}
          </div>
        </CollapsibleSection>

        {/* دروس تحتاج مراجعة */}
        <CollapsibleSection
          title="📚 دروس تحتاج مراجعة إضافية"
          emptyText={(profile?.weak_lessons.length ?? 0) === 0 ? "لا توجد دروس تحتاج مراجعة حاليًا — أحسنت! 🎉" : undefined}
        >
          <div className="space-y-3">
            {profile?.weak_lessons.map((w) => (
              <Link key={w.lesson_id} href={`/lessons/${w.lesson_id}`} className="block px-4 py-3 bg-amber-50/60 rounded-2xl border border-amber-100 hover:shadow-md transition">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-sm text-slate-800">{w.lesson_title}</span>
                  <span className="font-extrabold text-amber-700">{w.mastery_score}%</span>
                </div>
                <div className="mt-2 h-2 bg-white rounded-full overflow-hidden border border-amber-100">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: `${w.mastery_score}%` }} />
                </div>
                <p className="mt-1.5 text-[11px] text-slate-500">
                  {w.confidence < 1
                    ? `تقدير مبكر (الثقة ${Math.round(w.confidence * 100)}% — بناءً على ${w.sample_size} إجابات)`
                    : `تقدير موثوق (بناءً على ${w.sample_size} إجابات)`}
                </p>
              </Link>
            ))}
          </div>
        </CollapsibleSection>

        {/* الأخطاء المتكررة */}
        <CollapsibleSection
          title="🔁 الأخطاء المتكررة"
          emptyText={openMistakes.length === 0 && resolvedCount === 0 ? "لا توجد أخطاء متكررة مفتوحة حاليًا." : undefined}
        >
          {openMistakes.length > 0 && (
            <div className="space-y-2">
              {openMistakes.map((m) => (
                <div key={m.id} className="px-4 py-3 bg-red-50/60 rounded-2xl border border-red-100">
                  <p className="font-semibold text-sm text-slate-800">
                    ظهر لديك خطأ متكرر {m.mistake_count} مرات{m.question_text ? ":" : ""}
                  </p>
                  {m.question_text && <p className="text-sm text-slate-600 mt-1">«{m.question_text}»</p>}
                  <p className="text-xs text-slate-400 mt-1">في درس: {m.lesson_title}</p>
                </div>
              ))}
            </div>
          )}
          {resolvedCount > 0 && (
            <p className="mt-4 text-center text-sm font-semibold text-emerald-700 bg-emerald-50 rounded-2xl border border-emerald-100 px-4 py-3">
              🎉 تحسن أداؤك — تم حل {resolvedCount} من أخطائك السابقة!
            </p>
          )}
        </CollapsibleSection>
      </main>
    </div>
  );
}
