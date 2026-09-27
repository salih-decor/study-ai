"use client";

import { useState, type ReactNode } from "react";

interface CollapsibleSectionProps {
  title: string;
  children?: ReactNode;
  /** نص الرسالة عندما تكون القائمة فارغة — تُعرض مباشرة بدون زر */
  emptyText?: string;
  defaultOpen?: boolean;
}

/** قسم قابل للطي: مغلق افتراضيًا، زر أخضر إظهار/إخفاء، فتح بانسيابية (CSS grid بدون JS). */
export default function CollapsibleSection({ title, children, emptyText, defaultOpen = false }: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-bold text-lg text-slate-800">{title}</h2>
        {emptyText == null && (
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            className="px-5 py-2 text-sm font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 active:scale-[0.98] transition shrink-0"
          >
            {open ? "إخفاء" : "إظهار"}
          </button>
        )}
      </div>
      {emptyText != null ? (
        <p className="text-slate-400 text-sm text-center py-4">{emptyText}</p>
      ) : (
        <div
          className={`grid transition-all duration-300 ease-in-out ${
            open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
          }`}
        >
          <div className="overflow-hidden min-h-0">
            <div className="pt-4">{children}</div>
          </div>
        </div>
      )}
    </section>
  );
}
