"""
老闆決策秘書
執行頻率：每日 07:30
工作：整合所有員工日報 → 產出「今日你需要做的 3 件事」推 Telegram
"""
import os, sys, json
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import anthropic
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send, send_alert

AGENT_NAME = "老闆決策秘書"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品老闆的 AI 決策秘書。

今天日期：{date}
以下是今日各 AI 員工的執行報告：

{reports}

待審核內容：{pending_count} 件
庫存警報商品：{low_stock}

請整合以上資訊，給老闆最精簡的每日簡報。

輸出 JSON（只輸出 JSON）：
{{
  "good_morning": "一句早安開場（溫暖簡短）",
  "top3_actions": [
    {{
      "priority": 1,
      "action": "具體行動描述",
      "reason": "為什麼重要",
      "time_needed": "5分鐘"
    }}
  ],
  "opportunities": "今日最大商機一句話",
  "alerts": "需要注意的風險（沒有就填空字串）",
  "agent_summary": "員工整體表現一句話"
}}

top3_actions 必須是真正需要老闆親自做的事，不是 AI 能自動處理的。
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = date.today().isoformat()

    try:
        # 讀取今日日報
        all_reports = sheets.get_all_records("日報表")
        today_reports = [r for r in all_reports if r.get("執行時間", "").startswith(today)]

        # 讀取待審核數量
        queue = sheets.get_all_records("審核隊列")
        pending_count = sum(1 for r in queue if r.get("狀態") == "待審")

        # 讀取低庫存
        inventory = sheets.get_all_records("庫存表")
        low_stock_items = [
            r.get("商品名稱", "") for r in inventory
            if r.get("現有庫存") and r.get("警戒庫存量")
            and int(r.get("現有庫存", 999)) <= int(r.get("警戒庫存量", 20))
        ]
        low_stock_str = "、".join(low_stock_items) if low_stock_items else "無"

        # 整理報告摘要
        reports_text = "\n".join([
            f"- {r.get('員工名稱')}：{r.get('執行狀態')} — {r.get('輸出摘要', '')}"
            for r in today_reports
        ]) or "今日尚無員工執行記錄"

        logger.info(f"整合 {len(today_reports)} 份日報，待審 {pending_count} 件")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": PROMPT.format(
                date=today,
                reports=reports_text,
                pending_count=pending_count,
                low_stock=low_stock_str,
            )}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        # 組成 Telegram 訊息
        lines = [
            f"🔮 {data.get('good_morning', '早安！')}",
            f"\n📋 <b>今日你需要做的 3 件事：</b>",
        ]
        for item in data.get("top3_actions", []):
            lines.append(
                f"\n{item['priority']}. <b>{item['action']}</b>\n"
                f"   → {item['reason']}（約 {item['time_needed']}）"
            )
        if data.get("opportunities"):
            lines.append(f"\n💡 {data['opportunities']}")
        if data.get("alerts"):
            lines.append(f"\n⚠️ {data['alerts']}")
        lines.append(f"\n🤖 {data.get('agent_summary', '')}")
        lines.append(f"\n📊 待審核 {pending_count} 件 → qi-yi-crystal-company.vercel.app/review")

        send("\n".join(lines))

        summary = f"推送今日決策簡報｜待審 {pending_count} 件｜低庫存 {len(low_stock_items)} 項"
        log_execution(AGENT_NAME, "成功", summary, 1, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, 1, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
