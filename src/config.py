from pathlib import Path
import json
from src.appdirs import get_app_dir


class configError(Exception):
    pass


DEFAULT_CONFIG = {
    "sources": [],
    "backup_root": str(Path.home() / "Backup"),
    "log_dir": "logs",
    "hash_algorithm": "sha256",
    "retention": {
        "max_versions_per_file": 10
    }
}


def load_config():
    app_dir = get_app_dir()
    app_dir.mkdir(parents=True, exist_ok=True)

    config_path = app_dir / "config.json"

    # First run → create default config
    if not config_path.exists():
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    required_keys = {
        "sources",
        "backup_root",
        "log_dir",
        "hash_algorithm",
        "retention"
    }

    missing = required_keys - config.keys()
    if missing:
        raise configError(f"Missing config keys: {missing}")

    # Normalize paths
    config["sources"] = [
        Path(p).expanduser().resolve()
        for p in config["sources"]
    ]

    config["backup_root"] = Path(
        config["backup_root"]
    ).expanduser().resolve()

    # Log dir now inside app dir
    config["log_dir"] = (app_dir / config["log_dir"]).resolve()

    # Ensure directories exist
    config["backup_root"].mkdir(parents=True, exist_ok=True)
    config["log_dir"].mkdir(parents=True, exist_ok=True)

    # Store app_dir for engine/state usage
    config["app_dir"] = app_dir

    return config


def save_config(config: dict):
    app_dir = config["app_dir"]
    config_path = app_dir / "config.json"

    # Convert Path objects back to strings for JSON
    serializable = config.copy()
    serializable["sources"] = [str(p) for p in config["sources"]]
    serializable["backup_root"] = str(config["backup_root"])
    serializable["log_dir"] = "logs"  # keep relative inside app dir
    serializable.pop("app_dir", None)

    with config_path.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)
