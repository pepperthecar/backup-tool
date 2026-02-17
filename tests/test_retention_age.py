import os
import time
from datetime import datetime, timedelta
from src.retention import apply_retention
from src.logger import setup_logger


def test_retention_keep_days(tmp_path):
    versions_dir = tmp_path / "versions" / "file.txt"
    versions_dir.mkdir(parents=True)

    old_file = versions_dir / "v1.bak"
    old_file.write_text("old")

    # Make file appear 10 days old
    old_time = time.time() - (10 * 24 * 60 * 60)
    os.utime(old_file, (old_time, old_time))

    logger = setup_logger(tmp_path)

    apply_retention(
        versions_root=tmp_path / "versions",
        retention={"keep_days": 5},
        logger=logger,
    )

    assert not old_file.exists()
