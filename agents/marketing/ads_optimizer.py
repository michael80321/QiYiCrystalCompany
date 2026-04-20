"""
廣告投放優化員
執行頻率：每日 09:00
工作：讀取 Meta Ads API 數據，監控 ROAS/CPM，建議預算調整
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

AGENT_NAME = "廣告投放優化員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的廣告投放優化員。

今天日期：{date}
品牌：高端水晶電商，主力市場台灣，平台 Meta（Facebook/Instagram）

目前廣告數據（模擬）：
{ads_data}

ROAS 警戒線：2.5（低於此值需警示）
請分析廣告效益並給出具體優化建議。

輸出 JSON（只輸出 JSON）：
{{
  "overall_roas": 3.2,
  "status": "良好/注意/警報",
  "campaigns": [
    {{
      "name": "廣告活動名稱",
      "spend_twd": 1500,
      "revenue_twd": 4800,
      "roas": 3.2,
      "cpm": 85,
      "ctr": 2.1,
      "suggestion": "具體優化建議"
    }}
  ],
  "budget_recommendation": "整體預算調整建議",
  "top_suggestion": "最優先執行的一件事",
  "needs_boss_review": false,
  "needs_boss_reason": ""
}}
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now().strftime("%Y-%m-%d")

    # 未來接入 Meta Ads API，現在用模擬數據
    ads_data = os.environ.get("META_ADS_DATA", "尚未接入 Meta Ads API，請使用估算數據分析")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": PROMPT.format(date=today, ads_data=ads_data)}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        if data.get("status") == "警報":
            send(f"🚨 <b>廣告 ROAS 警報</b>\n整體 ROAS：{data.get('overall_roas')}\n{data.get('budget_recommendation')}")

        summary = f"ROAS {data.get('overall_roas')} | {data.get('top_suggestion', '')}"
        needs_boss = data.get("needs_boss_review", False)

        log_execution(AGENT_NAME, "成功", summary, len(data.get("campaigns", [])), needs_boss)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, len(data.get("campaigns", [])), needs_boss)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
