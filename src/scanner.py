from pathlib import Path


def scan_sources(sources: list[Path]):
    files = []

    for src in sources:
        for path in src.rglob("*"):
            if path.is_file():
                files.append(path)
    return files
