from datetime import datetime, timedelta


def apply_retention(versions_root, retention, logger):
    
    max_versions = retention.get("max_versions_per_file")
    keep_days = retention.get("keep_days")
    
    
    cutoff = None
    
    if keep_days:
        cutoff = datetime.now() - timedelta(days=keep_days)
        
    for file_dir in versions_root.iterdir():
        versions = sorted(file_dir.glob("v*.bak"), key=lambda p:p.stat().st_mtime)
        
        if cutoff:
            for v in versions:
                if datetime.fromtimestamp(v.stat().st_mtime) < cutoff:
                    v.unlink()
                    logger.info(f"RETENTION delete (age): {v}")
                    
        if max_versions and len(versions) > max_versions:
            for v in versions[:-max_versions]:
                v.unlink()
                logger.info(f"RETENTION delete (count): {v}")