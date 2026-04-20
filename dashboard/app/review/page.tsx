import { getRecords } from "@/lib/sheets";
import ReviewCard from "@/components/ReviewCard";
import BulkActions from "@/components/BulkActions";

export const revalidate = 0;

export default async function ReviewPage() {
  let queue: Record<string, string>[] = [];
  try {
    queue = await getRecords("審核隊列");
  } catch { /* 空資料 */ }

  type QueueRow = { [key: string]: string | number; _row: number };
  const rows = queue.map((r, i) => ({ ...r, _row: i + 2 })) as QueueRow[];

  const pending = rows.filter((r) => r["狀態"] === "待審");
  const approved = rows.filter((r) => r["狀態"] === "核准").slice(-10);
  const rejected = rows.filter((r) => r["狀態"] === "退回").slice(-5);

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-purple-300">內容審核</h1>
          <p className="text-gray-500 text-sm mt-1">
            待審 <span className="text-yellow-400 font-semibold">{pending.length}</span> 件 ·
            核准 <span className="text-green-400 font-semibold">{approved.length}</span> 件
          </p>
        </div>
      </div>

      {/* 待審區 */}
      {pending.length > 1 && <BulkActions items={pending} />}

      {pending.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
          <div className="text-4xl mb-3">🎉</div>
          <p className="text-gray-500">目前沒有待審核內容</p>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider">
            ⏳ 待審核（{pending.length} 件）
          </h2>
          {pending.map((item, i) => (
            <ReviewCard key={i} item={item} />
          ))}
        </div>
      )}

      {/* 最近核准 */}
      {approved.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-green-400 uppercase tracking-wider">
            ✅ 最近核准（{approved.length} 件）
          </h2>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl divide-y divide-gray-800">
            {approved.map((r, i) => (
              <div key={i} className="px-5 py-3 flex items-center gap-3">
                <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{r["類型"]}</span>
                <span className="text-sm text-gray-400 flex-1 truncate">{r["內容摘要"]}</span>
                <span className="text-xs text-gray-600 shrink-0">{r["預定發布時間"]}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 最近退回 */}
      {rejected.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider">
            ❌ 最近退回（{rejected.length} 件）
          </h2>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl divide-y divide-gray-800">
            {rejected.map((r, i) => (
              <div key={i} className="px-5 py-3 flex items-center gap-3">
                <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{r["類型"]}</span>
                <span className="text-sm text-gray-500 flex-1 truncate">{r["內容摘要"]}</span>
                {r["老闆批注"] && (
                  <span className="text-xs text-red-400 shrink-0">{r["老闆批注"]}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
