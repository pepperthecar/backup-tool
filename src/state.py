import json
import os
import time
from pathlib import Path

STATE_FILE = "state.json"


def load_state(state_dir: Path):
    state_path = state_dir / STATE_FILE
    if not state_path.exists():
        return {}

    try:
        with state_path.open('r', encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Corrupted state fallback
        backup_path = state_path.with_suffix(".corrupted")
        state_path.replace(backup_path)
        return {}


def save_state(state_dir: Path, state: dict):
    state_path = state_dir / STATE_FILE
    temp_path = state_path.with_suffix(".tmp")

    # Write to temporary file first
    with temp_path.open('w', encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        
    last_error = None

    for _ in range(5):
        try:
            os.replace(temp_path, state_path)
            break
        except PermissionError as e:
            last_error = e
            time.sleep(0.05)
    
        raise last_error

    # Atomic replace
    # temp_path.replace(state_path)
