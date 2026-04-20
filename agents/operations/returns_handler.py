"""
退換貨處理員
執行頻率：每日
工作：標準化退換貨流程、自動分類與回覆模板
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

AGENT_NAME = "退換貨處理員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的退換貨處理員。

品牌：高端水晶電商，台灣/香港/大陸市場
語調：溫暖、專業，即使處理退貨也要維護品牌形象

請生成完整的退換貨處理 SOP 和回覆模板：

輸出 JSON（只輸出 JSON）：
{{
  "return_policy": {{
    "days": 7,
    "conditions": ["商品未使用", "原包裝完整", "附購買憑證"],
    "exceptions": ["訂製商品", "已啟用水晶（能量開光）"]
  }},
  "categories": [
    {{
      "type": "破損到貨",
      "priority": "高",
      "sla_hours": 2,
      "reply_tw": "破損退換回覆（附照片索取話術）",
      "action": "立即補寄或全額退款"
    }},
    {{
      "type": "不符預期",
      "priority": "中",
      "sla_hours": 24,
      "reply_tw": "不符預期回覆（溫暖安撫+解釋天然水晶特性）",
      "action": "7天內退換"
    }},
    {{
      "type": "改變心意",
      "priority": "低",
      "sla_hours": 48,
      "reply_tw": "改變心意回覆（嘗試留客+說明政策）",
      "action": "依退貨政策處理"
    }}
  ],
  "compensation_guide": "補償建議（優惠券/折扣）",
  "escalation_rule": "需升級老闆處理的情況"
}}
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": PROMPT}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        cat_count = len(data.get("categories", []))
        summary = f"退換貨 SOP {cat_count} 類｜退貨期限 {data.get('return_policy', {}).get('days', 7)} 天"
        log_execution(AGENT_NAME, "成功", summary, cat_count, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, cat_count, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
