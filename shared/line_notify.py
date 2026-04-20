import os
import requests
from datetime import datetime

LINE_API_URL = "https://api.line.me/v2/bot/message/push"


def _get_token() -> str:
    return os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")


def _get_user_id() -> str:
    return os.environ.get("LINE_USER_ID", "")


def send(message: str) -> bool:
    token = _get_token()
    user_id = _get_user_id()
    if not token or not user_id:
        print("[LINE] TOKEN 或 USER_ID 未設定，跳過推送")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }
    resp = requests.post(LINE_API_URL, headers=headers, json=payload, timeout=10)
    if resp.status_code != 200:
        print(f"[LINE] 推送失敗：{resp.status_code} {resp.text}")
    return resp.status_code == 200


def send_daily_report(agent_reports: list[dict]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"🔮 騏藝逸品 AI 日報 {now}"]
    for r in agent_reports:
        icon = "✅" if r["status"] == "成功" else "❌"
        lines.append(f"{icon} {r['agent']}: {r['summary']}")
        if r.get("needs_boss"):
            lines.append(f"   ⚠️ 需要介入：{r.get('reason', '')}")
    send("\n".join(lines))


def send_alert(title: str, message: str):
    send(f"🚨 【警報】{title}\n{message}")


def send_trend_alert(item: str, multiplier: float, market: str):
    send(f"📈 【爆款預警】{market} 市場\n{item} 互動率超過基準 {multiplier:.1f} 倍！\n建議立即跟進選品。")


def send_inventory_alert(product: str, quantity: int):
    send(f"📦 【庫存警報】\n{product} 剩餘 {quantity} 件，低於警戒值，請盡快補貨。")
