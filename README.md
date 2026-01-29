# Python Incremental Backup Tool

A deterministic, hash-based backup tool written in Python that performs **incremental backups**, **duplicate detection**, **versioned history**, and **retention cleanup** with full logging.

This project focuses on **correctness, safety, and auditability**, not UI or automation magic.

---

## Features

### Incremental backups
- Only new or modified files are processed
- Uses content hashing (not timestamps)
- Safe across restarts

### Duplicate detection
- Detects duplicates by hash, not filename
- Copies duplicates into a `_duplicates/` folder
- Original files are never deleted

### Versioned backups
- Modified files are never overwritten
- Previous versions are archived automatically
- Latest version always exists at the top level

### Retention policies
- Keeps only the most recent N versions per file
- Old versions are deleted deterministically
- All deletions are logged

### Safety guarantees
- All actions are logged

---

## Project Structure
```
backup_tool/
├── src/
| |── __init__.py
│ ├── main.py # Entry point
│ ├── config.py # Config loading & validation
│ ├── state.py # Persistent state
│ ├── scanner.py # Filesystem scanning
│ ├── hasher.py # Hashing logic
│ ├── planner.py # Decision engine
│ ├── executor.py # Safe file operations
│ ├── retention.py # Retention rules
│ └── logger.py # Logging
├── config.json
├── logs/
├── testdata/
│ ├── source/
│ └── backup/
|── tests/
| |── test_planner.py
└── README.md
```
---

## How It Works

1. Scan source directories (read-only)
2. Hash each file
3. Compare against stored state
4. Plan actions:
   - `backup` – new file
   - `modified` – content changed
   - `duplicate` – same content, different path
   - `skip` – unchanged
5. Execute actions safely
6. Archive old versions
7. Apply retention rules
8. Save updated state

---

## Configuration

### `config.json`

```json
{
  "sources": ["./testdata/source"],
  "backup_root": "./testdata/backup",
  "log_dir": "./logs",
  "hash_algorithm": "sha256",
  "retention": {
    "max_versions_per_file": 10
  }
}
```

### Configuration fields

| Key                               | Description                          |
| --------------------------------- | ------------------------------------ |
| `sources`                         | Directories to back up               |
| `backup_root`                     | Backup destination                   |
| `log_dir`                         | Log output directory                 |
| `hash_algorithm`                  | Hash algorithm (recommended: sha256) |
| `retention.max_versions_per_file` | Versions to keep per file            |

---

### Run the backup:
```
python src/main.py
```
Behavior:
- First run copies all files
- Subsequent runs finish quickly
- Modified files create versions
- Retention is enforced automatically

---

### Backup Layout Example:
```
backup/
├── one.txt
├── two.txt
├── state.json
├── _duplicates/
│   └── one_copy.txt
└── versions/
    └── one.txt/
        ├── v3.bak
        ├── v4.bak
        ├── v5.bak
        ├── v6.bak
        └── v7.bak
```
Only the most recent N versions are retained.

---

### Logging

Each run creates a timestamped log file in logs/.

Example:
```
BACKUP: source/one.txt → backup/one.txt
DUPLICATE: source/one_copy.txt → backup/_duplicates/one_copy.txt
ARCHIVE: backup/one.txt → versions/one.txt/v3.bak
UPDATED: source/one.txt → backup/one.txt
RETENTION delete: versions/one.txt/v1.bak
Run complete
```

---
