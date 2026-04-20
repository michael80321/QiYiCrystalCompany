"""
社群自動排程發文員
執行頻率：每日 09:00
工作：將審核通過的內容自動發佈到 Instagram / Facebook
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

AGENT_NAME = "社群自動排程發文員"
logger = get_logger(AGENT_NAME)

# Meta Graph API
GRAPH_API = "https://graph.facebook.com/v19.0"
PAGE_ID = os.environ.get("META_PAGE_ID", "")
IG_ACCOUNT_ID = os.environ.get("META_IG_ACCOUNT_ID", "")
ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN", "")

# Threads API
THREADS_API = "https://graph.threads.net/v1.0"
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")
THREADS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")


def post_to_instagram(caption: str, image_url: str = None) -> str | None:
    """發佈到 Instagram（需要圖片 URL，或純文字限動）"""
    if not IG_ACCOUNT_ID or not ACCESS_TOKEN:
        logger.warning("META_IG_ACCOUNT_ID 或 META_PAGE_ACCESS_TOKEN 未設定")
        return None

    try:
        if image_url:
            # Step 1: 建立 media container
            container_resp = requests.post(
                f"{GRAPH_API}/{IG_ACCOUNT_ID}/media",
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": ACCESS_TOKEN,
                },
                timeout=30,
            )
            if container_resp.status_code != 200:
                logger.error(f"IG container 失敗：{container_resp.text[:200]}")
                return None
            container_id = container_resp.json().get("id")

            # Step 2: 發佈
            publish_resp = requests.post(
                f"{GRAPH_API}/{IG_ACCOUNT_ID}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": ACCESS_TOKEN,
                },
                timeout=30,
            )
            if publish_resp.status_code == 200:
                post_id = publish_resp.json().get("id")
                logger.info(f"  IG 發佈成功：{post_id}")
                return post_id
            else:
                logger.error(f"IG 發佈失敗：{publish_resp.text[:200]}")
        else:
            logger.warning("IG 需要圖片 URL，跳過純文字發佈")
    except Exception as e:
        logger.error(f"IG 發佈錯誤：{e}")
    return None


def post_to_facebook(message: str, image_url: str = None) -> str | None:
    """發佈到 Facebook 粉絲專頁"""
    if not PAGE_ID or not ACCESS_TOKEN:
        logger.warning("META_PAGE_ID 或 META_PAGE_ACCESS_TOKEN 未設定")
        return None

    try:
        if image_url:
            endpoint = f"{GRAPH_API}/{PAGE_ID}/photos"
            params = {"url": image_url, "caption": message, "access_token": ACCESS_TOKEN}
        else:
            endpoint = f"{GRAPH_API}/{PAGE_ID}/feed"
            params = {"message": message, "access_token": ACCESS_TOKEN}

        resp = requests.post(endpoint, params=params, timeout=30)
        if resp.status_code == 200:
            post_id = resp.json().get("id") or resp.json().get("post_id")
            logger.info(f"  FB 發佈成功：{post_id}")
            return post_id
        else:
            logger.error(f"FB 發佈失敗：{resp.text[:200]}")
    except Exception as e:
        logger.error(f"FB 發佈錯誤：{e}")
    return None


def post_to_threads(text: str) -> str | None:
    """發佈純文字到 Threads"""
    if not THREADS_USER_ID or not THREADS_TOKEN:
        logger.warning("THREADS_USER_ID 或 THREADS_ACCESS_TOKEN 未設定，跳過 Threads")
        return None

    try:
        # Step 1: 建立 container
        container_resp = requests.post(
            f"{THREADS_API}/{THREADS_USER_ID}/threads",
            params={
                "media_type": "TEXT",
                "text": text,
                "access_token": THREADS_TOKEN,
            },
            timeout=30,
        )
        if container_resp.status_code != 200:
            logger.error(f"Threads container 失敗：{container_resp.text[:200]}")
            return None
        container_id = container_resp.json().get("id")

        # Step 2: 發佈
        publish_resp = requests.post(
            f"{THREADS_API}/{THREADS_USER_ID}/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": THREADS_TOKEN,
            },
            timeout=30,
        )
        if publish_resp.status_code == 200:
            post_id = publish_resp.json().get("id")
            logger.info(f"  Threads 發佈成功：{post_id}")
            return post_id
        else:
            logger.error(f"Threads 發佈失敗：{publish_resp.text[:200]}")
    except Exception as e:
        logger.error(f"Threads 發佈錯誤：{e}")
    return None


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        queue = sheets.get_all_records("審核隊列")
        # 找今日核准且尚未發佈的內容
        to_publish = [
            r for r in queue
            if r.get("狀態") == "核准"
            and r.get("預定發布時間", "").startswith(today)
            and r.get("類型") in ("貼文", "商品圖片", "能量文案")
        ]

        if not to_publish:
            logger.info("今日無待發佈內容")
            sheets.update_agent_status(AGENT_NAME, "成功", "無待發佈內容", 0, False)
            return

        published = 0
        failed = 0
        for item in to_publish[:5]:  # 每日最多 5 則
            content = item.get("內容摘要", "")
            image_url = item.get("圖片網址", "") or None
            post_id_ig = None
            post_id_fb = None
            post_id_threads = None

            # Instagram
            post_id_ig = post_to_instagram(content, image_url)
            # Facebook
            post_id_fb = post_to_facebook(content, image_url)
            # Threads（純文字）
            post_id_threads = post_to_threads(content)

            if post_id_ig or post_id_fb or post_id_threads:
                published += 1
                logger.info(f"  [{item.get('ID')}] 發佈完成 IG={post_id_ig} FB={post_id_fb} Threads={post_id_threads}")
            else:
                failed += 1
                logger.warning(f"  [{item.get('ID')}] 發佈失敗")

        summary = f"發佈 {published} 則｜失敗 {failed} 則"
        needs_boss = failed > 0
        log_execution(AGENT_NAME, "成功", summary, published, needs_boss,
                      f"{failed} 則發佈失敗" if needs_boss else "")
        sheets.update_agent_status(AGENT_NAME, "成功", summary, published, needs_boss)

        if published > 0:
            send(f"📱 <b>社群發文完成</b>\n今日發佈 {published} 則內容")

        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise


if __name__ == "__main__":
    run()
