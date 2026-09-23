"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, Subject, SubjectProgress } from "@/lib/api";

export default function SubjectsPage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [progressMap, setProgressMap] = useState<Record<number, SubjectProgress>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    apiFetch<Subject[]>("/api/v1/subjects", { cache: "no-store" })
      .then(async (list) => {
        setSubjects(list);
        const entries = await Promise.all(
          list.map(async (s) => {
            try {
              const p = await apiFetch<SubjectProgress>(`/api/v1/progress/subjects/${s.id}`, { cache: "no-store" });
              return [s.id, p] as const;
            } catch {
              return null;
            }
          })
        );
        const map: Record<number, SubjectProgress> = {};
        for (const e of entries) if (e) map[e[0]] = e[1];
        setProgressMap(map);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "تعذر تحميل المواد"))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500">جاري تحميل المواد...</div>;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-lg text-slate-800">مراجعي الذكي</span>
        </Link>
        <Link href="/dashboard" className="text-sm font-semibold text-blue-600 hover:underline">← لوحتي</Link>
      </header>

      <main className="max-w-7xl mx-auto w-full p-6">
        <h1 className="text-3xl font-extrabold text-slate-900 mb-2">موادي الدراسية 📚</h1>
        <p className="text-slate-500 mb-8">اختر مادة لعرض دروسها وابدأ المراجعة</p>

        {error && <div className="p-4 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center mb-6">{error}</div>}

        {subjects.length === 0 && !error && (
          <div className="text-center py-20 text-slate-400">لا توجد مواد متاحة حاليًا</div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {subjects.map((s) => {
            const pct = Math.round(progressMap[s.id]?.progress_percentage ?? 0);
            return (
            <Link
              key={s.id}
              href={`/subjects/${s.id}`}
              className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition"
            >
              <div className="text-4xl mb-3">{s.icon || "📖"}</div>
              <h2 className="font-bold text-xl text-slate-900">{s.name}</h2>
              {s.description && <p className="mt-1 text-sm text-slate-500 line-clamp-2">{s.description}</p>}
              <div className="mt-4 flex items-center justify-between text-sm">
                <span className="text-slate-600">📝 {s.lessons_count} دروس</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-600 rounded-full transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-slate-600 text-xs font-bold">{pct}%</span>
                </div>
              </div>
            </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
