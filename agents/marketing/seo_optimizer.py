"""
SEO 優化員
執行頻率：每週一次（週二）
工作：水晶關鍵字研究、商品頁 meta description 優化建議
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

AGENT_NAME = "SEO優化員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的 SEO 優化員，專注台灣繁體中文電商 SEO。

今天日期：{date}
平台：蝦皮台灣、品牌官網

請提供：
1. 高搜尋量水晶關鍵字分析（台灣市場）
2. 5 個主要商品的 meta description 優化範本
3. 蝦皮商品標題優化建議

輸出 JSON（只輸出 JSON）：
{{
  "report_date": "{date}",
  "top_keywords": [
    {{
      "keyword": "水晶手鍊",
      "estimated_monthly_search": 12000,
      "competition": "高/中/低",
      "opportunity_score": 75,
      "suggested_content": "內容建議"
    }}
  ],
  "meta_descriptions": [
    {{
      "product": "白水晶柱",
      "current_issue": "原始描述問題",
      "optimized": "優化後 meta description（120字內）",
      "focus_keyword": "白水晶"
    }}
  ],
  "shopee_title_tips": ["蝦皮標題優化要點1", "要點2"],
  "priority_action": "本週最優先的 SEO 行動",
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

        kw_count = len(data.get("top_keywords", []))
        summary = f"分析 {kw_count} 個關鍵字｜{data.get('priority_action', '')}"

        log_execution(AGENT_NAME, "成功", summary, kw_count, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, kw_count, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
