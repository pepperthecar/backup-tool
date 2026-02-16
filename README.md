# Python Incremental Backup Tool

A deterministic, hash-based backup engine written in Python that performs **incremental backups**, **duplicate detection**, **versioned history**, and **retention cleanup** with full logging and crash-safe state management.

This project focuses on **correctness, safety, and auditability**, not UI Shortcuts or automation gimmicks.

---

## Features

### Incremental backups
- Only new or modified files are processed
- Uses content hashing (not timestamps)
- Safe across restarts
- Deterministic decision logic

### Real-time monitoring (event-driven mode)
- Filesystem event monitoring using `watchdog`
- Processes changes incrementally
- Debounced to prevent duplicate processing
- Thread-safe under concurrent file activity

### Duplicate detection
- Detects duplicates by content hash, not filename
- Copies duplicates into a `_duplicates/` folder
- Original files are never deleted automatically
- Deterministic behavior across run

### Versioned backups
- Modified files are never overwritten
- Previous versions are archived automatically
- Latest version always exists at the top level
- Historical versions stored in `versions/`

### Delete archival
When a source file is deleted:
- The corresponding backup file is moved to `_deleted/` 
- The file is removed from persistent state
- No data is permanently deleted automatically
- All actions are logged

Example:
```
backup/
├── file.txt
├── _deleted/
│   └── file.txt
```

This ensures:
- No accidental data loss
- Full audit trail
- Deterministic lifecycle behavior

### Retention policies
- Keeps only the most recent N versions per file
- Old versions are deleted deterministically
- All deletions are logged

### Safety guarantees
- All actions are logged

### Backup-root exclusion safety
The system automatically ignores filesystem events originating from the backup directory.

This prevents:
- Recursive self-backup loops
- Infinite nested backup growth
- Disk exhaustion due to misconfiguration

Even if `backup_root` is placed inside a monitored source directory, the system remains stable.

### Thread-safe state management

- Engine-level locking prevents race conditions
- Concurrent file events handled safely
- State updates are atomic

### Crash-safe state persistence

- State writes use temporary file + atomic replace
- Windows-safe retry logic prevents file-lock failures
- Protects against JSON corruption
- Safe under forced termination

---

## Project Structure
```
backup_tool/
├── src/
│ ├── __init__.py
│ ├── main.py           # Entry point
│ ├── engine.py         # Orchestration layer
│ ├── config.py         # Config loading & validation
│ ├── state.py          # Atomic state persistence
│ ├── scanner.py        # Filesystem scanning
│ ├── hasher.py         # Hashing logic
│ ├── planner.py        # Decision engine
│ ├── executor.py       # Safe file operations
│ ├── retention.py      # Retention rules
│ ├── watcher.py        # Event-driven monitoring
│ └── logger.py         # Logging
├── config.json
├── logs/
├── testdata/
│ ├── source/
│ └── backup/
├── tests/
│ └── test_planner.py
└── README.md
```
---

## How It Works

1. Monitor source directories (event-driven)
2. Hash modified or new files
3. Compare against stored state
4. Plan actions:
   - `backup` – new file
   - `modified` – content changed
   - `duplicate` – same content, different path
   - `skip` – unchanged
5. Execute file operations safely
6. Archive previous versions
7. Archive deleted files into `_deleted/`
8. Apply retention rules
9. Persist updated state atomically

The system is deterministic and safe across restarts.

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
- State updated atomically

### Monitoring mode (real-time)

When monitoring is enabled, the tool:

- Watches source folders continuously
- Reacts to file creation/modification/deletion
- Archives deleted files safely
- Maintains deterministic state
---

### Backup Layout Example:
```
backup/
├── one.txt
├── two.txt
├── state.json
├── _duplicates/
│   └── one_copy.txt
├── _deleted/
│   └── old_file.txt
└── versions/
    └── one.txt/
        ├── v3.bak
        ├── v4.bak
        ├── v5.bak
        ├── v6.bak
        └── v7.bak
```
Only the most recent N versions are retained. 
 
Deleted files are archived in `_deleted/`

---

### Logging

Each run creates a timestamped log file in logs/.

Example:
```
PLANNER → BACKUP: source/one.txt
BACKUP: source/one.txt → backup/one.txt
ARCHIVE: backup/one.txt → versions/one.txt/v3.bak
UPDATED: source/one.txt → backup/one.txt
ARCHIVE DELETE: backup/old.txt → backup/_deleted/old.txt
STATE REMOVE: source/old.txt
RETENTION delete: versions/one.txt/v1.bak
Run complete
```
All actions are logged deterministically.

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