"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, API_URL, Subject, Lesson, Quiz, QuizDetail, QuizQuestionAdmin, LessonDocument } from "@/lib/api";

export interface AdminOverview {
  totals: { subjects: number; lessons: number; quizzes: number; questions: number; users: number; completed_attempts: number };
  lessons: { lesson_id: number; title: string; attempts: number; avg_percentage: number | null; open_mistakes: number }[];
}

type Tab = "subjects" | "lessons" | "quizzes" | "documents";

const EMPTY_SUBJECT = { name: "", description: "", icon: "", image_url: "", display_order: 0, is_active: true };
const EMPTY_LESSON = {
  subject_id: 0, title: "", description: "", content: "",
  display_order: 0, is_published: false, scheduled_at: "",
};

export default function AdminPage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [tab, setTab] = useState<Tab>("subjects");
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [filterSubject, setFilterSubject] = useState<string>("all");
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [okMsg, setOkMsg] = useState("");

  // نماذج المواد
  const [showSubjectForm, setShowSubjectForm] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null);
  const [subjectForm, setSubjectForm] = useState(EMPTY_SUBJECT);

  // نماذج الدروس
  const [showLessonForm, setShowLessonForm] = useState(false);
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null);
  const [lessonForm, setLessonForm] = useState(EMPTY_LESSON);

  // الاختبارات
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [selectedQuizId, setSelectedQuizId] = useState<number | null>(null);
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestionAdmin[]>([]);
  const [showQuizForm, setShowQuizForm] = useState(false);
  const [editingQuiz, setEditingQuiz] = useState<Quiz | null>(null);
  const [quizForm, setQuizForm] = useState({ lesson_id: 0, title: "", description: "", is_active: true });
  const [showQuestionForm, setShowQuestionForm] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<QuizQuestionAdmin | null>(null);
  const [questionForm, setQuestionForm] = useState({
    question_text: "", question_type: "multiple_choice", optionsText: "",
    correct_answer: "", explanation: "", points: 1, display_order: 0,
  });

  const loadAll = async () => {
    const [s, l, q, ov] = await Promise.all([
      apiFetch<Subject[]>("/api/v1/subjects", { cache: "no-store" }),
      apiFetch<Lesson[]>("/api/v1/lessons", { cache: "no-store" }),
      apiFetch<Quiz[]>("/api/v1/quizzes", { cache: "no-store" }),
      apiFetch<AdminOverview>("/api/v1/learning/admin/overview", { cache: "no-store" }).catch(() => null),
    ]);
    setSubjects(s);
    setLessons(l);
    setQuizzes(q);
    if (ov) setOverview(ov);
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("user_role");
    if (!token) {
      router.push("/login");
      return;
    }
    if (role !== "admin") {
      router.push("/dashboard");
      return;
    }
    loadAll()
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "تعذر التحميل"))
      .finally(() => setChecking(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  const flash = (msg: string) => {
    setOkMsg(msg);
    setError("");
    setTimeout(() => setOkMsg(""), 3000);
  };
  const fail = (e: unknown) => {
    setError(e instanceof Error ? e.message : "حدث خطأ");
    setOkMsg("");
  };

  // منع الطلبات المكررة: تغليف واحد لكل نماذج الحفظ
  const guarded = (fn: (e: React.FormEvent) => Promise<void>) => async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    try {
      await fn(e);
    } finally {
      setSaving(false);
    }
  };

  // ---------- المواد ----------
  const openNewSubject = () => {
    setEditingSubject(null);
    setSubjectForm(EMPTY_SUBJECT);
    setShowSubjectForm(true);
  };
  const openEditSubject = (s: Subject) => {
    setEditingSubject(s);
    setSubjectForm({
      name: s.name, description: s.description ?? "", icon: s.icon ?? "",
      image_url: s.image_url ?? "", display_order: s.display_order, is_active: s.is_active,
    });
    setShowSubjectForm(true);
  };
  const saveSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSubject) {
        await apiFetch(`/api/v1/subjects/${editingSubject.id}`, {
          method: "PUT", body: JSON.stringify(subjectForm),
        });
        flash("تم تعديل المادة ✅");
      } else {
        await apiFetch("/api/v1/subjects", { method: "POST", body: JSON.stringify(subjectForm) });
        flash("تمت إضافة المادة ✅");
      }
      setShowSubjectForm(false);
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const deleteSubject = async (s: Subject) => {
    if (!confirm(`حذف المادة "${s.name}" مع كل دروسها؟`)) return;
    try {
      await apiFetch(`/api/v1/subjects/${s.id}`, { method: "DELETE" });
      flash("تم حذف المادة 🗑️");
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const toggleSubjectActive = async (s: Subject) => {
    try {
      await apiFetch(`/api/v1/subjects/${s.id}`, {
        method: "PUT", body: JSON.stringify({ is_active: !s.is_active }),
      });
      flash(s.is_active ? "تم تعطيل المادة" : "تم تفعيل المادة ✅");
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };

  // ---------- الدروس ----------
  const openNewLesson = () => {
    setEditingLesson(null);
    setLessonForm({ ...EMPTY_LESSON, subject_id: subjects[0]?.id ?? 0 });
    setShowLessonForm(true);
  };
  const openEditLesson = (l: Lesson) => {
    setEditingLesson(l);
    setLessonForm({
      subject_id: l.subject_id, title: l.title, description: l.description ?? "",
      content: l.content ?? "", display_order: l.display_order,
      is_published: l.is_published, scheduled_at: l.scheduled_at ? l.scheduled_at.slice(0, 16) : "",
    });
    setShowLessonForm(true);
  };
  const saveLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: Record<string, unknown> = {
        subject_id: Number(lessonForm.subject_id),
        title: lessonForm.title,
        description: lessonForm.description || null,
        content: lessonForm.content || null,
        display_order: Number(lessonForm.display_order),
        is_published: lessonForm.is_published,
        scheduled_at: lessonForm.scheduled_at ? lessonForm.scheduled_at + ":00" : null,
      };
      if (editingLesson) {
        await apiFetch(`/api/v1/lessons/${editingLesson.id}`, { method: "PUT", body: JSON.stringify(payload) });
        flash("تم تعديل الدرس ✅");
      } else {
        await apiFetch("/api/v1/lessons", { method: "POST", body: JSON.stringify(payload) });
        flash("تمت إضافة الدرس ✅");
      }
      setShowLessonForm(false);
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const deleteLesson = async (l: Lesson) => {
    if (!confirm(`حذف الدرس "${l.title}"؟`)) return;
    try {
      await apiFetch(`/api/v1/lessons/${l.id}`, { method: "DELETE" });
      flash("تم حذف الدرس 🗑️");
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const togglePublish = async (l: Lesson) => {
    try {
      await apiFetch(`/api/v1/lessons/${l.id}`, {
        method: "PUT", body: JSON.stringify({ is_published: !l.is_published }),
      });
      flash(l.is_published ? "تم إخفاء الدرس" : "تم نشر الدرس ✅");
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };

  // ---------- الاختبارات ----------
  const selectQuiz = async (quizId: number) => {
    setSelectedQuizId(quizId);
    setShowQuestionForm(false);
    setEditingQuestion(null);
    try {
      const detail = await apiFetch<QuizDetail>(`/api/v1/quizzes/${quizId}`, { cache: "no-store" });
      setQuizQuestions((detail.questions as QuizQuestionAdmin[]) ?? []);
    } catch (e: unknown) { fail(e); }
  };
  const openNewQuiz = () => {
    setEditingQuiz(null);
    setQuizForm({ lesson_id: lessons[0]?.id ?? 0, title: "", description: "", is_active: true });
    setShowQuizForm(true);
  };
  const openEditQuiz = (q: Quiz) => {
    setEditingQuiz(q);
    setQuizForm({ lesson_id: q.lesson_id, title: q.title, description: q.description ?? "", is_active: q.is_active });
    setShowQuizForm(true);
  };
  const saveQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = { ...quizForm, lesson_id: Number(quizForm.lesson_id), description: quizForm.description || null };
      if (editingQuiz) {
        await apiFetch(`/api/v1/quizzes/${editingQuiz.id}`, { method: "PUT", body: JSON.stringify(payload) });
        flash("تم تعديل الاختبار ✅");
      } else {
        await apiFetch("/api/v1/quizzes", { method: "POST", body: JSON.stringify(payload) });
        flash("تمت إضافة الاختبار ✅");
      }
      setShowQuizForm(false);
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const deleteQuiz = async (q: Quiz) => {
    if (!confirm(`حذف الاختبار "${q.title}" مع أسئلته ومحاولاته؟`)) return;
    try {
      await apiFetch(`/api/v1/quizzes/${q.id}`, { method: "DELETE" });
      if (selectedQuizId === q.id) { setSelectedQuizId(null); setQuizQuestions([]); }
      flash("تم حذف الاختبار 🗑️");
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const toggleQuizActive = async (q: Quiz) => {
    try {
      await apiFetch(`/api/v1/quizzes/${q.id}`, { method: "PUT", body: JSON.stringify({ is_active: !q.is_active }) });
      flash(q.is_active ? "تم تعطيل الاختبار" : "تم تفعيل الاختبار ✅");
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const openNewQuestion = () => {
    setEditingQuestion(null);
    setQuestionForm({
      question_text: "", question_type: "multiple_choice", optionsText: "",
      correct_answer: "", explanation: "", points: 1, display_order: quizQuestions.length,
    });
    setShowQuestionForm(true);
  };
  const openEditQuestion = (q: QuizQuestionAdmin) => {
    setEditingQuestion(q);
    setQuestionForm({
      question_text: q.question_text, question_type: q.question_type,
      optionsText: (q.options ?? []).join("\n"),
      correct_answer: q.correct_answer, explanation: q.explanation ?? "",
      points: q.points, display_order: q.display_order,
    });
    setShowQuestionForm(true);
  };
  const saveQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedQuizId === null) return;
    try {
      const options = questionForm.optionsText.split("\n").map((o) => o.trim()).filter(Boolean);
      const payload = {
        question_text: questionForm.question_text,
        question_type: questionForm.question_type,
        options: options.length ? options : null,
        correct_answer: questionForm.correct_answer,
        explanation: questionForm.explanation || null,
        points: Number(questionForm.points),
        display_order: Number(questionForm.display_order),
      };
      if (editingQuestion) {
        await apiFetch(`/api/v1/questions/${editingQuestion.id}`, { method: "PUT", body: JSON.stringify(payload) });
        flash("تم تعديل السؤال ✅");
      } else {
        await apiFetch(`/api/v1/quizzes/${selectedQuizId}/questions`, { method: "POST", body: JSON.stringify(payload) });
        flash("تمت إضافة السؤال ✅");
      }
      setShowQuestionForm(false);
      await selectQuiz(selectedQuizId);
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };
  const deleteQuestion = async (q: QuizQuestionAdmin) => {
    if (!confirm("حذف هذا السؤال؟")) return;
    try {
      await apiFetch(`/api/v1/questions/${q.id}`, { method: "DELETE" });
      flash("تم حذف السؤال 🗑️");
      if (selectedQuizId !== null) await selectQuiz(selectedQuizId);
      await loadAll();
    } catch (e: unknown) { fail(e); }
  };

  // ---------- المستندات (RAG) ----------
  const [docLessonId, setDocLessonId] = useState<string>("");
  const [docs, setDocs] = useState<LessonDocument[]>([]);
  const [showDocTextForm, setShowDocTextForm] = useState(false);
  const [docTitle, setDocTitle] = useState("");
  const [docContent, setDocContent] = useState("");
  const [uploading, setUploading] = useState(false);

  const loadDocs = async (lessonId: string) => {
    if (!lessonId) { setDocs([]); return; }
    try {
      const list = await apiFetch<LessonDocument[]>(`/api/v1/lessons/${lessonId}/documents`, { cache: "no-store" });
      setDocs(list);
    } catch (e: unknown) { fail(e); }
  };

  const saveTextDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docLessonId) return;
    try {
      await apiFetch("/api/v1/documents/text", {
        method: "POST",
        body: JSON.stringify({ lesson_id: Number(docLessonId), title: docTitle, content: docContent }),
      });
      flash("تمت إضافة المستند وفهرسته ✅");
      setShowDocTextForm(false);
      setDocTitle("");
      setDocContent("");
      await loadDocs(docLessonId);
    } catch (e: unknown) { fail(e); }
  };

  const uploadDocFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !docLessonId) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("lesson_id", docLessonId);
      form.append("title", file.name);
      form.append("file", file);
      const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token") ?? ""}` },
        body: form,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((data as { detail?: string }).detail || `خطأ ${res.status}`);
      flash(`تم رفع وفهرسة الملف ✅ (${(data as { chunks_count?: number }).chunks_count ?? "?"} مقاطع)`);
      await loadDocs(docLessonId);
    } catch (e: unknown) { fail(e); } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const reprocessDoc = async (d: LessonDocument) => {
    try {
      await apiFetch(`/api/v1/documents/${d.id}/process`, { method: "POST" });
      flash("تمت إعادة الفهرسة ✅");
      await loadDocs(docLessonId);
    } catch (e: unknown) { fail(e); }
  };

  const deleteDoc = async (d: LessonDocument) => {
    if (!confirm(`حذف المستند "${d.title}" مع مقاطعه؟`)) return;
    try {
      await apiFetch(`/api/v1/documents/${d.id}`, { method: "DELETE" });
      flash("تم حذف المستند 🗑️");
      await loadDocs(docLessonId);
    } catch (e: unknown) { fail(e); }
  };

  const visibleLessons = lessons.filter(    (l) => filterSubject === "all" || l.subject_id === Number(filterSubject)
  );

  if (checking) return <div className="min-h-screen flex items-center justify-center text-slate-500">جاري التحقق من الصلاحيات...</div>;

  const inputCls =
    "w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white";

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900 text-white px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full rounded-b-3xl">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🛡️</span>
          <span className="font-bold text-lg">لوحة الإدارة</span>
        </div>
        <Link href="/dashboard" className="text-sm font-semibold text-slate-300 hover:text-white">← لوحة الطالب</Link>
      </header>

      <main className="max-w-7xl mx-auto w-full p-6">
        {error && <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center">{error}</div>}
        {okMsg && <div className="mb-4 p-3 text-sm text-emerald-700 bg-emerald-50 rounded-xl border border-emerald-100 text-center">{okMsg}</div>}

        {/* التبويبات */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setTab("subjects")}
            className={`px-6 py-2.5 rounded-xl font-bold text-sm transition ${tab === "subjects" ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "bg-white text-slate-600 border border-slate-200"}`}
          >
            📚 إدارة المواد ({subjects.length})
          </button>
          <button
            onClick={() => setTab("lessons")}
            className={`px-6 py-2.5 rounded-xl font-bold text-sm transition ${tab === "lessons" ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "bg-white text-slate-600 border border-slate-200"}`}
          >
            📝 إدارة الدروس ({lessons.length})
          </button>
          <button
            onClick={() => setTab("quizzes")}
            className={`px-6 py-2.5 rounded-xl font-bold text-sm transition ${tab === "quizzes" ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "bg-white text-slate-600 border border-slate-200"}`}
          >
            🧠 إدارة الاختبارات ({quizzes.length})
          </button>
          <button
            onClick={() => setTab("documents")}
            className={`px-6 py-2.5 rounded-xl font-bold text-sm transition ${tab === "documents" ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "bg-white text-slate-600 border border-slate-200"}`}
          >
            📄 مستندات RAG
          </button>
        </div>

        {/* ===== نظرة عامة (بيانات حقيقية) ===== */}
        {overview && (
          <div className="mb-6 bg-white p-5 rounded-3xl border border-slate-100 shadow-sm">
            <h2 className="font-bold text-slate-800 mb-3">📊 نظرة عامة</h2>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 text-center">
              {[
                { label: "المواد", value: overview.totals.subjects },
                { label: "الدروس", value: overview.totals.lessons },
                { label: "الاختبارات", value: overview.totals.quizzes },
                { label: "الأسئلة", value: overview.totals.questions },
                { label: "المستخدمون", value: overview.totals.users },
                { label: "محاولات مكتملة", value: overview.totals.completed_attempts },
              ].map((s) => (
                <div key={s.label} className="p-3 bg-slate-50 rounded-2xl border border-slate-100">
                  <div className="text-2xl font-extrabold text-slate-800">{s.value}</div>
                  <div className="text-[11px] text-slate-500 font-semibold">{s.label}</div>
                </div>
              ))}
            </div>
            {overview.lessons.length > 0 && (
              <div className="mt-4 space-y-1.5">
                {overview.lessons.map((l) => (
                  <div key={l.lesson_id} className="flex flex-wrap items-center justify-between gap-2 text-sm px-3 py-2 bg-slate-50/60 rounded-xl">
                    <span className="font-semibold text-slate-700">{l.title}</span>
                    <span className="text-xs text-slate-500">
                      محاولات: {l.attempts} • المتوسط: {l.avg_percentage === null ? "—" : `${l.avg_percentage}%`} • أخطاء مفتوحة: {l.open_mistakes}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ===== المواد ===== */}
        {tab === "subjects" && (
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-slate-800">المواد الدراسية</h2>
              <button onClick={openNewSubject} className="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 shadow-md shadow-blue-200">
                + مادة جديدة
              </button>
            </div>

            {showSubjectForm && (
              <form onSubmit={guarded(saveSubject)} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm mb-6 space-y-4">
                <h3 className="font-bold text-slate-800">{editingSubject ? "تعديل مادة" : "مادة جديدة"}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <input required placeholder="اسم المادة *" value={subjectForm.name} onChange={(e) => setSubjectForm({ ...subjectForm, name: e.target.value })} className={inputCls} />
                  <input placeholder="أيقونة (مثال: 📐)" value={subjectForm.icon} onChange={(e) => setSubjectForm({ ...subjectForm, icon: e.target.value })} className={inputCls} />
                </div>
                <textarea placeholder="الوصف" value={subjectForm.description} onChange={(e) => setSubjectForm({ ...subjectForm, description: e.target.value })} className={inputCls} rows={2} />
                <input placeholder="رابط صورة (اختياري)" value={subjectForm.image_url} onChange={(e) => setSubjectForm({ ...subjectForm, image_url: e.target.value })} className={inputCls} dir="ltr" />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    الترتيب:
                    <input type="number" value={subjectForm.display_order} onChange={(e) => setSubjectForm({ ...subjectForm, display_order: Number(e.target.value) })} className={inputCls} />
                  </label>
                  <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <input type="checkbox" checked={subjectForm.is_active} onChange={(e) => setSubjectForm({ ...subjectForm, is_active: e.target.checked })} className="w-5 h-5 accent-blue-600" />
                    مفعّلة (ظاهرة للطلاب)
                  </label>
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={saving} className="px-6 py-2.5 font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-50">{saving ? "جاري الحفظ..." : "حفظ"}</button>
                  <button type="button" onClick={() => setShowSubjectForm(false)} className="px-6 py-2.5 font-semibold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200">إلغاء</button>
                </div>
              </form>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {subjects.map((s) => (
                <div key={s.id} className={`bg-white p-5 rounded-3xl border shadow-sm ${s.is_active ? "border-slate-100" : "border-amber-200 bg-amber-50/40"}`}>
                  <div className="flex justify-between items-start">
                    <div className="text-3xl">{s.icon || "📖"}</div>
                    <span className={`text-[11px] font-bold px-2 py-1 rounded-lg ${s.is_active ? "bg-emerald-50 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                      {s.is_active ? "مفعّلة" : "معطّلة"}
                    </span>
                  </div>
                  <h3 className="mt-2 font-bold text-slate-900">{s.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">ترتيب: {s.display_order} • دروس: {s.lessons_count}</p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold">
                    <button onClick={() => openEditSubject(s)} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">تعديل</button>
                    <button onClick={() => toggleSubjectActive(s)} className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200">
                      {s.is_active ? "تعطيل" : "تفعيل"}
                    </button>
                    <button onClick={() => deleteSubject(s)} className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100">حذف</button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ===== الدروس ===== */}
        {tab === "lessons" && (
          <section>
            <div className="flex flex-wrap justify-between items-center gap-3 mb-4">
              <h2 className="text-xl font-bold text-slate-800">الدروس</h2>
              <div className="flex gap-2">
                <select value={filterSubject} onChange={(e) => setFilterSubject(e.target.value)} className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm">
                  <option value="all">كل المواد</option>
                  {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
                <button onClick={openNewLesson} className="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 shadow-md shadow-blue-200">
                  + درس جديد
                </button>
              </div>
            </div>

            {showLessonForm && (
              <form onSubmit={guarded(saveLesson)} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm mb-6 space-y-4">
                <h3 className="font-bold text-slate-800">{editingLesson ? "تعديل درس" : "درس جديد"}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <label className="text-sm text-slate-700">المادة:
                    <select value={lessonForm.subject_id} onChange={(e) => setLessonForm({ ...lessonForm, subject_id: Number(e.target.value) })} className={inputCls + " mt-1"}>
                      {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>
                  </label>
                  <label className="text-sm text-slate-700">عنوان الدرس *:
                    <input required value={lessonForm.title} onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })} className={inputCls + " mt-1"} />
                  </label>
                </div>
                <input placeholder="وصف مختصر" value={lessonForm.description} onChange={(e) => setLessonForm({ ...lessonForm, description: e.target.value })} className={inputCls} />
                <textarea placeholder="محتوى الدرس..." value={lessonForm.content} onChange={(e) => setLessonForm({ ...lessonForm, content: e.target.value })} className={inputCls} rows={5} />
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <label className="text-sm text-slate-700">الترتيب:
                    <input type="number" value={lessonForm.display_order} onChange={(e) => setLessonForm({ ...lessonForm, display_order: Number(e.target.value) })} className={inputCls + " mt-1"} />
                  </label>
                  <label className="text-sm text-slate-700">موعد النشر (اختياري):
                    <input type="datetime-local" value={lessonForm.scheduled_at} onChange={(e) => setLessonForm({ ...lessonForm, scheduled_at: e.target.value })} className={inputCls + " mt-1"} />
                  </label>
                  <label className="flex items-end gap-2 text-sm font-semibold text-slate-700 pb-2">
                    <input type="checkbox" checked={lessonForm.is_published} onChange={(e) => setLessonForm({ ...lessonForm, is_published: e.target.checked })} className="w-5 h-5 accent-blue-600" />
                    منشور
                  </label>
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={saving} className="px-6 py-2.5 font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-50">{saving ? "جاري الحفظ..." : "حفظ"}</button>
                  <button type="button" onClick={() => setShowLessonForm(false)} className="px-6 py-2.5 font-semibold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200">إلغاء</button>
                </div>
              </form>
            )}

            <div className="space-y-3">
              {visibleLessons.map((l) => (
                <div key={l.id} className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex flex-wrap items-center gap-3">
                  <span className={`text-[11px] font-bold px-2 py-1 rounded-lg ${l.is_published ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                    {l.is_published ? "منشور" : "مسودة"}
                  </span>
                  <div className="flex-1 min-w-40">
                    <h3 className="font-bold text-slate-800">{l.title}</h3>
                    <p className="text-xs text-slate-500">{l.subject_name} • ترتيب: {l.display_order}{l.scheduled_at ? ` • 🕒 ${l.scheduled_at.slice(0, 16).replace("T", " ")}` : ""}</p>
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs font-semibold">
                    <button onClick={() => openEditLesson(l)} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">تعديل</button>
                    <button onClick={() => togglePublish(l)} className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200">
                      {l.is_published ? "إخفاء" : "نشر"}
                    </button>
                    <button onClick={() => deleteLesson(l)} className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100">حذف</button>
                  </div>
                </div>
              ))}
              {visibleLessons.length === 0 && (
                <div className="text-center py-12 text-slate-400 bg-white rounded-3xl border border-slate-100">لا توجد دروس هنا بعد</div>
              )}
            </div>
          </section>
        )}

        {/* ===== الاختبارات ===== */}
        {tab === "quizzes" && (
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-slate-800">الاختبارات</h2>
              <button onClick={openNewQuiz} className="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 shadow-md shadow-blue-200">
                + اختبار جديد
              </button>
            </div>

            {showQuizForm && (
              <form onSubmit={guarded(saveQuiz)} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm mb-6 space-y-4">
                <h3 className="font-bold text-slate-800">{editingQuiz ? "تعديل اختبار" : "اختبار جديد"}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <label className="text-sm text-slate-700">الدرس:
                    <select value={quizForm.lesson_id} onChange={(e) => setQuizForm({ ...quizForm, lesson_id: Number(e.target.value) })} className={inputCls + " mt-1"}>
                      {lessons.map((l) => <option key={l.id} value={l.id}>{l.subject_name} — {l.title}</option>)}
                    </select>
                  </label>
                  <label className="text-sm text-slate-700">عنوان الاختبار *:
                    <input required value={quizForm.title} onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })} className={inputCls + " mt-1"} />
                  </label>
                </div>
                <input placeholder="وصف الاختبار (اختياري)" value={quizForm.description} onChange={(e) => setQuizForm({ ...quizForm, description: e.target.value })} className={inputCls} />
                <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <input type="checkbox" checked={quizForm.is_active} onChange={(e) => setQuizForm({ ...quizForm, is_active: e.target.checked })} className="w-5 h-5 accent-blue-600" />
                  مفعّل (ظاهر للطلاب)
                </label>
                <div className="flex gap-2">
                  <button type="submit" disabled={saving} className="px-6 py-2.5 font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-50">{saving ? "جاري الحفظ..." : "حفظ"}</button>
                  <button type="button" onClick={() => setShowQuizForm(false)} className="px-6 py-2.5 font-semibold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200">إلغاء</button>
                </div>
              </form>
            )}

            <div className="space-y-3 mb-6">
              {quizzes.map((q) => (
                <div key={q.id} className={`bg-white p-4 rounded-2xl border shadow-sm ${selectedQuizId === q.id ? "border-blue-400 ring-2 ring-blue-100" : "border-slate-100"}`}>
                  <div className="flex flex-wrap items-center gap-3">
                    <span className={`text-[11px] font-bold px-2 py-1 rounded-lg ${q.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                      {q.is_active ? "مفعّل" : "معطّل"}
                    </span>
                    <div className="flex-1 min-w-40">
                      <h3 className="font-bold text-slate-800">{q.title}</h3>
                      <p className="text-xs text-slate-500">{q.lesson_title} • أسئلة: {q.questions_count}</p>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs font-semibold">
                      <button onClick={() => selectQuiz(q.id)} className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100">إدارة الأسئلة</button>
                      <button onClick={() => openEditQuiz(q)} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">تعديل</button>
                      <button onClick={() => toggleQuizActive(q)} className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200">{q.is_active ? "تعطيل" : "تفعيل"}</button>
                      <button onClick={() => deleteQuiz(q)} className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100">حذف</button>
                    </div>
                  </div>
                </div>
              ))}
              {quizzes.length === 0 && (
                <div className="text-center py-12 text-slate-400 bg-white rounded-3xl border border-slate-100">لا توجد اختبارات بعد</div>
              )}
            </div>

            {selectedQuizId !== null && (
              <div className="bg-slate-100/70 p-5 rounded-3xl border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-slate-800">أسئلة الاختبار المحدد ({quizQuestions.length})</h3>
                  <button onClick={openNewQuestion} className="px-4 py-2 text-sm font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700">+ سؤال جديد</button>
                </div>

                {showQuestionForm && (
                  <form onSubmit={guarded(saveQuestion)} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm mb-4 space-y-3">
                    <h4 className="font-bold text-sm text-slate-800">{editingQuestion ? "تعديل سؤال" : "سؤال جديد"}</h4>
                    <textarea required placeholder="نص السؤال *" value={questionForm.question_text} onChange={(e) => setQuestionForm({ ...questionForm, question_text: e.target.value })} className={inputCls} rows={2} />
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <label className="text-xs text-slate-700">النوع:
                        <select value={questionForm.question_type} onChange={(e) => setQuestionForm({ ...questionForm, question_type: e.target.value })} className={inputCls + " mt-1"}>
                          <option value="multiple_choice">اختيار من متعدد</option>
                          <option value="true_false">صح / خطأ</option>
                          <option value="short_answer">إجابة قصيرة</option>
                        </select>
                      </label>
                      <label className="text-xs text-slate-700">النقاط:
                        <input type="number" step="0.5" min="0" value={questionForm.points} onChange={(e) => setQuestionForm({ ...questionForm, points: Number(e.target.value) })} className={inputCls + " mt-1"} />
                      </label>
                      <label className="text-xs text-slate-700">الترتيب:
                        <input type="number" value={questionForm.display_order} onChange={(e) => setQuestionForm({ ...questionForm, display_order: Number(e.target.value) })} className={inputCls + " mt-1"} />
                      </label>
                    </div>
                    <label className="text-xs text-slate-700 block">الاختيارات (سطر لكل اختيار — للاختيار من متعدد):
                      <textarea placeholder={"الخيار الأول\nالخيار الثاني\nالخيار الثالث"} value={questionForm.optionsText} onChange={(e) => setQuestionForm({ ...questionForm, optionsText: e.target.value })} className={inputCls + " mt-1"} rows={3} />
                    </label>
                    <label className="text-xs text-slate-700 block">الإجابة الصحيحة *:
                      <input required value={questionForm.correct_answer} onChange={(e) => setQuestionForm({ ...questionForm, correct_answer: e.target.value })} className={inputCls + " mt-1"} />
                    </label>
                    <label className="text-xs text-slate-700 block">شرح الإجابة (يظهر للطالب بعد الإرسال):
                      <textarea value={questionForm.explanation} onChange={(e) => setQuestionForm({ ...questionForm, explanation: e.target.value })} className={inputCls + " mt-1"} rows={2} />
                    </label>
                    <div className="flex gap-2">
                      <button type="submit" disabled={saving} className="px-6 py-2.5 font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 disabled:opacity-50">{saving ? "جاري الحفظ..." : "حفظ السؤال"}</button>
                      <button type="button" onClick={() => setShowQuestionForm(false)} className="px-6 py-2.5 font-semibold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200">إلغاء</button>
                    </div>
                  </form>
                )}

                <div className="space-y-2">
                  {quizQuestions.map((q, idx) => (
                    <div key={q.id} className="bg-white p-4 rounded-2xl border border-slate-200">
                      <div className="flex flex-wrap items-start gap-2">
                        <span className="text-xs font-bold bg-slate-100 text-slate-600 px-2 py-1 rounded-lg">#{idx + 1}</span>
                        <div className="flex-1 min-w-40">
                          <p className="font-bold text-sm text-slate-800">{q.question_text}</p>
                          <p className="text-xs text-slate-500 mt-1">
                            النوع: {q.question_type} • النقاط: {q.points} • الترتيب: {q.display_order}
                          </p>
                          <p className="text-xs text-emerald-700 mt-1">✓ الصحيحة: {q.correct_answer}</p>
                          {(q.options ?? []).length > 0 && (
                            <p className="text-xs text-slate-400 mt-1">الاختيارات: {(q.options ?? []).join(" | ")}</p>
                          )}
                        </div>
                        <div className="flex gap-2 text-xs font-semibold">
                          <button onClick={() => openEditQuestion(q)} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">تعديل</button>
                          <button onClick={() => deleteQuestion(q)} className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100">حذف</button>
                        </div>
                      </div>
                    </div>
                  ))}
                  {quizQuestions.length === 0 && (
                    <div className="text-center py-8 text-slate-400 text-sm">لا توجد أسئلة — أضف أول سؤال</div>
                  )}
                </div>
              </div>
            )}
          </section>
        )}

        {/* ===== مستندات RAG ===== */}
        {tab === "documents" && (
          <section>
            <div className="flex flex-wrap justify-between items-center gap-3 mb-4">
              <h2 className="text-xl font-bold text-slate-800">مستندات RAG للدرس</h2>
              <select
                value={docLessonId}
                onChange={(e) => { setDocLessonId(e.target.value); loadDocs(e.target.value); }}
                className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm"
              >
                <option value="">— اختر الدرس —</option>
                {lessons.map((l) => <option key={l.id} value={l.id}>{l.subject_name} — {l.title}</option>)}
              </select>
            </div>

            {!docLessonId && (
              <div className="text-center py-12 text-slate-400 bg-white rounded-3xl border border-slate-100">اختر درسًا لعرض مستنداته</div>
            )}

            {docLessonId && (
              <>
                <div className="flex flex-wrap gap-2 mb-4">
                  <button onClick={() => setShowDocTextForm((v) => !v)} className="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 shadow-md shadow-blue-200">
                    + مستند نصي
                  </button>
                  <label className="px-5 py-2.5 text-sm font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 shadow-md shadow-emerald-200 cursor-pointer">
                    {uploading ? "جاري الرفع..." : "📤 رفع ملف (TXT/PDF)"}
                    <input type="file" accept=".txt,.pdf" onChange={uploadDocFile} className="hidden" disabled={uploading} />
                  </label>
                </div>

                {showDocTextForm && (
                  <form onSubmit={guarded(saveTextDoc)} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm mb-4 space-y-3">
                    <input required placeholder="عنوان المستند *" value={docTitle} onChange={(e) => setDocTitle(e.target.value)} className={inputCls} />
                    <textarea required placeholder="الصق محتوى المستند هنا..." value={docContent} onChange={(e) => setDocContent(e.target.value)} className={inputCls} rows={6} />
                    <div className="flex gap-2">
                      <button type="submit" disabled={saving} className="px-6 py-2.5 font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-50">{saving ? "جاري الحفظ..." : "حفظ وفهرسة"}</button>
                      <button type="button" onClick={() => setShowDocTextForm(false)} className="px-6 py-2.5 font-semibold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200">إلغاء</button>
                    </div>
                  </form>
                )}

                <div className="space-y-3">
                  {docs.map((d) => (
                    <div key={d.id} className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex flex-wrap items-center gap-3">
                      <span className={`text-[11px] font-bold px-2 py-1 rounded-lg ${
                        d.status === "ready" ? "bg-emerald-50 text-emerald-700" :
                        d.status === "failed" ? "bg-red-50 text-red-600" :
                        d.status === "processing" ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-500"
                      }`}>
                        {d.status === "ready" ? "جاهز" : d.status === "failed" ? "فشل" : d.status === "processing" ? "يُعالج" : "بانتظار"}
                      </span>
                      <div className="flex-1 min-w-40">
                        <h3 className="font-bold text-slate-800">{d.title}</h3>
                        <p className="text-xs text-slate-500">النوع: {d.source_type}{d.source_path ? ` • ${d.source_path}` : ""} • مقاطع: {d.chunks_count}</p>
                      </div>
                      <div className="flex flex-wrap gap-2 text-xs font-semibold">
                        <button onClick={() => reprocessDoc(d)} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">إعادة فهرسة</button>
                        <button onClick={() => deleteDoc(d)} className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100">حذف</button>
                      </div>
                    </div>
                  ))}
                  {docs.length === 0 && (
                    <div className="text-center py-12 text-slate-400 bg-white rounded-3xl border border-slate-100">لا توجد مستندات — أضف نصًا أو ارفع ملفًا</div>
                  )}
                </div>
              </>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
