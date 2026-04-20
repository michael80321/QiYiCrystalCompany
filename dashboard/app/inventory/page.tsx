import { getRecords } from "@/lib/sheets";
import InventoryTable from "@/components/InventoryTable";
import AddInventoryForm from "@/components/AddInventoryForm";

export const revalidate = 0;

export default async function InventoryPage() {
  let items: Record<string, string>[] = [];
  try {
    items = await getRecords("庫存表");
  } catch { /* 空資料 */ }

  type InventoryRow = { [key: string]: string; _row: string };
  const rows = items.map((r, i) => ({ ...r, _row: String(i + 2) })) as InventoryRow[];

  const lowStock = rows.filter((r) => {
    const current = Number(r["現有庫存"] || 0);
    const warning = Number(r["警戒庫存量"] || 0);
    return current <= warning && current > 0;
  });

  const outOfStock = rows.filter((r) => Number(r["現有庫存"] || 0) === 0 && r["商品名稱"]);

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-purple-300">庫存管理</h1>
          <p className="text-gray-500 text-sm mt-1">
            共 <span className="text-white font-semibold">{rows.length}</span> 項商品 ·
            低庫存 <span className="text-yellow-400 font-semibold">{lowStock.length}</span> 項 ·
            缺貨 <span className="text-red-400 font-semibold">{outOfStock.length}</span> 項
          </p>
        </div>
      </div>

      {/* 警示區 */}
      {(lowStock.length > 0 || outOfStock.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {outOfStock.length > 0 && (
            <div className="bg-red-950/40 border border-red-800 rounded-2xl p-4">
              <div className="text-sm font-semibold text-red-400 mb-2">🚨 缺貨商品</div>
              {outOfStock.map((r, i) => (
                <div key={i} className="text-sm text-red-300">{r["商品名稱"]}</div>
              ))}
            </div>
          )}
          {lowStock.length > 0 && (
            <div className="bg-yellow-950/40 border border-yellow-800 rounded-2xl p-4">
              <div className="text-sm font-semibold text-yellow-400 mb-2">⚠️ 低庫存商品</div>
              {lowStock.map((r, i) => (
                <div key={i} className="text-sm text-yellow-300">
                  {r["商品名稱"]} — 剩 {r["現有庫存"]} 件
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 新增商品 */}
      <AddInventoryForm />

      {/* 商品列表 */}
      {rows.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
          <div className="text-4xl mb-3">📦</div>
          <p className="text-gray-500">尚未建立任何商品，請新增第一筆庫存</p>
        </div>
      ) : (
        <InventoryTable rows={rows} />
      )}
    </div>
  );
}
