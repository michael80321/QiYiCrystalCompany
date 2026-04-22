"""
選品委員會員
執行頻率：每週一 07:00
工作：整合趨勢研究員資料 + 庫存資料，決定本週引進/淘汰手串品項，
      輸出選品決策清單寫入「選品決策」分頁
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

AGENT_NAME = "選品委員會員"
logger = get_logger(AGENT_NAME)

# 手串選品篩選標準
CURATION_CRITERIA = """
## 騏藝逸品手串選品委員會 — 篩選標準

### 必須符合（全部通過才能引進）
1. **產地透明**：必須能標示明確產地（巴西/馬達加斯加/烏拉圭/緬甸等）
2. **品質分級**：A級以上（無明顯裂紋、顏色均勻、光澤度佳）
3. **毛利率**：售價需達成本 2.5 倍以上（毛利 ≥ 60%）
4. **市場差異**：蝦皮/露天前三名競品款式超過 200 件庫存的款式不做
5. **客群契合**：符合 25-45 歲女性能量療癒/星座/風水興趣

### 優先引進條件（加分項）
- 當季節氣/星座對應石種（季節性需求高）
- 趨勢分數 ≥ 70（社群熱度高）
- 可做個人化客製（生辰/星座刻字）
- 適合企業禮品（可批量、有質感包裝）

### 淘汰標準（任一符合即淘汰）
- 庫存滯留 > 60 天且售出率 < 20%
- 競品已大量跟進（同款蝦皮 > 500 件）
- 毛利率跌破 50%
- 退貨率 > 5%

### 手串規格規範
- 主石直徑：6mm / 8mm / 10mm / 12mm（主力做 8mm/10mm）
- 繩色：黑/紅/金（能量配色）
- 包裝：絨布袋 + 水晶功效小卡（必備）
"""

PROMPT = """你是騏藝逸品的選品委員會員，負責每週審核手串選品決策。

今天日期：{date}（{weekday}）

## 本週趨勢情報（來自選品趨勢研究員）
{trend_data}

## 現有庫存狀況
{inventory_data}

## 選品標準
{criteria}

請根據以上資料，輸出本週選品決策 JSON（只輸出 JSON）：
{{
  "review_date": "{date}",
  "week_theme": "本週主打能量主題（一句話）",
  "introduce": [
    {{
      "crystal_name": "水晶手串名稱",
      "stone_type": "石種",
      "bead_size": "8mm",
      "origin": "產地",
      "target_energy": "對應能量/功效",
      "target_zodiac": "適合星座（或「全星座」）",
      "suggested_retail_twd": 980,
      "suggested_cost_twd": 350,
      "gross_margin_pct": 64,
      "priority": "高/中",
      "reason": "引進原因（30字內）",
      "suitable_for_corporate": true,
      "shopee_keywords": ["關鍵字1", "關鍵字2", "關鍵字3"]
    }}
  ],
  "discontinue": [
    {{
      "crystal_name": "要淘汰的品項",
      "reason": "淘汰原因"
    }}
  ],
  "weekly_hero_product": "本週主打明星商品名稱",
  "corporate_gift_suggestion": "最適合企業禮品的款式與建議搭配",
  "sourcing_notes": "採購注意事項",
  "needs_boss_review": false,
  "needs_boss_reason": ""
}}
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["週一","週二","週三","週四","週五","週六","週日"][datetime.now().weekday()]

    try:
        # 讀取趨勢情報（最近 10 筆）
        try:
            trend_records = sheets.get_all_records("情報表")
            trend_data = json.dumps(trend_records[-10:], ensure_ascii=False, indent=2) if trend_records else "（暫無趨勢資料）"
        except Exception:
            trend_data = "（暫無趨勢資料）"

        # 讀取庫存（所有商品）
        try:
            inventory_records = sheets.get_all_records("庫存表")
            # 只取關鍵欄位
            inventory_summary = [
                {k: v for k, v in r.items() if k in ["商品名稱", "水晶種類", "現有庫存", "警戒庫存量", "售價", "成本"]}
                for r in inventory_records
            ]
            inventory_data = json.dumps(inventory_summary, ensure_ascii=False, indent=2) if inventory_summary else "（庫存表為空）"
        except Exception:
            inventory_data = "（庫存表為空）"

        logger.info("呼叫 Claude 進行選品審核...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": PROMPT.format(
                date=today,
                weekday=weekday,
                trend_data=trend_data,
                inventory_data=inventory_data,
                criteria=CURATION_CRITERIA,
            )}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        rows_written = 0

        # 寫入選品決策分頁
        for item in data.get("introduce", []):
            sheets.append_row("選品決策", [
                today,
                "引進",
                item.get("crystal_name", ""),
                item.get("stone_type", ""),
                item.get("bead_size", ""),
                item.get("origin", ""),
                item.get("target_energy", ""),
                item.get("target_zodiac", ""),
                item.get("suggested_retail_twd", ""),
                item.get("suggested_cost_twd", ""),
                item.get("gross_margin_pct", ""),
                item.get("priority", ""),
                item.get("reason", ""),
                "是" if item.get("suitable_for_corporate") else "否",
                ", ".join(item.get("shopee_keywords", [])),
                "待採購",
            ])
            rows_written += 1

        for item in data.get("discontinue", []):
            sheets.append_row("選品決策", [
                today,
                "淘汰",
                item.get("crystal_name", ""),
                "", "", "", "", "", "", "", "", "", item.get("reason", ""),
                "", "", "待下架",
            ])
            rows_written += 1

        week_theme = data.get("week_theme", "")
        hero = data.get("weekly_hero_product", "")
        needs_boss = data.get("needs_boss_review", False)
        introduce_count = len(data.get("introduce", []))
        discontinue_count = len(data.get("discontinue", []))
        summary = f"本週主題：{week_theme}｜引進 {introduce_count} 款｜淘汰 {discontinue_count} 款｜主打：{hero}"

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
