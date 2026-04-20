"""
系統健康監控員
執行頻率：每小時
工作：檢查所有員工執行狀態、API 健康、異常即時推送 Telegram
"""
import os, sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.api_health import run_all_checks
from shared.logger import get_logger, log_execution
from shared.line_notify import send, send_alert

AGENT_NAME = "系統健康監控員"
logger = get_logger(AGENT_NAME)


def check_agent_statuses() -> list[dict]:
    """讀取日報表，找出過去 2 小時內失敗的員工"""
    issues = []
    try:
        records = sheets.get_all_records("日報表")
        two_hours_ago = datetime.now() - timedelta(hours=2)
        for row in records:
            try:
                ts = datetime.strptime(str(row.get("執行時間", "")), "%Y-%m-%d %H:%M:%S")
                if ts > two_hours_ago and row.get("執行狀態") == "失敗":
                    issues.append({
                        "agent": row.get("員工名稱", ""),
                        "time": str(row.get("執行時間", "")),
                        "reason": str(row.get("原因備注", "")),
                    })
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"讀取日報表失敗：{e}")
    return issues


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    try:
        # API 健康檢查
        api_results = run_all_checks()
        api_ok = sum(1 for r in api_results.values() if r["ok"])
        api_total = len(api_results)

        # 員工狀態檢查
        issues = check_agent_statuses()

        # 彙整報告
        status_lines = [f"🔧 系統健康報告 {datetime.now().strftime('%H:%M')}"]
        status_lines.append(f"API 狀態：{api_ok}/{api_total} 正常")

        for name, result in api_results.items():
            icon = "✅" if result["ok"] else "❌"
            status_lines.append(f"  {icon} {name}：{result['msg']}")

        if issues:
            status_lines.append(f"\n⚠️ 近2小時失敗員工（{len(issues)}個）：")
            for issue in issues:
                status_lines.append(f"  • {issue['agent']}：{issue['reason']}")
            send_alert("員工執行失敗", "\n".join(
                [f"• {i['agent']}：{i['reason']}" for i in issues]
            ))

        # 只在有問題時才推送完整報告
        if api_ok < api_total or issues:
            send("\n".join(status_lines))

        summary = f"API {api_ok}/{api_total} 正常｜失敗員工 {len(issues)} 個"
        needs_boss = len(issues) > 2 or api_ok < api_total - 1

        log_execution(AGENT_NAME, "成功", summary, 0, needs_boss)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, 0, needs_boss)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        raise

if __name__ == "__main__":
    run()
