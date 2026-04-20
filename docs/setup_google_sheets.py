"""
一次性執行腳本：在 Google Sheets 建立 4 個分頁及標題列。
執行前：設定環境變數 SHEETS_ID 和 GOOGLE_SERVICE_ACCOUNT_JSON。
執行：python docs/setup_google_sheets.py
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEETS_CONFIG = {
    "日報表": [
        "執行時間", "員工名稱", "執行狀態", "輸出摘要",
        "寫入筆數", "需要老闆介入", "原因備注",
    ],
    "審核隊列": [
        "ID", "類型", "內容摘要", "語言", "平台",
        "預定發布時間", "狀態", "老闆批注",
    ],
    "員工開關": [
        "員工名稱", "模組路徑", "狀態", "執行頻率",
        "最後執行時間", "今日執行次數", "備注",
    ],
    "庫存表": [
        "商品ID", "商品名稱", "水晶種類", "現有庫存",
        "警戒庫存量", "售價(TWD)", "成本", "供應商", "最後更新",
    ],
    "情報表": [
        "日期", "市場", "平台", "來源帳號", "內容類型",
        "互動率", "是否爆款", "關鍵字", "建議行動",
    ],
    "知識庫": [
        "水晶名稱", "英文名", "顏色", "產地", "能量屬性",
        "適合星座", "功效描述(TW)", "功效描述(HK)", "功效描述(CN)",
    ],
}

AGENT_LIST = [
    ("亞太市場情報員", "agents/intelligence/market_intelligence.py", "開啟", "每6小時"),
    ("選品趨勢研究員", "agents/intelligence/trend_researcher.py", "開啟", "每日06:00"),
    ("競品定價策略員", "agents/intelligence/pricing_analyst.py", "開啟", "每日07:00"),
    ("商品知識庫管理員", "agents/intelligence/knowledge_manager.py", "開啟", "每週一次"),
    ("系統健康監控員", "agents/intelligence/system_health.py", "開啟", "每小時"),
    ("能量內容專員", "agents/content/energy_content.py", "開啟", "每日05:00"),
    ("圖像產出員", "agents/content/image_generator.py", "開啟", "每日05:30"),
    ("影片腳本員", "agents/content/video_scriptwriter.py", "開啟", "每日06:00"),
    ("數字人短影片生成", "agents/digital_human/video_generator.py", "開啟", "每日07:00"),
    ("影片後製自動化", "agents/digital_human/post_production.py", "開啟", "審核通過後"),
    ("行銷企劃員", "agents/marketing/campaign_planner.py", "開啟", "每日08:00"),
    ("廣告投放優化員", "agents/marketing/ads_optimizer.py", "開啟", "每日09:00"),
    ("SEO優化員", "agents/marketing/seo_optimizer.py", "開啟", "每週一次"),
    ("KOL合作追蹤員", "agents/marketing/kol_tracker.py", "開啟", "每日10:00"),
    ("客服接待員", "agents/operations/customer_service.py", "開啟", "每小時"),
    ("採購庫存員", "agents/operations/inventory_manager.py", "開啟", "每日08:00"),
    ("物流售後員", "agents/operations/logistics_tracker.py", "開啟", "每2小時"),
    ("會員經營員", "agents/operations/member_manager.py", "開啟", "每日"),
    ("財務秘書", "agents/finance/finance_secretary.py", "開啟", "每日23:00"),
    ("老闆決策秘書", "agents/decision/decision_secretary.py", "開啟", "每日07:30"),
]


def setup():
    import json as _json
    json_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if json_env.strip().startswith("{"):
        creds = Credentials.from_service_account_info(_json.loads(json_env), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            json_env or "service_account.json", scopes=SCOPES
        )
    client = gspread.authorize(creds)
    sheets_id = os.environ["SHEETS_ID"]
    spreadsheet = client.open_by_key(sheets_id)

    existing = [ws.title for ws in spreadsheet.worksheets()]

    for tab_name, headers in SHEETS_CONFIG.items():
        if tab_name not in existing:
            ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
            print(f"建立分頁：{tab_name}")
        else:
            ws = spreadsheet.worksheet(tab_name)
            print(f"分頁已存在，更新標題：{tab_name}")

        ws.update([headers], "A1:Z1")

        # 員工開關分頁預填資料
        if tab_name == "員工開關":
            from datetime import datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows = [[name, path, status, freq, now, 0, ""] for name, path, status, freq in AGENT_LIST]
            ws.update(rows, f"A2:G{len(rows)+1}")
            print(f"  已寫入 {len(rows)} 個員工開關設定")

    print("\n✅ Google Sheets 初始化完成！")
    print(f"📊 分頁：{list(SHEETS_CONFIG.keys())}")


if __name__ == "__main__":
    setup()
