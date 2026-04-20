import os
import requests
import anthropic
from shared.logger import get_logger
from shared.line_notify import send_alert

logger = get_logger("api_health")


def _check_anthropic() -> tuple[bool, str]:
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)


def _check_line() -> tuple[bool, str]:
    token = os.environ.get("LINE_NOTIFY_TOKEN", "")
    if not token:
        return False, "TOKEN 未設定"
    resp = requests.get(
        "https://notify-api.line.me/api/status",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return True, "OK"
    return False, f"HTTP {resp.status_code}"


def _check_heygen() -> tuple[bool, str]:
    key = os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        return False, "KEY 未設定"
    resp = requests.get(
        "https://api.heygen.com/v1/user/remaining_quota",
        headers={"X-Api-Key": key},
        timeout=10,
    )
    if resp.status_code == 200:
        quota = resp.json().get("data", {}).get("remaining_quota", "?")
        return True, f"剩餘配額 {quota}"
    return False, f"HTTP {resp.status_code}"


CHECKS = {
    "Anthropic": _check_anthropic,
    "LINE Notify": _check_line,
    "HeyGen": _check_heygen,
}


def run_all_checks() -> dict:
    results = {}
    failed = []

    for name, check_fn in CHECKS.items():
        try:
            ok, msg = check_fn()
            results[name] = {"ok": ok, "msg": msg}
            logger.info(f"{'✅' if ok else '❌'} {name}: {msg}")
            if not ok:
                failed.append(f"{name}: {msg}")
        except Exception as e:
            results[name] = {"ok": False, "msg": str(e)}
            failed.append(f"{name}: {e}")

    if failed:
        send_alert("API 健康異常", "\n".join(failed))

    return results


if __name__ == "__main__":
    run_all_checks()
