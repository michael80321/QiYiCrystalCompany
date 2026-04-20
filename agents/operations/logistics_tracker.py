"""
物流售後員
執行頻率：每 2 小時
工作：追蹤出貨狀態、延誤預警、自動發出貨通知
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

AGENT_NAME = "物流售後員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的物流售後員。

今天日期：{date}
請生成以下物流相關的標準回覆模板和處理流程，供客服使用：

1. 出貨通知訊息（台灣黑貓/新竹）
2. 延誤安撫訊息
3. 包裹遺失處理流程
4. 到貨確認感謝訊息

輸出 JSON（只輸出 JSON）：
{{
  "templates": {{
    "shipping_notice": {{
      "tw": "出貨通知（含運單號位置說明）",
      "hk": "香港SF速遞版本",
      "cn": "大陸快遞版本"
    }},
    "delay_apology": {{
      "tw": "延誤道歉（溫暖語調）",
      "hk": "",
      "cn": ""
    }},
    "loss_handling": "遺失處理標準流程（條列式）",
    "arrival_thanks": {{
      "tw": "到貨感謝+開箱拍照邀請",
      "hk": "",
      "cn": ""
    }}
  }},
  "delay_threshold_days": 5,
  "auto_followup_day": 7
}}
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": PROMPT.format(date=today)}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        summary = f"更新物流回覆模板｜延誤警戒 {data.get('delay_threshold_days', 5)} 天"
        log_execution(AGENT_NAME, "成功", summary, 4, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, 4, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
