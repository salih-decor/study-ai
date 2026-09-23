"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { apiFetch, QuizDetail, QuizQuestion, QuizAttempt, QuizResult } from "@/lib/api";

type Phase = "intro" | "exam" | "result";

export default function QuizPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [phase, setPhase] = useState<Phase>("intro");
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    apiFetch<QuizDetail>(`/api/v1/quizzes/${id}`, { cache: "no-store" })
      .then(setQuiz)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "تعذر تحميل الاختبار"))
      .finally(() => setLoading(false));
  }, [id, router]);

  const startQuiz = async () => {
    setBusy(true);
    setError("");
    try {
      const a = await apiFetch<QuizAttempt>(`/api/v1/quizzes/${id}/attempts`, { method: "POST" });
      setAttempt(a);
      setAnswers({});
      setCurrent(0);
      setResult(null);
      setPhase("exam");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "تعذر بدء المحاولة");
    } finally {
      setBusy(false);
    }
  };

  const submitQuiz = async () => {
    if (!attempt || !quiz) return;
    if (!confirm(`إنهاء الاختبار وإرسال ${Object.keys(answers).length} من ${quiz.questions.length} إجابات؟`)) return;
    setBusy(true);
    setError("");
    try {
      const payload = quiz.questions.map((q) => ({ question_id: q.id, answer: answers[q.id] ?? null }));
      const r = await apiFetch<QuizResult>(`/api/v1/attempts/${attempt.id}/submit`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setResult(r);
      setPhase("result");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "تعذر إرسال الإجابات");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500">جاري التحميل...</div>;

  const total = quiz?.questions.length ?? 0;
  const q: QuizQuestion | undefined = quiz?.questions[current];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-lg text-slate-800">مراجعي الذكي</span>
        </Link>
        {quiz && (
          <Link href={`/lessons/${quiz.lesson_id}`} className="text-sm font-semibold text-blue-600 hover:underline">
            ← عودة للدرس
          </Link>
        )}
      </header>

      <main className="max-w-3xl mx-auto w-full p-6">
        {error && <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center">{error}</div>}

        {/* المقدمة */}
        {quiz && phase === "intro" && (
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm text-center">
            <div className="text-5xl mb-4">🧠</div>
            <h1 className="text-2xl font-extrabold text-slate-900">{quiz.title}</h1>
            {quiz.description && <p className="mt-2 text-slate-500">{quiz.description}</p>}
            <p className="mt-3 text-sm text-slate-400">عدد الأسئلة: {total}</p>
            <button
              onClick={startQuiz}
              disabled={busy || total === 0}
              className="mt-6 px-10 py-3.5 font-bold text-white bg-blue-600 rounded-2xl hover:bg-blue-700 transition shadow-md shadow-blue-200 disabled:opacity-50"
            >
              {busy ? "جاري البدء..." : "ابدأ الاختبار 🚀"}
            </button>
          </div>
        )}

        {/* الامتحان */}
        {quiz && phase === "exam" && q && (
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-100 shadow-sm">
            <div className="flex justify-between items-center text-sm text-slate-500 mb-2">
              <span>السؤال {current + 1} من {total}</span>
              <span>{q.points} {q.points === 1 ? "نقطة" : "نقاط"}</span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-6">
              <div className="h-full bg-blue-600 rounded-full transition-all" style={{ width: `${((current + 1) / total) * 100}%` }} />
            </div>

            <h2 className="text-xl font-bold text-slate-900 leading-relaxed">{q.question_text}</h2>

            <div className="mt-5 space-y-3">
              {(q.question_type === "multiple_choice" || q.question_type === "true_false") && (q.options ?? []).map((opt) => (
                <button
                  key={opt}
                  onClick={() => setAnswers({ ...answers, [q.id]: opt })}
                  className={`w-full text-right px-5 py-3.5 rounded-2xl border-2 transition font-semibold ${
                    answers[q.id] === opt
                      ? "border-blue-600 bg-blue-50 text-blue-800"
                      : "border-slate-200 bg-white text-slate-700 hover:border-blue-300"
                  }`}
                >
                  {opt}
                </button>
              ))}
              {q.question_type === "short_answer" && (
                <input
                  value={answers[q.id] ?? ""}
                  onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                  placeholder="اكتب إجابتك هنا..."
                  className="w-full px-5 py-3.5 rounded-2xl border-2 border-slate-200 focus:outline-none focus:border-blue-600 transition"
                />
              )}
            </div>

            <div className="mt-8 flex justify-between gap-3">
              <button
                onClick={() => setCurrent((c) => Math.max(c - 1, 0))}
                disabled={current === 0}
                className="px-6 py-3 font-bold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200 disabled:opacity-40 transition"
              >
                السابق →
              </button>
              {current < total - 1 ? (
                <button
                  onClick={() => setCurrent((c) => c + 1)}
                  className="px-6 py-3 font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition"
                >
                  ← التالي
                </button>
              ) : (
                <button
                  onClick={submitQuiz}
                  disabled={busy}
                  className="px-8 py-3 font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 transition disabled:opacity-50"
                >
                  {busy ? "جاري الإرسال..." : "إنهاء الاختبار ✅"}
                </button>
              )}
            </div>
          </div>
        )}

        {/* النتيجة */}
        {phase === "result" && result && (
          <div className="space-y-5">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl p-8 text-white text-center shadow-xl shadow-blue-200/50">
              <div className="text-5xl mb-2">{result.percentage >= 50 ? "🎉" : "💪"}</div>
              <h1 className="text-3xl font-extrabold">نتيجتك: {result.percentage}%</h1>
              <p className="mt-2 text-blue-100">
                {result.score} من {result.total_points} نقطة • ✓ {result.correct_count} صحيحة • ✗ {result.wrong_count} خاطئة
              </p>
              <button
                onClick={startQuiz}
                disabled={busy}
                className="mt-5 px-8 py-3 font-bold text-blue-700 bg-white rounded-2xl hover:bg-blue-50 transition disabled:opacity-50"
              >
                {busy ? "جاري البدء..." : "🔄 إعادة الاختبار"}
              </button>
            </div>

            {result.answers.map((a, idx) => (
              <div key={a.question_id} className={`bg-white p-5 rounded-3xl border-2 ${a.is_correct ? "border-emerald-200" : "border-red-200"}`}>
                <h3 className="font-bold text-slate-900">
                  {idx + 1}. {a.question_text} {a.is_correct ? "✅" : "❌"}
                </h3>
                <div className="mt-3 space-y-1.5 text-sm">
                  <p className="text-slate-600">إجابتك: <span className="font-bold">{a.your_answer ?? "— (بدون إجابة)"}</span></p>
                  {!a.is_correct && (
                    <p className="text-emerald-700">الإجابة الصحيحة: <span className="font-bold">{a.correct_answer}</span></p>
                  )}
                  {a.explanation && (
                    <p className="p-3 bg-amber-50 rounded-xl border border-amber-100 text-amber-900">💡 {a.explanation}</p>
                  )}
                  <p className="text-slate-400 text-xs">النقاط: {a.points_earned} من {a.points}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
