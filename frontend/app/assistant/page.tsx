import { Suspense } from "react";
import AssistantClient from "./assistant-client";

export default function AssistantPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-slate-500">جاري التحميل...</div>}>
      <AssistantClient />
    </Suspense>
  );
}
