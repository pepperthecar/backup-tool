from pathlib import Path


def scan_sources(sources: list[Path]):
    files = []

    for src in sources:
        src_path = Path(src)
        
        for path in src_path.rglob("*"):
            if path.is_file():
                files.append(path)
    return files
