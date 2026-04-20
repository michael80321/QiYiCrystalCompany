"""
能量內容專員
執行頻率：每日 05:00
工作：生成星座水晶搭配、節氣貼文、滿月水逆主題，三語版本，寫入審核隊列
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

AGENT_NAME = "能量內容專員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的能量內容專員。品牌定位：高端水晶電商，溫暖專業有靈性感，目標客群 25-45 歲女性。

今天日期：{date}
請判斷當前節氣、星座運勢主題、是否接近滿月或特殊天象。

生成今日社群貼文內容，需要三語版本（台灣國語、香港粵語、大陸普通話）。
每個版本需符合各市場用語習慣。

禁忌：不使用醫療聲稱、不保證效果、不提競品、不過度靈異。
功效描述框架：「能量」「氣場」「象徵」。

輸出 JSON（只輸出 JSON）：
{{
  "theme": "今日主題",
  "crystal_focus": "主打水晶",
  "posts": [
    {{
      "type": "IG貼文",
      "language": "TW",
      "platform": "Instagram",
      "content": "完整貼文內容（含 hashtag）",
      "scheduled_time": "{date} 18:00",
      "crystal": "白水晶"
    }},
    {{
      "type": "IG貼文",
      "language": "HK",
      "platform": "Instagram",
      "content": "粵語版本",
      "scheduled_time": "{date} 18:00",
      "crystal": "白水晶"
    }},
    {{
      "type": "IG貼文",
      "language": "CN",
      "platform": "小紅書",
      "content": "普通話簡體版本",
      "scheduled_time": "{date} 18:00",
      "crystal": "白水晶"
    }},
    {{
      "type": "蝦皮貼文",
      "language": "TW",
      "platform": "蝦皮",
      "content": "蝦皮促銷貼文，附帶購買連結提示",
      "scheduled_time": "{date} 12:00",
      "crystal": "白水晶"
    }}
  ],
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
        logger.info("生成今日能量內容...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            messages=[{"role": "user", "content": PROMPT.format(date=today)}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        rows_written = 0
        for i, post in enumerate(data.get("posts", []), start=1):
            post_id = f"{today.replace('-','')}-C{i:03d}"
            sheets.append_row("審核隊列", [
                post_id,
                post.get("type", ""),
                post.get("content", "")[:100] + "...",
                post.get("language", ""),
                post.get("platform", ""),
                post.get("scheduled_time", ""),
                "待審",
                "",
            ])
            rows_written += 1

        theme = data.get("theme", "")
        crystal = data.get("crystal_focus", "")
        needs_boss = data.get("needs_boss_review", False)
        summary = f"主題：{theme}｜主打：{crystal}｜產出 {rows_written} 篇"

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
