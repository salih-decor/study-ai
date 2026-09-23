"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch, AiAskResponse } from "@/lib/api";

type Action = "ask" | "explain" | "summarize";

const PRESET_QUESTIONS: Record<Exclude<Action, "ask">, string> = {
  explain: "اشرح لي هذا الدرس بالتفصيل",
  summarize: "اختصر هذا الدرس في نقاط رئيسية",
};

export default function AssistantClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const lessonId = searchParams.get("lessonId");
  const actionParam = (searchParams.get("action") as Action) || "ask";

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AiAskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const autoRan = useRef(false);

  const sendQuestion = useCallback(
    async (q: string, act: Action) => {
      const text = q.trim();
      if (!text || loading) return;
      setLoading(true);
      setError("");
      setAnswer(null);
      try {
        const res = await apiFetch<AiAskResponse>("/api/v1/ai/ask", {
          method: "POST",
          body: JSON.stringify({
            question: text,
            lesson_id: lessonId ? Number(lessonId) : null,
            action: act,
          }),
        });
        setAnswer(res);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "تعذر الحصول على إجابة");
      } finally {
        setLoading(false);
      }
    },
    [lessonId, loading]
  );

  // تشغيل تلقائي لأزرار الشرح/التلخيص القادمة من صفحة الدرس
  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    if (!autoRan.current && lessonId && (actionParam === "explain" || actionParam === "summarize")) {
      autoRan.current = true;
      const preset = PRESET_QUESTIONS[actionParam];
      setQuestion(preset);
      sendQuestion(preset, actionParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuestion(question, "ask");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          <span className="font-bold text-lg text-slate-800">المساعد الذكي</span>
        </Link>
        {lessonId ? (
          <Link href={`/lessons/${lessonId}`} className="text-sm font-semibold text-blue-600 hover:underline">
            ← عودة للدرس
          </Link>
        ) : (
          <Link href="/dashboard" className="text-sm font-semibold text-blue-600 hover:underline">
            ← لوحتي
          </Link>
        )}
      </header>

      <main className="max-w-3xl mx-auto w-full p-6 flex-1 flex flex-col">
        {lessonId && (
          <div className="mb-4 p-3 text-sm text-blue-800 bg-blue-50 rounded-xl border border-blue-100 text-center">
            📖 الإجابات من محتوى الدرس المحدد فقط
          </div>
        )}

        {answer && (
          <div className="space-y-4 mb-6">
            {!answer.grounded && (
              <div className="p-4 text-sm text-amber-800 bg-amber-50 rounded-2xl border border-amber-200 text-center font-semibold">
                ⚠️ لم أجد في المحتوى المتاح معلومات كافية للإجابة — الإجابة أدناه غير مستندة لمحتوى الدرس.
              </div>
            )}
            {answer.grounded && (
              <div className="p-3 text-sm text-emerald-700 bg-emerald-50 rounded-2xl border border-emerald-200 text-center font-semibold">
                ✓ إجابة مستندة إلى محتوى دروس المنصة ({answer.sources.length} {answer.sources.length === 1 ? "مصدر" : "مصادر"})
              </div>
            )}
            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
              <div className="whitespace-pre-wrap leading-relaxed text-slate-800">{answer.answer}</div>
            </div>
            {answer.sources.length > 0 && (
              <div className="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm">
                <h3 className="font-bold text-sm text-slate-700 mb-3">📚 المصادر المستخدمة ({answer.sources.length})</h3>
                <div className="space-y-2">
                  {answer.sources.map((s) => (
                    <div key={s.chunk_id} className="text-sm text-slate-600 bg-slate-50 px-4 py-2.5 rounded-xl border border-slate-100">
                      📄 {s.title} <span className="text-slate-400">(مقطع #{s.chunk_id})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="mt-auto bg-white p-4 rounded-3xl border border-slate-200 shadow-sm">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="اكتب سؤالك هنا..."
            rows={3}
            className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition resize-none"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="mt-3 w-full py-3.5 font-bold text-white bg-blue-600 rounded-2xl hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? "جاري التفكير... 🤔" : "إرسال السؤال ✉️"}
          </button>
        </form>
      </main>
    </div>
  );
}
