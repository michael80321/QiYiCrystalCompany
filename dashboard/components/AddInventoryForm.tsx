"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function AddInventoryForm() {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: "", crystal: "", stock: "", warning: "", price: "", cost: "", supplier: "",
  });
  const router = useRouter();

  function set(key: string, val: string) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name) return;
    setSaving(true);
    const today = new Date().toISOString().split("T")[0];
    const id = `P${Date.now().toString().slice(-6)}`;
    await fetch("/api/sheets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "append",
        tab: "庫存表",
        rowData: [id, form.name, form.crystal, form.stock, form.warning, form.price, form.cost, form.supplier, today],
      }),
    });
    setSaving(false);
    setForm({ name: "", crystal: "", stock: "", warning: "", price: "", cost: "", supplier: "" });
    setOpen(false);
    router.refresh();
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full bg-gray-900 border border-dashed border-gray-700 hover:border-purple-500 rounded-2xl py-4 text-gray-500 hover:text-purple-400 text-sm transition-colors"
      >
        ＋ 新增商品
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="bg-gray-900 border border-purple-700 rounded-2xl p-5 space-y-4">
      <h3 className="font-semibold text-purple-300 text-sm">新增商品</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">商品名稱 *</label>
          <input value={form.name} onChange={(e) => set("name", e.target.value)} required
            placeholder="例：白水晶柱" className="input-field" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">水晶種類</label>
          <input value={form.crystal} onChange={(e) => set("crystal", e.target.value)}
            placeholder="例：白水晶" className="input-field" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">現有庫存</label>
          <input value={form.stock} onChange={(e) => set("stock", e.target.value)}
            type="number" placeholder="0" className="input-field" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">警戒庫存量</label>
          <input value={form.warning} onChange={(e) => set("warning", e.target.value)}
            type="number" placeholder="5" className="input-field" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">售價 (TWD)</label>
          <input value={form.price} onChange={(e) => set("price", e.target.value)}
            type="number" placeholder="1200" className="input-field" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">成本</label>
          <input value={form.cost} onChange={(e) => set("cost", e.target.value)}
            type="number" placeholder="600" className="input-field" />
        </div>
        <div className="sm:col-span-2">
          <label className="text-xs text-gray-500 mb-1 block">供應商</label>
          <input value={form.supplier} onChange={(e) => set("supplier", e.target.value)}
            placeholder="例：巴西礦石進口商" className="input-field" />
        </div>
      </div>
      <div className="flex gap-3 pt-1">
        <button type="submit" disabled={saving}
          className="flex-1 bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white py-2.5 rounded-lg text-sm font-semibold">
          {saving ? "新增中…" : "新增商品"}
        </button>
        <button type="button" onClick={() => setOpen(false)}
          className="px-5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg text-sm">
          取消
        </button>
      </div>
    </form>
  );
}
