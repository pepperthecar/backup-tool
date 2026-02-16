import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path


class DebouncedHandler(FileSystemEventHandler):
    # def __init__(self, engine, debounce_seconds=1):
    #     self.engine = engine
    #     self.debounce_seconds = debounce_seconds
    #     self.pending = {}
    #     self.lock = threading.Lock()

    # def _schedule(self, path, event_type):
    #     with self.lock:
    #         self.pending[path] = time.time()

    # def _process_pending(self):
    #     while True:
    #         now = time.time()
    #         to_process = []

    #         with self.lock:
    #             for path, ts in list(self.pending.items()):
    #                 if now - ts >= self.debounce_seconds:
    #                     to_process.append(path)
    #                     del self.pending[path]

    #         for path in to_process:
    #             try:
    #                 self.engine.process_single_file(path)
    #             except Exception as e:
    #                 print(f"ERROR Processing {path}: {e}" )

    #         time.sleep(0.5)

    # def start_background_worker(self):
    #     t = threading.Thread(target=self._process_pending, daemon=True)
    #     t.start()

    # def on_created(self, event):
    #     if not event.is_directory:
    #         self._schedule(event.src_path, "created")

    # def on_modified(self, event):
    #     if not event.is_directory:
    #         self._schedule(event.src_path, "modified")

    # def on_deleted(self, event):
    #     if not event.is_directory:
    #         self.engine.process_deleted(event.src_path)

    def __init__(self, engine, debounce_seconds=1):
        self.engine = engine
        self.debounce_seconds = debounce_seconds
        self.pending = {}
        self.lock = threading.Lock()

        # Resolve backup root once
        self.backup_root = Path(engine.config["backup_root"]).resolve()

    # ---------------------------
    # SAFETY FILTER
    # ---------------------------
    def _is_in_backup(self, path):
        path = Path(path).resolve()
        return path == self.backup_root or self.backup_root in path.parents

    def _schedule(self, path):
        with self.lock:
            self.pending[path] = time.time()

    def _process_pending(self):
        while True:
            now = time.time()
            to_process = []

            with self.lock:
                for path, ts in list(self.pending.items()):
                    if now - ts >= self.debounce_seconds:
                        to_process.append(path)
                        del self.pending[path]

            for path in to_process:
                try:
                    self.engine.process_single_file(path)
                except Exception as e:
                    print(f"ERROR Processing {path}: {e}")

            time.sleep(0.5)

    def start_background_worker(self):
        t = threading.Thread(target=self._process_pending, daemon=True)
        t.start()

    def on_created(self, event):
        if not event.is_directory and not self._is_in_backup(event.src_path):
            self._schedule(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and not self._is_in_backup(event.src_path):
            self._schedule(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and not self._is_in_backup(event.src_path):
            self.engine.process_deleted(event.src_path)


class FolderWatcher:
    def __init__(self, paths, engine):
        self.observer = Observer()
        self.handler = DebouncedHandler(engine)

        for path in paths:
            self.observer.schedule(self.handler, path, recursive=True)

    def start(self):
        self.handler.start_background_worker()
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
