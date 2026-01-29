from pathlib import Path
from src.retention import apply_retention
from src.logger import setup_logger

def test_retention_max_versions(tmp_path):
    versions_dir = tmp_path / "versions" / "file.txt"
    versions_dir.mkdir(parents=True)

    for i in range(1, 8):
        f = versions_dir / f"v{i}.bak"
        f.write_text(str(i))

    logger = setup_logger(tmp_path)

    apply_retention(
        versions_root=tmp_path / "versions",
        retention={"max_versions_per_file": 5},
        logger=logger,
    )

    remaining = list(versions_dir.glob("v*.bak"))
    assert len(remaining) == 5
