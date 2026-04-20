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

PROMPT = """你是騏藝逸品的能量內容專員。

品牌：騏藝逸品 @qiyicrystal，高端水晶電商
語調：溫暖、專業、有靈性感，不過度靈異
客群：25-45 歲對能量水晶、風水、星座有興趣的女性
禁忌：不用醫療聲稱、不保證效果、不提競品
功效框架：「能量」「氣場」「象徵」

貼文風格規範：
- 開頭必須有 1-2 個吸引眼球的 Emoji（如 ✨💎🔮🌙💜🌸🪨）
- 正文 3-5 行，每行簡短有力，帶有靈性溫度
- 結尾 CTA：引導到蝦皮/私訊詢問
- Hashtag 分兩段：品牌標籤 + 流量標籤，共 20-25 個

品牌固定 Hashtag（每篇必帶）：
#騏藝逸品 #QiYiCrystal #qiyicrystal #水晶 #能量水晶 #療癒水晶

台灣流量 Hashtag 池（每篇從中選 8-10 個）：
#水晶手鍊 #水晶擺件 #白水晶 #紫水晶 #粉晶 #黑碧璽 #黃水晶
#星座水晶 #風水水晶 #招財水晶 #療癒系 #靈性生活 #水晶控
#滿月儀式 #節氣養生 #能量淨化 #正能量 #吸引力法則

今天日期：{date}
請判斷當前節氣、星座運勢、是否接近滿月或特殊天象，融入貼文主題。

輸出 JSON（只輸出 JSON）：
{{
  "theme": "今日主題",
  "crystal_focus": "主打水晶",
  "posts": [
    {{
      "type": "IG貼文",
      "language": "TW",
      "platform": "Instagram",
      "content": "✨ 開頭emoji\\n\\n正文內容（3-5行）\\n\\n👉 私訊或蝦皮連結詢問\\n\\n#騏藝逸品 #QiYiCrystal #水晶 ... (完整hashtag)",
      "scheduled_time": "{date} 18:00",
      "crystal": "主打水晶名稱"
    }},
    {{
      "type": "IG貼文",
      "language": "HK",
      "platform": "Instagram",
      "content": "粵語版本（含適合香港市場的hashtag）",
      "scheduled_time": "{date} 18:00",
      "crystal": "主打水晶名稱"
    }},
    {{
      "type": "IG貼文",
      "language": "CN",
      "platform": "小紅書",
      "content": "簡體中文版本（小紅書風格，含#話題標籤）",
      "scheduled_time": "{date} 18:00",
      "crystal": "主打水晶名稱"
    }},
    {{
      "type": "蝦皮貼文",
      "language": "TW",
      "platform": "蝦皮",
      "content": "蝦皮短促銷文案，強調限量/優惠，無需hashtag",
      "scheduled_time": "{date} 12:00",
      "crystal": "主打水晶名稱"
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
                post.get("content", ""),
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
