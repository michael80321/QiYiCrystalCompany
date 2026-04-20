import { getRecords } from "@/lib/sheets";

const MARKET_COLORS: Record<string, string> = {
  台灣: "border-blue-700 bg-blue-900/20",
  香港: "border-green-700 bg-green-900/20",
  大陸: "border-red-700 bg-red-900/20",
  東南亞: "border-yellow-700 bg-yellow-900/20",
};

export default async function IntelligencePage() {
  let records: Record<string, string>[] = [];
  try {
    records = await getRecords("情報表");
  } catch { /* 空資料 */ }

  const today = new Date().toISOString().split("T")[0];
  const todayRecords = records.filter((r) => r["日期"]?.startsWith(today));
  const alerts = todayRecords.filter((r) => r["是否爆款"] === "是" || r["建議行動"]);

  const byMarket: Record<string, typeof records> = {};
  for (const r of todayRecords) {
    const m = r["市場"] ?? "其他";
    if (!byMarket[m]) byMarket[m] = [];
    byMarket[m].push(r);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-purple-300">市場情報</h1>
        <p className="text-gray-500 text-sm mt-1">今日蒐集 {todayRecords.length} 筆情報</p>
      </div>

      {alerts.length > 0 && (
        <div className="bg-orange-900/30 border border-orange-700 rounded-xl p-4">
          <div className="font-semibold text-orange-400 mb-2">📈 今日商機／爆款預警</div>
          {alerts.slice(0, 5).map((r, i) => (
            <div key={i} className="text-sm text-orange-200 mt-1">
              • [{r["市場"]}] {r["關鍵字"] || r["來源帳號"]}：{r["建議行動"]}
            </div>
          ))}
        </div>
      )}

      {todayRecords.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-10 text-center text-gray-600">
          今日尚無情報資料，員工執行後自動填入
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {Object.entries(byMarket).map(([market, items]) => (
            <div key={market} className={`border rounded-xl p-5 ${MARKET_COLORS[market] ?? "border-gray-700"}`}>
              <h2 className="font-semibold text-gray-200 mb-3">{market} ({items.length} 筆)</h2>
              <div className="space-y-2">
                {items.slice(0, 5).map((r, i) => (
                  <div key={i} className="text-sm border-b border-gray-800/50 pb-2 last:border-0">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">{r["平台"]}</span>
                      {r["是否爆款"] === "是" && <span className="text-xs bg-red-800 text-red-300 px-1.5 rounded">爆款</span>}
                    </div>
                    <div className="text-gray-300 mt-0.5">{r["關鍵字"] || r["來源帳號"]}</div>
                    {r["建議行動"] && <div className="text-gray-500 text-xs mt-0.5">→ {r["建議行動"]}</div>}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="font-semibold text-gray-300 mb-3">歷史情報（最新 20 筆）</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800">
                {["日期", "市場", "平台", "關鍵字", "建議行動"].map((h) => (
                  <th key={h} className="pb-2 pr-4 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...records].reverse().slice(0, 20).map((r, i) => (
                <tr key={i} className="border-b border-gray-800/50 text-gray-400">
                  <td className="py-1.5 pr-4">{r["日期"]?.slice(5)}</td>
                  <td className="py-1.5 pr-4">{r["市場"]}</td>
                  <td className="py-1.5 pr-4">{r["平台"]}</td>
                  <td className="py-1.5 pr-4 max-w-32 truncate">{r["關鍵字"]}</td>
                  <td className="py-1.5 pr-4 max-w-40 truncate">{r["建議行動"]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
