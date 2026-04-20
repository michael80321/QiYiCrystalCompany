"""
數字人短影片生成員
執行頻率：審核通過後自動觸發
工作：HeyGen API 全自動：腳本→說話影片，三語並行
"""
import os, sys, json, time, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert, send

AGENT_NAME = "數字人短影片生成"
logger = get_logger(AGENT_NAME)

HEYGEN_API = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_API = "https://api.heygen.com/v1/video_status.get"

# config.yaml 設定的 Avatar ID（需在 HeyGen 後台確認）
AVATAR_ID = os.environ.get("HEYGEN_AVATAR_ID", "")
VOICE_ID_TW = os.environ.get("HEYGEN_VOICE_TW", "")
VOICE_ID_HK = os.environ.get("HEYGEN_VOICE_HK", "")
VOICE_ID_CN = os.environ.get("HEYGEN_VOICE_CN", "")


def generate_video(script: str, voice_id: str, language: str) -> str | None:
    key = os.environ.get("HEYGEN_API_KEY")
    if not key or not AVATAR_ID or not voice_id:
        logger.warning(f"HeyGen 設定不完整（{language}），跳過")
        return None

    headers = {"X-Api-Key": key, "Content-Type": "application/json"}
    payload = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": AVATAR_ID,
                "avatar_style": "normal",
            },
            "voice": {
                "type": "text",
                "input_text": script,
                "voice_id": voice_id,
                "speed": 1.0,
            },
        }],
        "dimension": {"width": 1080, "height": 1920},
        "aspect_ratio": "9:16",
    }

    try:
        resp = requests.post(HEYGEN_API, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            video_id = resp.json().get("data", {}).get("video_id")
            logger.info(f"  [{language}] 影片生成中，video_id={video_id}")
            return video_id
    except Exception as e:
        logger.error(f"HeyGen 呼叫失敗：{e}")
    return None


def poll_video_status(video_id: str, max_wait: int = 300) -> str | None:
    key = os.environ.get("HEYGEN_API_KEY")
    headers = {"X-Api-Key": key}
    elapsed = 0
    while elapsed < max_wait:
        try:
            resp = requests.get(f"{HEYGEN_STATUS_API}?video_id={video_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                status = data.get("status")
                if status == "completed":
                    return data.get("video_url")
                elif status == "failed":
                    logger.error(f"影片生成失敗：{data.get('error')}")
                    return None
        except Exception:
            pass
        time.sleep(15)
        elapsed += 15
    return None


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        # 讀取今日核准的影片腳本
        queue = sheets.get_all_records("審核隊列")
        approved_scripts = [
            r for r in queue
            if r.get("狀態") == "核准"
            and r.get("類型") == "影片腳本"
            and r.get("預定發布時間", "").startswith(today)
        ]

        if not approved_scripts:
            logger.info("今日無核准腳本，跳過")
            sheets.update_agent_status(AGENT_NAME, "成功", "無核准腳本", 0, False)
            return

        rows_written = 0
        for script_row in approved_scripts[:3]:  # 每日最多 3 支
            script_text = script_row.get("內容摘要", "")
            # 依語言選聲音
            lang = script_row.get("語言", "TW")
            voice_map = {"TW": VOICE_ID_TW, "HK": VOICE_ID_HK, "CN": VOICE_ID_CN}
            voice_id = voice_map.get(lang, VOICE_ID_TW)

            video_id = generate_video(script_text, voice_id, lang)
            if video_id:
                video_url = poll_video_status(video_id)
                if video_url:
                    send(f"🎬 <b>影片生成完成</b>\n語言：{lang}\n{video_url}")
                    rows_written += 1

        summary = f"生成 {rows_written} 支數字人影片"
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
