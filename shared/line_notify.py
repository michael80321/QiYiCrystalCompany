"""
通知模組 — 使用 Telegram Bot API
環境變數：TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID
"""
import os
import requests
from datetime import datetime

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _get_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _get_chat_id() -> str:
    return os.environ.get("TELEGRAM_CHAT_ID", "")


def send(message: str, parse_mode: str = "HTML") -> bool:
    token = _get_token()
    chat_id = _get_chat_id()
    if not token or not chat_id:
        print("[Telegram] TOKEN 或 CHAT_ID 未設定，跳過推送")
        return False

    resp = requests.post(
        TELEGRAM_API.format(token=token),
        json={"chat_id": chat_id, "text": message, "parse_mode": parse_mode},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"[Telegram] 推送失敗：{resp.status_code} {resp.text}")
    return resp.status_code == 200


def send_daily_report(agent_reports: list[dict]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"<b>🔮 騏藝逸品 AI 日報 {now}</b>"]
    for r in agent_reports:
        icon = "✅" if r["status"] == "成功" else "❌"
        lines.append(f"{icon} <b>{r['agent']}</b>：{r['summary']}")
        if r.get("needs_boss"):
            lines.append(f"   ⚠️ 需要介入：{r.get('reason', '')}")
    send("\n".join(lines))


def send_alert(title: str, message: str):
    send(f"🚨 <b>【警報】{title}</b>\n{message}")


def send_trend_alert(item: str, multiplier: float, market: str):
    send(f"📈 <b>【爆款預警】{market} 市場</b>\n{item} 互動率超過基準 {multiplier:.1f} 倍！\n建議立即跟進選品。")


def send_inventory_alert(product: str, quantity: int):
    send(f"📦 <b>【庫存警報】</b>\n{product} 剩餘 {quantity} 件，低於警戒值，請盡快補貨。")
