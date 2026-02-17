from pathlib import Path
from src.config import load_config
from src.logger import setup_logger
from src.engine import BackupEngine
from src.watcher import FolderWatcher
import time


def main():
    try:
        config = load_config()
    except Exception as e:
        print(f"Config failed: {e}")
        return

    try:
        logger = setup_logger(config["log_dir"])
    except Exception as e:
        print(f"Logger setup failed: {e}")
        return

    try:
        engine = BackupEngine(config, logger)
        engine.process_full_scan()
    except Exception as e:
        print(f"Backup engine failed: {e}")
        return

    try:
        watcher = FolderWatcher(config['sources'], engine)
        watcher.start()
    except Exception as e:
        print(f"Watcher failed to start: {e}")
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    main()
