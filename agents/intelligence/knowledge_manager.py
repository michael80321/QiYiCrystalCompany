"""
商品知識庫管理員
執行頻率：每週一次（週一）
工作：維護水晶產地、功效、能量屬性百科，供其他員工調用
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

AGENT_NAME = "商品知識庫管理員"
logger = get_logger(AGENT_NAME)

CRYSTALS = [
    "白水晶", "紫水晶", "粉晶", "黑碧璽", "拉長石",
    "月光石", "藍晶石", "東菱玉", "虎眼石", "橄欖石",
    "海藍寶", "紅碧玉", "孔雀石", "黃水晶", "煙晶",
]

PROMPT = """你是騏藝逸品的商品知識庫管理員，維護專業水晶百科。

請為以下水晶生成詳細的知識庫條目：{crystals}

每個條目需包含三個市場的功效描述，使用「能量」「氣場」「象徵」框架，
不使用任何醫療聲稱或保證效果的語言。

輸出 JSON（只輸出 JSON）：
{{
  "entries": [
    {{
      "name": "白水晶",
      "name_en": "Clear Quartz",
      "color": "無色透明",
      "origin": ["巴西", "馬達加斯加", "阿肯色州"],
      "energy": "淨化、放大、療癒",
      "zodiac": ["牡羊座", "獅子座"],
      "desc_tw": "台灣用語功效描述（80字內）",
      "desc_hk": "香港粵語功效描述（80字內）",
      "desc_cn": "大陸普通話功效描述（80字內）",
      "care_tips": "保養方式",
      "price_range_twd": "500-2000"
    }}
  ]
}}
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": PROMPT.format(crystals="、".join(CRYSTALS))}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        # 清空舊資料並重寫（知識庫每週全量更新）
        rows_written = 0
        for entry in data.get("entries", []):
            sheets.append_row("知識庫", [
                entry.get("name", ""),
                entry.get("name_en", ""),
                entry.get("color", ""),
                "、".join(entry.get("origin", [])),
                entry.get("energy", ""),
                "、".join(entry.get("zodiac", [])),
                entry.get("desc_tw", ""),
                entry.get("desc_hk", ""),
                entry.get("desc_cn", ""),
            ])
            rows_written += 1

        summary = f"更新 {rows_written} 個水晶知識條目"
        log_execution(AGENT_NAME, "成功", summary, rows_written, False)
        sheets.update_agent_status(AGENT_NAME, "成功", summary, rows_written, False)
        logger.info(f"=== 完成，耗時 {(datetime.now()-start_time).seconds} 秒 ===")

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        send_alert(AGENT_NAME, str(e))
        sheets.update_agent_status(AGENT_NAME, "失敗", str(e), 0, True, str(e))
        raise

if __name__ == "__main__":
    run()
