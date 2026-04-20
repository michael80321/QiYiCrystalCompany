"""
影片腳本員
執行頻率：每日 06:00
工作：生成 Reels/TikTok/蝦皮帶貨腳本，三語版本，每日 3 支
"""
import os, sys, json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import anthropic
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert

AGENT_NAME = "影片腳本員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的影片腳本員，專門撰寫數字人帶貨短影片腳本。

今天日期：{date}
數字人設定：亞洲女性，28-35 歲，優雅靈性氣質，代表騏藝逸品品牌。
影片長度：60 秒以內（約 150-180 字）

請生成 3 支不同主題的短影片腳本，每支需要台灣國語版本。
腳本格式：開場鉤子（5秒）→ 商品介紹（30秒）→ 能量故事（15秒）→ CTA（10秒）

禁忌：不使用醫療聲稱、不保證效果。

輸出 JSON（只輸出 JSON）：
{{
  "scripts": [
    {{
      "title": "腳本標題",
      "crystal": "主打水晶",
      "platform": "Instagram Reels",
      "language": "TW",
      "duration_sec": 60,
      "hook": "開場鉤子台詞（吸引停留）",
      "body": "主體台詞（商品介紹+能量故事）",
      "cta": "結尾 CTA 台詞",
      "full_script": "完整腳本（hook+body+cta）",
      "visual_notes": "畫面說明（給後製參考）",
      "hashtags": "#水晶 #能量水晶 #騏藝逸品"
    }}
  ],
  "needs_boss_review": false,
  "needs_boss_reason": ""
}}

生成 3 支，涵蓋不同水晶、不同主題（療癒/風水/星座）。
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        logger.info("生成今日影片腳本...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": PROMPT.format(date=today)}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        rows_written = 0
        for i, script in enumerate(data.get("scripts", []), start=1):
            post_id = f"{today.replace('-','')}-V{i:03d}"
            sheets.append_row("審核隊列", [
                post_id,
                "影片腳本",
                f"{script.get('title','')}｜{script.get('hook','')}",
                script.get("language", "TW"),
                script.get("platform", ""),
                f"{today} 07:00",
                "待審",
                "",
            ])
            rows_written += 1

        needs_boss = data.get("needs_boss_review", False)
        summary = f"產出 {rows_written} 支腳本"

        log_execution(AGENT_NAME, "成功", summary, rows_written, needs_boss)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, rows_written, needs_boss)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
