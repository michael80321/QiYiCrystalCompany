import { getRecords } from "@/lib/sheets";
import AgentToggle from "@/components/AgentToggle";
import AutoRefresh from "@/components/AutoRefresh";
import BulkAgentControl from "@/components/BulkAgentControl";

export const revalidate = 0;

type ReportRow = { [key: string]: string };

export default async function AgentsPage() {
  let agents: Record<string, string>[] = [];
  let reports: ReportRow[] = [];
  try {
    [agents, reports] = await Promise.all([
      getRecords("員工開關"),
      getRecords("日報表"),
    ]);
  } catch { /* 空資料 */ }

  // Group last 5 runs per agent, sorted newest first
  const agentHistory: Record<string, ReportRow[]> = {};
  for (const r of reports) {
    const name = r["員工名稱"];
    if (!agentHistory[name]) agentHistory[name] = [];
    agentHistory[name].push(r);
  }
  for (const name in agentHistory) {
    agentHistory[name].sort((a, b) =>
      (b["執行時間"] ?? "").localeCompare(a["執行時間"] ?? "")
    );
    agentHistory[name] = agentHistory[name].slice(0, 5);
  }

  // Today's daily briefing: gather latest run per agent for today
  const today = new Date().toISOString().split("T")[0];
  const todayReports = reports.filter(r => r["執行時間"]?.startsWith(today));
  const latestToday: Record<string, ReportRow> = {};
  for (const r of todayReports) {
    const name = r["員工名稱"];
    if (!latestToday[name] || r["執行時間"] > latestToday[name]["執行時間"]) {
      latestToday[name] = r;
    }
  }
  const briefingAgents = Object.values(latestToday).sort((a, b) =>
    (b["執行時間"] ?? "").localeCompare(a["執行時間"] ?? "")
  );

  const categories: Record<string, string[]> = {
    "🛍 BD 開發引擎": ["選品委員會員", "企業禮品開發員", "蝦皮自動上架員"],
    "🔍 情報引擎": ["亞太市場情報員", "選品趨勢研究員", "競品定價策略員", "商品知識庫管理員", "系統健康監控員"],
    "✍️ 內容引擎": ["能量內容專員", "圖像產出員", "影片腳本員", "數字人短影片生成", "影片後製自動化"],
    "📣 行銷帶貨": ["行銷企劃員", "廣告投放優化員", "SEO優化員", "KOL合作追蹤員"],
    "⚙️ 營運管理": ["客服接待員", "採購庫存員", "物流售後員", "會員經營員"],
    "💰 財務決策": ["財務秘書", "老闆決策秘書"],
  };

  return (
    <div className="space-y-6 pb-10">
      <AutoRefresh intervalMs={30000} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-purple-300">員工控制台</h1>
          <p className="text-gray-500 text-sm mt-1">管理所有 AI 員工的開關狀態與即時記錄</p>
        </div>
        <div className="text-xs text-gray-600">每 30 秒自動更新</div>
      </div>

      {/* 一鍵全開/全關 */}
      <BulkAgentControl agents={agents} />

      {/* 今日匯報看板 */}
      {briefingAgents.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="font-semibold text-purple-300 mb-4 flex items-center gap-2">
            📋 今日員工匯報
            <span className="text-xs text-gray-600 font-normal">
              {briefingAgents.length} 位員工已執行
            </span>
          </h2>
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {briefingAgents.map((r, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                  r["執行狀態"] === "成功" ? "bg-green-500" : "bg-red-500"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-gray-200">{r["員工名稱"]}</span>
                    <span className="text-xs text-gray-600">{r["執行時間"]?.slice(11, 16)}</span>
                    {r["執行狀態"] === "失敗" && (
                      <span className="text-xs bg-red-900/50 text-red-400 px-1.5 py-0.5 rounded">失敗</span>
                    )}
                    {r["需要老闆介入"] === "是" && (
                      <span className="text-xs bg-yellow-900/50 text-yellow-400 px-1.5 py-0.5 rounded">⚠️ 需介入</span>
                    )}
                    {r["寫入筆數"] && Number(r["寫入筆數"]) > 0 && (
                      <span className="text-xs text-gray-600">寫入 {r["寫入筆數"]} 筆</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">
                    {r["輸出摘要"] || r["原因備注"] || "—"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 員工分類控制 */}
      {Object.entries(categories).map(([category, names]) => (
        <div key={category} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="font-semibold text-gray-300 mb-4">{category}</h2>
          <div className="space-y-4">
            {names.map((name) => {
              const agent = agents.find((a) => a["員工名稱"] === name);
              const enabled = agent?.["狀態"] === "開啟";
              const history = agentHistory[name] ?? [];
              const latest = history[0];
              const isRunningNow = latest &&
                (Date.now() - new Date(latest["執行時間"]).getTime()) < 5 * 60 * 1000;

              return (
                <div key={name} className="border-b border-gray-800 last:border-0 pb-4 last:pb-0">
                  {/* Agent header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`w-2 h-2 rounded-full shrink-0 ${
                        enabled
                          ? isRunningNow
                            ? "bg-green-400 animate-pulse"
                            : "bg-green-600"
                          : "bg-gray-600"
                      }`} />
                      <span className="text-sm font-medium text-gray-200">{name}</span>
                      <span className="text-xs text-gray-600">{agent?.["執行頻率"] ?? ""}</span>
                      {latest?.["執行狀態"] === "失敗" && (
                        <span className="text-xs bg-red-900/50 text-red-400 px-1.5 py-0.5 rounded">失敗</span>
                      )}
                      {latest?.["需要老闆介入"] === "是" && (
                        <span className="text-xs bg-yellow-900/50 text-yellow-400 px-1.5 py-0.5 rounded">⚠️</span>
                      )}
                    </div>
                    <AgentToggle name={name} enabled={enabled} />
                  </div>

                  {/* Execution history */}
                  {history.length > 0 ? (
                    <div className="mt-2 ml-4 space-y-1.5">
                      {history.map((r, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs">
                          <span className={`w-1.5 h-1.5 rounded-full mt-1 shrink-0 ${
                            r["執行狀態"] === "成功" ? "bg-green-500" : "bg-red-500"
                          }`} />
                          <span className="text-gray-600 shrink-0 tabular-nums w-24">
                            {r["執行時間"]?.slice(5, 16) ?? ""}
                          </span>
                          <span className={`flex-1 leading-relaxed ${
                            i === 0 ? "text-gray-400" : "text-gray-600"
                          }`}>
                            {r["輸出摘要"] || r["原因備注"] || "—"}
                          </span>
                          {r["寫入筆數"] && Number(r["寫入筆數"]) > 0 && (
                            <span className="text-gray-700 shrink-0">{r["寫入筆數"]} 筆</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="mt-1.5 ml-4 text-xs text-gray-700">尚無執行記錄</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
