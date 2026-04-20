"""
採購庫存員
執行頻率：每日 08:00
工作：檢查庫存低於警戒值，推 Telegram 通知，不需要 Anthropic API
"""
import os, sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send, send_inventory_alert

AGENT_NAME = "採購庫存員"
logger = get_logger(AGENT_NAME)


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    try:
        inventory = sheets.get_all_records("庫存表")
        low_stock = []
        out_of_stock = []

        for item in inventory:
            name = item.get("商品名稱", "")
            if not name:
                continue
            try:
                qty = int(item.get("現有庫存", 0))
                alert = int(item.get("警戒庫存量", 20))
            except (ValueError, TypeError):
                continue

            if qty == 0:
                out_of_stock.append((name, qty))
            elif qty <= alert:
                low_stock.append((name, qty))

        rows_written = 0
        needs_boss = False

        if out_of_stock:
            names = "、".join([n for n, _ in out_of_stock])
            send(f"🚨 <b>【斷貨警報】</b>\n{names} 已售完，請立即補貨！")
            needs_boss = True
            rows_written += len(out_of_stock)

        if low_stock:
            for name, qty in low_stock:
                send_inventory_alert(name, qty)
            rows_written += len(low_stock)

        if not low_stock and not out_of_stock:
            logger.info("所有商品庫存正常")

        summary = f"低庫存 {len(low_stock)} 件｜斷貨 {len(out_of_stock)} 件"
        log_execution(AGENT_NAME, "成功", summary, rows_written, needs_boss)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, rows_written, needs_boss,
                                   "有商品斷貨" if out_of_stock else "")
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
