import sys
import os
import threading
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QTextEdit, QMenu, QStyle, QProgressBar,
    QSplitter, QTreeView, QHeaderView
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QDir, QSize
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QFileSystemModel

from src.config import load_config, save_config
from src.logger import setup_logger
from src.engine import BackupEngine
from src.watcher import FolderWatcher


# ==========================================================
# Qt Log Handler (THREAD SAFE)
# ==========================================================

class QtLogHandler(QObject, logging.Handler):
    log_signal = Signal(str)

    def __init__(self):
        QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)


# ==========================================================
# Worker Signals
# ==========================================================

class WorkerSignals(QObject):
    monitoring_started = Signal()
    monitoring_stopped = Signal()

# ==========================================================
# Assets
# ==========================================================


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

ICON_PATH = ASSETS_DIR / "app.ico"
START_ICON = ASSETS_DIR / "start.ico"
STOP_ICON = ASSETS_DIR / "stop.ico"
REFRESH_ICON = ASSETS_DIR / "refresh.ico"
EXIT_ICON = ASSETS_DIR / "exit.ico"

for icon in [ICON_PATH, START_ICON, STOP_ICON, REFRESH_ICON, EXIT_ICON]:
    if not icon.exists():
        raise FileNotFoundError(f"Missing icon: {icon}")

# ==========================================================
# Main Application
# ==========================================================


class BackupApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Backup Tool")
        self.resize(1200, 800)

        self.config = load_config()
        self.logger = setup_logger(self.config["log_dir"])

        self.watcher = None

        self._build_ui()
        self._connect_logger_to_ui()
        self.engine = BackupEngine(self.config, self.logger)

        self._set_ui_state("idle")

        self.signals = WorkerSignals()
        self._connect_signals()
        self._setup_tray()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(3000)

        self.logger.info("Application started.")

    # ==========================================================
    # LOGGER → UI
    # ==========================================================

    def _connect_logger_to_ui(self):
        self.qt_handler = QtLogHandler()
        self.qt_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )

        self.qt_handler.log_signal.connect(self.log_text.append)
        self.logger.addHandler(self.qt_handler)

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)

        # ================= LEFT PANEL =================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("<b>Backup Summary</b>"))
        left_layout.addWidget(
            QLabel(f"Destination:\n{self.config['backup_root']}")
        )

        left_layout.addSpacing(15)
        left_layout.addWidget(QLabel("<b>Source Folders</b>"))

        # Source model
        self.source_model = QStandardItemModel()
        self.source_model.setHorizontalHeaderLabels(["Sources"])

        self.source_tree = QTreeView()
        self.source_tree.setModel(self.source_model)
        self.source_tree.setAnimated(True)

        self.source_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        left_layout.addWidget(self.source_tree)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(remove_btn)

        left_layout.addLayout(btn_layout)

        left_layout.addSpacing(15)
        left_layout.addWidget(QLabel("<b>Status</b>"))

        self.progress = QProgressBar()
        self.progress.setValue(0)
        left_layout.addWidget(self.progress)

        self.status_label = QLabel("Idle")
        left_layout.addWidget(self.status_label)

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        # ================= RIGHT PANEL =================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Backup Structure</b>"))
        header_layout.addStretch()

        self.start_btn = QPushButton()
        self.start_btn.setIcon(QIcon(str(START_ICON)))
        self.start_btn.setIconSize(QSize(24, 24))
        self.start_btn.setToolTip("Start Monitoring")
        self.start_btn.clicked.connect(self.start_monitoring)
        header_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(QIcon(str(STOP_ICON)))
        self.stop_btn.setIconSize(QSize(24, 24))
        self.stop_btn.setToolTip("Stop Monitoring")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        header_layout.addWidget(self.stop_btn)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon(str(REFRESH_ICON)))
        self.refresh_btn.setIconSize(QSize(24, 24))
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_backup_tree)
        header_layout.addWidget(self.refresh_btn)

        # ✅ Exit button added here
        self.exit_btn = QPushButton()
        self.exit_btn.setIcon(QIcon(str(EXIT_ICON)))
        self.exit_btn.setIconSize(QSize(24, 24))
        self.exit_btn.setToolTip("Exit Application")
        self.exit_btn.clicked.connect(QApplication.quit)
        header_layout.addWidget(self.exit_btn)

        right_layout.addLayout(header_layout)

        # Backup model
        self.backup_model = QFileSystemModel()
        self.backup_model.setRootPath(str(self.config["backup_root"]))

        self.backup_tree = QTreeView()
        self.backup_tree.setModel(self.backup_model)
        self.backup_tree.setRootIndex(
            self.backup_model.index(str(self.config["backup_root"]))
        )
        self.backup_tree.setAnimated(True)
        self.backup_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        right_layout.addWidget(self.backup_tree, stretch=3)

        right_layout.addWidget(QLabel("<b>Logs</b>"))

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text, stretch=2)

        splitter.addWidget(right_panel)

        # splitter.setStretchFactor(1, 1)
        # splitter.setStretchFactor(0, 1)
        # splitter.setStretchFactor(1, 3)

        self.refresh_sources()

    # ==========================================================
    # SOURCE MANAGEMENT
    # ==========================================================

    def refresh_sources(self):
        self.source_model.clear()
        self.source_model.setHorizontalHeaderLabels(["Sources"])

        for source in self.config["sources"]:
            path = Path(source)
            if not path.exists():
                continue

            root_item = QStandardItem(str(path))
            root_item.setEditable(False)
            self.source_model.appendRow(root_item)

    #         self._populate_directory(root_item, path)

    # def _populate_directory(self, parent_item, path: Path):
    #     try:
    #         for child in path.iterdir():
    #             item = QStandardItem(child.name)
    #             item.setEditable(False)
    #             parent_item.appendRow(item)

    #             if child.is_dir():
    #                 self._populate_directory(item, child)
    #     except PermissionError:
    #         pass

    # def on_source_selected(self, index):
    #     item = self.source_model.itemFromIndex(index)
    #     if not item:
    #         return

    #     path = item.text()

    #     if Path(path).is_dir():
    #         print(f"Selected source: {path}")

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")

        if folder:
            path = Path(folder).resolve()
            # if str(path) not in [str(s) for s in self.config["sources"]]:
            #     self.config["sources"].append(str(path))
            #     save_config(self.config)
            #     self.refresh_sources()
            if str(path) not in self.config["sources"]:
                self.config["sources"].append(str(path))
                save_config(self.config)
                self.refresh_sources()
                self.logger.info(f"Added source: {path}")

    def remove_selected(self):
        index = self.source_tree.currentIndex()
        if not index.isValid():
            return

        item = self.source_model.itemFromIndex(index)

        # Only allow removing top-level sources
        if item.parent() is not None:
            return

        selected_path = Path(item.text()).resolve()

        self.config["sources"] = [
            str(Path(s).resolve())
            for s in self.config["sources"]
            if Path(s).resolve() != selected_path
        ]

        save_config(self.config)
        self.refresh_sources()
        self.logger.info(f"Removed source: {selected_path}")

    # ==========================================================
    # MONITORING
    # ==========================================================

    def _connect_signals(self):
        self.signals.monitoring_started.connect(self._on_monitoring_started)
        self.signals.monitoring_stopped.connect(self._on_monitoring_stopped)

    def _set_ui_state(self, state: str):
        if state == "idle":
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.refresh_btn.setEnabled(True)

        elif state == "scanning":
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)

        elif state == "monitoring":
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.refresh_btn.setEnabled(False)

    def _on_monitoring_started(self):
        self.status_label.setText("Monitoring...")
        self._set_ui_state("monitoring")

    def _on_monitoring_stopped(self):
        self.status_label.setText("Stopped")
        self._set_ui_state("idle")

    def start_monitoring(self):
        if not self.config["sources"]:
            QMessageBox.warning(
                self,
                "No Sources",
                "Add at least one source folder."
            )
            return

        if self.watcher:
            return

        self._set_ui_state("scanning")
        self.status_label.setText("Scanning...")

        threading.Thread(
            target=self._start_engine,
            daemon=True
        ).start()

    def _start_engine(self):
        try:
            self.engine.process_full_scan()

            self.watcher = FolderWatcher(
                self.config["sources"],
                self.engine
            )

            self.watcher.start()

            self.signals.monitoring_started.emit()

        except Exception:
            import traceback
            traceback.print_exc()

    def stop_monitoring(self):
        if self.watcher:
            self.watcher.stop()
            self.watcher = None

        self.signals.monitoring_stopped.emit()

    # ==========================================================
    # REFRESH
    # ==========================================================

    def refresh_backup_tree(self):
        self.backup_model.setRootPath(str(self.config["backup_root"]))
        self.backup_tree.setRootIndex(
            self.backup_model.index(str(self.config["backup_root"]))
        )

    def auto_refresh(self):
        if self.watcher:
            self.refresh_backup_tree()

    # ==========================================================
    # TRAY
    # ==========================================================

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        # self.tray = QSystemTrayIcon(icon, self)
        self.tray = QSystemTrayIcon(QIcon(str(ICON_PATH)), self)

        menu = QMenu()

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.showNormal)
        menu.addAction(open_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def closeEvent(self, event):
        if hasattr(self, "tray") and self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()


# ==========================================================
# ENTRY
# ==========================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))

    window = BackupApp()
    window.setWindowIcon(QIcon(str(ICON_PATH)))

    window.show()
    sys.exit(app.exec())
