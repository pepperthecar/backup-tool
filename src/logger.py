import logging
from pathlib import Path
from datetime import datetime


def setup_logger(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"backup_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("backup_tool")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    return logger
