"""
品質把關員
執行頻率：內容上線前
工作：商品圖/文案上線前自動審核品質標準
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

AGENT_NAME = "品質把關員"
logger = get_logger(AGENT_NAME)

QUALITY_PROMPT = """你是騏藝逸品的品質把關員，審核即將上線的內容。

品牌規範：
- 語調：溫暖、專業、有靈性感
- 禁忌：醫療聲稱、保證效果、競品名稱、過度靈異
- 功效框架：「能量」「氣場」「象徵」

待審核內容：
{content}

請對以下面向評分（1-10）並給出具體改善建議：

輸出 JSON（只輸出 JSON）：
{{
  "overall_score": 8,
  "passed": true,
  "checks": [
    {{
      "item": "品牌語調一致性",
      "score": 9,
      "pass": true,
      "issue": "",
      "suggestion": ""
    }},
    {{
      "item": "禁忌詞檢查",
      "score": 10,
      "pass": true,
      "issue": "",
      "suggestion": ""
    }},
    {{
      "item": "三語用詞正確性",
      "score": 8,
      "pass": true,
      "issue": "",
      "suggestion": ""
    }},
    {{
      "item": "CTA 明確度",
      "score": 7,
      "pass": true,
      "issue": "缺少明確行動指引",
      "suggestion": "加入「立即收藏」或「點擊購買」"
    }}
  ],
  "must_fix": [],
  "nice_to_fix": ["建議改善項目"],
  "approved": true
}}
"""


def review_content(content: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": QUALITY_PROMPT.format(content=content)}]
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    try:
        # 讀取待審核隊列中「待審」的內容
        queue = sheets.get_all_records("審核隊列")
        pending = [r for r in queue if r.get("狀態") == "待審"]

        if not pending:
            logger.info("無待審核內容")
            sheets.update_agent_status(AGENT_NAME, "成功", "無待審核內容", 0, False)
            return

        reviewed = 0
        failed = 0
        for item in pending[:10]:  # 每次最多審核 10 件
            content = item.get("內容摘要", "")
            if not content:
                continue
            try:
                result = review_content(content)
                score = result.get("overall_score", 0)
                approved = result.get("approved", True)
                must_fix = result.get("must_fix", [])

                logger.info(f"  [{item.get('ID', '')}] 評分 {score}/10 {'✅' if approved else '❌'}")
                if must_fix:
                    logger.warning(f"  必修：{must_fix}")
                    failed += 1
                reviewed += 1
            except Exception as e:
                logger.warning(f"審核失敗：{e}")

        summary = f"審核 {reviewed} 件｜{failed} 件需修改"
        needs_boss = failed > 0
        log_execution(AGENT_NAME, "成功", summary, reviewed, needs_boss,
                      f"{failed} 件品質不達標" if needs_boss else "")
        sheets.update_agent_status(AGENT_NAME, "成功", summary, reviewed, needs_boss)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
