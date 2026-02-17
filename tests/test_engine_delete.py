from pathlib import Path
from src.engine import BackupEngine
from src.logger import setup_logger


def test_engine_process_deleted_moves_file_and_removes_state(tmp_path):
    source = tmp_path / "source"
    backup = tmp_path / "backup"

    source.mkdir()
    backup.mkdir()

    f = source / "file.txt"
    f.write_text("data")

    config = {
        "sources": [source],
        "backup_root": backup,
        "log_dir": tmp_path,
        "hash_algorithm": "sha256",
        "retention": {"max_versions_per_file": 5},
        "app_dir": tmp_path,
    }

    logger = setup_logger(tmp_path)
    engine = BackupEngine(config, logger)

    # First backup
    engine.process_full_scan()

    # Simulate deletion
    f.unlink()
    engine.process_deleted(f)

    deleted_dir = backup / "_deleted"
    assert (deleted_dir / "file.txt").exists()

    # State should not contain file
    assert str(f.resolve()) not in engine.state
