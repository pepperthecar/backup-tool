from pathlib import Path
from src.hasher import hash_file


def plan(files, state, algorithm):
    actions = []

    hash_to_paths = {}
    for path_key, meta in state.items():
        hash_to_paths.setdefault(meta["hash"], set()).add(path_key)
    # known_hashes = {v["hash"] for v in state.values()}

    for path in files:
        h = hash_file(path, algorithm)
        key = str(path.resolve())

        if key in state:
            if state[key]["hash"] != h:
                actions.append(("modified", path, h))
            else:
                actions.append(("skip", path, h))
        else:
            if h in hash_to_paths:
                actions.append(("duplicate", path, h))
            else:
                actions.append(("backup", path, h))

    return actions
