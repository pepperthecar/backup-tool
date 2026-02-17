from src.state import load_state


def test_state_corruption_creates_backup_and_returns_empty(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("INVALID JSON")

    state = load_state(tmp_path)

    assert state == {}
    assert (tmp_path / "state.corrupted").exists()
