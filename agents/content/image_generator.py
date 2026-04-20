"""
圖像產出員
執行頻率：每日 05:30
工作：Gemini Imagen 3 批次生成商品情境圖，結果寫入審核隊列
"""
import os, sys
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

DAILY_PROMPTS = [
    {
        "crystal": "白水晶柱",
        "prompt": "Clear quartz crystal tower on white marble surface, soft natural lighting, luxury crystal shop aesthetic, minimalist background, 8K photorealistic, product photography, no text",
        "style": "商品主圖",
    },
    {
        "crystal": "紫水晶簇",
        "prompt": "Purple amethyst cluster geode, mystical violet tones, spiritual healing energy, dark moody background with soft rim lighting, high-end jewelry photography style, no text",
        "style": "氛圍圖",
    },
    {
        "crystal": "粉晶球",
        "prompt": "Rose quartz sphere on wooden tray with dried flowers, warm golden hour light, feminine spiritual aesthetic, soft bokeh background, lifestyle product shot, no text",
        "style": "情境圖",
    },
    {
        "crystal": "黑碧璽手鍊",
        "prompt": "Black tourmaline bracelet on dark slate stone, protection crystal energy aesthetic, dramatic studio lighting, luxury jewelry photography, no text",
        "style": "商品主圖",
    },
]

OUTPUT_DIR = Path("images/output")


def generate_image(prompt: str, crystal: str) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY 未設定")
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        result = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="3:4",
            safety_filter_level="block_few",
            person_generation="dont_allow",
        )
        if result.images:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{crystal}.png"
            filepath = OUTPUT_DIR / filename
            result.images[0].save(str(filepath))
            logger.info(f"  圖片儲存：{filepath}")
            return str(filepath)
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
            logger.info(f"生成 {item['crystal']} {item['style']}...")
            filepath = generate_image(item["prompt"], item["crystal"])

            post_id = f"{today.replace('-','')}-IMG{i:03d}"
            summary = f"{item['crystal']} {item['style']}"
            if filepath:
                summary += f" ✅ 已存至 {filepath}"
            else:
                summary += " ⏳ 待人工生成（未設定 Gemini API）"

            sheets.append_row("審核隊列", [
                post_id, "商品圖片", summary, "TW", "通用", today, "待審", "",
            ])
            rows_written += 1

        summary_msg = f"產出 {rows_written} 張商品情境圖（Gemini Imagen 3）"
        log_execution(AGENT_NAME, "成功", summary_msg, rows_written, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary_msg, rows_written, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
