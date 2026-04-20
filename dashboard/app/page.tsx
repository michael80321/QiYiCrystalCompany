import { getRecords } from "@/lib/sheets";

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
    return { todayReports, pendingReview, activeAgents, failedAgents, needsBoss };
  } catch {
    return { todayReports: [], pendingReview: [], activeAgents: [], failedAgents: [], needsBoss: [] };
  }
}

function StatCard({ label, value, sub, highlight }: {
  label: string; value: string | number; sub?: string; highlight?: boolean;
}) {
  return (
    <div className={`bg-gray-900 border rounded-xl p-5 ${highlight ? "border-yellow-700" : "border-gray-800"}`}>
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className="text-3xl font-bold">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

export default async function HomePage() {
  const { todayReports, pendingReview, activeAgents, failedAgents, needsBoss } = await getDashboardData();
  const today = new Date().toLocaleDateString("zh-TW", {
    year: "numeric", month: "long", day: "numeric", weekday: "long",
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-purple-300">今日總覽</h1>
        <p className="text-gray-500 text-sm mt-1">{today}</p>
      </div>

      {needsBoss.length > 0 && (
        <div className="bg-yellow-900/30 border border-yellow-700 rounded-xl p-4">
          <div className="font-semibold text-yellow-400 mb-2">⚠️ 需要你介入（{needsBoss.length} 件）</div>
          {needsBoss.map((r, i) => (
            <div key={i} className="text-sm text-yellow-200">• {r["員工名稱"]}：{r["原因備注"]}</div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="今日執行次數" value={todayReports.length} sub="次" />
        <StatCard label="待審核內容" value={pendingReview.length} sub="件等待核准" highlight={pendingReview.length > 5} />
        <StatCard label="啟用中員工" value={activeAgents.length} sub="/ 20 個員工" />
        <StatCard label="今日失敗" value={failedAgents.length} sub="需要檢查" highlight={failedAgents.length > 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="font-semibold text-gray-300 mb-4">今日員工執行記錄</h2>
          {todayReports.length === 0 ? (
            <p className="text-gray-600 text-sm">今日尚無執行記錄</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {[...todayReports].reverse().slice(0, 10).map((r, i) => (
                <div key={i} className="flex items-start text-sm">
                  <span className={`inline-block w-2 h-2 rounded-full mt-1.5 mr-2 shrink-0 ${r["執行狀態"] === "成功" ? "bg-green-500" : "bg-red-500"}`} />
                  <div>
                    <span className="text-gray-300">{r["員工名稱"]}</span>
                    <span className="text-gray-600 ml-2 text-xs">{r["執行時間"]?.slice(11, 16)}</span>
                    <div className="text-gray-500 text-xs mt-0.5">{r["輸出摘要"]}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="font-semibold text-gray-300 mb-4">待審核內容</h2>
          {pendingReview.length === 0 ? (
            <p className="text-gray-600 text-sm">目前無待審核內容</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {pendingReview.slice(0, 8).map((r, i) => (
                <div key={i} className="flex items-center justify-between text-sm border-b border-gray-800 pb-2">
                  <div className="flex-1 min-w-0 mr-3">
                    <span className="text-purple-300 font-medium">{r["類型"]}</span>
                    <span className="text-gray-400 ml-2">{r["語言"]} · {r["平台"]}</span>
                    <div className="text-gray-500 text-xs mt-0.5 truncate">{r["內容摘要"]}</div>
                  </div>
                  <a href="/review" className="text-xs bg-purple-700 hover:bg-purple-600 px-2 py-1 rounded text-white shrink-0">審核</a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
