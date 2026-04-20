"""
行銷企劃員
執行頻率：每日 08:00（審核通過後）
工作：將核准內容推入 Buffer 排程，自動在指定時間發布
"""
import os, sys, json, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert, send

AGENT_NAME = "行銷企劃員"
logger = get_logger(AGENT_NAME)

BUFFER_API = "https://api.bufferapp.com/1/updates/create.json"

PLATFORM_PROFILE_MAP = {
    "Instagram": os.environ.get("BUFFER_IG_PROFILE_ID", ""),
    "Facebook":  os.environ.get("BUFFER_FB_PROFILE_ID", ""),
    "TikTok":    os.environ.get("BUFFER_TT_PROFILE_ID", ""),
}


def push_to_buffer(content: str, platform: str, scheduled_at: str) -> bool:
    token = os.environ.get("BUFFER_TOKEN")
    profile_id = PLATFORM_PROFILE_MAP.get(platform)
    if not token or not profile_id:
        logger.warning(f"Buffer {platform} 未設定，跳過排程")
        return False

    try:
        # 轉換時間格式為 Unix timestamp
        dt = datetime.strptime(scheduled_at, "%Y-%m-%d %H:%M")
        timestamp = int(dt.timestamp())

        resp = requests.post(BUFFER_API, data={
            "access_token": token,
            "profile_ids[]": profile_id,
            "text": content,
            "scheduled_at": timestamp,
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Buffer 推送失敗：{e}")
        return False


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        queue = sheets.get_all_records("審核隊列")
        approved = [
            r for r in queue
            if r.get("狀態") == "核准"
            and r.get("類型") in ["IG貼文", "蝦皮貼文", "影片腳本"]
            and r.get("預定發布時間", "").startswith(today)
        ]

        rows_written = 0
        for item in approved:
            platform = item.get("平台", "Instagram")
            content = item.get("內容摘要", "")
            scheduled = item.get("預定發布時間", f"{today} 18:00")

            if push_to_buffer(content, platform, scheduled):
                logger.info(f"  ✅ {platform} 排程成功：{scheduled}")
                rows_written += 1
            else:
                logger.warning(f"  ⚠️ {platform} 排程跳過（Buffer 未設定）")

        summary = f"排程 {rows_written} 篇內容到 Buffer｜共 {len(approved)} 篇核准"
        log_execution(AGENT_NAME, "成功", summary, rows_written, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, rows_written, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
