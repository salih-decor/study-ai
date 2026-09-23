import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Navbar */}
      <header className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex justify-between items-center max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="text-xl font-bold text-blue-600">مراجعي الذكي</span>
        </div>
        <div className="flex gap-4">
          <Link href="/login" className="px-4 py-2 text-sm font-semibold text-gray-700 hover:text-blue-600 transition">
            تسجيل الدخول
          </Link>
          <Link href="/register" className="px-5 py-2 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition shadow-md shadow-blue-200">
            إنشاء حساب
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 max-w-4xl mx-auto py-20">
        <span className="px-4 py-1.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 mb-6">
          ✨ منصة ذكية موجهة للطلاب
        </span>
        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 leading-tight">
          دراستك أصبحت أذكى مع <span className="text-blue-600">مراجعي الذكي</span>
        </h1>
        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl leading-relaxed">
          نظام تعليمي يفهم محتوى دروسك، يختبر مستواك، يكتشف أخطاءك المتكررة، ويبني لك خطة مراجعة تناسب قدراتك طوال العام.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
          <Link href="/register" className="px-8 py-4 text-base font-bold text-white bg-blue-600 rounded-2xl hover:bg-blue-700 transition shadow-lg shadow-blue-200 text-center">
            ابدأ المراجعة الآن مجاناً 🚀
          </Link>
          <Link href="/login" className="px-8 py-4 text-base font-bold text-slate-700 bg-white border border-slate-200 rounded-2xl hover:bg-slate-50 transition text-center">
            لدي حساب بالفعل
          </Link>
        </div>
      </main>
    </div>
  );
}
