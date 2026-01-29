from pathlib import Path
from src.executor import execute
from src.logger import setup_logger


def test_executor_backup_and_duplicate(tmp_path):
    source = tmp_path / "source"
    backup = tmp_path / "backup"

    source.mkdir()
    backup.mkdir()

    a = source / "a.txt"
    b = source / "b.txt"

    a.write_text("one")
    b.write_text("one")

    actions = [
        ("backup", a, "h1"),
        ("duplicate", b, "h1"),
    ]

    logger = setup_logger(tmp_path)
    execute(actions, backup, backup / "_duplicates", logger)

    assert (backup / "a.txt").exists()
    assert (backup / "_duplicates" / "b.txt").exists()
    assert a.exists()
    assert b.exists()
