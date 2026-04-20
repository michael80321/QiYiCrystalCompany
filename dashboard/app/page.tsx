import { getRecords } from "@/lib/sheets";
import AutoRefresh from "@/components/AutoRefresh";
import Link from "next/link";

export const revalidate = 0;

async function getDashboardData() {
  try {
    const [reports, queue, agents] = await Promise.all([
      getRecords("日報表"),
      getRecords("審核隊列"),
      getRecords("員工開關"),
    ]);
    const today = new Date().toISOString().split("T")[0];
    const todayReports = reports.filter((r) => r["執行時間"]?.startsWith(today));
    const pendingReview = queue.filter((r) => r["狀態"] === "待審");
    const activeAgents = agents.filter((a) => a["狀態"] === "開啟");
    const failedAgents = todayReports.filter((r) => r["執行狀態"] === "失敗");
    const needsBoss = todayReports.filter((r) => r["需要老闆介入"] === "是");
    return { todayReports, pendingReview, activeAgents, failedAgents, needsBoss, agents };
  } catch {
    return { todayReports: [], pendingReview: [], activeAgents: [], failedAgents: [], needsBoss: [], agents: [] };
  }
}

function StatCard({ label, value, sub, highlight, color }: {
  label: string; value: string | number; sub?: string; highlight?: boolean; color?: string;
}) {
  return (
    <div className={`bg-gray-900 border rounded-2xl p-5 ${highlight ? "border-yellow-700" : "border-gray-800"}`}>
      <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">{label}</div>
      <div className={`text-3xl font-bold ${color || "text-white"}`}>{value}</div>
      {sub && <div className="text-xs text-gray-600 mt-1">{sub}</div>}
    </div>
  );
}

function AgentStatusDot({ status, lastRun }: { status: string; lastRun?: string }) {
  const isRecent = lastRun && (Date.now() - new Date(lastRun).getTime()) < 6 * 60 * 60 * 1000;
  if (status !== "開啟") return <span className="w-2 h-2 rounded-full bg-gray-600 inline-block" />;
  if (isRecent) return <span className="w-2 h-2 rounded-full bg-green-400 inline-block animate-pulse" />;
  return <span className="w-2 h-2 rounded-full bg-green-600 inline-block" />;
}

export default async function HomePage() {
  const { todayReports, pendingReview, activeAgents, failedAgents, needsBoss, agents } = await getDashboardData();
  const today = new Date().toLocaleDateString("zh-TW", {
    year: "numeric", month: "long", day: "numeric", weekday: "long",
  });

  // 最新一筆決策秘書報告
  const latestBriefing = [...todayReports].reverse().find(r => r["員工名稱"] === "老闆決策秘書");

  return (
    <div className="space-y-6 pb-10">
      <AutoRefresh intervalMs={60000} />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-purple-300">今日總覽</h1>
          <p className="text-gray-500 text-sm mt-1">{today}</p>
        </div>
        <div className="text-xs text-gray-600">每分鐘自動更新</div>
      </div>

      {/* 需要介入警示 */}
      {needsBoss.length > 0 && (
        <div className="bg-yellow-900/30 border border-yellow-700 rounded-2xl p-4">
          <div className="font-semibold text-yellow-400 mb-2">⚠️ 需要你介入（{needsBoss.length} 件）</div>
          {needsBoss.map((r, i) => (
            <div key={i} className="text-sm text-yellow-200 mt-1">
              • <span className="font-medium">{r["員工名稱"]}</span>：{r["原因備注"]}
            </div>
          ))}
        </div>
      )}

      {/* 今日決策秘書簡報 */}
      {latestBriefing && (
        <div className="bg-purple-950/40 border border-purple-800 rounded-2xl p-5">
          <div className="text-xs text-purple-400 font-semibold uppercase tracking-wider mb-2">📋 今日決策秘書簡報</div>
          <p className="text-gray-300 text-sm leading-relaxed">{latestBriefing["輸出摘要"]}</p>
          <p className="text-gray-600 text-xs mt-2">{latestBriefing["執行時間"]}</p>
        </div>
      )}

      {/* 數據卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="今日執行" value={todayReports.length} sub="次" />
        <StatCard label="待審核" value={pendingReview.length} sub="件等待核准"
          highlight={pendingReview.length > 0} color={pendingReview.length > 0 ? "text-yellow-400" : "text-white"} />
        <StatCard label="啟用員工" value={activeAgents.length} sub={`/ ${agents.length} 個`} color="text-green-400" />
        <StatCard label="今日失敗" value={failedAgents.length} sub="需要檢查"
          highlight={failedAgents.length > 0} color={failedAgents.length > 0 ? "text-red-400" : "text-white"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 員工即時狀態 */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <h2 className="font-semibold text-gray-300 mb-4 flex items-center gap-2">
            員工即時狀態
            <span className="text-xs text-gray-600 font-normal">今日執行記錄</span>
          </h2>
          {todayReports.length === 0 ? (
            <p className="text-gray-600 text-sm">今日尚無執行記錄</p>
          ) : (
            <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
              {[...todayReports].reverse().map((r, i) => (
                <div key={i} className="flex items-start gap-3 text-sm">
                  <span className={`inline-block w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                    r["執行狀態"] === "成功" ? "bg-green-500" : "bg-red-500"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-gray-200 font-medium">{r["員工名稱"]}</span>
                      <span className="text-gray-600 text-xs">{r["執行時間"]?.slice(11, 16)}</span>
                      {r["執行狀態"] === "失敗" && (
                        <span className="text-xs bg-red-900/50 text-red-400 px-1.5 py-0.5 rounded">失敗</span>
                      )}
                    </div>
                    <div className="text-gray-500 text-xs mt-0.5 leading-relaxed">{r["輸出摘要"]}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 待審核 + 員工清單 */}
        <div className="space-y-4">
          {/* 待審核 */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-gray-300">待審核內容</h2>
              {pendingReview.length > 0 && (
                <Link href="/review" className="text-xs bg-purple-700 hover:bg-purple-600 px-3 py-1 rounded-lg text-white">
                  前往審核 →
                </Link>
              )}
            </div>
            {pendingReview.length === 0 ? (
              <p className="text-gray-600 text-sm">目前無待審核內容 🎉</p>
            ) : (
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {pendingReview.slice(0, 5).map((r, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="bg-purple-900/50 text-purple-300 px-1.5 py-0.5 rounded shrink-0">{r["類型"]}</span>
                    <span className="text-gray-500 truncate">{r["語言"]} · {r["平台"]}</span>
                  </div>
                ))}
                {pendingReview.length > 5 && (
                  <p className="text-xs text-gray-600">還有 {pendingReview.length - 5} 件...</p>
                )}
              </div>
            )}
          </div>

          {/* 員工清單狀態 */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <h2 className="font-semibold text-gray-300 mb-3">員工在線狀態</h2>
            <div className="grid grid-cols-2 gap-1.5 max-h-40 overflow-y-auto">
              {agents.slice(0, 12).map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-gray-400">
                  <AgentStatusDot status={a["狀態"]} lastRun={a["最後執行時間"]} />
                  <span className="truncate">{a["員工名稱"]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
