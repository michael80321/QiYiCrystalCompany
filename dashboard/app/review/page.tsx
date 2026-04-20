import { getRecords } from "@/lib/sheets";
import ReviewActions from "@/components/ReviewActions";

export default async function ReviewPage() {
  let queue: Record<string, string>[] = [];
  try {
    queue = await getRecords("審核隊列");
  } catch { /* 空資料 */ }

  type QueueRow = { [key: string]: string | number; _row: number };
  const pending: QueueRow[] = (queue.map((r, i) => ({ ...r, _row: i + 2 })) as QueueRow[]).filter((r) => r["狀態"] === "待審");
  const approved = queue.filter((r) => r["狀態"] === "核准").slice(-5);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-purple-300">內容審核</h1>
        <p className="text-gray-500 text-sm mt-1">待審核 {pending.length} 件 · 核准後自動排程發布</p>
      </div>

      {pending.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-10 text-center text-gray-600">
          目前沒有待審核內容 🎉
        </div>
      ) : (
        <div className="space-y-3">
          {pending.map((item, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <span className="text-xs bg-purple-900 text-purple-300 px-2 py-0.5 rounded">{item["類型"]}</span>
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{item["語言"]}</span>
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{item["平台"]}</span>
                    <span className="text-xs text-gray-600">{item["預定發布時間"]}</span>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed">{item["內容摘要"]}</p>
                  {item["老闆批注"] && (
                    <p className="text-yellow-400 text-xs mt-2">批注：{item["老闆批注"]}</p>
                  )}
                </div>
                <ReviewActions row={item._row} />
              </div>
            </div>
          ))}
        </div>
      )}

      {approved.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="font-semibold text-gray-400 mb-3 text-sm">最近核准（{approved.length} 件）</h2>
          <div className="space-y-1">
            {approved.map((r, i) => (
              <div key={i} className="text-sm text-gray-600 flex gap-2">
                <span className="text-green-600">✓</span>
                <span>{r["類型"]} · {r["平台"]} · {r["預定發布時間"]}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
