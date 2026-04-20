"""
會員經營員
執行頻率：每日
工作：30 天未回購喚醒訊息、VIP 分級維繫、生日觸發優惠
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

AGENT_NAME = "會員經營員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的會員經營員，負責設計會員溝通策略。

今天日期：{date}
品牌：高端水晶電商，語調溫暖靈性

請生成以下會員溝通模板：
1. 30 天未回購喚醒訊息（三語版本）
2. VIP 客戶專屬感謝訊息（三語版本）
3. 生日祝福 + 優惠訊息（三語版本）
4. 本月會員經營策略建議

輸出 JSON（只輸出 JSON）：
{{
  "report_date": "{date}",
  "reactivation_messages": {{
    "tw": "台灣30天喚醒訊息",
    "hk": "香港30天喚醒訊息",
    "cn": "大陸30天喚醒訊息"
  }},
  "vip_messages": {{
    "tw": "台灣VIP感謝訊息",
    "hk": "香港VIP感謝訊息",
    "cn": "大陸VIP感謝訊息"
  }},
  "birthday_messages": {{
    "tw": "台灣生日祝福+優惠",
    "hk": "香港生日祝福+優惠",
    "cn": "大陸生日祝福+優惠"
  }},
  "monthly_strategy": "本月會員經營重點建議",
  "vip_threshold_twd": 3000,
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

        summary = f"更新三語會員訊息模板｜{data.get('monthly_strategy', '')[:30]}"
        log_execution(AGENT_NAME, "成功", summary, 3, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, 3, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
