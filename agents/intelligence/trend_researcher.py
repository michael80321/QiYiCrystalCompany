"""
選品趨勢研究員
執行頻率：每日 06:00
工作：分析 TikTok、Pinterest 爆紅水晶關鍵字，建議備貨品項
"""
import os, sys, json, yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import anthropic
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert

AGENT_NAME = "選品趨勢研究員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的選品趨勢研究員，專門分析水晶相關的社群爆款趨勢。

今天日期：{date}
當前節氣/節日背景：請根據日期判斷

請分析以下平台當前最熱門的水晶趨勢（基於你的訓練知識）：
- TikTok / 抖音
- Pinterest
- Instagram Reels
- 小紅書

輸出 JSON（只輸出 JSON）：
{{
  "report_date": "{date}",
  "trending_crystals": [
    {{
      "name": "水晶名稱",
      "name_en": "英文名",
      "trend_score": 85,
      "platforms": ["TikTok", "Pinterest"],
      "reason": "爆紅原因",
      "target_market": ["TW", "HK"],
      "suggested_price_twd": 980,
      "stock_priority": "高/中/低"
    }}
  ],
  "trending_keywords": ["關鍵字1", "關鍵字2", "關鍵字3"],
  "seasonal_opportunity": "本週節氣/節日機會描述",
  "top_recommendation": "最建議備貨的品項一句話",
  "needs_boss_review": false,
  "needs_boss_reason": ""
}}
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": PROMPT.format(date=today)}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        rows_written = 0
        for item in data.get("trending_crystals", []):
            sheets.append_row("情報表", [
                today, "趨勢研究", "TikTok/Pinterest",
                item.get("name", ""), item.get("name_en", ""),
                item.get("trend_score", 0),
                ", ".join(item.get("platforms", [])),
                item.get("reason", ""),
                item.get("stock_priority", ""),
                item.get("suggested_price_twd", ""),
            ])
            rows_written += 1

        top = data.get("top_recommendation", "")
        needs_boss = data.get("needs_boss_review", False)
        summary = f"發現 {rows_written} 個趨勢品項｜{top}"

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
