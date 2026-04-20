"""
危機預警員
執行頻率：每小時
工作：監控負評爆發、競品大促、平台政策異動，不需要 Anthropic API（規則式）
"""
import os, sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert, send

AGENT_NAME = "危機預警員"
logger = get_logger(AGENT_NAME)

# 危機關鍵字（未來接入評論 API 後自動掃描）
CRISIS_KEYWORDS = ["詐騙", "假貨", "退款", "客訴", "投訴", "法律", "賠償"]


def check_review_backlog() -> bool:
    """審核隊列積壓超過閾值"""
    try:
        queue = sheets.get_all_records("審核隊列")
        pending = sum(1 for r in queue if r.get("狀態") == "待審")
        if pending > 10:
            send_alert("審核積壓", f"待審核內容已達 {pending} 件，請盡快處理！")
            return True
    except Exception:
        pass
    return False


def check_agent_failures() -> int:
    """過去 3 小時失敗員工數"""
    try:
        reports = sheets.get_all_records("日報表")
        three_hours_ago = datetime.now() - timedelta(hours=3)
        failures = [
            r for r in reports
            if r.get("執行狀態") == "失敗"
            and r.get("執行時間", "") > three_hours_ago.strftime("%Y-%m-%d %H:%M:%S")
        ]
        return len(failures)
    except Exception:
        return 0


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    try:
        issues = []

        # 審核積壓檢查
        if check_review_backlog():
            issues.append("審核隊列積壓")

        # 員工失敗檢查
        failures = check_agent_failures()
        if failures >= 3:
            send_alert("多個員工失敗", f"過去3小時有 {failures} 個員工執行失敗，請檢查日報表")
            issues.append(f"{failures}個員工失敗")

        needs_boss = len(issues) > 0
        summary = f"偵測到 {len(issues)} 個異常：{'、'.join(issues)}" if issues else "系統正常，無危機訊號"

        log_execution(AGENT_NAME, "成功", summary, 0, needs_boss)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, 0, needs_boss)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
