"""
財務秘書
執行頻率：每日 23:00
工作：當日收支對帳摘要、每月 1 日產出損益摘要，不需要 Anthropic API
"""
import os, sys
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send, send_alert

AGENT_NAME = "財務秘書"
logger = get_logger(AGENT_NAME)


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    today = date.today()

    try:
        inventory = sheets.get_all_records("庫存表")

        # 估算庫存總值
        total_inventory_value = 0
        total_items = 0
        for item in inventory:
            try:
                qty = int(item.get("現有庫存", 0))
                cost = float(str(item.get("成本", "0")).replace(",", "") or 0)
                total_inventory_value += qty * cost
                total_items += qty
            except (ValueError, TypeError):
                continue

        # 每月1日發損益摘要
        is_month_start = today.day == 1
        report_lines = [f"📊 <b>騏藝逸品財務日報 {today}</b>"]
        report_lines.append(f"庫存總值：NT${total_inventory_value:,.0f}")
        report_lines.append(f"庫存總件數：{total_items} 件")

        if is_month_start:
            report_lines.append(f"\n📅 <b>月初財務摘要</b>")
            report_lines.append("請至 Google Sheets 庫存表確認上月結算數字")

        report_lines.append("\n⚠️ 蝦皮/Meta 廣告費用請手動核對")
        send("\n".join(report_lines))

        summary = f"庫存總值 NT${total_inventory_value:,.0f}｜{total_items} 件"
        log_execution(AGENT_NAME, "成功", summary, 1, is_month_start, "月初損益請確認" if is_month_start else "")
        sheets.update_agent_status(AGENT_NAME, "成功", summary, 1, is_month_start)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
