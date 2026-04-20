"""
競品定價策略員
執行頻率：每日 07:00
工作：分析蝦皮、露天競品售價，建議調整方向
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

AGENT_NAME = "競品定價策略員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的競品定價策略員。

今天日期：{date}
品牌定位：高端水晶電商，台灣市場主力平台蝦皮

請根據你對台灣水晶電商市場的知識，分析以下常見水晶品項的市場定價範圍，
並針對騏藝逸品「高端、療癒、東方美學」定位給出定價建議。

分析品項：白水晶柱、紫水晶簇、粉晶球、黑碧璽手鍊、拉長石、月光石、
         藍晶石、東菱玉、虎眼石手鍊、橄欖石

輸出 JSON（只輸出 JSON）：
{{
  "report_date": "{date}",
  "pricing_analysis": [
    {{
      "product": "白水晶柱",
      "market_low_twd": 299,
      "market_high_twd": 1200,
      "market_avg_twd": 680,
      "qiyi_suggested_price": 880,
      "positioning": "中高端",
      "pricing_rationale": "定價理由",
      "competitor_notes": "競品觀察"
    }}
  ],
  "price_adjustment_alerts": [],
  "summary": "本日定價建議摘要",
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
        for item in data.get("pricing_analysis", []):
            sheets.append_row("情報表", [
                today, "定價分析", "蝦皮/露天",
                item.get("product", ""), "",
                "", "", item.get("pricing_rationale", ""),
                item.get("positioning", ""),
                item.get("qiyi_suggested_price", ""),
            ])
            rows_written += 1

        summary = data.get("summary", f"分析 {rows_written} 個品項定價")
        needs_boss = data.get("needs_boss_review", False)

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
