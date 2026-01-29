from pathlib import Path
from config import load_config
from logger import setup_logger
from state import load_state, save_state
from scanner import scan_sources
from planner import plan
from executor import execute
from retention import apply_retention

def main():
    config = load_config(Path("config.json"))
    logger = setup_logger(config["log_dir"])

    state_dir = config["backup_root"]
    state = load_state(state_dir)

    files = scan_sources(config["sources"])
    actions = plan(files, state, config["hash_algorithm"])

    for a, p, _ in actions:
        logger.info(f"PLANNER → {a.upper()}: {p}")

    duplicates_dir = config["backup_root"] / "_duplicates"
    execute(actions, config["backup_root"], duplicates_dir, logger)

    versions_root = config["backup_root"] / "versions"
    if "retention" in config:
        apply_retention(versions_root, config["retention"], logger)

    for action, path, h in actions:
        if action in ("backup", "modified"):
            state[str(path)] = {"hash": h}

    save_state(state_dir, state)
    logger.info("Run complete")


if __name__ == "__main__":
    main()
