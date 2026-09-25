"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import type { Subject, Lesson } from "@/lib/api";

interface SolvedQuestion {
  question_text: string;
  options: string[] | null;
  correct_answer: string;
  explanation: string;
  lesson_id: number | null;
}

export default function ImageAnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [questions, setQuestions] = useState<SolvedQuestion[]>([]);
  const [lessonTitles, setLessonTitles] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiFetch<Subject[]>("/api/v1/subjects", { cache: "no-store" })
      .then(setSubjects)
      .catch(() => {});
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function handleSubject(id: string) {
    setSubjectId(id);
    setLessonId("");
    setLessons([]);
    if (!id) return;
    try {
      const ls = await apiFetch<Lesson[]>(`/api/v1/subjects/${id}/lessons`, { cache: "no-store" });
      setLessons(ls);
    } catch {
      /* تبقى القائمة فارغة — الباكند يستخدم نطاق المادة تلقائيًا */
    }
  }

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const next = e.target.files?.[0] || null;
    setFile(next);
    setPreviewUrl(next ? URL.createObjectURL(next) : null);
    setQuestions([]);
    setError("");
    setMessage("");
    e.target.value = "";
  }

  async function handleAnalyze() {
    if (!file) { setError("اختر صورة أولاً"); return; }
    setLoading(true); setError(""); setQuestions([]); setMessage(""); setLessonTitles({});
    try {
      const form = new FormData();
      form.append("file", file);
      if (subjectId) form.append("subject_id", subjectId);
      if (lessonId) form.append("lesson_id", lessonId);
      const res = await apiFetch<{ questions: SolvedQuestion[]; message?: string }>(
        "/api/v1/image-analysis/solve", { method: "POST", body: form });
      const qs = res.questions || [];
      setQuestions(qs);
      if (res.message) setMessage(res.message);
      const ids = Array.from(new Set(
        qs.map((q) => q.lesson_id).filter((v): v is number => typeof v === "number")
      ));
      const titles: Record<number, string> = {};
      await Promise.all(ids.map(async (id) => {
        try {
          const l = await apiFetch<Lesson>(`/api/v1/lessons/${id}`, { cache: "no-store" });
          if (l && l.title) titles[id] = l.title;
        } catch {
          /* تجاهل — يُعرض السؤال بدون اسم الدرس */
        }
      }));
      setLessonTitles(titles);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "فشل التحليل");
    } finally { setLoading(false); }
  }

  function formatBold(text: string): string {
    return (text || "").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col" style={{ fontFamily: "'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif" }}>
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
        <Link href="/dashboard" className="text-sm font-semibold text-blue-400 hover:underline">
          ← لوحتي
        </Link>
        <h1 className="font-bold text-xl text-white">📸 تحليل الصورة</h1>
        <div></div>
      </header>

      <main className="max-w-3xl mx-auto w-full p-6 flex-1">
        <div className="bg-gray-900 p-8 rounded-3xl border border-gray-700 shadow-lg">
          <label className="block text-sm font-bold text-gray-300 mb-2">
            اختر صورة (jpg، png، webp — الحد 5MB)
          </label>
          <input ref={galleryRef} type="file" accept="image/*" onChange={handleFile} className="hidden" />
          <input ref={cameraRef} type="file" accept="image/*" capture="environment" onChange={handleFile} className="hidden" />
          <div className="flex gap-3 mb-4" dir="rtl">
            <button type="button" onClick={() => galleryRef.current?.click()}
                    className="flex-1 py-3 font-bold text-white bg-blue-600 rounded-2xl hover:bg-blue-700 active:scale-[0.98] transition text-base">
              🖼️ اختيار صورة
            </button>
            <button type="button" onClick={() => cameraRef.current?.click()}
                    className="flex-1 py-3 font-bold text-white bg-teal-600 rounded-2xl hover:bg-teal-700 active:scale-[0.98] transition text-base">
              📷 تصوير بالكاميرا
            </button>
          </div>
          {previewUrl && (
            <div className="mb-4">
              <img src={previewUrl} alt="معاينة الصورة المختارة"
                   className="w-full max-h-72 object-contain rounded-2xl border border-gray-700 bg-gray-800" />
            </div>
          )}

          <label className="block text-sm font-bold text-gray-300 mb-2">
            المادة (اختياري — لتحسين البحث في الدروس)
          </label>
          <select value={subjectId} onChange={(e) => handleSubject(e.target.value)}
                  className="block w-full text-sm text-gray-200 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 mb-4">
            <option value="">كل المواد</option>
            {subjects.map((s) => (
              <option key={s.id} value={String(s.id)}>{s.name}</option>
            ))}
          </select>

          {lessons.length > 0 && (
            <>
              <label className="block text-sm font-bold text-gray-300 mb-2">
                الدرس (اختياري)
              </label>
              <select value={lessonId} onChange={(e) => setLessonId(e.target.value)}
                      className="block w-full text-sm text-gray-200 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 mb-4">
                <option value="">كل الدروس</option>
                {lessons.map((l) => (
                  <option key={l.id} value={String(l.id)}>{l.title}</option>
                ))}
              </select>
            </>
          )}

          <button onClick={handleAnalyze} disabled={loading || !file}
                  className="w-full py-4 font-bold text-white bg-blue-600 rounded-2xl hover:bg-blue-700 disabled:opacity-50 transition text-lg">
            {loading ? "جاري التحليل... 🤖" : "حلّل الصورة 📸"}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 text-sm text-red-400 bg-red-900/50 rounded-xl border border-red-700">{error}</div>
        )}
        {message && questions.length === 0 && (
          <div className="mt-4 p-3 text-sm text-amber-300 bg-amber-900/50 rounded-xl border border-amber-700">{message}</div>
        )}

        {questions.map((q, i) => (
          <div key={i} className="mt-4 bg-gray-900 p-6 rounded-3xl border border-gray-700 shadow-lg">
            <h3 className="font-bold text-base text-white mb-3">السؤال {i + 1}: {q.question_text}</h3>
            {q.options && q.options.length > 0 && (
              <ul className="list-disc list-inside mb-3 text-gray-200 text-sm space-y-1">
                {q.options.map((opt, j) => (
                  <li key={j}>{opt}</li>
                ))}
              </ul>
            )}
            <div className="mt-3 bg-emerald-900/50 p-4 rounded-2xl border border-emerald-700">
              <p className="text-sm text-emerald-300 font-bold mb-1">الإجابة الصحيحة:</p>
              <div className="whitespace-pre-wrap leading-relaxed text-gray-100 font-medium"
                   dangerouslySetInnerHTML={{ __html: formatBold(q.correct_answer) }} />
            </div>
            {q.explanation && (
              <div className="mt-3">
                <p className="text-sm text-gray-300 font-bold mb-1">شرح الحل:</p>
                <div className="whitespace-pre-wrap leading-relaxed text-gray-100 font-medium text-sm"
                     dangerouslySetInnerHTML={{ __html: formatBold(q.explanation) }} />
              </div>
            )}
            <p className="mt-3 text-xs text-gray-400">
              الدرس المستخدم: {q.lesson_id ? (lessonTitles[q.lesson_id] || "جاري التحميل...") : "عام — بلا درس مرتبط"}
            </p>
          </div>
        ))}
      </main>
    </div>
  );
}
