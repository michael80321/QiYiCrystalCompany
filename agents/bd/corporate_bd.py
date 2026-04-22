"""
企業禮品開發員
執行頻率：每日 09:30
工作：主動開發企業禮品訂單。分析適合場景（尾牙/週年慶/員工禮品），
      生成本週企業開發策略、潛在客戶名單、提案文案，寫入 BD開發 分頁。
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

AGENT_NAME = "企業禮品開發員"
logger = get_logger(AGENT_NAME)

PROMPT = """你是騏藝逸品的企業禮品開發員，專責 B2B 業務開發。

品牌背景：騏藝逸品 @qiyicrystal，高端水晶手串電商，主打能量療癒
主力產品：天然水晶手串（售價 $600–$3,000/條，批量 50 條以上享優惠）
企業禮品特色：可客製刻字、附品牌絨布袋、附水晶功效說明卡

今天日期：{date}
{seasonal_context}

## 本週主打手串選品
{product_data}

請輸出今日企業開發計劃 JSON（只輸出 JSON）：
{{
  "date": "{date}",
  "seasonal_opportunity": "本週最適合切入的企業送禮場景（30字）",
  "target_segments": [
    {{
      "segment": "目標產業/族群",
      "reason": "為什麼現在是好時機",
      "approaching_channel": "接觸管道（如：LinkedIn/FB社團/email/電話）",
      "estimated_order_size": "50-100條",
      "decision_maker": "通常誰決策（HR主管/行政/老闆）"
    }}
  ],
  "outreach_templates": [
    {{
      "channel": "LINE/email/Instagram DM",
      "tone": "溫暖專業",
      "subject": "訊息主旨（email用）",
      "body": "完整開發信/訊息內容（繁體中文，200字內）",
      "cta": "行動呼籲"
    }},
    {{
      "channel": "Instagram DM",
      "tone": "輕鬆有質感",
      "subject": "",
      "body": "IG DM 開發訊息（100字內，自然不推銷）",
      "cta": "行動呼籲"
    }}
  ],
  "proposal_highlight": {{
    "product_name": "本週主推企業禮品款",
    "unit_price_twd": 880,
    "min_quantity": 50,
    "bulk_discount": "50條9折，100條8折",
    "customization": "可刻公司名/員工姓名/祝福語",
    "packaging": "絨布袋 + 燙金功效說明卡 + 品牌提袋",
    "lead_time_days": 7,
    "pitch_one_liner": "一句話讓對方心動的產品說明"
  }},
  "follow_up_tasks": [
    "今天要做的具體行動1",
    "今天要做的具體行動2"
  ],
  "weekly_bd_goal": "本週 BD 目標（具體數字）",
  "needs_boss_review": false,
  "needs_boss_reason": ""
}}
"""

def get_seasonal_context(today: datetime) -> str:
    """根據日期判斷企業送禮旺季"""
    month = today.month
    day = today.day

    contexts = []

    # 尾牙季（12月–2月）
    if month == 12:
        contexts.append("🎊 尾牙旺季來臨！企業開始採購年終禮品，是最佳切入時機")
    elif month in [1, 2]:
        contexts.append("🧧 農曆新年 + 尾牙高峰期，企業禮品需求最旺")

    # 三八婦女節（3月）
    elif month == 3 and day <= 15:
        contexts.append("🌸 三八婦女節前夕，企業採購女性員工禮品需求高")

    # 母親節（5月）
    elif month == 5 and day <= 15:
        contexts.append("💝 母親節即將到來，適合推「感謝媽媽」企業禮品方案")

    # 員工旅遊季（5–6月）
    elif month in [5, 6]:
        contexts.append("✈️ 員工旅遊旺季，適合推伴手禮採購方案")

    # 中秋節（9月）
    elif month == 9:
        contexts.append("🥮 中秋節禮品旺季，企業送禮預算充足")

    # 聖誕 + 年終（11月底–12月）
    elif month == 11 and day >= 15:
        contexts.append("🎄 聖誕節 + 年終禮品季開始，提前佈局")

    # 全年適合場景
    contexts.append("📅 全年適合：新員工入職禮、週年慶紀念、客戶感謝禮")

    return "\n".join(contexts)

def run():
    logger.info(f"=== {AGENT_NAME} 開始執行 ===")
    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    seasonal_context = get_seasonal_context(today)

    try:
        # 讀取本週最新選品決策
        try:
            curation_records = sheets.get_all_records("選品決策")
            # 取最近 7 天的引進品項
            week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            recent_products = [
                r for r in curation_records
                if r.get("決策日期", "") >= week_ago and r.get("決策類型", "") == "引進"
            ]
            product_data = json.dumps(recent_products[:5], ensure_ascii=False, indent=2) if recent_products else "（請參考主力商品：天然紫水晶手串、粉晶手串、黑碧璽手串）"
        except Exception:
            product_data = "（主力商品：天然紫水晶手串 $880、粉晶手串 $780、黑碧璽手串 $980）"

        logger.info("生成企業開發計劃...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            messages=[{"role": "user", "content": PROMPT.format(
                date=today_str,
                seasonal_context=seasonal_context,
                product_data=product_data,
            )}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        rows_written = 0

        # 寫入 BD開發 分頁（開發信模板）
        for tmpl in data.get("outreach_templates", []):
            sheets.append_row("BD開發", [
                today_str,
                data.get("seasonal_opportunity", ""),
                tmpl.get("channel", ""),
                tmpl.get("subject", ""),
                tmpl.get("body", ""),
                tmpl.get("cta", ""),
                data.get("proposal_highlight", {}).get("product_name", ""),
                data.get("proposal_highlight", {}).get("unit_price_twd", ""),
                data.get("proposal_highlight", {}).get("pitch_one_liner", ""),
                "待發送",
            ])
            rows_written += 1

        # 寫入目標客群
        for seg in data.get("target_segments", []):
            sheets.append_row("BD開發", [
                today_str,
                seg.get("segment", ""),
                seg.get("approaching_channel", ""),
                "目標客群分析",
                seg.get("reason", ""),
                seg.get("decision_maker", ""),
                seg.get("estimated_order_size", ""),
                "", "", "分析",
            ])
            rows_written += 1

        seasonal_opp = data.get("seasonal_opportunity", "")
        hero = data.get("proposal_highlight", {}).get("product_name", "")
        goal = data.get("weekly_bd_goal", "")
        needs_boss = data.get("needs_boss_review", False)
        summary = f"場景：{seasonal_opp}｜主推：{hero}｜本週目標：{goal}"

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
