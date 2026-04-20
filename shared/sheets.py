import os
import yaml
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_client = None
_sheet = None


def _get_client():
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(
            os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json"),
            scopes=SCOPES,
        )
        _client = gspread.authorize(creds)
    return _client


def _get_sheet():
    global _sheet
    if _sheet is None:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        sheets_id = os.environ.get("SHEETS_ID") or config["apis"]["google_sheets_id"]
        _sheet = _get_client().open_by_key(sheets_id)
    return _sheet


def get_worksheet(tab_name: str):
    return _get_sheet().worksheet(tab_name)


def read_cell(tab_name: str, row_key: str, col_name: str) -> str:
    ws = get_worksheet(tab_name)
    data = ws.get_all_records()
    for row in data:
        if str(row.get("名稱", "")) == row_key or str(row.get("員工名稱", "")) == row_key:
            return str(row.get(col_name, ""))
    return ""


def append_row(tab_name: str, row: list):
    ws = get_worksheet(tab_name)
    ws.append_row(row, value_input_option="USER_ENTERED")


def write_cell(tab_name: str, row: int, col: int, value):
    ws = get_worksheet(tab_name)
    ws.update_cell(row, col, value)


def get_all_records(tab_name: str) -> list[dict]:
    ws = get_worksheet(tab_name)
    return ws.get_all_records()


def update_agent_status(agent_name: str, status: str, output_summary: str, rows_written: int, needs_boss: bool, reason: str = ""):
    """標準化員工執行後寫入日報表"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    append_row("日報表", [
        now,
        agent_name,
        status,
        output_summary,
        rows_written,
        "是" if needs_boss else "否",
        reason,
    ])
