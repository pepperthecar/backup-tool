import hashlib
from pathlib import Path


def hash_file(path: Path, algorithm: str = "sha256"):
    h = hashlib.new(algorithm)

    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
