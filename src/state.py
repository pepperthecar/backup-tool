import json
from pathlib import Path

STATE_FILE = "state.json"


def load_state(state_dir: Path):
    state_path = state_dir / STATE_FILE
    if not state_path.exists():
        return {}

    with state_path.open('r', encoding="utf-8") as f:
        return json.load(f)


def save_state(state_dir: Path, state: dict):
    state_path = state_dir / STATE_FILE

    with state_path.open('w', encoding="utf-8") as f:
        json.dump(state, f, indent=2)
