"use client";
import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

export default function ImageAnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [extractedText, setExtractedText] = useState("");
  const [aiSolution, setAiSolution] = useState<{ answer: string; grounded: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    setFile(e.target.files?.[0] || null);
    setExtractedText("");
    setAiSolution(null);
    setError("");
    setMessage("");
  }

  async function handleAnalyze() {
    if (!file) { setError("اختر صورة أولاً"); return; }
    setLoading(true); setError(""); setExtractedText(""); setAiSolution(null); setMessage("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch<{
        extracted_text: string | null;
        ai_solution: { answer: string; grounded: boolean } | null;
        message: string;
        filename: string;
        ocr_available: boolean;
      }>("/api/v1/image-analysis", { method: "POST", body: form });
      if (res.extracted_text) setExtractedText(res.extracted_text);
      if (res.ai_solution) setAiSolution(res.ai_solution);
      setMessage(res.message);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "فشل التحليل");
    } finally { setLoading(false); }
  }

  function formatBold(text: string): string {
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
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
          <input type="file" accept="image/*" onChange={handleFile}
                 className="block w-full text-sm text-gray-400 mb-4" />

          <button onClick={handleAnalyze} disabled={loading || !file}
                  className="w-full py-4 font-bold text-white bg-blue-600 rounded-2xl hover:bg-blue-700 disabled:opacity-50 transition text-lg">
            {loading ? "جاري التحليل... 🤖" : "حلّل الصورة 📸"}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 text-sm text-red-400 bg-red-900/50 rounded-xl border border-red-700">{error}</div>
        )}
        {message && !aiSolution && (
          <div className="mt-4 p-3 text-sm text-amber-300 bg-amber-900/50 rounded-xl border border-amber-700">{message}</div>
        )}

        {extractedText && (
          <div className="mt-4 bg-gray-900 p-6 rounded-3xl border border-gray-700 shadow-lg">
            <h3 className="font-bold text-base text-gray-200 mb-3">النص المستخرج:</h3>
            <div className="whitespace-pre-wrap leading-relaxed text-gray-100 font-medium"
                 dangerouslySetInnerHTML={{ __html: formatBold(extractedText) }} />
          </div>
        )}

        {aiSolution && (
          <div className="mt-4 bg-emerald-900/50 p-6 rounded-3xl border border-emerald-700 shadow-lg">
            <h3 className="font-bold text-base text-emerald-300 mb-3">
              {aiSolution.grounded ? "✅ إجابة مستندة إلى محتوى الدرس" : "💡 شرح عام — ليس من محتوى الدرس"}
            </h3>
            <div className="whitespace-pre-wrap leading-relaxed text-gray-100 font-medium"
                 dangerouslySetInnerHTML={{ __html: formatBold(aiSolution.answer) }} />
          </div>
        )}
      </main>
    </div>
  );
}
