import { getRecords } from "@/lib/sheets";
import AgentToggle from "@/components/AgentToggle";

export default async function AgentsPage() {
  let agents: Record<string, string>[] = [];
  let reports: Record<string, string>[] = [];
  try {
    [agents, reports] = await Promise.all([
      getRecords("員工開關"),
      getRecords("日報表"),
    ]);
  } catch { /* 空資料 */ }

  const lastRun: Record<string, string> = {};
  const lastSummary: Record<string, string> = {};
  for (const r of reports) {
    const name = r["員工名稱"];
    if (!lastRun[name] || r["執行時間"] > lastRun[name]) {
      lastRun[name] = r["執行時間"];
      lastSummary[name] = r["輸出摘要"];
    }
  }

  const categories: Record<string, string[]> = {
    "情報引擎": ["亞太市場情報員", "選品趨勢研究員", "競品定價策略員", "商品知識庫管理員", "系統健康監控員"],
    "內容引擎": ["能量內容專員", "圖像產出員", "影片腳本員", "數字人短影片生成", "影片後製自動化"],
    "行銷帶貨": ["行銷企劃員", "廣告投放優化員", "SEO優化員", "KOL合作追蹤員"],
    "營運管理": ["客服接待員", "採購庫存員", "物流售後員", "會員經營員"],
    "財務決策": ["財務秘書", "老闆決策秘書"],
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-purple-300">員工控制台</h1>
        <p className="text-gray-500 text-sm mt-1">管理所有 AI 員工的開關狀態</p>
      </div>

      {Object.entries(categories).map(([category, names]) => (
        <div key={category} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="font-semibold text-gray-300 mb-4">{category}</h2>
          <div className="space-y-3">
            {names.map((name) => {
              const agent = agents.find((a) => a["員工名稱"] === name);
              const enabled = agent?.["狀態"] === "開啟";
              return (
                <div key={name} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full shrink-0 ${enabled ? "bg-green-500" : "bg-gray-600"}`} />
                      <span className="text-sm font-medium text-gray-200">{name}</span>
                      <span className="text-xs text-gray-600">{agent?.["執行頻率"] ?? ""}</span>
                    </div>
                    {lastRun[name] && (
                      <div className="text-xs text-gray-600 mt-0.5 ml-4 truncate">
                        上次：{lastRun[name]?.slice(0, 16)} — {lastSummary[name]}
                      </div>
                    )}
                  </div>
                  <AgentToggle name={name} enabled={enabled} />
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
