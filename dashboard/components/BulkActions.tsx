"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

type QueueRow = { [key: string]: string | number; _row: number };

export default function BulkActions({ items }: { items: QueueRow[] }) {
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);
  const [done, setDone] = useState(false);
  const router = useRouter();

  async function bulkAction(action: "approve" | "reject") {
    if (!confirm(action === "approve"
      ? `確定要一鍵核准全部 ${items.length} 件內容？`
      : `確定要一鍵退回全部 ${items.length} 件內容？`
    )) return;

    setLoading(action);
    const value = action === "approve" ? "核准" : "退回";

    await Promise.all(items.map((item) =>
      fetch("/api/sheets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "update",
          tab: "審核隊列",
          row: item._row,
          col: 7,
          value,
        }),
      })
    ));

    setLoading(null);
    setDone(true);
    setTimeout(() => { setDone(false); router.refresh(); }, 800);
  }

  if (items.length === 0) return null;

  return (
    <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-2xl px-5 py-3">
      <span className="text-sm text-gray-400 flex-1">
        批次操作 <span className="text-white font-semibold">{items.length}</span> 件待審內容
      </span>
      <button
        onClick={() => bulkAction("reject")}
        disabled={loading !== null || done}
        className="text-sm px-4 py-2 rounded-xl bg-gray-800 hover:bg-red-900/40 text-red-400 hover:text-red-300 disabled:opacity-40 transition-colors font-medium"
      >
        {loading === "reject" ? "退回中…" : "❌ 全部退回"}
      </button>
      <button
        onClick={() => bulkAction("approve")}
        disabled={loading !== null || done}
        className="text-sm px-4 py-2 rounded-xl bg-green-800/50 hover:bg-green-700/60 text-green-400 hover:text-green-300 disabled:opacity-40 transition-colors font-medium"
      >
        {loading === "approve" ? "核准中…" : done ? "✅ 完成！" : "✅ 全部核准"}
      </button>
    </div>
  );
}
