import type { Metadata } from "next";
import { Cairo } from "next/font/google";
import "./globals.css";

const cairo = Cairo({
  subsets: ["arabic"],
  weight: ["400", "600", "700", "800"]
});

export const metadata: Metadata = {
  title: "مراجعي الذكي | منصة الدراسة والتكويّن الذكية",
  description: "مساعدك الشخصي للتعلم الفعال وفهم الدروس واجتياز الامتحانات بنجاح.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body className={`${cairo.className} bg-slate-50 text-slate-900 min-h-screen antialiased`}>
        {children}
      </body>
    </html>
  );
}
