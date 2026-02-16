from pathlib import Path
from src.hasher import hash_file


def _build_hash_index(state):
    hash_to_paths = {}
    for path_key, meta in state.items():
        hash_to_paths.setdefault(meta["hash"], set()).add(path_key)
    return hash_to_paths


def plan_single(path, state, algorithm, hash_index=None):
    path = Path(path)
    h = hash_file(path, algorithm)
    key = str(path.resolve())

    # Build index only if not provided
    if hash_index is None:
        hash_index = _build_hash_index(state)

    if key in state:
        if state[key]["hash"] != h:
            return ("modified", path, h)
        else:
            return ("skip", path, h)
    else:
        if h in hash_index:
            return ("duplicate", path, h)
        else:
            return ("backup", path, h)


def plan(files, state, algorithm):
    actions = []
    hash_index = _build_hash_index(state)

    for path in files:
        action = plan_single(path, state, algorithm, hash_index)
        actions.append(action)

    return actions
