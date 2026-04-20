"""
跨境稅務合規員
執行頻率：每週
工作：台港陸各地稅率、申報規則、平台費率異動監控
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
from shared.line_notify import send_alert, send

AGENT_NAME = "跨境稅務合規員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的跨境稅務合規員。

今天日期：{date}
品牌：台灣水晶電商，跨境銷售台灣/香港/大陸/東南亞

請提供當前跨境電商稅務合規重點：

輸出 JSON（只輸出 JSON）：
{{
  "report_date": "{date}",
  "markets": [
    {{
      "market": "台灣",
      "vat_rate": "5%",
      "threshold_twd": 480000,
      "platform_fee": "蝦皮 2-5%",
      "key_rules": ["年營業額超過48萬需申報", "電商發票規定"],
      "action_items": ["本月注意事項"],
      "risk_level": "低/中/高"
    }},
    {{
      "market": "香港",
      "vat_rate": "0%（免稅）",
      "threshold_twd": 0,
      "platform_fee": "Shopee HK 費率",
      "key_rules": ["香港無增值稅", "進口申報規定"],
      "action_items": [],
      "risk_level": "低"
    }},
    {{
      "market": "大陸",
      "vat_rate": "跨境電商綜合稅",
      "threshold_twd": 5000,
      "platform_fee": "平台費率",
      "key_rules": ["AI人臉法規確認", "跨境電商進口稅"],
      "action_items": ["大陸市場進入前需確認AI人臉合規"],
      "risk_level": "高"
    }}
  ],
  "urgent_alerts": [],
  "monthly_deadline": "本月申報截止日（如有）",
  "needs_boss_review": false
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

        high_risk = [m for m in data.get("markets", []) if m.get("risk_level") == "高"]
        if high_risk:
            markets = "、".join([m["market"] for m in high_risk])
            send(f"⚠️ <b>稅務合規提醒</b>\n{markets} 市場有高風險項目需注意")

        urgent = data.get("urgent_alerts", [])
        needs_boss = bool(urgent) or data.get("needs_boss_review", False)
        summary = f"監控 {len(data.get('markets', []))} 個市場稅務｜{data.get('monthly_deadline', '本月無截止')}"

        log_execution(AGENT_NAME, "成功", summary, len(data.get("markets", [])), needs_boss)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, len(data.get("markets", [])), needs_boss)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
