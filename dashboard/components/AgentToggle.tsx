"use client";
import { useState } from "react";

export default function AgentToggle({ name, enabled }: { name: string; enabled: boolean }) {
  const [on, setOn] = useState(enabled);
  const [loading, setLoading] = useState(false);

  async function toggle() {
    setLoading(true);
    const newStatus = on ? "關閉" : "開啟";
    try {
      const records = await fetch("/api/sheets?tab=員工開關").then((r) => r.json());
      const idx = records.findIndex((r: Record<string, string>) => r["員工名稱"] === name);
      if (idx !== -1) {
        await fetch("/api/sheets", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "update", tab: "員工開關", row: idx + 2, col: 3, value: newStatus }),
        });
        setOn(!on);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
        on ? "bg-purple-600" : "bg-gray-700"
      } ${loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
    >
      <span className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${on ? "translate-x-6" : "translate-x-1"}`} />
    </button>
  );
}
