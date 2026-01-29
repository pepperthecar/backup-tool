from pathlib import Path
from src.planner import plan
from src.hasher import hash_file

def test_planner_duplicate_and_skip(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"

    a.write_text("same")
    b.write_text("same")

    state = {
        str(a.resolve()): {"hash": hash_file(a)}
    }

    actions = plan([a, b], state, "sha256")
    result = {p.name: action for action, p, _ in actions}

    assert result["a.txt"] == "skip"
    assert result["b.txt"] == "duplicate"


def test_planner_modified(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("old")

    state = {
        str(f.resolve()): {"hash": hash_file(f)}
    }

    f.write_text("new")

    actions = plan([f], state, "sha256")
    action, _, _ = actions[0]

    assert action == "modified"
