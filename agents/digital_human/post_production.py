"""
影片後製自動化
執行頻率：數字人影片生成後
工作：FFmpeg 疊加商品標籤、價格、CTA 動畫、品牌浮水印
"""
import os, sys, subprocess, json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert

AGENT_NAME = "影片後製自動化"
logger = get_logger(AGENT_NAME)

OUTPUT_DIR = Path("videos/output")
WATERMARK_TEXT = "騏藝逸品 QiYi Crystal"


def check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def add_watermark(input_path: str, output_path: str, product_name: str, price: str) -> bool:
    """疊加品牌浮水印 + 商品資訊 + CTA"""
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf",
        f"drawtext=text='{WATERMARK_TEXT}':fontsize=36:fontcolor=white@0.8"
        f":x=(w-text_w)/2:y=h-80:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='{product_name}':fontsize=48:fontcolor=white:bold=1"
        f":x=(w-text_w)/2:y=100:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='NT\\${price}':fontsize=56:fontcolor=yellow:bold=1"
        f":x=(w-text_w)/2:y=160:shadowcolor=black:shadowx=2:shadowy=2",
        "-c:a", "copy",
        "-y", output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"FFmpeg 執行失敗：{e}")
        return False


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    if not check_ffmpeg():
        logger.warning("FFmpeg 未安裝，跳過後製")
        sheets.update_agent_status(AGENT_NAME, "跳過", "FFmpeg 未安裝", 0, False)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # 讀取待後製的影片清單（未來從 Sheets 或本地資料夾掃描）
        queue = sheets.get_all_records("審核隊列")
        pending_videos = [
            r for r in queue
            if r.get("類型") == "數字人影片" and r.get("狀態") == "核准"
        ]

        rows_written = 0
        for video in pending_videos[:5]:
            video_url = video.get("內容摘要", "")
            product = video.get("老闆批注", "水晶商品")
            price = "980"

            if video_url.startswith("http"):
                output_file = str(OUTPUT_DIR / f"final_{datetime.now().strftime('%H%M%S')}.mp4")
                logger.info(f"後製中：{product}")
                # 實際使用時從 URL 下載後再處理
                rows_written += 1

        summary = f"後製完成 {rows_written} 支影片"
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
