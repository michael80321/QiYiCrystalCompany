"""
圖像產出員
執行頻率：每日 05:30
工作：Flux 2 批次生成商品情境圖，結果寫入審核隊列
"""
import os, sys, json, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert

AGENT_NAME = "圖像產出員"
logger = get_logger(AGENT_NAME)

FAL_API_URL = "https://fal.run/fal-ai/flux-pro/v1.1"

DAILY_PROMPTS = [
    {
        "crystal": "白水晶柱",
        "prompt": "Clear quartz crystal tower on marble surface, soft natural lighting, luxury crystal shop aesthetic, minimalist background, 8K photorealistic, product photography",
        "style": "商品主圖",
    },
    {
        "crystal": "紫水晶簇",
        "prompt": "Purple amethyst cluster geode, mystical purple and violet tones, spiritual healing energy, dark moody background with soft rim lighting, high-end jewelry photography style",
        "style": "氛圍圖",
    },
    {
        "crystal": "粉晶球",
        "prompt": "Rose quartz sphere on wooden tray with dried flowers, warm golden hour light, feminine spiritual aesthetic, soft bokeh background, lifestyle product shot",
        "style": "情境圖",
    },
]


def generate_image(prompt: str) -> str | None:
    fal_key = os.environ.get("FAL_API_KEY") or os.environ.get("FLUX_KEY")
    if not fal_key:
        logger.warning("FAL_API_KEY 未設定，跳過圖像生成")
        return None

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "image_size": "portrait_4_3",
        "num_inference_steps": 28,
        "num_images": 1,
    }
    try:
        resp = requests.post(FAL_API_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("images", [{}])[0].get("url")
    except Exception as e:
        logger.error(f"圖像生成失敗：{e}")
    return None


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        rows_written = 0
        for i, item in enumerate(DAILY_PROMPTS, start=1):
            post_id = f"{today.replace('-','')}-IMG{i:03d}"
            image_url = generate_image(item["prompt"])

            summary = f"{item['crystal']} {item['style']}"
            if image_url:
                summary += f" | {image_url[:60]}..."
            else:
                summary += " | 待人工生成（未設定 Flux API）"

            sheets.append_row("審核隊列", [
                post_id, "商品圖片", summary, "TW", "通用", today, "待審", "",
            ])
            rows_written += 1
            logger.info(f"  {item['crystal']}：{'✅' if image_url else '⏳'}")

        summary = f"產出 {rows_written} 張商品情境圖"
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
