"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, Lesson, Progress, ReviewPlan, ReviewItem } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [completedCount, setCompletedCount] = useState(0);
  const [totalLessons, setTotalLessons] = useState(0);
  const [planItems, setPlanItems] = useState<ReviewItem[]>([]);

  useEffect(() => {
    const storedName = localStorage.getItem("user_name");
    const token = localStorage.getItem("token");

    if (!token) {
      router.push("/login");
    } else {
      setName(storedName || "الطالب");
      setIsAdmin(localStorage.getItem("user_role") === "admin");
      Promise.all([
        apiFetch<Lesson[]>("/api/v1/lessons", { cache: "no-store" }).catch(() => [] as Lesson[]),
        apiFetch<Progress[]>("/api/v1/progress/me", { cache: "no-store" }).catch(() => [] as Progress[]),
        apiFetch<ReviewPlan>("/api/v1/learning/review-plan", { cache: "no-store" }).catch(() => null),
      ]).then(([lessons, progress, plan]) => {
        const doneIds = new Set(progress.filter((p) => p.is_completed).map((p) => p.lesson_id));
        setTotalLessons(lessons.length);
        setCompletedCount(lessons.filter((l) => doneIds.has(l.id)).length);
        if (plan) setPlanItems(plan.items.slice(0, 3));
      });
    }
  }, [router]);

  const remaining = Math.max(totalLessons - completedCount, 0);
  const overallPct = totalLessons > 0 ? Math.round((completedCount / totalLessons) * 100) : 0;

  const handleLogout = () => {
    localStorage.clear();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-lg text-white">مراجعي الذكي</span>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && (
            <Link
              href="/admin"
              className="text-sm font-semibold text-white bg-slate-900 px-3 py-1.5 rounded-lg hover:bg-slate-700 transition"
            >
              🛡️ لوحة الإدارة
            </Link>
          )}
             <Link
               href="/subjects"
               className="text-sm font-semibold text-blue-400 hover:bg-blue-900/30 px-3 py-1.5 rounded-lg transition"
             >
               📚 موادي
             </Link>
             <button
               onClick={handleLogout}
               className="text-sm font-semibold text-red-400 hover:bg-red-900/30 px-3 py-1.5 rounded-lg transition"
             >
               خروج
             </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto w-full p-6 flex-1 space-y-8">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl p-8 text-white shadow-xl shadow-blue-200/50">
          <h1 className="text-3xl font-extrabold">مرحباً بك 👋 {name}</h1>
          <p className="mt-2 text-blue-100 text-lg">
            منصتك الذكية لفهم دروسك، مراجعتها واختبار مستواك طوال العام.
          </p>
        </div>

        {/* Action Cards */}
        <div>
           <h2 className="text-xl font-bold text-white mb-4">ماذا تحتاج اليوم؟</h2>
           <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
             {[
               { title: "دروسي", icon: "📚", color: "bg-gray-800 text-blue-400", href: "/subjects" },
               { title: "اختبرني", icon: "🧠", color: "bg-gray-800 text-purple-400", href: "/subjects" },
               { title: "حلل صورة", icon: "📸", color: "bg-gray-800 text-amber-400", href: "/image-analysis" },
               { title: "اسأل مساعدي", icon: "🤖", color: "bg-gray-800 text-emerald-400", href: "/assistant" },
               { title: "تقدمي", icon: "📊", color: "bg-gray-800 text-rose-400", href: "/progress" },
               { title: "خطة اليوم", icon: "🎯", color: "bg-gray-800 text-indigo-400", href: "/progress" },
             ].map((card, idx) => {
               const inner = (
                 <>
                   <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${card.color}`}>
                     {card.icon}
                   </div>
                   <span className="font-bold text-sm text-gray-200">{card.title}</span>
                 </>
               );
               const cls = "bg-gray-800 p-5 rounded-2xl border border-gray-700 shadow-sm hover:shadow-md transition text-center flex flex-col items-center justify-center gap-2";
               if ("href" in card && card.href) {
                 return <Link key={idx} href={card.href as string} className={cls + " cursor-pointer"}>{inner}</Link>;
               }
               return <div key={idx} className={cls + " opacity-80"}>{inner}</div>;
             })}
           </div>
         </div>

         {/* خطة اليوم 🎯 */}
         <div className="bg-gray-900 p-6 rounded-3xl border border-gray-700 shadow-sm">
           <h3 className="font-bold text-lg text-white mb-4 flex items-center gap-2">
             🎯 خطة اليوم
           </h3>
           {planItems.length === 0 ? (
             <p className="text-gray-400 text-sm text-center py-4 leading-relaxed">
               لا توجد توصيات كافية بعد. أكمل بعض الدروس والاختبارات حتى نتمكن من بناء خطة مناسبة لك.
             </p>
           ) : (
             <div className="space-y-3">
               {planItems.map((item) => (
                 <Link
                   key={item.lesson_id}
                   href={item.kind === "review_lesson" || !item.quiz_id ? `/lessons/${item.lesson_id}` : `/quizzes/${item.quiz_id}`}
                   className="flex items-center gap-3 px-4 py-3 bg-gray-800 rounded-2xl border border-gray-700 hover:shadow-md transition"
                 >
                   <span className="text-2xl">
                     {item.kind === "fix_mistake" ? "🔁" : item.kind === "retry_quiz" ? "🧠" : "📚"}
                   </span>
                   <div className="flex-1">
                     <p className="font-bold text-sm text-white">{item.lesson_title}</p>
                     <p className="text-xs text-gray-400">{item.reason}</p>
                   </div>
                   <span className="text-xs font-extrabold text-blue-300 bg-blue-900/30 px-2 py-1 rounded-lg">
                     {item.priority}
                   </span>
                 </Link>
               ))}
               <Link href="/progress" className="block text-center text-sm font-semibold text-blue-400 hover:underline pt-1">
                 عرض ملف التقدم الكامل ←
               </Link>
             </div>
           )}
         </div>

         {/* Real Progress Summary */}
         <div className="bg-gray-900 p-6 rounded-3xl border border-gray-700 shadow-sm">
           <h3 className="font-bold text-lg text-white mb-4 flex items-center gap-2">
             📊 تقدمي العام
           </h3>
           <div className="flex items-center gap-4 mb-5">
             <div className="flex-1 h-3 bg-gray-800 rounded-full overflow-hidden">
               <div className="h-full bg-blue-600 rounded-full transition-all" style={{ width: `${overallPct}%` }} />
             </div>
             <span className="font-extrabold text-white">{overallPct}%</span>
           </div>
           <div className="grid grid-cols-2 gap-4 text-center">
             <div className="p-4 bg-emerald-900/30 rounded-2xl border border-emerald-800">
               <div className="text-2xl font-extrabold text-emerald-300">{completedCount}</div>
               <div className="text-xs font-semibold text-emerald-400">دروس مكتملة ✓</div>
             </div>
             <div className="p-4 bg-amber-900/30 rounded-2xl border border-amber-800">
               <div className="text-2xl font-extrabold text-amber-300">{remaining}</div>
               <div className="text-xs font-semibold text-amber-400">دروس متبقية ○</div>
             </div>
           </div>
         </div>
      </main>
    </div>
  );
}
