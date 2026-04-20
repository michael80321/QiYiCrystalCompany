"""
客服接待員
執行頻率：每小時
工作：生成常見問題自動回覆模板、分類客服問題類型
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

AGENT_NAME = "客服接待員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的客服接待員，處理水晶電商客服問題。

品牌語調：溫暖、專業、有靈性感
市場：台灣（主）、香港、大陸

請生成今日客服 FAQ 自動回覆模板，涵蓋最常見的 10 個問題類型：

輸出 JSON（只輸出 JSON）：
{{
  "faq_templates": [
    {{
      "category": "退換貨",
      "question": "收到的水晶破損了怎麼辦？",
      "reply_tw": "台灣版回覆（溫暖語調）",
      "reply_hk": "香港版回覆",
      "reply_cn": "大陸版回覆",
      "escalate_to_human": false
    }}
  ],
  "escalation_keywords": ["法律", "詐騙", "嚴重破損", "全部退款"],
  "today_tips": "今日客服注意事項（如特殊節日、促銷期）"
}}

生成 10 個不同類別的 FAQ，類別包含：退換貨、物流、水晶保養、能量問題、付款、預購、批發、尺寸規格、真偽鑑別、促銷優惠。
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{"role": "user", "content": PROMPT}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        faq_count = len(data.get("faq_templates", []))
        summary = f"更新 {faq_count} 個 FAQ 模板｜{data.get('today_tips', '')}"

        log_execution(AGENT_NAME, "成功", summary, faq_count, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, faq_count, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
