"""
智財保護員
執行頻率：每週
工作：掃描仿冒品、抄襲內容、數字人形象被盜用
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

AGENT_NAME = "智財保護員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的智財保護員。

品牌：騏藝逸品 / QiYi Crystal，高端水晶電商
保護範圍：品牌名稱、數字人形象、原創內容、商品照片

請生成本週智財保護檢查清單和應對策略：

輸出 JSON（只輸出 JSON）：
{{
  "check_list": [
    {{
      "item": "蝦皮仿冒店家掃描",
      "platform": "蝦皮",
      "keywords_to_monitor": ["騏藝逸品", "QiYi Crystal", "qi yi crystal"],
      "action_if_found": "截圖存證 → 向蝦皮舉報 → LINE 通知老闆"
    }},
    {{
      "item": "Instagram 帳號仿冒",
      "platform": "Instagram",
      "keywords_to_monitor": ["qiyicrystal", "骑艺逸品"],
      "action_if_found": "向 Meta 舉報並記錄"
    }},
    {{
      "item": "數字人形象盜用",
      "platform": "全平台",
      "keywords_to_monitor": ["數字人名稱"],
      "action_if_found": "法律信函準備 → 通知老闆"
    }}
  ],
  "legal_response_template": "侵權通知信模板（繁體中文）",
  "weekly_summary": "本週無發現侵權（初始狀態）",
  "needs_boss_review": false
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

        summary = data.get("weekly_summary", f"掃描 {len(data.get('check_list', []))} 個保護項目")
        needs_boss = data.get("needs_boss_review", False)

        log_execution(AGENT_NAME, "成功", summary, len(data.get("check_list", [])), needs_boss)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, len(data.get("check_list", [])), needs_boss)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
