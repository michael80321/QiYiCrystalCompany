"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

type QueueRow = { [key: string]: string | number; _row: number };

const PLATFORM_ICONS: Record<string, string> = {
  通用: "📱", IG: "📸", FB: "👥", Threads: "🧵", 蝦皮: "🛍️",
};

const TYPE_COLORS: Record<string, string> = {
  貼文: "bg-blue-900 text-blue-300",
  商品圖片: "bg-purple-900 text-purple-300",
  能量文案: "bg-amber-900 text-amber-300",
  影片腳本: "bg-pink-900 text-pink-300",
};

export default function ReviewCard({ item }: { item: QueueRow }) {
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);
  const [showReject, setShowReject] = useState(false);
  const [note, setNote] = useState("");
  const [expanded, setExpanded] = useState(false);
  const router = useRouter();

  const content = String(item["內容摘要"] || "");
  const isLong = content.length > 100;

  async function approve() {
    setLoading("approve");
    await fetch("/api/sheets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "update", tab: "審核隊列", row: item._row, col: 7, value: "核准" }),
    });
    setLoading(null);
    router.refresh();
  }

  async function reject() {
    if (!showReject) { setShowReject(true); return; }
    setLoading("reject");
    await fetch("/api/sheets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "update", tab: "審核隊列", row: item._row, col: 7, value: "退回" }),
    });
    if (note.trim()) {
      await fetch("/api/sheets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "update", tab: "審核隊列", row: item._row, col: 8, value: note }),
      });
    }
    setLoading(null);
    router.refresh();
  }

  const typeColor = TYPE_COLORS[String(item["類型"])] || "bg-gray-800 text-gray-400";
  const platformIcon = PLATFORM_ICONS[String(item["平台"])] || "📱";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center gap-2 px-5 pt-4 pb-3 flex-wrap">
        <span className={`text-xs px-2 py-0.5 rounded font-medium ${typeColor}`}>
          {item["類型"]}
        </span>
        <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">
          {platformIcon} {item["平台"]}
        </span>
        <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">
          {item["語言"]}
        </span>
        <span className="text-xs text-gray-600 ml-auto">{item["預定發布時間"]}</span>
      </div>

      {/* Content */}
      <div className="px-5 pb-4">
        <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
          {isLong && !expanded ? content.slice(0, 100) + "…" : content}
        </p>
        {isLong && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-purple-400 mt-1 hover:text-purple-300"
          >
            {expanded ? "收起" : "展開全文"}
          </button>
        )}
        {item["老闆批注"] && (
          <p className="text-yellow-400 text-xs mt-2 bg-yellow-900/20 rounded px-2 py-1">
            💬 {item["老闆批注"]}
          </p>
        )}
      </div>

      {/* Reject note input */}
      {showReject && (
        <div className="px-5 pb-3">
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="退回原因（選填）"
            rows={2}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 placeholder-gray-600 resize-none focus:outline-none focus:border-red-500"
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex border-t border-gray-800">
        <button
          onClick={approve}
          disabled={loading !== null}
          className="flex-1 py-3.5 text-sm font-semibold text-green-400 hover:bg-green-900/30 disabled:opacity-40 transition-colors active:scale-95"
        >
          {loading === "approve" ? "處理中…" : "✅ 核准發布"}
        </button>
        <div className="w-px bg-gray-800" />
        <button
          onClick={reject}
          disabled={loading !== null}
          className="flex-1 py-3.5 text-sm font-semibold text-red-400 hover:bg-red-900/20 disabled:opacity-40 transition-colors active:scale-95"
        >
          {loading === "reject" ? "處理中…" : showReject ? "確認退回" : "❌ 退回"}
        </button>
        {showReject && (
          <>
            <div className="w-px bg-gray-800" />
            <button
              onClick={() => { setShowReject(false); setNote(""); }}
              className="px-4 py-3.5 text-sm text-gray-500 hover:text-gray-300 transition-colors"
            >
              取消
            </button>
          </>
        )}
      </div>
    </div>
  );
}
