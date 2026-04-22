"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

type AgentRow = { [key: string]: string };

export default function BulkAgentControl({ agents }: { agents: AgentRow[] }) {
  const [loading, setLoading] = useState<"on" | "off" | null>(null);
  const router = useRouter();

  async function bulkToggle(action: "on" | "off") {
    const label = action === "on" ? "開啟" : "關閉";
    if (!confirm(`確定要一鍵${label}全部 ${agents.length} 位員工？`)) return;

    setLoading(action);
    const value = action === "on" ? "開啟" : "關閉";

    // Get current records to find row indices
    const records: AgentRow[] = await fetch("/api/sheets?tab=員工開關").then(r => r.json());

    await Promise.all(agents.map((agent) => {
      const idx = records.findIndex(r => r["員工名稱"] === agent["員工名稱"]);
      if (idx === -1) return Promise.resolve();
      return fetch("/api/sheets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "update", tab: "員工開關", row: idx + 2, col: 3, value }),
      });
    }));

    setLoading(null);
    router.refresh();
  }

  const onCount = agents.filter(a => a["狀態"] === "開啟").length;
  const offCount = agents.length - onCount;

  return (
    <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-xl px-5 py-3">
      <div className="flex-1 text-sm text-gray-400">
        目前 <span className="text-green-400 font-semibold">{onCount}</span> 位開啟 ·{" "}
        <span className="text-gray-500 font-semibold">{offCount}</span> 位關閉
      </div>
      <button
        onClick={() => bulkToggle("off")}
        disabled={loading !== null}
        className="text-sm px-4 py-2 rounded-xl bg-gray-800 hover:bg-red-900/40 text-red-400 hover:text-red-300 disabled:opacity-40 transition-colors font-medium"
      >
        {loading === "off" ? "關閉中…" : "⏹ 全部關閉"}
      </button>
      <button
        onClick={() => bulkToggle("on")}
        disabled={loading !== null}
        className="text-sm px-4 py-2 rounded-xl bg-purple-800/50 hover:bg-purple-700/60 text-purple-300 hover:text-purple-200 disabled:opacity-40 transition-colors font-medium"
      >
        {loading === "on" ? "開啟中…" : "▶ 全部開啟"}
      </button>
    </div>
  );
}
