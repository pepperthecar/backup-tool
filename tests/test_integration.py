from pathlib import Path
from src.scanner import scan_sources
from src.planner import plan
from src.executor import execute
from src.state import load_state, save_state
from src.hasher import hash_file
from src.logger import setup_logger


def test_full_run(tmp_path):
    source = tmp_path / "source"
    backup = tmp_path / "backup"

    source.mkdir()
    backup.mkdir()

    f = source / "file.txt"
    f.write_text("data")

    logger = setup_logger(tmp_path)

    state = load_state(backup)
    files = scan_sources([source])
    actions = plan(files, state, "sha256")

    execute(actions, backup, backup / "_duplicates", logger)

    for action, path, h in actions:
        if action == "backup":
            state[str(path.resolve())] = {"hash": h}

    save_state(backup, state)

    assert (backup / "file.txt").exists()
    assert (backup / "state.json").exists()
