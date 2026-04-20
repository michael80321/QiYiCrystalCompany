"""
KOL 合作追蹤員
執行頻率：每日 10:00
工作：分析潛在 KOL 合作名單，整理 IG/TikTok 水晶相關網紅
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

AGENT_NAME = "KOL合作追蹤員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的 KOL 合作追蹤員。

今天日期：{date}
品牌定位：高端水晶電商，目標客群 25-45 歲女性

請根據你的知識，推薦適合騏藝逸品合作的 KOL 類型與策略：

1. 台灣 IG/TikTok 水晶/靈性/星座類型網紅特徵
2. 香港同類網紅特徵
3. 合作方式建議（試用品合作、分潤、買斷等）
4. 評估指標建議

輸出 JSON（只輸出 JSON）：
{{
  "report_date": "{date}",
  "kol_criteria": {{
    "ideal_followers": "1萬-50萬",
    "engagement_rate_min": 3.0,
    "content_themes": ["水晶", "靈性", "星座", "能量療癒"],
    "avoid": ["純商業帳號", "互刷帳號"]
  }},
  "tw_recommendations": [
    {{
      "type": "KOL 類型描述",
      "platform": "Instagram",
      "follower_range": "5萬-20萬",
      "collaboration_type": "試用品合作",
      "estimated_cost_twd": 5000,
      "expected_reach": "3萬人"
    }}
  ],
  "hk_recommendations": [],
  "outreach_template_tw": "合作邀約 DM 模板（台灣版）",
  "monthly_budget_suggestion_twd": 30000,
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

        tw_count = len(data.get("tw_recommendations", []))
        hk_count = len(data.get("hk_recommendations", []))
        summary = f"台灣 {tw_count} 個 KOL 建議｜香港 {hk_count} 個"

        log_execution(AGENT_NAME, "成功", summary, tw_count + hk_count, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, tw_count + hk_count, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
