from pathlib import Path
import json


class configError(Exception):
    pass


def load_config(path: Path):
    if not path.exists():
        raise configError(f"config file not found: {path}")

    with path.open('r', encoding="utf-8") as f:
        config = json.load(f)

    required_keys = {
        "sources",
        "backup_root",
        "log_dir",
        "organize",
        "hash_algorithm",
        "versioning"
    }

    missing = required_keys - config.keys()
    if missing:
        raise configError(f"Missing config keys: {missing}")

    config["sources"] = [Path(p).expanduser().resolve()
                         for p in config["sources"]]
    config["backup_root"] = Path(config["backup_root"]).expanduser().resolve()
    config["log_dir"] = Path(config["log_dir"]).expanduser().resolve()

    for src in config["sources"]:
        if not src.exists():
            raise configError(f"Source does not exist: {src}")

    config["backup_root"].mkdir(parents=True, exist_ok=True)
    config["log_dir"].mkdir(parents=True, exist_ok=True)

    return config
