import os
import platform
from pathlib import Path

APP_NAME = "BackupTool"


def get_app_dir() -> Path:
    system = platform.system()

    if system == "Windows":
        return Path(os.getenv("APPDATA")) / APP_NAME # type: ignore
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        return Path.home() / ".config" / APP_NAME
