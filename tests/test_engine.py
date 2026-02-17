from pathlib import Path
from src.engine import BackupEngine
from src.logger import setup_logger


def test_engine_full_scan_creates_backup_and_state(tmp_path):
    
    source = tmp_path / "source"    
    backup = tmp_path / "backup"    
    
    source.mkdir()
    backup.mkdir()
    
    f = source / 'file.txt'
    f.write_text("data")
    
    config = {
        "sources": [source],
        "backup_root": backup,
        "log_dir": tmp_path,
        "hash_algorithm": 'sha256',
        "retention": {"max_versions_per_file": 5},
        "app_dir": tmp_path,
    }
    
    logger = setup_logger(tmp_path)
    engine = BackupEngine(config, logger)
    
    engine.process_full_scan()
    
    assert (backup / "file.txt").exists()
    
    assert (tmp_path / "state.json").exists()
    