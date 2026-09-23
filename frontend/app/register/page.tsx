"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: "",
    username: "",
    password: "",
    confirmPassword: "",
    level: "السنة الثالثة ثانوي",
    branch: "علوم تجريبية"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError("كلمتا المرور غير متطابقتين");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: formData.name,
          username: formData.username,
          password: formData.password,
          level: formData.level,
          branch: formData.branch
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "فشل إنشاء الحساب");
      }

      // توجيه المستخدم لصفحة الدخول بعد النجاح
      router.push("/login?registered=success");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "فشل إنشاء الحساب");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-4 py-12 bg-slate-100">
      <div className="w-full max-w-lg p-8 space-y-6 bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100">
        <div className="text-center">
          <Link href="/" className="inline-block text-3xl mb-2">🧠</Link>
          <h1 className="text-2xl font-bold text-slate-900">حساب طالب جديد ✨</h1>
          <p className="mt-1 text-sm text-slate-500">انضم لمنصة مراجعي الذكي وابدأ رحلتك التعليمية</p>
        </div>

        {error && (
          <div className="p-3 text-sm text-red-600 bg-red-50 rounded-xl border border-red-100 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">الاسم الكامل</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                placeholder="سفيان بتير"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">اسم المستخدم</label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                placeholder="sofian_dev"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">المستوى الدراسي</label>
              <select
                value={formData.level}
                onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
              >
                <option value="السنة الثالثة ثانوي">السنة الثالثة ثانوي</option>
                <option value="السنة الثانية ثانوي">السنة الثانية ثانوي</option>
                <option value="السنة الأولى ثانوي">السنة الأولى ثانوي</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">الشعبة</label>
              <select
                value={formData.branch}
                onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
              >
                <option value="علوم تجريبية">علوم تجريبية</option>
                <option value="آداب وفلسفة">آداب وفلسفة</option>
                <option value="رياضيات">رياضيات</option>
                <option value="تقني رياضي">تقني رياضي</option>
                <option value="تسيير واقتصاد">تسيير واقتصاد</option>
                <option value="لغات أجنبية">لغات أجنبية</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">كلمة المرور</label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">تأكيد كلمة المرور</label>
              <input
                type="password"
                required
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-4 font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition shadow-md shadow-blue-200 disabled:opacity-50"
          >
            {loading ? "جاري الإنشاء..." : "إنشاء حساب طالب"}
          </button>
        </form>

        <div className="text-center text-sm text-slate-500 pt-2">
          لديك حساب بالفعل؟{" "}
          <Link href="/login" className="font-semibold text-blue-600 hover:underline">
            تسجيل الدخول
          </Link>
        </div>
      </div>
    </div>
  );
}
