from src.executor import execute
from src.logger import setup_logger


def test_executor_modified_creates_version(tmp_path):
    source = tmp_path / "source"
    backup = tmp_path / "backup"

    source.mkdir()
    backup.mkdir()

    f = source / "file.txt"
    f.write_text("v1")

    logger = setup_logger(tmp_path)

    # Initial backup
    execute([("backup", f, "h1")], backup, backup / "_duplicates", logger)

    # Modify file
    f.write_text("v2")

    execute([("modified", f, "h2")], backup, backup / "_duplicates", logger)

    # Current file exists
    assert (backup / "file.txt").exists()

    # Version archive exists
    versions = list((backup / "versions" / "file.txt").glob("v*.bak"))
    assert len(versions) == 1
