"""
初始化 BD 引擎需要的 Google Sheets 分頁和員工開關資料
執行一次即可
"""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent))
import shared.sheets as sheets
import gspread

def setup():
    print("=== 初始化 BD 引擎 Google Sheets ===")

    client = sheets._get_client()
    spreadsheet = sheets._get_sheet()
    existing_tabs = [ws.title for ws in spreadsheet.worksheets()]
    print(f"現有分頁：{existing_tabs}")

    # 1. 建立「選品決策」分頁
    if "選品決策" not in existing_tabs:
        ws = spreadsheet.add_worksheet(title="選品決策", rows=1000, cols=20)
        ws.append_row([
            "決策日期", "決策類型", "手串名稱", "石種", "珠徑", "產地",
            "對應能量", "適合星座", "建議售價", "建議成本", "毛利率%",
            "優先級", "決策原因", "適合企業禮品", "蝦皮關鍵字", "上架狀態"
        ])
        print("✅ 建立「選品決策」分頁")
    else:
        print("⏭ 「選品決策」分頁已存在")

    # 2. 建立「BD開發」分頁
    if "BD開發" not in existing_tabs:
        ws = spreadsheet.add_worksheet(title="BD開發", rows=1000, cols=15)
        ws.append_row([
            "日期", "場景/客群", "接觸管道", "類型", "主旨/內容",
            "行動呼籲", "主推商品", "單價", "一句話說明", "狀態"
        ])
        print("✅ 建立「BD開發」分頁")
    else:
        print("⏭ 「BD開發」分頁已存在")

    # 3. 建立「上架草稿」分頁
    if "上架草稿" not in existing_tabs:
        ws = spreadsheet.add_worksheet(title="上架草稿", rows=1000, cols=20)
        ws.append_row([
            "建立日期", "商品名稱", "蝦皮標題", "售價", "原價",
            "主關鍵字", "長尾關鍵字", "描述摘要", "完整描述",
            "規格JSON", "變體JSON", "FAQJSON",
            "備用標題", "預估SEO分", "備注", "上架狀態"
        ])
        print("✅ 建立「上架草稿」分頁")
    else:
        print("⏭ 「上架草稿」分頁已存在")

    # 4. 在員工開關加入三位新員工
    try:
        agent_records = sheets.get_all_records("員工開關")
        existing_names = [r["員工名稱"] for r in agent_records]

        new_agents = [
            ["選品委員會員", "agents/bd/product_curator.py", "開啟", "每週一 07:00", "", "0", "整合趨勢+庫存資料，輸出本週手串選品決策"],
            ["企業禮品開發員", "agents/bd/corporate_bd.py", "開啟", "每日 09:30", "", "0", "主動開發企業禮品B2B訂單，生成開發信模板"],
            ["蝦皮自動上架員", "agents/bd/shopee_lister.py", "開啟", "每週二 08:00", "", "0", "生成蝦皮商品頁面文案，含SEO標題/描述/FAQ"],
        ]

        for agent in new_agents:
            if agent[0] not in existing_names:
                sheets.append_row("員工開關", agent)
                print(f"✅ 加入員工：{agent[0]}")
            else:
                print(f"⏭ 員工已存在：{agent[0]}")
    except Exception as e:
        print(f"⚠️ 員工開關更新失敗：{e}")

    print("\n=== 初始化完成 ===")

if __name__ == "__main__":
    setup()
