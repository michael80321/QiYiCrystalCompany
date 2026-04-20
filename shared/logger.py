import logging
import os
from datetime import datetime
from pathlib import Path

Path("logs").mkdir(exist_ok=True)


def get_logger(agent_name: str) -> logging.Logger:
    logger = logging.getLogger(agent_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s — %(message)s", "%Y-%m-%d %H:%M:%S")

    # 輸出到 console（GitHub Actions 會抓到）
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 寫入本地 log 檔
    date_str = datetime.now().strftime("%Y-%m-%d")
    fh = logging.FileHandler(f"logs/{agent_name}_{date_str}.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def log_execution(agent_name: str, status: str, summary: str, rows: int, needs_boss: bool, reason: str = ""):
    logger = get_logger(agent_name)
    logger.info(f"執行狀態：{status}")
    logger.info(f"輸出摘要：{summary}")
    logger.info(f"寫入筆數：{rows}")
    logger.info(f"需要老闆介入：{'是 — ' + reason if needs_boss else '否'}")
