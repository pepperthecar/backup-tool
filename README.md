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
python -m src.main
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

## Quick Test Setup (After Initial Setup)

After installing dependencies and verifying the project runs, you can create a local test environment to observe incremental behavior, versioning, duplicates, and logs.

### 1. Create test directories

From the project root:
```
mkdir -p testdata/source
mkdir -p testdata/backup
```

Your structure should now include:
```
testdata/
├── source/
└── backup/
```
---
### 2. Add initial test files

Create some files in the source directory:
```
echo "hello world" > testdata/source/one.txt
echo "another file" > testdata/source/two.txt
echo "hello world" > testdata/source/one_copy.txt
```

This setup intentionally includes:
- A duplicate file (one_copy.txt)
- Multiple distinct files
---
### 3. Run the backup (first run)

```
python -m src.main
```

Expected behavior:

- All files are copied
- Duplicates are detected by hash
- State file is created
- Log file is written

Example log output:
```
BACKUP: source/one.txt → backup/one.txt
BACKUP: source/two.txt → backup/two.txt
DUPLICATE: source/one_copy.txt → backup/_duplicates/one_copy.txt
Run complete
```
---
### 4. Modify files and re-run

Edit an existing file:
```
echo "hello world v2" >> testdata/source/one.txt
```

Add a new file:
```
echo "new file" > testdata/source/three.txt
```

Run again:
```
python -m src.main
```

Expected behavior:

- Modified files are archived, not overwritten
- New files are backed up
- Unchanged files are skipped

Example log output:
```
ARCHIVE: backup/one.txt → versions/one.txt/v1.bak
UPDATED: source/one.txt → backup/one.txt
BACKUP: source/three.txt → backup/three.txt
SKIP: source/two.txt
Run complete
```
---
### 5. Trigger retention cleanup

If you repeatedly modify the same file:
```
echo "change" >> testdata/source/one.txt
```
```
python -m src.main
```

Once the number of versions exceeds the configured limit:
```
RETENTION delete: versions/one.txt/v1.bak
```
Older versions are removed deterministically and logged.
---
### 6. Inspect results

Check:
- ```testdata/backup/``` → current files
- ```testdata/backup/versions/``` → version history
- ```testdata/backup/_duplicates/``` → detected duplicates
- ```logs/``` → full audit trail

What this verifies:

- Incremental behavior
- Hash-based duplicate detection
- Versioned backups
- Retention enforcement
- Deterministic logging
---