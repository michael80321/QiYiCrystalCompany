"""
亞太市場情報員
執行頻率：每 6 小時
工作：偵測台港陸東南亞水晶市場爆款訊號，寫入 Sheets，異常時推 Telegram
"""
import os
import sys
import yaml
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

import anthropic
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert, send_trend_alert

AGENT_NAME = "亞太市場情報員"
logger = get_logger(AGENT_NAME)


def load_config() -> dict:
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_enabled() -> bool:
    try:
        status = sheets.read_cell("員工開關", AGENT_NAME, "狀態")
        if status and status != "開啟":
            logger.info("員工已暫停，跳過執行")
            return False
    except Exception:
        pass  # Sheets 不可用時預設執行
    return True


INTELLIGENCE_PROMPT = """你是騏藝逸品的亞太市場情報員，專門監控台灣、香港、大陸、東南亞的水晶市場動態。

今天日期：{date}
品牌定位：高端水晶電商，目標客群 25-45 歲女性，關注能量療癒、風水、星座。

請根據你的知識，針對以下四個市場分析當前水晶市場趨勢：
1. 台灣（蝦皮、Instagram、Threads）
2. 香港（Instagram、Facebook）
3. 大陸（小紅書、抖音）
4. 東南亞（Shopee、TikTok）

請輸出 JSON 格式（只輸出 JSON，不要其他文字）：
{{
  "report_date": "{date}",
  "markets": [
    {{
      "market": "台灣",
      "platform": "蝦皮/IG",
      "trending_items": ["商品1", "商品2", "商品3"],
      "hot_keywords": ["關鍵字1", "關鍵字2"],
      "competitor_moves": "友商動態描述",
      "opportunity": "建議行動",
      "alert_level": "正常/注意/警報",
      "alert_reason": ""
    }}
  ],
  "top_opportunity": "今日最大商機一句話",
  "needs_boss_review": false,
  "needs_boss_reason": ""
}}

四個市場都要填入，alert_level 只在發現爆款或競品大動作時填「警報」。"""


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    if not check_enabled():
        return

    config = load_config()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        logger.info("呼叫 Claude API 分析市場情報...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": INTELLIGENCE_PROMPT.format(date=today)
            }]
        )

        import json
        raw = response.usage
        logger.info(f"Token 使用：input={raw.input_tokens}, output={raw.output_tokens}")

        content = response.content[0].text.strip()
        # 清除可能的 markdown code block
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        # 寫入 Google Sheets
        rows_written = 0
        alerts = []
        for market_data in data.get("markets", []):
            row = [
                today,
                market_data.get("market", ""),
                market_data.get("platform", ""),
                ", ".join(market_data.get("trending_items", [])),
                ", ".join(market_data.get("hot_keywords", [])),
                market_data.get("competitor_moves", ""),
                market_data.get("opportunity", ""),
                market_data.get("alert_level", "正常"),
                market_data.get("alert_reason", ""),
            ]
            sheets.append_row("情報表", row)
            rows_written += 1

            if market_data.get("alert_level") == "警報":
                alerts.append(market_data)

        # 發送爆款警報
        for alert in alerts:
            send_trend_alert(
                item=", ".join(alert.get("trending_items", [])[:2]),
                multiplier=3.0,
                market=alert.get("market", ""),
            )

        top_opportunity = data.get("top_opportunity", "")
        needs_boss = data.get("needs_boss_review", False)
        needs_boss_reason = data.get("needs_boss_reason", "")

        elapsed = (datetime.now() - start_time).seconds
        summary = f"分析 {rows_written} 個市場｜{top_opportunity}"

        log_execution(AGENT_NAME, "成功", summary, rows_written, needs_boss, needs_boss_reason)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, rows_written, needs_boss, needs_boss_reason)

        logger.info(f"=== 執行完成，耗時 {elapsed} 秒 ===")
        logger.info(f"今日最大商機：{top_opportunity}")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, f"執行失敗：{e}")
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise


if __name__ == "__main__":
    run()
