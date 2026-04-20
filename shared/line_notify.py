import os
import requests
import yaml
from datetime import datetime

LINE_NOTIFY_URL = "https://notify-api.line.me/api/notify"


def _get_token() -> str:
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    if not token:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        token = config["apis"]["line_token"]
    return token


def send(message: str, image_url: str = None) -> bool:
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": message}
    if image_url:
        payload["imageThumbnail"] = image_url
        payload["imageFullsize"] = image_url

    resp = requests.post(LINE_NOTIFY_URL, headers=headers, data=payload, timeout=10)
    return resp.status_code == 200


def send_daily_report(agent_reports: list[dict]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n🔮 騏藝逸品 AI 日報 {now}"]
    for r in agent_reports:
        status_icon = "✅" if r["status"] == "成功" else "❌"
        lines.append(f"{status_icon} {r['agent']}: {r['summary']}")
        if r.get("needs_boss"):
            lines.append(f"   ⚠️ 需要老闆介入：{r.get('reason', '')}")
    send("\n".join(lines))


def send_alert(title: str, message: str):
    send(f"\n🚨 【警報】{title}\n{message}")


def send_trend_alert(item: str, multiplier: float, market: str):
    send(f"\n📈 【爆款預警】{market} 市場\n{item} 互動率超過基準 {multiplier:.1f} 倍！\n建議立即跟進選品。")


def send_inventory_alert(product: str, quantity: int):
    send(f"\n📦 【庫存警報】\n{product} 剩餘 {quantity} 件，低於警戒值，請盡快補貨。")
