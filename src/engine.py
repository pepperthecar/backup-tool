from pathlib import Path
from src.scanner import scan_sources
from src.planner import plan, plan_single
from src.executor import execute
from src.retention import apply_retention
from src.state import load_state, save_state
import threading
import shutil


class BackupEngine:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        self.state_dir = config["app_dir"]
        self.state = load_state(self.state_dir)

        self._lock = threading.Lock()

    # ---------------------------
    # FULL SCAN (existing CLI)
    # ---------------------------
    def process_full_scan(self):
        with self._lock:
            files = scan_sources(self.config["sources"])
            actions = plan(files, self.state, self.config["hash_algorithm"])

            self._log_actions(actions)

            duplicates_dir = self.config["backup_root"] / "_duplicates"
            execute(actions, self.config["backup_root"],
                    duplicates_dir, self.logger)

            self._update_state(actions)

            self._apply_retention()

            save_state(self.state_dir, self.state)
            self.logger.info("Run complete")

    # ---------------------------
    # SINGLE FILE SUPPORT
    # ---------------------------
    def process_single_file(self, file_path):
        with self._lock:
            action = plan_single(
                file_path,
                self.state,
                self.config["hash_algorithm"]
            )

            if not action:
                return

            self._log_actions([action])

            duplicates_dir = self.config["backup_root"] / "_duplicates"
            execute([action], self.config["backup_root"],
                    duplicates_dir, self.logger)

            self._update_state([action])
            save_state(self.state_dir, self.state)

    # ---------------------------
    # DELETION SUPPORT (basic)
    # ---------------------------
    def process_deleted(self, file_path):
        with self._lock:
            file_path = Path(file_path).resolve()
            key = str(file_path)

            backup_root = Path(self.config["backup_root"]).resolve()
            backup_file = backup_root / file_path.name

            deleted_dir = backup_root / "_deleted"
            deleted_dir.mkdir(exist_ok=True)

            # Move main backup file
            if backup_file.exists():
                target = deleted_dir / backup_file.name
                shutil.move(str(backup_file), str(target))
                self.logger.info(f"ARCHIVE DELETE: {backup_file} -> {target}")

            # Remove from state
            if key in self.state:
                del self.state[key]
                save_state(self.state_dir, self.state)
                self.logger.info(f"STATE REMOVE: {file_path}")

    # ---------------------------
    # INTERNAL HELPERS
    # ---------------------------
    def _log_actions(self, actions):
        for a, p, _ in actions:
            self.logger.info(f"PLANNER → {a.upper()}: {p}")

    def _update_state(self, actions):
        for action, path, h in actions:
            if action in ("backup", "modified"):
                self.state[str(path)] = {"hash": h}

    def _apply_retention(self):
        versions_root = self.config["backup_root"] / "versions"
        if "retention" in self.config:
            apply_retention(
                versions_root, self.config["retention"], self.logger)
