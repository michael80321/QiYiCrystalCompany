"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ReviewActions({ row }: { row: number }) {
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);
  const router = useRouter();

  async function act(action: "approve" | "reject") {
    setLoading(action);
    const value = action === "approve" ? "核准" : "退回";
    await fetch("/api/sheets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "update", tab: "審核隊列", row, col: 7, value }),
    });
    setLoading(null);
    router.refresh();
  }

  return (
    <div className="flex gap-2 shrink-0">
      <button
        onClick={() => act("approve")}
        disabled={loading !== null}
        className="text-sm bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg"
      >
        {loading === "approve" ? "..." : "核准"}
      </button>
      <button
        onClick={() => act("reject")}
        disabled={loading !== null}
        className="text-sm bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg"
      >
        {loading === "reject" ? "..." : "退回"}
      </button>
    </div>
  );
}
