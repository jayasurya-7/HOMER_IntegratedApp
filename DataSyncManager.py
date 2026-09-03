import sys
import os
import logging
import shutil
import subprocess
import zstandard as zstd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QComboBox, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

LOG_FILE = "C:/pythonscripts/dataSyncManager.log"
PLUTO_STATUS_FILE = "C:/DeviceSetups/Pluto/uploadStatus.txt"
MARS_STATUS_FILE = "C:/DeviceSetups/Mars/uploadStatus.txt"
BUCKET_NAME = "homerclouds"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

MODERN_STYLESHEET = """
    QMainWindow {
        background-color: #0d1117;
    }

    QWidget {
        background-color: #0d1117;
        color: #e6edf3;
    }

    QLabel {
        color: #e6edf3;
    }

    QPushButton {
        background-color: #238636;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 10px 18px;
        font-weight: bold;
        font-size: 12px;
    }

    QPushButton:hover {
        background-color: #2ea043;
    }

    QPushButton:pressed {
        background-color: #1f6feb;
    }

    QPushButton:disabled {
        background-color: #444c56;
        color: #8b949e;
    }

    QComboBox {
        background-color: #161b22;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 8px;
        font-size: 11px;
    }

    QProgressBar {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 4px;
        text-align: center;
        color: #e6edf3;
        height: 20px;
    }

    QProgressBar::chunk {
        background-color: #238636;
        border-radius: 3px;
    }

    QListWidget {
        background-color: #161b22;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 6px;
        font-size: 11px;
    }

    QFrame {
        background-color: #161b22;
        border: 2px solid #30363d;
        border-radius: 10px;
        padding: 15px;
    }
"""

def read_upload_status(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                parts = f.read().strip().split(',')
                if len(parts) >= 5:
                    return {
                        'path': parts[0].strip(),
                        'status': parts[1].strip(),
                        'device': parts[2].strip(),
                        'user': parts[3].strip(),
                        'location': parts[4].strip()
                    }
    except Exception as e:
        logging.error(f"Failed to read {filepath}: {e}")
    return None

def compress_file(file_path, compression_level=3):
    """Compress a single file using zstandard with checksum verification"""
    try:
        compressed_path = f"{file_path}.zst"
        original_size = os.path.getsize(file_path)
        cctx = zstd.ZstdCompressor(level=compression_level, write_checksum=True)

        with open(file_path, 'rb') as f_in:
            with open(compressed_path, 'wb') as f_out:
                f_out.write(cctx.compress(f_in.read()))

        compressed_size = os.path.getsize(compressed_path)
        ratio = (1 - compressed_size / original_size) * 100
        logging.info(f"Compressed: {file_path} -> {compressed_size} bytes (saved {ratio:.1f}%)")
        return compressed_path
    except Exception as e:
        logging.error(f"Failed to compress {file_path}: {e}")
        return None

def compress_rawdata_folder(folder_path, compression_level=3):
    """Compress all rawdata files in folder, skip .zst and .meta files"""
    compressed_files = []
    try:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.zst', '.meta')):
                    continue

                if 'rawdata' not in file.lower():
                    continue

                file_path = os.path.join(root, file)
                compressed_path = f"{file_path}.zst"

                if os.path.exists(compressed_path):
                    original_mtime = os.path.getmtime(file_path)
                    compressed_mtime = os.path.getmtime(compressed_path)
                    if original_mtime <= compressed_mtime:
                        logging.info(f"Skipping (already compressed): {file}")
                        compressed_files.append((file_path, compressed_path))
                        continue

                compressed = compress_file(file_path, compression_level)
                if compressed:
                    compressed_files.append((file_path, compressed))

        logging.info(f"Compression complete. Total files compressed: {len(compressed_files)}")
        return compressed_files
    except Exception as e:
        logging.error(f"Error during folder compression: {e}")
        return []

def check_aws_sync(local_path, device_name, user_id, location):
    try:
        data_folder = os.path.join(local_path, "data")
        s3_path = f"s3://{BUCKET_NAME}/{location}/patients/{user_id}/{device_name}/"
        command = f'aws s3 sync "{data_folder}" {s3_path} --dryrun --exclude "*.meta" --exclude "*rawdata*.csv"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        pending_count = sum(1 for line in result.stdout.splitlines() if "upload:" in line or "copy:" in line)
        return pending_count == 0
    except Exception as e:
        logging.error(f"AWS sync check failed: {e}")
        return False

class VerifyWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, dict)

    def run(self):
        try:
            results = {}
            self.status.emit("Verifying Pluto...")
            pluto_info = read_upload_status(PLUTO_STATUS_FILE)
            if pluto_info:
                results['pluto'] = check_aws_sync(pluto_info['path'], pluto_info['device'], pluto_info['user'], pluto_info['location'])
            else:
                results['pluto'] = False
            self.progress.emit(50)

            self.status.emit("Verifying Mars...")
            mars_info = read_upload_status(MARS_STATUS_FILE)
            if mars_info:
                results['mars'] = check_aws_sync(mars_info['path'], mars_info['device'], mars_info['user'], mars_info['location'])
            else:
                results['mars'] = False
            self.progress.emit(100)

            self.finished.emit(True, results)
        except Exception as e:
            self.finished.emit(False, {})
            logging.error(f"Verification error: {e}")

class AWSyncWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, local_path, device_name, user_id, location):
        super().__init__()
        self.local_path = local_path
        self.device_name = device_name
        self.user_id = user_id
        self.location = location

    def run(self):
        try:
            data_folder = os.path.join(self.local_path, "data")

            self.status.emit(f"Compressing rawdata files...")
            rawdata_folder = os.path.join(data_folder, "rawdata")
            if os.path.exists(rawdata_folder):
                compressed_files = compress_rawdata_folder(rawdata_folder, compression_level=3)
                logging.info(f"Compressed {len(compressed_files)} rawdata files")
            self.progress.emit(15)

            self.status.emit(f"Syncing {self.device_name}...")
            s3_path = f"s3://{BUCKET_NAME}/{self.location}/patients/{self.user_id}/{self.device_name}/"
            command = f'aws s3 sync "{data_folder}" {s3_path} --exclude "*.meta" --exclude "*rawdata*.csv"'
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            uploaded = 0
            for line in process.stdout:
                if "upload:" in line or "copy:" in line:
                    uploaded += 1
                    self.progress.emit(min(15 + (uploaded * 2), 95))
            process.wait()
            if process.returncode == 0:
                self.progress.emit(100)
                self.finished.emit(True, "AWS sync completed")
            else:
                self.finished.emit(False, "AWS sync failed")
        except Exception as e:
            self.finished.emit(False, str(e))
            logging.error(f"AWS sync error: {e}")

class SyncWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, source_path, dest_path, device_name, user_id):
        super().__init__()
        self.source_path = source_path
        self.device_name = device_name
        self.user_id = user_id
        self.final_dest = os.path.join(dest_path, f"{user_id}_{device_name}")

    def run(self):
        try:
            if not os.path.exists(self.source_path):
                self.finished.emit(False, f"Source path not found")
                return

            if os.path.exists(self.final_dest) and self._count_files(self.final_dest) > 0:
                self.finished.emit(False, f"Already copied")
                return

            file_count = self._count_files(self.source_path)
            if file_count == 0:
                self.finished.emit(False, "No files found")
                return

            copied = self._copy_with_verification(self.source_path, self.final_dest, file_count)
            if copied == file_count:
                self.finished.emit(True, f"All {file_count} files copied")
            else:
                self.finished.emit(True, f"{copied}/{file_count} files copied")
        except Exception as e:
            self.finished.emit(False, str(e))
            logging.error(f"Sync error: {e}")

    def _count_files(self, path):
        count = 0
        for root, _, files in os.walk(path):
            count += len(files)
        return count

    def _copy_with_verification(self, src, dst, total):
        copied = 0
        for root, _, files in os.walk(src):
            rel_root = os.path.relpath(root, src)
            dst_root = dst if rel_root == '.' else os.path.join(dst, rel_root)
            os.makedirs(dst_root, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_root, file)
                try:
                    shutil.copy2(src_file, dst_file)
                    if os.path.getsize(src_file) == os.path.getsize(dst_file):
                        copied += 1
                    self.progress.emit(int((copied / total) * 100) if total > 0 else 0)
                except Exception as e:
                    logging.error(f"Failed to copy {src_file}: {e}")
        return copied

class DataSyncManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_device = None
        self.selected_destination = None
        self.device_info = {}
        self.sync_status = {}
        self.copy_status_map = {'Pluto': False, 'Mars': False}
        self.step_status = {'verify': '⏳', 'sync': '⏳', 'copy': '⏳', 'erase': '⏳'}
        self.setStyleSheet(MODERN_STYLESHEET)
        self.initUI()
        self.load_devices()

    def initUI(self):
        self.setWindowTitle("Data Sync Manager - Pluto & Mars")
        self.setGeometry(50, 50, 1400, 800)
        self.showMaximized()  # Start in fullscreen

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        layout.setStretch(0, 0)  # Header doesn't stretch
        layout.setStretch(1, 0)  # Timeline doesn't stretch
        layout.setStretch(2, 1)  # Content stretches to fill

        # ===== HEADER =====
        header_h_layout = QHBoxLayout()
        header_h_layout.setContentsMargins(0, 0, 0, 0)
        header_h_layout.setSpacing(0)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("📦 Data Sync Manager")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel("Pluto & Mars - Sync, Copy & Backup")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #8b949e;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        self.device_status = QLabel("Loading device information...")
        self.device_status.setFont(QFont("Segoe UI", 10))
        self.device_status.setStyleSheet("color: #58a6ff; font-weight: bold;")
        header_layout.addWidget(self.device_status)

        header_h_layout.addLayout(header_layout, 1)

        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        close_btn.setFixedSize(120, 48)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #da3633;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f85149;
            }
            QPushButton:pressed {
                background-color: #c5222b;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_h_layout.addWidget(close_btn, alignment=Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(header_h_layout)

        # ===== TIMELINE =====
        timeline_layout = QHBoxLayout()
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        timeline_layout.setSpacing(12)

        self.step_labels = {}
        self.step_boxes = {}
        steps = [
            ('verify', '✓ Verify Sync'),
            ('sync', '✓ Sync AWS'),
            ('copy', '✓ Copy Local'),
            ('erase', '✓ Erase Source')
        ]

        for idx, (step_id, step_text) in enumerate(steps):
            # Simple step box
            step_box = QLabel(f"{self.step_status[step_id]}\n{step_text}")
            step_box.setAlignment(Qt.AlignCenter)
            step_box.setStyleSheet("""
                QLabel {
                    background-color: #161b22;
                    color: #ffffff;
                    border: 2px solid #1f6feb;
                    border-radius: 8px;
                    padding: 12px;
                    font-weight: bold;
                    font-size: 12px;
                    min-width: 140px;
                    min-height: 60px;
                }
            """)
            self.step_labels[step_id] = step_box
            self.step_boxes[step_id] = step_box
            timeline_layout.addWidget(step_box, 1)  # Stretch factor = 1 (expands equally)

            # Arrow between steps
            if idx < len(steps) - 1:
                arrow = QLabel("→")
                arrow.setAlignment(Qt.AlignCenter)
                arrow.setStyleSheet("color: #30363d; font-size: 18px; font-weight: bold;")
                arrow.setMinimumWidth(30)
                timeline_layout.addWidget(arrow, 0)  # Arrow doesn't stretch

        layout.addLayout(timeline_layout)

        # ===== CONTENT AREA =====
        content_layout = QGridLayout()
        content_layout.setSpacing(12)
        content_layout.setRowStretch(0, 1)  # Make content stretch vertically
        content_layout.setColumnStretch(0, 1)  # Equal column widths
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(2, 1)

        # LEFT: VERIFY & SYNC
        verify_frame = QFrame()
        verify_layout = QVBoxLayout(verify_frame)
        verify_layout.setSpacing(10)
        verify_layout.setStretch(3, 1)  # Results list stretches

        verify_title = QLabel("🔍 Verify & Sync Status")
        verify_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        verify_layout.addWidget(verify_title)

        verify_btn = QPushButton("Check Sync Status")
        verify_btn.setMinimumHeight(40)
        verify_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        verify_btn.clicked.connect(self.verify_sync)
        verify_layout.addWidget(verify_btn)

        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(120)
        verify_layout.addWidget(self.results_list)

        self.verify_progress = QProgressBar()
        self.verify_progress.setMinimumHeight(20)
        self.verify_progress.setVisible(False)
        verify_layout.addWidget(self.verify_progress)

        sync_btn_layout = QHBoxLayout()
        sync_btn_layout.setSpacing(8)

        self.aws_sync_pluto_btn = QPushButton("⬆ Sync Pluto to AWS")
        self.aws_sync_pluto_btn.setMinimumHeight(36)
        self.aws_sync_pluto_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.aws_sync_pluto_btn.clicked.connect(lambda: self.sync_to_aws("Pluto"))
        self.aws_sync_pluto_btn.setVisible(False)
        self.aws_sync_pluto_btn.setStyleSheet("QPushButton { background-color: #d1542e; } QPushButton:hover { background-color: #da5c41; }")
        sync_btn_layout.addWidget(self.aws_sync_pluto_btn)

        self.aws_sync_mars_btn = QPushButton("⬆ Sync Mars to AWS")
        self.aws_sync_mars_btn.setMinimumHeight(36)
        self.aws_sync_mars_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.aws_sync_mars_btn.clicked.connect(lambda: self.sync_to_aws("Mars"))
        self.aws_sync_mars_btn.setVisible(False)
        self.aws_sync_mars_btn.setStyleSheet("QPushButton { background-color: #d1542e; } QPushButton:hover { background-color: #da5c41; }")
        sync_btn_layout.addWidget(self.aws_sync_mars_btn)

        verify_layout.addLayout(sync_btn_layout)

        self.verify_status = QLabel("Status: Ready")
        self.verify_status.setFont(QFont("Segoe UI", 10))
        self.verify_status.setStyleSheet("color: #8b949e;")
        verify_layout.addWidget(self.verify_status)

        verify_layout.addStretch()
        content_layout.addWidget(verify_frame, 0, 0)

        # MIDDLE: COPY
        copy_frame = QFrame()
        copy_layout = QVBoxLayout(copy_frame)
        copy_layout.setSpacing(10)
        copy_layout.setStretch(5, 1)  # Status stretches

        copy_title = QLabel("💾 Copy to Local Drive")
        copy_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        copy_layout.addWidget(copy_title)

        dev_label = QLabel("Select Source Device:")
        dev_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        copy_layout.addWidget(dev_label)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumHeight(75)
        self.device_combo.setMinimumWidth(400)
        self.device_combo.setMaximumHeight(80)
        self.device_combo.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.device_combo.addItems(["🚀 Pluto", "🔴 Mars"])
        self.device_combo.currentTextChanged.connect(self.on_device_changed)
        self.device_combo.setStyleSheet("""
            QComboBox {
                background-color: #161b22;
                color: #e6edf3;
                border: 2px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
                width: 40px;
            }
            QComboBox QAbstractItemView {
                background-color: #161b22;
                color: #e6edf3;
                selection-background-color: #1f6feb;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px;
                height: 50px;
                font-size: 15px;
            }
        """)
        copy_layout.addWidget(self.device_combo)

        dest_lbl = QLabel("Select Destination Drive:")
        dest_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        copy_layout.addWidget(dest_lbl)

        dest_layout = QHBoxLayout()
        dest_layout.setSpacing(8)
        self.dest_label = QLabel("Not selected")
        self.dest_label.setFont(QFont("Segoe UI", 10))
        self.dest_label.setStyleSheet("color: #8b949e; padding: 8px; background-color: #0d1117; border-radius: 5px;")
        dest_layout.addWidget(self.dest_label, 1)

        select_dest_btn = QPushButton("📁 Browse")
        select_dest_btn.setMaximumWidth(100)
        select_dest_btn.setMinimumHeight(36)
        select_dest_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        select_dest_btn.clicked.connect(self.select_destination)
        dest_layout.addWidget(select_dest_btn)
        copy_layout.addLayout(dest_layout)

        self.copy_btn = QPushButton("▶ Start Copy")
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.copy_btn.setStyleSheet("QPushButton { background-color: #238636; }")
        self.copy_btn.clicked.connect(self.start_sync)
        self.copy_btn.setEnabled(False)
        copy_layout.addWidget(self.copy_btn)

        self.copy_progress = QProgressBar()
        self.copy_progress.setMinimumHeight(20)
        self.copy_progress.setVisible(False)
        copy_layout.addWidget(self.copy_progress)

        self.copy_status = QLabel("Status: Ready")
        self.copy_status.setFont(QFont("Segoe UI", 10))
        self.copy_status.setStyleSheet("color: #8b949e;")
        copy_layout.addWidget(self.copy_status)

        copy_layout.addStretch()
        content_layout.addWidget(copy_frame, 0, 1)

        # RIGHT: ERASE & ACTIONS
        erase_frame = QFrame()
        erase_layout = QVBoxLayout(erase_frame)
        erase_layout.setSpacing(10)
        erase_layout.setStretch(6, 1)  # Summary stretches

        erase_title = QLabel("🗑️ Erase Source Data")
        erase_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        erase_layout.addWidget(erase_title)

        info_text = QLabel("After successful copy\nverification, safely erase\nthe source data")
        info_text.setFont(QFont("Segoe UI", 10))
        info_text.setStyleSheet("color: #8b949e; line-height: 1.6;")
        erase_layout.addWidget(info_text)

        self.erase_btn = QPushButton("🗑️  Erase Source Data")
        self.erase_btn.setMinimumHeight(40)
        self.erase_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.erase_btn.setStyleSheet("QPushButton { background-color: #d1542e; } QPushButton:hover { background-color: #da5c41; }")
        self.erase_btn.clicked.connect(self.erase_source_data)
        self.erase_btn.setEnabled(False)
        erase_layout.addWidget(self.erase_btn)

        erase_layout.addSpacing(16)

        summary_title = QLabel("📋 Workflow Guide:")
        summary_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        erase_layout.addWidget(summary_title)

        summary = QLabel("✅ Step 1: Verify sync status\n✅ Step 2: Sync to AWS if needed\n✅ Step 3: Copy data locally\n✅ Step 4: Erase source data")
        summary.setFont(QFont("Segoe UI", 9))
        summary.setStyleSheet("color: #8b949e; line-height: 1.8;")
        erase_layout.addWidget(summary)

        erase_layout.addStretch()
        content_layout.addWidget(erase_frame, 0, 2)

        layout.addLayout(content_layout, 1)  # Stretches to fill available space

    def update_timeline(self):
        """Update timeline based on current status"""
        colors = {
            '⏳': '#1f6feb',  # Blue - pending
            '⚙️': '#ff9800',  # Orange - processing
            '✅': '#4caf50',  # Green - completed
            '⚠️': '#f44336'   # Red - error
        }

        step_texts = {
            'verify': '✓ Verify Sync',
            'sync': '✓ Sync AWS',
            'copy': '✓ Copy Local',
            'erase': '✓ Erase Source'
        }

        for step_id, label in self.step_labels.items():
            icon = self.step_status.get(step_id, '⏳')
            step_text = step_texts.get(step_id, 'Step')
            label.setText(f"{icon}\n{step_text}")

            # Update box border color
            if step_id in self.step_boxes:
                box = self.step_boxes[step_id]
                border_color = colors.get(icon, '#1f6feb')

                box.setStyleSheet(f"""
                    QLabel {{
                        background-color: #161b22;
                        color: #ffffff;
                        border: 2px solid {border_color};
                        border-radius: 8px;
                        padding: 12px;
                        font-weight: bold;
                        font-size: 12px;
                        min-width: 140px;
                        min-height: 60px;
                    }}
                """)

    def load_devices(self):
        pluto_info = read_upload_status(PLUTO_STATUS_FILE)
        mars_info = read_upload_status(MARS_STATUS_FILE)
        if pluto_info:
            self.device_info['Pluto'] = pluto_info
        if mars_info:
            self.device_info['Mars'] = mars_info

        # Update device status display
        device_display = []
        if pluto_info:
            device_display.append(f"🚀 Pluto: {pluto_info['user']}")
        if mars_info:
            device_display.append(f"🔴 Mars: {mars_info['user']}")

        if device_display:
            self.device_status.setText("Loaded Devices • " + " | ".join(device_display))
            self.device_status.setStyleSheet("color: #58a6ff; font-weight: bold;")
        else:
            self.device_status.setText("⚠️ No devices found - Check uploadStatus.txt files")
            self.device_status.setStyleSheet("color: #f85149; font-weight: bold;")

    def check_if_already_copied(self):
        """Check if data has already been copied for each device"""
        for device_name in ['Pluto', 'Mars']:
            if device_name in self.device_info:
                device_info = self.device_info[device_name]
                user_id = device_info.get('user', '')
                copied_folder = f"{user_id}_{device_name}"

                if self.selected_destination:
                    dest_path = os.path.join(self.selected_destination, copied_folder)
                    if os.path.exists(dest_path) and os.listdir(dest_path):
                        self.copy_status_map[device_name] = True

    def update_button_states(self):
        """Enable/disable buttons based on workflow step completion"""
        verify_done = self.step_status['verify'] == '✅'
        sync_done = self.step_status['sync'] == '✅'

        self.check_if_already_copied()
        both_copied = all(self.copy_status_map.values())

        self.copy_btn.setEnabled(verify_done and sync_done)
        self.erase_btn.setEnabled(verify_done and sync_done and both_copied)

        # Update copy status display to show both devices
        copied = [d for d, c in self.copy_status_map.items() if c]
        remaining = [d for d, c in self.copy_status_map.items() if not c]

        if both_copied:
            self.copy_status.setText(f"Status: ✅ Both devices copied - Pluto: ✓ Mars: ✓")
        else:
            status_text = f"Status: Pluto: {'✓' if 'Pluto' in copied else '✗'} | Mars: {'✓' if 'Mars' in copied else '✗'}"
            self.copy_status.setText(status_text)

        if not self.copy_btn.isEnabled():
            self.copy_btn.setToolTip("Complete verification and sync first")
        else:
            self.copy_btn.setToolTip("")

        if not self.erase_btn.isEnabled():
            tooltip = f"Copy both devices first. Copied: {', '.join(copied) if copied else 'None'}. Remaining: {', '.join(remaining)}"
            self.erase_btn.setToolTip(tooltip)
        else:
            self.erase_btn.setToolTip("")

    def on_device_changed(self, device):
        device_name = device.split()[-1] if device else device
        self.selected_device = device_name
        if device_name in self.device_info:
            user_id = self.device_info[device_name].get('user', 'Unknown')
            self.copy_status.setText(f"Status: Ready • Current: {device_name} (ID: {user_id})")
        else:
            self.copy_status.setText("Status: Ready")

    def select_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Drive")
        if folder:
            self.selected_destination = folder
            display = folder if len(folder) <= 40 else "..." + folder[-37:]
            self.dest_label.setText(display)
            self.dest_label.setToolTip(folder)
            self.update_button_states()

    def verify_sync(self):
        self.copy_status_map = {'Pluto': False, 'Mars': False}
        self.step_status['verify'] = '⚙️'
        self.update_timeline()
        self.verify_status.setText("Verifying...")
        self.verify_progress.setVisible(True)
        self.verify_progress.setValue(0)
        self.results_list.clear()

        self.verify_worker = VerifyWorker()
        self.verify_worker.progress.connect(self.verify_progress.setValue)
        self.verify_worker.status.connect(self.verify_status.setText)
        self.verify_worker.finished.connect(self.on_verify_complete)
        self.verify_worker.start()

    def on_verify_complete(self, success, results):
        self.verify_progress.setVisible(False)
        self.results_list.clear()
        self.aws_sync_pluto_btn.setVisible(False)
        self.aws_sync_mars_btn.setVisible(False)

        if success:
            self.sync_status = results
            all_synced = True

            for device, synced in results.items():
                status = "✅ SYNCED" if synced else "⚠️ NOT SYNCED"
                item = QListWidgetItem(f"  {device.upper()}: {status}")
                item.setFont(QFont("Segoe UI", 11, QFont.Bold))
                if synced:
                    item.setBackground(QColor(30, 40, 50))
                    item.setForeground(QColor(88, 166, 255))
                else:
                    all_synced = False
                    item.setBackground(QColor(50, 30, 30))
                    item.setForeground(QColor(248, 113, 113))
                    if device == "pluto":
                        self.aws_sync_pluto_btn.setVisible(True)
                    elif device == "mars":
                        self.aws_sync_mars_btn.setVisible(True)
                self.results_list.addItem(item)

            self.step_status['verify'] = '✅'
            self.step_status['sync'] = '✅' if all_synced else '⏳'
            self.update_timeline()
            self.update_button_states()
            self.verify_status.setText("✓ Verification complete")
            self.verify_status.setStyleSheet("color: #58a6ff;")
        else:
            self.step_status['verify'] = '⚠️'
            self.update_timeline()
            self.update_button_states()
            self.verify_status.setText("✗ Verification failed")
            self.verify_status.setStyleSheet("color: #f85149;")

    def sync_to_aws(self, device):
        if device not in self.device_info:
            QMessageBox.warning(self, "Error", f"{device} not found")
            return

        info = self.device_info[device]
        if QMessageBox.question(self, "Confirm Sync", f"Sync {device} to AWS?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.step_status['sync'] = '⚙️'
            self.update_timeline()
            self.verify_progress.setVisible(True)
            self.verify_progress.setValue(0)

            self.aws_sync_worker = AWSyncWorker(info['path'], info['device'], info['user'], info['location'])
            self.aws_sync_worker.progress.connect(self.verify_progress.setValue)
            self.aws_sync_worker.status.connect(self.verify_status.setText)
            self.aws_sync_worker.finished.connect(lambda success, msg: self.on_aws_sync_complete(success, msg, device))
            self.aws_sync_worker.start()

    def on_aws_sync_complete(self, success, message, device):
        self.verify_progress.setVisible(False)
        if success:
            self.step_status['sync'] = '✅'
            self.update_timeline()
            self.update_button_states()
            QMessageBox.information(self, "Success", f"{device} synced to AWS successfully!")
            self.verify_sync()
        else:
            self.step_status['sync'] = '⚠️'
            self.update_timeline()
            self.update_button_states()
            QMessageBox.critical(self, "Error", f"AWS sync failed: {message}")

    def start_sync(self):
        try:
            if not self.selected_device or self.selected_device not in self.device_info:
                QMessageBox.warning(self, "Error", "Please select a source device")
                return

            if not self.selected_destination:
                QMessageBox.warning(self, "Error", "Please select a destination drive")
                return

            info = self.device_info[self.selected_device]
            source = os.path.join(info['path'], "data")

            if not os.path.exists(source):
                QMessageBox.critical(self, "Error", f"Source path not found:\n{source}")
                return

            folder_name = f"{info['user']}_{info['device']}"
            if QMessageBox.question(self, "Confirm Copy", f"Copy {folder_name} from {self.selected_device}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.step_status['copy'] = '⚙️'
                self.update_timeline()
                self.copy_progress.setVisible(True)
                self.copy_progress.setValue(0)
                self.copy_status.setText(f"Copying {folder_name}... Please wait")

                self.sync_worker = SyncWorker(source, self.selected_destination, info['device'], info['user'])
                self.sync_worker.progress.connect(self.copy_progress.setValue)
                self.sync_worker.status.connect(self.copy_status.setText)
                self.sync_worker.finished.connect(self.on_sync_complete)
                self.sync_worker.start()

        except Exception as e:
            self.step_status['copy'] = '⚠️'
            self.update_timeline()
            QMessageBox.critical(self, "Error", str(e))
            logging.error(f"Error: {e}", exc_info=True)

    def on_sync_complete(self, success, message):
        self.copy_progress.setVisible(False)
        if success:
            if self.selected_device in self.copy_status_map:
                self.copy_status_map[self.selected_device] = True

            both_copied = all(self.copy_status_map.values())
            if both_copied:
                self.step_status['copy'] = '✅'
                self.copy_status.setText("Status: ✅ Copy Complete - All devices copied")
            else:
                self.step_status['copy'] = '⏳'
                self.copy_status.setText("Status: ✅ Copy Complete - Ready for next device")

            self.update_timeline()
            self.update_button_states()
            copied_devices = [d for d, c in self.copy_status_map.items() if c]
            QMessageBox.information(self, "Success", f"{message}\n\nCopied: {', '.join(copied_devices)}")
        else:
            self.step_status['copy'] = '⚠️'
            self.update_timeline()
            self.update_button_states()
            self.copy_status.setText("Status: ❌ Copy Failed - Please try again")
            if "Already copied" in message:
                QMessageBox.warning(self, "Already Copied", message)
            else:
                QMessageBox.critical(self, "Error", message)

    def erase_source_data(self):
        devices_to_erase = []
        for device_name, device_info in self.device_info.items():
            parent_path = device_info['path']
            if os.path.exists(parent_path):
                devices_to_erase.append((device_name, parent_path))

        if not devices_to_erase:
            QMessageBox.warning(self, "Error", "No devices found to erase")
            return

        devices_list = "\n".join([f"• {name}: {path}" for name, path in devices_to_erase])
        if QMessageBox.question(self, "⚠️ Final Confirmation", f"Are you ABSOLUTELY SURE you want to DELETE the entire ID folder:\n\n{devices_list}\n\nThis action CANNOT be undone!", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                for device_name, parent_path in devices_to_erase:
                    shutil.rmtree(parent_path)
                    logging.info(f"ID folder deleted: {parent_path}")

                self.step_status['erase'] = '✅'
                self.update_timeline()
                QMessageBox.information(self, "Success", f"✅ ID folders deleted successfully:\n\n{devices_list}\n\nAll steps completed!")
            except Exception as e:
                self.step_status['erase'] = '⚠️'
                self.update_timeline()
                QMessageBox.critical(self, "Error", f"Failed to erase: {str(e)}")
                logging.error(f"Erase failed: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataSyncManager()
    window.showFullScreen()
    sys.exit(app.exec_())
