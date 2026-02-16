from pathlib import Path
from src.config import load_config
from src.logger import setup_logger
from src.engine import BackupEngine
from src.watcher import FolderWatcher
import time


def main():
    config = load_config(Path("config.json"))
    logger = setup_logger(config["log_dir"])

    engine = BackupEngine(config, logger)
    engine.process_full_scan()
    
    watcher = FolderWatcher(config['sources'], engine)
    watcher.start()
    
    print('Monitoring Started... Press Ctrl+C to exit.')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()

if __name__ == "__main__":
    main()
