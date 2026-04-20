import { getRecords } from "@/lib/sheets";

export default async function PerformancePage() {
  let inventory: Record<string, string>[] = [];
  try {
    inventory = await getRecords("庫存表");
  } catch { /* 空資料 */ }

  const lowStock = inventory.filter((r) => {
    const qty = parseInt(r["現有庫存"] ?? "999");
    const alert = parseInt(r["警戒庫存量"] ?? "20");
    return qty <= alert;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-purple-300">帶貨成效</h1>
        <p className="text-gray-500 text-sm mt-1">庫存狀況 · 蝦皮訂單（接入 API 後顯示即時數據）</p>
      </div>

      {lowStock.length > 0 && (
        <div className="bg-red-900/30 border border-red-700 rounded-xl p-4">
          <div className="font-semibold text-red-400 mb-2">📦 庫存警報（{lowStock.length} 件）</div>
          {lowStock.map((r, i) => (
            <div key={i} className="text-sm text-red-200">
              • {r["商品名稱"]}：剩 {r["現有庫存"]} 件（警戒線 {r["警戒庫存量"]}）
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[
          { label: "蝦皮今日 GMV", value: "—", sub: "接入 Shopee API 後顯示" },
          { label: "直播在線人數", value: "—", sub: "接入 BocaLive 後顯示" },
          { label: "廣告 ROAS", value: "—", sub: "接入 Meta Ads API 後顯示" },
        ].map((s) => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="text-sm text-gray-400 mb-1">{s.label}</div>
            <div className="text-3xl font-bold text-gray-600">{s.value}</div>
            <div className="text-xs text-gray-700 mt-1">{s.sub}</div>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="font-semibold text-gray-300 mb-4">庫存總覽（{inventory.length} 件商品）</h2>
        {inventory.length === 0 ? (
          <p className="text-gray-600 text-sm">庫存資料尚未建立，請在 Google Sheets 庫存表填入商品</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="text-gray-500 border-b border-gray-800">
                  {["商品名稱", "水晶種類", "現有庫存", "警戒庫存量", "售價(TWD)", "供應商"].map((h) => (
                    <th key={h} className="pb-2 pr-4 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {inventory.map((r, i) => {
                  const low = parseInt(r["現有庫存"] ?? "999") <= parseInt(r["警戒庫存量"] ?? "20");
                  return (
                    <tr key={i} className="border-b border-gray-800/50">
                      <td className="py-2 pr-4 text-gray-300">{r["商品名稱"]}</td>
                      <td className="py-2 pr-4 text-gray-400">{r["水晶種類"]}</td>
                      <td className={`py-2 pr-4 font-medium ${low ? "text-red-400" : "text-green-400"}`}>{r["現有庫存"]}</td>
                      <td className="py-2 pr-4 text-gray-500">{r["警戒庫存量"]}</td>
                      <td className="py-2 pr-4 text-gray-400">{r["售價(TWD)"]}</td>
                      <td className="py-2 pr-4 text-gray-500">{r["供應商"]}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
