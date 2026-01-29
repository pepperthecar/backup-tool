import shutil
from pathlib import Path


def execute(actions, backup_root: Path, duplicates_dir: Path, logger):
    versions_root = backup_root / "versions"
    versions_root.mkdir(parents=True, exist_ok=True)
    duplicates_dir.mkdir(parents=True, exist_ok=True)

    for action, path, h in actions:
        dest = backup_root / path.name

        if action == "backup":
            if dest.exists():
                logger.warning(f"SKIP overwrite: {dest}")
                continue
            shutil.copy2(path, dest)
            logger.info(f"BACKUP: {path} → {dest}")
            # logger.info(f"{action.upper()}: {path} → {dest}")

        elif action == "modified":
            version_dir = versions_root / path.name
            version_dir.mkdir(parents=True, exist_ok=True)

            existing_versions = sorted(version_dir.glob("v*.bak"))
            next_version = f"v{len(existing_versions)+1}.bak"

            archived = version_dir / next_version
            shutil.move(dest, archived)

            shutil.copy2(path, dest)

            logger.info(f"ARCHIVE: {dest} -> {archived}")
            logger.info(f"UPDATED: {path} -> {dest}")

        elif action == "duplicate":
            dup_dest = duplicates_dir / path.name
            if not dup_dest.exists():
                shutil.copy2(path, dup_dest)
                logger.info(f"DUPLICATE: {path} -> {dup_dest}")

        elif action == "skip":
            logger.info(f"SKIP unchanged: {path}")
