"""
蝦皮自動上架員
執行頻率：每週二 08:00（選品委員會週一決策後隔天執行）
工作：讀取選品決策中「待採購→已到貨」的品項，
      自動生成完整蝦皮商品頁面文案（標題/描述/規格/FAQ），
      寫入「上架草稿」分頁供老闆確認後上架。
"""
import os, sys, json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import anthropic
import shared.sheets as sheets
from shared.logger import get_logger, log_execution
from shared.line_notify import send_alert

AGENT_NAME = "蝦皮自動上架員"
logger = get_logger(AGENT_NAME)

SHOPEE_PROMPT = """你是騏藝逸品的蝦皮上架專員，精通台灣蝦皮 SEO 和轉換率優化。

品牌：騏藝逸品 @qiyicrystal
平台：蝦皮購物（台灣）
目標：高搜尋排名 + 高轉換率

## 商品資料
{product_info}

## 蝦皮上架規範
- 標題：30–60 字，前 20 字放核心關鍵字，避免重複詞
- 關鍵字策略：石種 + 功效 + 星座 + 品牌 + 材質
- 描述結構：開場吸引（能量故事）→ 產品特色 → 規格 → 適合族群 → FAQ → 購買提醒
- 禁忌：不用醫療聲稱、不保證效果、不比較競品
- 語調：溫暖、有質感、有靈性感，不低俗促銷

輸出完整蝦皮商品頁面 JSON（只輸出 JSON）：
{{
  "product_name": "完整商品名稱（中文）",
  "shopee_title": "蝦皮商品標題（30–60字，SEO優化）",
  "shopee_title_alt": "備用標題（A/B測試用）",
  "price_twd": 980,
  "original_price_twd": 1280,
  "category": "蝦皮分類路徑",
  "main_keywords": ["主關鍵字1", "主關鍵字2", "主關鍵字3"],
  "long_tail_keywords": ["長尾詞1", "長尾詞2"],
  "description": "完整商品描述（繁體中文，500–800字，分段清晰）",
  "specs": {{
    "石種": "紫水晶",
    "珠徑": "8mm / 10mm 可選",
    "串長": "約 16–18cm（可調整）",
    "產地": "巴西天然",
    "淨重": "約 18–22g",
    "適合腕圍": "14–18cm"
  }},
  "variations": [
    {{"name": "珠徑", "options": ["6mm", "8mm", "10mm"]}},
    {{"name": "串長", "options": ["15cm", "16cm", "17cm", "18cm"]}}
  ],
  "faq": [
    {{"q": "是天然水晶嗎？", "a": "是的，本品採用巴西天然紫水晶，每顆都有自然的色澤變化，非染色或合成。"}},
    {{"q": "如何判斷尺寸？", "a": "建議用軟尺測量手腕最細處周長，再加 1–2cm 為舒適配戴長度。"}},
    {{"q": "有保固嗎？", "a": "我們提供 30 天瑕疵品換貨服務，如有品質問題請直接私訊客服。"}}
  ],
  "logistics": {{
    "shipping": "超商取貨 / 宅配到府",
    "processing_days": 1,
    "packaging": "絨布袋 + 水晶功效說明卡 + 氣泡袋防護"
  }},
  "promotion_tags": ["天然水晶", "開運手串", "能量石"],
  "instagram_hashtags": "#騏藝逸品 #QiYiCrystal #水晶手串",
  "seo_score_estimated": 85,
  "notes": "上架注意事項或採購備注"
}}
"""

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    try:
        # 讀取選品決策 — 找「引進」且「待採購」或「已到貨」的品項
        try:
            curation_records = sheets.get_all_records("選品決策")
            week_ago = (today - timedelta(days=14)).strftime("%Y-%m-%d")
            pending_products = [
                r for r in curation_records
                if r.get("決策類型", "") == "引進"
                and r.get("決策日期", "") >= week_ago
                and r.get("上架狀態", "") in ["待採購", "已到貨", ""]
            ]
        except Exception:
            pending_products = []

        # 若沒有選品決策，用預設主力商品示範
        if not pending_products:
            logger.info("無新增選品，使用預設主力商品示範上架文案")
            pending_products = [
                {
                    "crystal_name": "天然紫水晶手串",
                    "stone_type": "紫水晶",
                    "bead_size": "8mm/10mm",
                    "origin": "巴西",
                    "target_energy": "智慧、靈感、淨化",
                    "target_zodiac": "雙魚座、水瓶座、射手座",
                    "suggested_retail_twd": 980,
                    "suggested_cost_twd": 380,
                    "shopee_keywords": "紫水晶手串, 天然水晶, 開運手鍊",
                }
            ]

        rows_written = 0
        products_done = []

        for product in pending_products[:3]:  # 每次最多處理 3 個，避免超時
            product_info = json.dumps(product, ensure_ascii=False, indent=2)
            logger.info(f"生成上架文案：{product.get('crystal_name', '')}")

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                messages=[{"role": "user", "content": SHOPEE_PROMPT.format(
                    product_info=product_info
                )}]
            )

            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            listing = json.loads(content)

            # 寫入上架草稿分頁
            sheets.append_row("上架草稿", [
                today_str,
                listing.get("product_name", ""),
                listing.get("shopee_title", ""),
                listing.get("price_twd", ""),
                listing.get("original_price_twd", ""),
                ", ".join(listing.get("main_keywords", [])),
                ", ".join(listing.get("long_tail_keywords", [])),
                listing.get("description", "")[:500],  # 截短存入，完整版見下一欄
                listing.get("description", ""),
                json.dumps(listing.get("specs", {}), ensure_ascii=False),
                json.dumps(listing.get("variations", []), ensure_ascii=False),
                json.dumps(listing.get("faq", []), ensure_ascii=False),
                listing.get("shopee_title_alt", ""),
                listing.get("seo_score_estimated", ""),
                listing.get("notes", ""),
                "待審核",  # 上架狀態
            ])
            rows_written += 1
            products_done.append(listing.get("product_name", ""))

        needs_boss = rows_written > 0  # 有新草稿就通知老闆審核
        summary = f"生成 {rows_written} 件商品上架草稿｜{'、'.join(products_done)}｜請至「上架草稿」分頁確認後上架"

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
