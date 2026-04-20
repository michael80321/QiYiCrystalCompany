"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

type Row = { [key: string]: string; _row: string };

const COLS = ["商品名稱", "水晶種類", "現有庫存", "警戒庫存量", "售價(TWD)", "成本", "供應商"];
const COL_INDEX: Record<string, number> = {
  "商品名稱": 2, "水晶種類": 3, "現有庫存": 4,
  "警戒庫存量": 5, "售價(TWD)": 6, "成本": 7, "供應商": 8,
};

export default function InventoryTable({ rows }: { rows: Row[] }) {
  const [editing, setEditing] = useState<{ row: string; col: string } | null>(null);
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const router = useRouter();

  function startEdit(row: Row, col: string) {
    setEditing({ row: row._row, col });
    setValue(row[col] || "");
  }

  async function save() {
    if (!editing) return;
    setSaving(true);
    await fetch("/api/sheets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "update",
        tab: "庫存表",
        row: Number(editing.row),
        col: COL_INDEX[editing.col],
        value,
      }),
    });
    setSaving(false);
    setEditing(null);
    router.refresh();
  }

  function stockColor(row: Row) {
    const cur = Number(row["現有庫存"] || 0);
    const warn = Number(row["警戒庫存量"] || 0);
    if (cur === 0) return "text-red-400 font-bold";
    if (cur <= warn) return "text-yellow-400 font-semibold";
    return "text-green-400";
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
      {/* Mobile view */}
      <div className="sm:hidden divide-y divide-gray-800">
        {rows.map((row, i) => (
          <div key={i} className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-100">{row["商品名稱"] || "—"}</span>
              <span className={`text-sm ${stockColor(row)}`}>庫存 {row["現有庫存"] || "0"}</span>
            </div>
            <div className="text-xs text-gray-500 flex gap-3 flex-wrap">
              <span>{row["水晶種類"]}</span>
              <span>售 NT${row["售價(TWD)"]}</span>
              <span>{row["供應商"]}</span>
            </div>
            <div className="flex gap-2 flex-wrap">
              {["現有庫存", "售價(TWD)", "供應商"].map((col) => (
                <button
                  key={col}
                  onClick={() => startEdit(row, col)}
                  className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-400 px-2 py-1 rounded"
                >
                  改 {col}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Desktop table */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-left">
              <th className="px-4 py-3 text-gray-500 font-medium text-xs uppercase tracking-wider">商品</th>
              <th className="px-4 py-3 text-gray-500 font-medium text-xs uppercase tracking-wider">水晶種類</th>
              <th className="px-4 py-3 text-gray-500 font-medium text-xs uppercase tracking-wider">庫存</th>
              <th className="px-4 py-3 text-gray-500 font-medium text-xs uppercase tracking-wider">警戒量</th>
              <th className="px-4 py-3 text-gray-500 font-medium text-xs uppercase tracking-wider">售價</th>
              <th className="px-4 py-3 text-gray-500 font-medium text-xs uppercase tracking-wider">成本</th>
              <th className="px-4 py-3 text-gray-500 font-medium text-xs uppercase tracking-wider">供應商</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-gray-800/50 transition-colors group">
                <td className="px-4 py-3 font-medium text-gray-100">{row["商品名稱"]}</td>
                {COLS.slice(1).map((col) => (
                  <td key={col} className="px-4 py-3">
                    {editing?.row === row._row && editing?.col === col ? (
                      <div className="flex gap-1">
                        <input
                          autoFocus
                          value={value}
                          onChange={(e) => setValue(e.target.value)}
                          onKeyDown={(e) => { if (e.key === "Enter") save(); if (e.key === "Escape") setEditing(null); }}
                          className="w-24 bg-gray-800 border border-purple-500 rounded px-2 py-0.5 text-sm text-white focus:outline-none"
                        />
                        <button onClick={save} disabled={saving} className="text-green-400 hover:text-green-300 text-xs px-1">
                          {saving ? "…" : "✓"}
                        </button>
                        <button onClick={() => setEditing(null)} className="text-gray-500 hover:text-gray-300 text-xs px-1">✕</button>
                      </div>
                    ) : (
                      <span
                        onClick={() => startEdit(row, col)}
                        className={`cursor-pointer hover:underline ${col === "現有庫存" ? stockColor(row) : "text-gray-300"}`}
                      >
                        {col === "售價(TWD)" || col === "成本" ? `NT$${row[col] || "—"}` : row[col] || "—"}
                      </span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit modal for mobile */}
      {editing && (
        <div className="sm:hidden fixed inset-0 bg-black/70 flex items-end z-50" onClick={() => setEditing(null)}>
          <div className="bg-gray-900 border-t border-gray-700 w-full p-5 space-y-3" onClick={(e) => e.stopPropagation()}>
            <p className="text-sm text-gray-400">編輯：{editing.col}</p>
            <input
              autoFocus
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="w-full bg-gray-800 border border-purple-500 rounded-lg px-4 py-2.5 text-white focus:outline-none"
            />
            <div className="flex gap-3">
              <button onClick={save} disabled={saving} className="flex-1 bg-purple-700 hover:bg-purple-600 text-white py-2.5 rounded-lg text-sm font-semibold">
                {saving ? "儲存中…" : "儲存"}
              </button>
              <button onClick={() => setEditing(null)} className="flex-1 bg-gray-800 text-gray-400 py-2.5 rounded-lg text-sm">取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
