"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { apiFetch, Subject, Lesson, Progress, SubjectProgress } from "@/lib/api";

export default function SubjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const [subject, setSubject] = useState<Subject | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [completedIds, setCompletedIds] = useState<Set<number>>(new Set());
  const [subjectProgress, setSubjectProgress] = useState<SubjectProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    Promise.all([
      apiFetch<Subject>(`/api/v1/subjects/${id}`, { cache: "no-store" }),
      apiFetch<Lesson[]>(`/api/v1/subjects/${id}/lessons`, { cache: "no-store" }),
      apiFetch<Progress[]>(`/api/v1/progress/me`, { cache: "no-store" }).catch(() => [] as Progress[]),
      apiFetch<SubjectProgress>(`/api/v1/progress/subjects/${id}`, { cache: "no-store" }).catch(() => null),
    ])
      .then(([s, l, p, sp]) => {
        setSubject(s);
        setLessons(l);
        setCompletedIds(new Set(p.filter((r) => r.is_completed).map((r) => r.lesson_id)));
        if (sp) setSubjectProgress(sp);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "تعذر تحميل المادة"))
      .finally(() => setLoading(false));
  }, [id, router]);

  const pct = Math.round(subjectProgress?.progress_percentage ?? 0);

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500">جاري التحميل...</div>;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-lg text-slate-800">مراجعي الذكي</span>
        </Link>
        <Link href="/subjects" className="text-sm font-semibold text-blue-600 hover:underline">← كل المواد</Link>
      </header>

      <main className="max-w-4xl mx-auto w-full p-6">
        {error && <div className="p-4 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center">{error}</div>}

        {subject && (
          <>
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl p-8 text-white shadow-xl shadow-blue-200/50 mb-8">
              <div className="text-4xl mb-2">{subject.icon || "📖"}</div>
              <h1 className="text-3xl font-extrabold">{subject.name}</h1>
              {subject.description && <p className="mt-2 text-blue-100">{subject.description}</p>}
              <p className="mt-3 text-sm text-blue-200">📝 {lessons.length} دروس منشورة</p>
              <div className="mt-4 flex items-center gap-3">
                <div className="flex-1 h-2.5 bg-white/25 rounded-full overflow-hidden">
                  <div className="h-full bg-white rounded-full transition-all" style={{ width: `${pct}%` }} />
                </div>
                <span className="text-sm font-bold">تقدمك: {pct}%</span>
              </div>
            </div>

            <h2 className="text-xl font-bold text-slate-800 mb-4">دروس المادة (مرتبة)</h2>
            {lessons.length === 0 && (
              <div className="text-center py-12 text-slate-400 bg-white rounded-3xl border border-slate-100">لا توجد دروس منشورة بعد</div>
            )}
            <div className="space-y-3">
              {lessons.map((lesson, idx) => (
                <Link
                  key={lesson.id}
                  href={`/lessons/${lesson.id}`}
                  className="flex items-center gap-4 bg-white p-4 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition"
                >
                  <span className="w-10 h-10 shrink-0 rounded-xl bg-blue-50 text-blue-600 font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <div className="flex-1">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2">
                      {completedIds.has(lesson.id) ? (
                        <span className="text-emerald-600 font-bold" title="مكتمل">✓</span>
                      ) : (
                        <span className="text-slate-300" title="غير مكتمل">○</span>
                      )}
                      {lesson.title}
                    </h3>
                    {lesson.description && <p className="text-sm text-slate-500 line-clamp-1">{lesson.description}</p>}
                  </div>
                  <span className="text-slate-300">←</span>
                </Link>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
