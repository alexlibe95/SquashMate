#!/usr/bin/env python3
"""
SquashMate - AppImage Installation Manager
A desktop application for managing AppImage installations on Linux.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import logging
import datetime
import shlex
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                            QWidget, QPushButton, QLabel, QTextEdit, QFileDialog,
                            QMessageBox, QProgressBar, QFrame, QListWidget, QListWidgetItem,
                            QTabWidget, QInputDialog, QStackedLayout, QSizePolicy)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QCursor, QIcon, QPixmap


APP_ICON_PATH = str(Path(__file__).parent / "squashmate_icon.png")
VERSION_FILE_PATH = Path(__file__).parent / "VERSION"


def _read_app_version() -> str:
    """Read the canonical app version from the VERSION file at the project root."""
    try:
        text = VERSION_FILE_PATH.read_text(encoding="utf-8").strip()
        return text or "0.0.0"
    except Exception:
        return "0.0.0"


__version__ = _read_app_version()


class Theme:
    """Centralized design tokens (2026 modern UI)."""

    # Surfaces
    BG = "#F6F7FB"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#FAFBFD"
    BORDER = "#E5E7EB"
    BORDER_STRONG = "#D1D5DB"

    # Text
    TEXT = "#0F172A"
    TEXT_MUTED = "#64748B"
    TEXT_SUBTLE = "#94A3B8"
    TEXT_INVERSE = "#FFFFFF"

    # Brand / Accents
    PRIMARY = "#6366F1"          # indigo-500
    PRIMARY_HOVER = "#4F46E5"    # indigo-600
    PRIMARY_PRESSED = "#4338CA"  # indigo-700
    PRIMARY_SOFT = "#EEF2FF"
    PRIMARY_BORDER = "#C7D2FE"

    SUCCESS = "#10B981"          # emerald-500
    SUCCESS_HOVER = "#059669"
    SUCCESS_SOFT = "#ECFDF5"
    SUCCESS_BORDER = "#A7F3D0"

    VIOLET = "#8B5CF6"
    VIOLET_HOVER = "#7C3AED"
    VIOLET_SOFT = "#F5F3FF"

    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"
    DANGER_SOFT = "#FEF2F2"

    INFO = "#0EA5E9"

    # Logs
    TERMINAL_BG = "#0B1220"
    TERMINAL_TEXT = "#E2E8F0"
    TERMINAL_MUTED = "#94A3B8"
    TERMINAL_BORDER = "#1F2937"

    # Radii
    R_SM = 8
    R_MD = 12
    R_LG = 16

    # Spacing
    SP_2 = 8
    SP_3 = 12
    SP_4 = 16
    SP_5 = 20
    SP_6 = 24
    SP_8 = 32


def app_stylesheet() -> str:
    """Build the global QSS using the design tokens."""
    t = Theme
    return f"""
        /* ---------- Window ---------- */
        QMainWindow, QWidget#rootSurface {{
            background-color: {t.BG};
            color: {t.TEXT};
            font-family: 'Inter', 'Segoe UI', 'SF Pro Text', 'Ubuntu', 'Roboto', sans-serif;
            font-size: 14px;
        }}

        QLabel {{
            color: {t.TEXT};
        }}

        QLabel[role="muted"] {{
            color: {t.TEXT_MUTED};
        }}

        QLabel[role="subtle"] {{
            color: {t.TEXT_SUBTLE};
            font-size: 12.5px;
        }}

        QLabel[role="title"] {{
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.3px;
            color: {t.TEXT};
        }}

        QLabel[role="subtitle"] {{
            font-size: 13.5px;
            color: {t.TEXT_MUTED};
            font-weight: 500;
        }}

        QLabel[role="sectionTitle"] {{
            font-size: 15px;
            font-weight: 600;
            color: {t.TEXT};
        }}

        QLabel[role="sectionDesc"] {{
            font-size: 13px;
            color: {t.TEXT_MUTED};
        }}

        /* ---------- Cards ---------- */
        QFrame[role="card"] {{
            background-color: {t.SURFACE};
            border: 1px solid {t.BORDER};
            border-radius: {t.R_LG}px;
        }}

        QFrame[role="dropzone"] {{
            background-color: {t.SURFACE_ALT};
            border: 1.5px dashed {t.BORDER_STRONG};
            border-radius: {t.R_MD}px;
        }}

        QFrame[role="dropzone"][state="active"] {{
            background-color: {t.PRIMARY_SOFT};
            border: 1.5px dashed {t.PRIMARY};
        }}

        QFrame[role="brandHeader"] {{
            background-color: {t.SURFACE};
            border: 1px solid {t.BORDER};
            border-radius: {t.R_LG}px;
        }}

        /* ---------- Tabs ---------- */
        QTabWidget::pane {{
            border: none;
            background-color: transparent;
            top: 4px;
        }}

        QTabBar {{
            qproperty-drawBase: 0;
            background: transparent;
        }}

        QTabBar::tab {{
            background-color: {t.SURFACE};
            color: {t.TEXT_MUTED};
            padding: 10px 18px;
            margin-right: 6px;
            border: 1px solid {t.BORDER};
            border-radius: 999px;
            font-weight: 600;
            font-size: 13px;
            min-width: 130px;
        }}

        QTabBar::tab:hover {{
            color: {t.TEXT};
            border-color: {t.BORDER_STRONG};
        }}

        QTabBar::tab:selected {{
            background-color: {t.TEXT};
            color: {t.TEXT_INVERSE};
            border: 1px solid {t.TEXT};
        }}

        /* ---------- Buttons (default = primary) ---------- */
        QPushButton {{
            background-color: {t.PRIMARY};
            color: {t.TEXT_INVERSE};
            border: 1px solid {t.PRIMARY};
            padding: 10px 18px;
            border-radius: 10px;
            font-size: 13.5px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {t.PRIMARY_HOVER};
            border-color: {t.PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {t.PRIMARY_PRESSED};
            border-color: {t.PRIMARY_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: #E5E7EB;
            color: #9CA3AF;
            border-color: #E5E7EB;
        }}

        /* Primary CTA (large) */
        QPushButton[variant="primary-cta"] {{
            background-color: {t.PRIMARY};
            color: {t.TEXT_INVERSE};
            border: 1px solid {t.PRIMARY};
            padding: 14px 22px;
            border-radius: 12px;
            font-size: 14.5px;
            font-weight: 700;
        }}
        QPushButton[variant="primary-cta"]:hover {{
            background-color: {t.PRIMARY_HOVER};
            border-color: {t.PRIMARY_HOVER};
        }}
        QPushButton[variant="primary-cta"]:pressed {{
            background-color: {t.PRIMARY_PRESSED};
        }}
        QPushButton[variant="primary-cta"]:disabled {{
            background-color: #E5E7EB;
            color: #9CA3AF;
            border-color: #E5E7EB;
        }}

        /* Success CTA (AppImage) */
        QPushButton[variant="success-cta"] {{
            background-color: {t.SUCCESS};
            color: {t.TEXT_INVERSE};
            border: 1px solid {t.SUCCESS};
            padding: 14px 22px;
            border-radius: 12px;
            font-size: 14.5px;
            font-weight: 700;
        }}
        QPushButton[variant="success-cta"]:hover {{
            background-color: {t.SUCCESS_HOVER};
            border-color: {t.SUCCESS_HOVER};
        }}
        QPushButton[variant="success-cta"]:disabled {{
            background-color: #E5E7EB;
            color: #9CA3AF;
            border-color: #E5E7EB;
        }}

        /* Violet CTA (.deb) */
        QPushButton[variant="violet-cta"] {{
            background-color: {t.VIOLET};
            color: {t.TEXT_INVERSE};
            border: 1px solid {t.VIOLET};
            padding: 14px 22px;
            border-radius: 12px;
            font-size: 14.5px;
            font-weight: 700;
        }}
        QPushButton[variant="violet-cta"]:hover {{
            background-color: {t.VIOLET_HOVER};
            border-color: {t.VIOLET_HOVER};
        }}
        QPushButton[variant="violet-cta"]:disabled {{
            background-color: #E5E7EB;
            color: #9CA3AF;
            border-color: #E5E7EB;
        }}

        /* Outline / secondary */
        QPushButton[variant="ghost"] {{
            background-color: {t.SURFACE};
            color: {t.TEXT};
            border: 1px solid {t.BORDER};
            padding: 9px 14px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton[variant="ghost"]:hover {{
            background-color: {t.SURFACE_ALT};
            border-color: {t.BORDER_STRONG};
        }}
        QPushButton[variant="ghost"]:pressed {{
            background-color: #F1F5F9;
        }}

        /* Soft (filled-tonal) */
        QPushButton[variant="soft"] {{
            background-color: {t.PRIMARY_SOFT};
            color: {t.PRIMARY_HOVER};
            border: 1px solid {t.PRIMARY_BORDER};
            padding: 9px 14px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton[variant="soft"]:hover {{
            background-color: #E0E7FF;
        }}

        /* Danger */
        QPushButton[variant="danger"] {{
            background-color: {t.DANGER};
            color: {t.TEXT_INVERSE};
            border: 1px solid {t.DANGER};
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 600;
        }}
        QPushButton[variant="danger"]:hover {{
            background-color: {t.DANGER_HOVER};
            border-color: {t.DANGER_HOVER};
        }}
        QPushButton[variant="danger"]:disabled {{
            background-color: #E5E7EB;
            color: #9CA3AF;
            border-color: #E5E7EB;
        }}

        /* Danger ghost (less aggressive) */
        QPushButton[variant="danger-ghost"] {{
            background-color: {t.SURFACE};
            color: {t.DANGER_HOVER};
            border: 1px solid {t.BORDER};
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 600;
        }}
        QPushButton[variant="danger-ghost"]:hover {{
            background-color: {t.DANGER_SOFT};
            border-color: #FCA5A5;
            color: {t.DANGER_HOVER};
        }}
        QPushButton[variant="danger-ghost"]:disabled {{
            background-color: #F8FAFC;
            color: #CBD5E1;
            border-color: {t.BORDER};
        }}

        /* ---------- Inputs / Text ---------- */
        QTextEdit#statusLog {{
            background-color: {t.TERMINAL_BG};
            color: {t.TERMINAL_TEXT};
            border: 1px solid {t.TERMINAL_BORDER};
            border-radius: {t.R_MD}px;
            padding: 12px 14px;
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12.5px;
            selection-background-color: {t.PRIMARY};
        }}

        /* ---------- List ---------- */
        QListWidget {{
            background-color: {t.SURFACE};
            border: 1px solid {t.BORDER};
            border-radius: {t.R_MD}px;
            padding: 6px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 12px 14px;
            border-radius: 10px;
            margin: 2px 0px;
            color: {t.TEXT};
        }}
        QListWidget::item:hover {{
            background-color: {t.SURFACE_ALT};
        }}
        QListWidget::item:selected {{
            background-color: {t.PRIMARY_SOFT};
            color: {t.PRIMARY_PRESSED};
            border: 1px solid {t.PRIMARY_BORDER};
        }}

        /* Compact list (Manage tab) - lives inside its parent card */
        QListWidget#appsList {{
            background-color: transparent;
            border: none;
            padding: 0px;
            font-size: 12.5px;
        }}
        QListWidget#appsList::item {{
            padding: 6px 10px;
            border-radius: 6px;
            margin: 1px 2px;
            color: {t.TEXT};
            font-size: 12.5px;
        }}
        QListWidget#appsList::item:hover {{
            background-color: {t.SURFACE_ALT};
        }}
        QListWidget#appsList::item:selected {{
            background-color: {t.PRIMARY_SOFT};
            color: {t.PRIMARY_PRESSED};
            border: 1px solid {t.PRIMARY_BORDER};
        }}

        /* ---------- Progress ---------- */
        QProgressBar {{
            border: 1px solid {t.BORDER};
            border-radius: 10px;
            text-align: center;
            background-color: {t.SURFACE_ALT};
            color: {t.TEXT};
            font-weight: 600;
            font-size: 12.5px;
            min-height: 44px;
            max-height: 44px;
        }}
        QProgressBar::chunk {{
            background-color: {t.PRIMARY};
            border-radius: 9px;
        }}
        QProgressBar[accent="success"]::chunk {{
            background-color: {t.SUCCESS};
        }}
        QProgressBar[accent="violet"]::chunk {{
            background-color: {t.VIOLET};
        }}

        /* ---------- Scroll ---------- */
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 4px 2px;
        }}
        QScrollBar::handle:vertical {{
            background: #CBD5E1;
            border-radius: 5px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #94A3B8;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* ---------- Badges (QLabel role) ---------- */
        QLabel[role="badge"] {{
            background-color: {t.PRIMARY_SOFT};
            color: {t.PRIMARY_HOVER};
            border: 1px solid {t.PRIMARY_BORDER};
            border-radius: 999px;
            padding: 3px 10px;
            font-size: 11.5px;
            font-weight: 600;
        }}
        QLabel[role="badge"][tone="success"] {{
            background-color: {t.SUCCESS_SOFT};
            color: {t.SUCCESS_HOVER};
            border-color: {t.SUCCESS_BORDER};
        }}
        QLabel[role="badge"][tone="violet"] {{
            background-color: {t.VIOLET_SOFT};
            color: {t.VIOLET_HOVER};
            border-color: #DDD6FE;
        }}
        QLabel[role="badge"][tone="muted"] {{
            background-color: #F1F5F9;
            color: {t.TEXT_MUTED};
            border-color: {t.BORDER};
        }}

        /* ---------- Status pill (file selection state) ---------- */
        QLabel[role="filename"] {{
            color: {t.TEXT};
            font-size: 14px;
            font-weight: 600;
        }}
        QLabel[role="filemeta"] {{
            color: {t.TEXT_MUTED};
            font-size: 12.5px;
        }}
        QLabel[role="filename"][state="empty"] {{
            color: {t.TEXT_SUBTLE};
            font-weight: 500;
            font-style: italic;
        }}
    """


class SquashMateLogger:
    """Comprehensive logging system for SquashMate operations and app launches."""
    
    def __init__(self):
        self.log_dir = Path.home() / ".local" / "share" / "squashmate"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup main SquashMate logger
        self.setup_main_logger()
        
        # Apps log directory
        self.apps_log_dir = self.log_dir / "apps"
        self.apps_log_dir.mkdir(exist_ok=True)
    
    def setup_main_logger(self):
        """Setup the main SquashMate logger."""
        self.logger = logging.getLogger('squashmate')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler for persistent logging
        log_file = self.log_dir / "squashmate.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log startup
        self.logger.info("SquashMate logger initialized")
    
    def log_operation(self, level, message):
        """Log an operation with the specified level."""
        getattr(self.logger, level.lower())(message)
    
    def log_app_launch(self, app_name, command, success=True, error_output=None):
        """Log application launch attempts and results."""
        app_log_file = self.apps_log_dir / f"{app_name}.log"

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(app_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Launch attempt: {timestamp}\n")
            f.write(f"Command: {' '.join(command)}\n")
            f.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")

            if not success and error_output:
                f.write(f"\nError Output:\n{error_output}\n")

            f.write(f"{'='*60}\n")

        # Also log to main logger
        status = "successfully" if success else "failed"
        self.logger.info(f"App launch {status}: {app_name}")
        if not success:
            self.logger.error(f"App launch error for {app_name}: {error_output}")

    def log_deb_installation(self, package_name, version, success=True, error_output=None):
        """Log .deb package installation attempts and results."""
        deb_log_file = self.log_dir / "deb_packages.log"

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(deb_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Installation attempt: {timestamp}\n")
            f.write(f"Package: {package_name} {version}\n")
            f.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")

            if not success and error_output:
                f.write(f"\nError Output:\n{error_output}\n")

            f.write(f"{'='*60}\n")

        # Also log to main logger
        status = "successfully" if success else "failed"
        self.logger.info(f"Deb package installation {status}: {package_name} {version}")
        if not success:
            self.logger.error(f"Deb package installation error for {package_name}: {error_output}")

    def log_deb_uninstallation(self, package_name, success=True, error_output=None):
        """Log .deb package uninstallation attempts and results."""
        deb_log_file = self.log_dir / "deb_packages.log"

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(deb_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Uninstallation attempt: {timestamp}\n")
            f.write(f"Package: {package_name}\n")
            f.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")

            if not success and error_output:
                f.write(f"\nError Output:\n{error_output}\n")

            f.write(f"{'='*60}\n")

        # Also log to main logger
        status = "successfully" if success else "failed"
        self.logger.info(f"Deb package uninstallation {status}: {package_name}")
        if not success:
            self.logger.error(f"Deb package uninstallation error for {package_name}: {error_output}")
    
    def get_app_logs(self, app_name):
        """Get logs for a specific application."""
        app_log_file = self.apps_log_dir / f"{app_name}.log"
        if app_log_file.exists():
            try:
                with open(app_log_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading log file: {str(e)}"
        return "No log file found for this application."
    
    def get_main_logs(self, lines=100):
        """Get recent main SquashMate logs."""
        log_file = self.log_dir / "squashmate.log"
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:])
            except Exception as e:
                return f"Error reading main log file: {str(e)}"
        return "No main log file found."
    
    def clear_app_logs(self, app_name=None):
        """Clear logs for a specific app or all apps."""
        if app_name:
            app_log_file = self.apps_log_dir / f"{app_name}.log"
            if app_log_file.exists():
                app_log_file.unlink()
                self.logger.info(f"Cleared logs for {app_name}")
        else:
            for log_file in self.apps_log_dir.glob("*.log"):
                log_file.unlink()
            self.logger.info("Cleared all application logs")
    
    def get_log_summary(self):
        """Get a summary of all log files."""
        summary = []
        
        # Main log
        main_log = self.log_dir / "squashmate.log"
        if main_log.exists():
            size = main_log.stat().st_size / 1024  # KB
            modified = datetime.datetime.fromtimestamp(main_log.stat().st_mtime)
            summary.append({
                'name': 'SquashMate Main Log',
                'file': 'squashmate.log',
                'size': f"{size:.1f} KB",
                'modified': modified.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # App logs
        for log_file in sorted(self.apps_log_dir.glob("*.log")):
            size = log_file.stat().st_size / 1024  # KB
            modified = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
            app_name = log_file.stem
            summary.append({
                'name': f'{app_name} App Log',
                'file': log_file.name,
                'size': f"{size:.1f} KB",
                'modified': modified.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return summary


class AppImageInstaller(QThread):
    """Worker thread for AppImage installation operations."""
    
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, appimage_path):
        super().__init__()
        self.appimage_path = appimage_path
        
    def run(self):
        """Execute the installation process."""
        try:
            self.install_appimage()
        except Exception as e:
            self.finished_signal.emit(False, str(e))
    
    def install_appimage(self):
        """Main installation logic."""
        # Step 1: Extract AppImage
        self.status_update.emit("Extracting AppImage...")
        self.progress_update.emit(10)
        
        if not self.extract_appimage():
            self.finished_signal.emit(False, "Failed to extract AppImage")
            return
            
        # Step 2: Determine app name
        self.status_update.emit("Determining application name...")
        self.progress_update.emit(25)
        
        app_name = self.get_app_name()
        if not app_name:
            self.finished_signal.emit(False, "Could not determine application name")
            return
            
        # Step 3: Move to Applications directory
        self.status_update.emit(f"Installing {app_name}...")
        self.progress_update.emit(40)
        
        if not self.move_to_applications(app_name):
            self.finished_signal.emit(False, "Failed to install application")
            return
            
        # Step 4: Create desktop file
        self.status_update.emit("Creating desktop entry...")
        self.progress_update.emit(70)
        
        if not self.create_desktop_file(app_name):
            self.finished_signal.emit(False, "Failed to create desktop entry")
            return
            
        # Step 5: Set permissions
        self.status_update.emit("Setting permissions...")
        self.progress_update.emit(90)
        
        if not self.set_permissions(app_name):
            self.finished_signal.emit(False, "Failed to set permissions")
            return
            
        self.status_update.emit(f"Successfully installed {app_name}!")
        self.progress_update.emit(100)
        self.finished_signal.emit(True, f"{app_name} has been successfully installed!")
    
    def extract_appimage(self):
        """Extract AppImage using --appimage-extract."""
        original_dir = os.getcwd()
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            os.chdir(temp_dir)
            
            # Make AppImage executable
            os.chmod(self.appimage_path, 0o755)
            
            # Extract AppImage
            result = subprocess.run([self.appimage_path, '--appimage-extract'], 
                                  capture_output=True, text=True, cwd=temp_dir)
            
            if result.returncode != 0:
                return False
                
            self.extraction_dir = temp_dir
            return True
            
        except Exception as e:
            self.status_update.emit(f"Extraction error: {str(e)}")
            if temp_dir and os.path.isdir(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            return False
        finally:
            os.chdir(original_dir)
    
    def get_app_name(self):
        """Derive app name from file name, removing version numbers."""
        filename = Path(self.appimage_path).stem
        
        # Remove common version patterns
        import re
        # Remove patterns like -v1.2.3, _1.2.3, -1.2.3, etc.
        app_name = re.sub(r'[-_]?v?\d+(\.\d+)*[-_]?.*$', '', filename, flags=re.IGNORECASE)
        # Remove patterns like (x86_64), [AppImage], etc.
        app_name = re.sub(r'[\(\[].*?[\)\]]', '', app_name)
        # Clean up any remaining special characters and spaces
        app_name = re.sub(r'[-_]+$', '', app_name.strip())
        
        return app_name if app_name else filename
    
    def move_to_applications(self, app_name):
        """Move extracted folder to ~/Applications/<AppName>."""
        try:
            home_dir = Path.home()
            apps_dir = home_dir / "Applications"
            target_dir = apps_dir / app_name
            source_dir = Path(self.extraction_dir) / "squashfs-root"
            
            # Create Applications directory if it doesn't exist
            apps_dir.mkdir(exist_ok=True)
            
            # Check if target already exists
            if target_dir.exists():
                self.status_update.emit(f"Updating existing installation of {app_name}...")
                # Backup user config directories before replacement
                config_backup = None
                config_dir = home_dir / ".config" / app_name
                if config_dir.exists():
                    config_backup = home_dir / f".config_backup_{app_name}_temp"
                    if config_backup.exists():
                        shutil.rmtree(config_backup)
                    shutil.copytree(config_dir, config_backup)
                    self.status_update.emit(f"Backed up user configuration...")
                
                # Remove old installation
                shutil.rmtree(target_dir)
                
                # Restore config if it was backed up
                if config_backup and config_backup.exists():
                    if config_dir.exists():
                        shutil.rmtree(config_dir)
                    shutil.move(str(config_backup), str(config_dir))
                    self.status_update.emit(f"Restored user configuration...")
            
            # Move the extracted folder
            shutil.move(str(source_dir), str(target_dir))
            
            # Clean up temp directory
            shutil.rmtree(self.extraction_dir)
            
            self.app_dir = target_dir
            return True
            
        except Exception as e:
            self.status_update.emit(f"Installation error: {str(e)}")
            return False
    
    def create_desktop_file(self, app_name):
        """Create .desktop file in ~/.local/share/applications."""
        try:
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = desktop_dir / f"{app_name}.desktop"
            
            # Find icon file
            icon_path = self.find_icon_file()
            
            # Ensure launcher wrapper is available in system location
            self.setup_launcher_wrapper()
            
            # Use the launcher wrapper for desktop entries
            launcher_path = Path.home() / ".local" / "bin" / "squashmate_launcher.py"
            apprun_path = self.app_dir / "AppRun"
            
            desktop_content = f"""[Desktop Entry]
Name={app_name}
Exec={launcher_path} "{app_name}" "{apprun_path}"
Icon={icon_path}
Type=Application
Categories=Utility;
Terminal=false
StartupNotify=true
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
                
            self.desktop_file = desktop_file
            return True
            
        except Exception as e:
            self.status_update.emit(f"Desktop file error: {str(e)}")
            return False
    
    def setup_launcher_wrapper(self):
        """Copy the launcher wrapper to a system location."""
        try:
            # Create ~/.local/bin if it doesn't exist
            local_bin = Path.home() / ".local" / "bin"
            local_bin.mkdir(parents=True, exist_ok=True)
            
            # Get the path to the current squashmate_launcher.py
            current_dir = Path(__file__).parent
            source_launcher = current_dir / "squashmate_launcher.py"
            target_launcher = local_bin / "squashmate_launcher.py"
            
            # Copy the launcher if it doesn't exist or is older
            if not target_launcher.exists() or (
                source_launcher.exists() and 
                source_launcher.stat().st_mtime > target_launcher.stat().st_mtime
            ):
                if source_launcher.exists():
                    import shutil
                    shutil.copy2(source_launcher, target_launcher)
                    os.chmod(target_launcher, 0o755)
                    self.status_update.emit("Updated launcher wrapper...")
                
        except Exception as e:
            self.status_update.emit(f"Warning: Could not setup launcher wrapper: {str(e)}")
            # Continue anyway - fallback to direct execution
    
    def find_icon_file(self):
        """Find the best icon file for the application."""
        icon_extensions = ['.png', '.svg', '.ico', '.xpm']
        
        # Look for icon files in the app directory
        for ext in icon_extensions:
            for icon_file in self.app_dir.rglob(f"*{ext}"):
                if any(keyword in icon_file.name.lower() for keyword in ['icon', 'logo', 'app']):
                    return str(icon_file)
        
        # Fallback to any image file
        for ext in icon_extensions:
            icon_files = list(self.app_dir.rglob(f"*{ext}"))
            if icon_files:
                return str(icon_files[0])
                
        return str(self.app_dir / "AppRun")  # Fallback to AppRun
    
    def set_permissions(self, app_name):
        """Set executable permissions for AppRun and .desktop file."""
        try:
            # Set AppRun executable
            apprun_path = self.app_dir / "AppRun"
            if apprun_path.exists():
                os.chmod(apprun_path, 0o755)
            
            # Set desktop file executable
            os.chmod(self.desktop_file, 0o755)
            
            return True
            
        except Exception as e:
            self.status_update.emit(f"Permission error: {str(e)}")
            return False


class DebInstaller(QThread):
    """Worker thread for .deb package installation operations."""

    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, deb_path):
        super().__init__()
        self.deb_path = deb_path
        self.pkexec_available = self.check_pkexec_available()

    def check_pkexec_available(self):
        """Check if pkexec is available for GUI sudo operations."""
        try:
            return shutil.which('pkexec') is not None
        except Exception:
            return False

    def run(self):
        """Execute the .deb installation process."""
        try:
            # Add a timeout wrapper to prevent hanging
            import threading
            result = [None, None]

            def target():
                try:
                    self.install_deb()
                except Exception as e:
                    result[0] = False
                    result[1] = str(e)

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=600)  # 10 minute timeout

            if thread.is_alive():
                self.status_update.emit("Installation timed out after 10 minutes")
                self.finished_signal.emit(False, "Installation timed out - the process may still be running in the background")
            elif result[0] is False:
                self.finished_signal.emit(False, result[1])

        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def install_deb(self):
        """Main .deb installation logic."""
        # Step 0: Check if pkexec is available
        if not self.pkexec_available:
            self.status_update.emit("Error: pkexec not available for GUI operations")
            self.finished_signal.emit(False, "pkexec is required for .deb installation but is not available.\n\nPlease install policykit-1 with:\nsudo apt install policykit-1")
            return

        # Step 1: Validate .deb file
        self.status_update.emit("Validating .deb package...")
        self.progress_update.emit(10)

        if not self.validate_deb():
            self.finished_signal.emit(False, "Invalid .deb file")
            return

        # Step 2: Get package information
        self.status_update.emit("Extracting package information...")
        self.progress_update.emit(25)

        package_info = self.get_package_info()
        if not package_info:
            self.finished_signal.emit(False, "Could not extract package information")
            return

        package_name = package_info.get('Package', 'Unknown')
        version = package_info.get('Version', 'Unknown')

        # Step 3: Check if package is already installed
        if self.is_package_installed(package_name):
            self.status_update.emit(f"Updating {package_name}...")
        else:
            self.status_update.emit(f"Installing {package_name}...")

        self.progress_update.emit(40)

        # Step 4: Update package cache
        self.status_update.emit("Preparing package system...")
        self.progress_update.emit(60)

        self.install_dependencies()  # This just updates cache now

        # Step 5: Install the package
        self.progress_update.emit(80)

        if not self.install_package():
            error_msg = (f"Failed to install package automatically.\n\n"
                        f"You can install it manually using these terminal commands:\n"
                        f"sudo dpkg -i {shlex.quote(self.deb_path)}\n"
                        f"sudo apt-get install -f\n\n"
                        f"Or using apt directly:\n"
                        f"sudo apt install {shlex.quote(self.deb_path)}")
            self.finished_signal.emit(False, error_msg)
            return

        # Step 6: Verify installation
        self.status_update.emit("Verifying installation...")
        self.progress_update.emit(95)

        if self.verify_installation(package_name):
            self.status_update.emit(f"Successfully installed {package_name}!")
            self.progress_update.emit(100)
            self.finished_signal.emit(True, f"{package_name} {version} has been successfully installed!")
        else:
            self.finished_signal.emit(False, "Package installation could not be verified")

    def validate_deb(self):
        """Validate that the file is a proper .deb package."""
        try:
            # Check file extension
            if not self.deb_path.endswith('.deb'):
                return False

            # Check if file exists and is readable
            if not os.path.exists(self.deb_path):
                return False

            # Try to read the debian control file
            result = subprocess.run(['dpkg', '--info', self.deb_path],
                                  capture_output=True, text=True)
            return result.returncode == 0

        except Exception as e:
            self.status_update.emit(f"Validation error: {str(e)}")
            return False

    def get_package_info(self):
        """Extract package information from .deb file."""
        try:
            result = subprocess.run(['dpkg', '--info', self.deb_path],
                                  capture_output=True, text=True)

            if result.returncode != 0:
                return None

            info = {}
            for line in result.stdout.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    info[key.strip()] = value.strip()

            return info

        except Exception as e:
            self.status_update.emit(f"Error extracting package info: {str(e)}")
            return None

    def is_package_installed(self, package_name):
        """Check if a package is already installed."""
        try:
            result = subprocess.run(['dpkg', '-l', package_name],
                                  capture_output=True, text=True)
            return result.returncode == 0 and 'ii' in result.stdout
        except Exception:
            return False

    def install_dependencies(self):
        """Prepare for package installation."""
        # Skip complex dependency preparation - let the installation handle it
        self.status_update.emit("Ready for package installation")
        return True

    def install_package(self):
        """Install the .deb package using streamlined approach."""
        try:
            self.status_update.emit("Installing package...")

            # Try the most direct approach first - pkexec with no extra windows
            self.status_update.emit("Attempting direct installation...")

            # Create installation commands
            install_cmds = [
                f"dpkg -i '{self.deb_path}'",
                "apt-get install -f -y"
            ]

            # Try pkexec approach first (most streamlined)
            all_commands_succeeded = True
            for cmd in install_cmds:
                try:
                    self.status_update.emit(f"Running: {cmd}")
                    pkexec_cmd = ['pkexec', 'bash', '-c', cmd]
                    result = subprocess.run(pkexec_cmd, capture_output=True, text=True, timeout=120)

                    if result.returncode == 0:
                        self.status_update.emit("Command completed successfully")
                    else:
                        self.status_update.emit(f"Command failed: {result.stderr}")
                        all_commands_succeeded = False
                        break  # Stop if any command fails

                except subprocess.TimeoutExpired:
                    self.status_update.emit("Command timed out")
                    all_commands_succeeded = False
                    break
                except Exception as e:
                    self.status_update.emit(f"Command error: {str(e)}")
                    all_commands_succeeded = False
                    break

            if all_commands_succeeded:
                self.status_update.emit("Package installed successfully!")
                return True

            # If pkexec fails, try terminal approach as fallback
            self.status_update.emit("Direct approach failed, trying terminal method...")

            # Create a temporary script with the installation commands
            import tempfile
            import os

            script_content = f"""#!/bin/bash
echo "Installing {os.path.basename(self.deb_path)}..."
dpkg -i "{self.deb_path}"
echo "Resolving dependencies..."
apt-get install -f -y
echo "Installation completed successfully!"
"""

            # Write the script to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                script_path = f.name

            # Make the script executable
            os.chmod(script_path, 0o755)

            # Try using gnome-terminal with minimal window
            try:
                self.status_update.emit("Opening terminal for authentication...")
                terminal_cmd = [
                    'gnome-terminal',
                    '--title=SquashMate Installation',
                    '--geometry=80x10',
                    '--', 'bash', '-c', f'sudo bash "{script_path}"; echo "Press Enter to close"; read'
                ]
                result = subprocess.run(terminal_cmd, timeout=600)
                success = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                success = False

            # Clean up the temporary script
            try:
                os.unlink(script_path)
            except:
                pass

            if success:
                self.status_update.emit("Package installed successfully via terminal")
                return True
            else:
                # Final fallback: provide manual instructions
                manual_cmd = f"sudo dpkg -i '{self.deb_path}' && sudo apt-get install -f"
                self.status_update.emit(f"For manual installation, run: {manual_cmd}")
                return False

        except Exception as e:
            self.status_update.emit(f"Installation error: {str(e)}")
            return False

    def verify_installation(self, package_name):
        """Verify that the package was installed successfully."""
        try:
            result = subprocess.run(['dpkg', '-l', package_name],
                                  capture_output=True, text=True)
            return result.returncode == 0 and 'ii' in result.stdout
        except Exception:
            return False


class InstalledAppsManager:
    """Helper class for managing installed applications."""
    
    @staticmethod
    def get_applications_dir():
        """Get the Applications directory path."""
        return Path.home() / "Applications"
    
    @staticmethod
    def get_installed_apps():
        """Get list of installed applications."""
        apps_dir = InstalledAppsManager.get_applications_dir()
        if not apps_dir.exists():
            return []
        
        installed_apps = []
        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir():
                apprun_path = app_dir / "AppRun"
                if apprun_path.exists():
                    # Get app info
                    app_info = {
                        'name': app_dir.name,
                        'path': str(app_dir),
                        'apprun': str(apprun_path),
                        'size': InstalledAppsManager.get_directory_size(app_dir),
                        'desktop_file': InstalledAppsManager.get_desktop_file(app_dir.name)
                    }
                    installed_apps.append(app_info)
        
        return sorted(installed_apps, key=lambda x: x['name'])
    
    @staticmethod
    def get_directory_size(path):
        """Calculate directory size in MB."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
        return round(total_size / (1024 * 1024), 1)  # Convert to MB
    
    @staticmethod
    def get_desktop_file(app_name):
        """Get desktop file path for an app."""
        desktop_dir = Path.home() / ".local" / "share" / "applications"
        desktop_file = desktop_dir / f"{app_name}.desktop"
        return str(desktop_file) if desktop_file.exists() else None
    
    @staticmethod
    def uninstall_app(app_name):
        """Uninstall an application."""
        try:
            apps_dir = InstalledAppsManager.get_applications_dir()
            app_dir = apps_dir / app_name
            
            # Remove application directory
            if app_dir.exists():
                shutil.rmtree(app_dir)
            
            # Remove desktop files from all common locations
            desktop_locations = [
                Path.home() / ".local" / "share" / "applications",
                Path("/usr/share/applications"),  # System-wide (requires sudo, but we try)
            ]
            
            desktop_file_removed = False
            for desktop_dir in desktop_locations:
                desktop_file = desktop_dir / f"{app_name}.desktop"
                if desktop_file.exists():
                    try:
                        desktop_file.unlink()
                        desktop_file_removed = True
                    except PermissionError:
                        # System-wide desktop files require sudo - skip silently
                        pass
                    except Exception:
                        pass
            
            # Remove associated icon files from common locations
            icon_locations = [
                Path.home() / ".local" / "share" / "icons",
                Path("/usr/share/pixmaps"),  # System-wide icons
            ]
            
            icon_extensions = ['.png', '.svg', '.xpm', '.ico']
            for icon_dir in icon_locations:
                if icon_dir.exists():
                    for ext in icon_extensions:
                        icon_file = icon_dir / f"{app_name}{ext}"
                        if icon_file.exists():
                            try:
                                icon_file.unlink()
                            except PermissionError:
                                # System-wide icons require sudo - skip silently
                                pass
                            except Exception:
                                pass
            
            # Also check for icons in subdirectories (e.g., hicolor theme)
            hicolor_icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor"
            if hicolor_icon_dir.exists():
                for size_dir in hicolor_icon_dir.iterdir():
                    if size_dir.is_dir():
                        apps_icon_dir = size_dir / "apps"
                        if apps_icon_dir.exists():
                            for ext in icon_extensions:
                                icon_file = apps_icon_dir / f"{app_name}{ext}"
                                if icon_file.exists():
                                    try:
                                        icon_file.unlink()
                                    except Exception:
                                        pass
            
            # Update desktop database to refresh menu
            if desktop_file_removed:
                try:
                    # Update user desktop database
                    desktop_dir = Path.home() / ".local" / "share" / "applications"
                    if desktop_dir.exists():
                        subprocess.run(['update-desktop-database', str(desktop_dir)], 
                                     capture_output=True, timeout=5)
                except Exception:
                    pass  # Ignore errors updating database
            
            # Clean up launcher wrapper if no more apps are installed
            InstalledAppsManager.cleanup_launcher_if_needed()
            
            return True
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def cleanup_launcher_if_needed():
        """Remove launcher wrapper if no SquashMate apps remain."""
        try:
            installed_apps = InstalledAppsManager.get_installed_apps()
            if not installed_apps:
                # No apps left, can remove the launcher
                launcher_path = Path.home() / ".local" / "bin" / "squashmate_launcher.py"
                if launcher_path.exists():
                    launcher_path.unlink()
        except Exception:
            # Ignore cleanup errors
            pass

    @staticmethod
    def get_installed_deb_packages():
        """Get list of installed .deb packages."""
        try:
            # Use dpkg to list all installed packages
            result = subprocess.run(['dpkg', '-l'], capture_output=True, text=True)

            if result.returncode != 0:
                return []

            packages = []
            lines = result.stdout.strip().split('\n')

            # Skip header lines (first 5 lines)
            for line in lines[5:]:
                if line.startswith('ii'):  # Only properly installed packages
                    parts = line.split()
                    if len(parts) >= 4:
                        status = parts[0]
                        package_name = parts[1]
                        version = parts[2]
                        description = ' '.join(parts[3:]) if len(parts) > 3 else ''

                        packages.append({
                            'name': package_name,
                            'version': version,
                            'status': status,
                            'description': description,
                            'type': 'deb',
                            'size': 'N/A'  # Size calculation for system packages is complex
                        })

            return sorted(packages, key=lambda x: x['name'])

        except Exception as e:
            print(f"Error getting installed .deb packages: {str(e)}")
            return []

    @staticmethod
    def get_combined_installed_items():
        """Get combined list of AppImages and .deb packages."""
        appimages = InstalledAppsManager.get_installed_apps()
        deb_packages = InstalledAppsManager.get_installed_deb_packages()

        # Mark AppImages with type
        for app in appimages:
            app['type'] = 'appimage'

        return appimages + deb_packages

    @staticmethod
    def uninstall_deb_package(package_name):
        """Uninstall a .deb package."""
        try:
            # Check if pkexec is available
            pkexec_check = subprocess.run(['which', 'pkexec'], capture_output=True, text=True)
            if pkexec_check.returncode != 0:
                return False, "pkexec is required for .deb uninstallation but is not available.\n\nPlease install policykit-1 with:\nsudo apt install policykit-1"

            # Use apt-get to remove the package with pkexec for GUI compatibility
            result = subprocess.run(['pkexec', 'apt-get', 'remove', '-y', package_name],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                # Clean up any remaining desktop entries and icons
                InstalledAppsManager.cleanup_desktop_entries(package_name)
                
                # Update desktop database
                try:
                    desktop_dir = Path.home() / ".local" / "share" / "applications"
                    if desktop_dir.exists():
                        subprocess.run(['update-desktop-database', str(desktop_dir)], 
                                     capture_output=True, timeout=5)
                except Exception:
                    pass  # Ignore errors updating database
                
                return True, None
            else:
                return False, result.stderr

        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def cleanup_desktop_entries(app_name):
        """Clean up desktop entries and icons for an application."""
        try:
            # Remove desktop files from common locations
            desktop_locations = [
                Path.home() / ".local" / "share" / "applications",
            ]
            
            for desktop_dir in desktop_locations:
                desktop_file = desktop_dir / f"{app_name}.desktop"
                if desktop_file.exists():
                    try:
                        desktop_file.unlink()
                    except Exception:
                        pass
            
            # Remove associated icon files
            icon_locations = [
                Path.home() / ".local" / "share" / "icons",
            ]
            
            icon_extensions = ['.png', '.svg', '.xpm', '.ico']
            for icon_dir in icon_locations:
                if icon_dir.exists():
                    # Check root icon directory
                    for ext in icon_extensions:
                        icon_file = icon_dir / f"{app_name}{ext}"
                        if icon_file.exists():
                            try:
                                icon_file.unlink()
                            except Exception:
                                pass
                    
                    # Check hicolor theme subdirectories
                    hicolor_dir = icon_dir / "hicolor"
                    if hicolor_dir.exists():
                        for size_dir in hicolor_dir.iterdir():
                            if size_dir.is_dir():
                                apps_icon_dir = size_dir / "apps"
                                if apps_icon_dir.exists():
                                    for ext in icon_extensions:
                                        icon_file = apps_icon_dir / f"{app_name}{ext}"
                                        if icon_file.exists():
                                            try:
                                                icon_file.unlink()
                                            except Exception:
                                                pass
        except Exception:
            pass  # Ignore cleanup errors

    @staticmethod
    def get_package_info(package_name):
        """Get detailed information about a .deb package."""
        try:
            result = subprocess.run(['dpkg', '-s', package_name],
                                  capture_output=True, text=True)

            if result.returncode != 0:
                return None

            info = {}
            for line in result.stdout.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    info[key.strip()] = value.strip()

            return info

        except Exception as e:
            return None
    
    @staticmethod
    def update_desktop_entries_to_use_wrapper():
        """Removed: previously updated desktop entries to use the launcher wrapper."""
        return False, "Desktop entry update feature removed."


class SquashMateGUI(QMainWindow):
    """Main GUI application for SquashMate."""
    
    def __init__(self):
        super().__init__()
        self.appimage_path = None
        self.deb_path = None
        self.installer_thread = None
        self.deb_installer_thread = None

        # Initialize logger
        self.logger = SquashMateLogger()
        self.logger.log_operation('info', 'SquashMate GUI starting up')

        self.init_ui()
        self.refresh_installed_apps()

        # Removed desktop entries update checks
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("SquashMate - AppImage & .deb Manager")
        self.setGeometry(100, 100, 1080, 780)
        self.setMinimumSize(960, 680)

        if Path(APP_ICON_PATH).exists():
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.setStyleSheet(app_stylesheet())

        central_widget = QWidget()
        central_widget.setObjectName("rootSurface")
        self.setCentralWidget(central_widget)
        root = QVBoxLayout(central_widget)
        root.setSpacing(Theme.SP_5)
        root.setContentsMargins(Theme.SP_8, Theme.SP_6, Theme.SP_8, Theme.SP_6)

        root.addWidget(self._build_brand_header(), 0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.tab_widget, 1)

        self.create_install_tab()
        self.create_deb_install_tab()
        self.create_manage_tab()

        root.addWidget(self._build_status_panel(), 0)

    def _build_brand_header(self) -> QFrame:
        """Top branding header with logo, title, and inline status."""
        card = QFrame()
        card.setProperty("role", "brandHeader")
        card.setFixedHeight(86)

        outer = QHBoxLayout(card)
        outer.setContentsMargins(Theme.SP_5, Theme.SP_4, Theme.SP_5, Theme.SP_4)
        outer.setSpacing(Theme.SP_4)

        logo = QLabel()
        logo.setFixedSize(56, 56)
        logo.setAlignment(Qt.AlignCenter)
        if Path(APP_ICON_PATH).exists():
            pixmap = QPixmap(APP_ICON_PATH).scaled(
                56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo.setPixmap(pixmap)
            logo.setStyleSheet("background: transparent; border: none;")
        else:
            logo.setStyleSheet(
                f"background-color: {Theme.PRIMARY_SOFT}; "
                f"color: {Theme.PRIMARY_HOVER}; "
                f"border: 1px solid {Theme.PRIMARY_BORDER}; "
                f"border-radius: 12px; font-size: 22px; font-weight: 700;"
            )
            logo.setText("⊟")
        outer.addWidget(logo)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        title = QLabel("SquashMate")
        title.setProperty("role", "title")
        text_col.addWidget(title)

        subtitle = QLabel("Install, manage, and launch AppImages and .deb packages")
        subtitle.setProperty("role", "subtitle")
        text_col.addWidget(subtitle)

        outer.addLayout(text_col)
        outer.addStretch()

        version_pill = QLabel(f"v{__version__}")
        version_pill.setProperty("role", "badge")
        version_pill.setProperty("tone", "muted")
        outer.addWidget(version_pill, alignment=Qt.AlignVCenter)

        return card

    def _build_status_panel(self) -> QFrame:
        """Bottom status / activity panel styled like a terminal pane."""
        card = QFrame()
        card.setProperty("role", "card")
        card.setStyleSheet(
            f"QFrame[role=\"card\"] {{ background-color: {Theme.SURFACE}; "
            f"border: 1px solid {Theme.BORDER}; border-radius: {Theme.R_LG}px; }}"
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Theme.SP_5, Theme.SP_4, Theme.SP_5, Theme.SP_4)
        layout.setSpacing(Theme.SP_3)

        header_row = QHBoxLayout()
        header_row.setSpacing(Theme.SP_3)

        title = QLabel("Activity")
        title.setProperty("role", "sectionTitle")
        header_row.addWidget(title)

        live_pill = QLabel("● Live")
        live_pill.setProperty("role", "badge")
        live_pill.setProperty("tone", "success")
        header_row.addWidget(live_pill)
        header_row.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("variant", "ghost")
        clear_btn.setCursor(QCursor(Qt.PointingHandCursor))
        clear_btn.clicked.connect(lambda: self.status_log.clear())
        header_row.addWidget(clear_btn)

        layout.addLayout(header_row)

        self.status_log = QTextEdit()
        self.status_log.setObjectName("statusLog")
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(140)
        self.status_log.append("Ready. Pick an AppImage or .deb to get started.")
        layout.addWidget(self.status_log)

        return card
    
    def _build_install_card(self, *, kind: str) -> QFrame:
        """Build a unified install card for either AppImage or .deb."""
        is_deb = kind == "deb"

        card = QFrame()
        card.setProperty("role", "card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Theme.SP_6, Theme.SP_5, Theme.SP_6, Theme.SP_5)
        layout.setSpacing(Theme.SP_4)

        header_row = QHBoxLayout()
        header_row.setSpacing(Theme.SP_3)

        title = QLabel("Install .deb package" if is_deb else "Install AppImage")
        title.setProperty("role", "sectionTitle")
        header_row.addWidget(title)

        type_badge = QLabel(".deb" if is_deb else "AppImage")
        type_badge.setProperty("role", "badge")
        type_badge.setProperty("tone", "violet" if is_deb else "success")
        header_row.addWidget(type_badge)
        header_row.addStretch()
        layout.addLayout(header_row)

        desc = QLabel(
            "Pick a .deb file. SquashMate uses pkexec, dpkg and apt to install it system-wide."
            if is_deb else
            "Pick an .AppImage file. SquashMate extracts it into ~/Applications and registers a desktop entry."
        )
        desc.setProperty("role", "sectionDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        dropzone = QFrame()
        dropzone.setProperty("role", "dropzone")
        dropzone.setProperty("state", "empty")
        dropzone.setMinimumHeight(120)
        dz_layout = QHBoxLayout(dropzone)
        dz_layout.setContentsMargins(Theme.SP_5, Theme.SP_4, Theme.SP_5, Theme.SP_4)
        dz_layout.setSpacing(Theme.SP_4)

        icon = QLabel("📋" if is_deb else "📦")
        icon.setFixedSize(56, 56)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"background-color: {Theme.SURFACE}; "
            f"border: 1px solid {Theme.BORDER}; "
            f"border-radius: 12px; font-size: 24px;"
        )
        dz_layout.addWidget(icon)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.setContentsMargins(0, 0, 0, 0)

        filename_label = QLabel(
            "No .deb package selected" if is_deb else "No AppImage selected"
        )
        filename_label.setProperty("role", "filename")
        filename_label.setProperty("state", "empty")
        filename_label.setWordWrap(True)
        info_col.addWidget(filename_label)

        meta_label = QLabel("Click \"Browse\" to pick a file")
        meta_label.setProperty("role", "filemeta")
        info_col.addWidget(meta_label)

        dz_layout.addLayout(info_col, stretch=1)

        browse_btn = QPushButton("Browse files")
        browse_btn.setProperty("variant", "ghost")
        browse_btn.setCursor(QCursor(Qt.PointingHandCursor))
        if is_deb:
            browse_btn.clicked.connect(self.select_deb_package)
        else:
            browse_btn.clicked.connect(self.select_appimage)
        dz_layout.addWidget(browse_btn, alignment=Qt.AlignVCenter)

        layout.addWidget(dropzone)

        action_container = QWidget()
        action_stack = QStackedLayout(action_container)
        action_stack.setContentsMargins(0, 0, 0, 0)

        cta = QPushButton(
            "Install .deb package" if is_deb else "Install / update AppImage"
        )
        cta.setProperty("variant", "violet-cta" if is_deb else "success-cta")
        cta.setCursor(QCursor(Qt.PointingHandCursor))
        cta.setMinimumHeight(52)
        cta.setEnabled(False)
        if is_deb:
            cta.clicked.connect(self.install_deb_package)
        else:
            cta.clicked.connect(self.install_appimage)

        progress = QProgressBar()
        progress.setProperty("accent", "violet" if is_deb else "success")
        progress.setValue(0)

        action_stack.addWidget(cta)
        action_stack.addWidget(progress)
        action_stack.setCurrentWidget(cta)

        layout.addWidget(action_container)

        if is_deb:
            self.deb_dropzone = dropzone
            self.deb_file_icon = icon
            self.deb_file_label = filename_label
            self.deb_file_meta = meta_label
            self.select_deb_button = browse_btn
            self.deb_install_button = cta
            self.deb_progress_bar = progress
            self.deb_install_action_container = action_container
            self.deb_install_action_stack = action_stack
        else:
            self.dropzone = dropzone
            self.file_icon = icon
            self.file_label = filename_label
            self.file_meta = meta_label
            self.select_button = browse_btn
            self.install_button = cta
            self.progress_bar = progress
            self.install_action_container = action_container
            self.install_action_stack = action_stack

        return card

    def create_install_tab(self):
        """Create the AppImage installation tab."""
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setSpacing(Theme.SP_5)
        layout.setContentsMargins(Theme.SP_6, Theme.SP_6, Theme.SP_6, Theme.SP_6)

        layout.addWidget(self._build_install_card(kind="appimage"))
        layout.addStretch()

        self.tab_widget.addTab(wrapper, "AppImage")

    def create_deb_install_tab(self):
        """Create the .deb installation tab."""
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setSpacing(Theme.SP_5)
        layout.setContentsMargins(Theme.SP_6, Theme.SP_6, Theme.SP_6, Theme.SP_6)

        layout.addWidget(self._build_install_card(kind="deb"))
        layout.addStretch()

        self.tab_widget.addTab(wrapper, ".deb")

    def create_manage_tab(self):
        """Create the management tab with header counts, compact list, and bottom action bar."""
        manage_widget = QWidget()
        layout = QVBoxLayout(manage_widget)
        layout.setSpacing(Theme.SP_3)
        layout.setContentsMargins(Theme.SP_6, Theme.SP_5, Theme.SP_6, Theme.SP_5)

        list_card = QFrame()
        list_card.setProperty("role", "card")
        list_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_card_layout = QVBoxLayout(list_card)
        list_card_layout.setContentsMargins(Theme.SP_5, Theme.SP_4, Theme.SP_5, Theme.SP_4)
        list_card_layout.setSpacing(Theme.SP_3)

        header_row = QHBoxLayout()
        header_row.setSpacing(Theme.SP_3)

        title = QLabel("Installed")
        title.setProperty("role", "sectionTitle")
        header_row.addWidget(title)

        self.appimage_badge = QLabel("0 AppImages")
        self.appimage_badge.setProperty("role", "badge")
        self.appimage_badge.setProperty("tone", "success")
        header_row.addWidget(self.appimage_badge)

        self.deb_badge = QLabel("0 .deb")
        self.deb_badge.setProperty("role", "badge")
        self.deb_badge.setProperty("tone", "violet")
        header_row.addWidget(self.deb_badge)

        header_row.addStretch()

        self.refresh_button = QPushButton("⟳  Refresh")
        self.refresh_button.setProperty("variant", "ghost")
        self.refresh_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.refresh_button.clicked.connect(self.refresh_installed_apps)
        header_row.addWidget(self.refresh_button)

        list_card_layout.addLayout(header_row)

        self.apps_list = QListWidget()
        self.apps_list.setObjectName("appsList")
        self.apps_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apps_list.setMinimumHeight(160)
        self.apps_list.setUniformItemSizes(True)
        self.apps_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.apps_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.apps_list.setFrameShape(QFrame.NoFrame)
        self.apps_list.itemSelectionChanged.connect(self.on_app_selection_changed)
        list_card_layout.addWidget(self.apps_list, stretch=1)

        layout.addWidget(list_card, stretch=1)

        action_bar = QFrame()
        action_bar.setProperty("role", "card")
        action_bar.setStyleSheet(
            f"QFrame[role=\"card\"] {{ background-color: {Theme.SURFACE}; "
            f"border: 1px solid {Theme.BORDER}; border-radius: {Theme.R_MD}px; }}"
        )
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(Theme.SP_4, Theme.SP_3, Theme.SP_4, Theme.SP_3)
        action_layout.setSpacing(Theme.SP_3)

        self.launch_button = QPushButton("🚀  Launch")
        self.launch_button.setEnabled(False)
        self.launch_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.launch_button.setMinimumWidth(140)
        self.launch_button.clicked.connect(self.launch_selected_app)
        action_layout.addWidget(self.launch_button)

        self.uninstall_button = QPushButton("🗑  Uninstall")
        self.uninstall_button.setProperty("variant", "danger-ghost")
        self.uninstall_button.setEnabled(False)
        self.uninstall_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.uninstall_button.setMinimumWidth(140)
        self.uninstall_button.clicked.connect(self.uninstall_selected_app)
        action_layout.addWidget(self.uninstall_button)

        action_layout.addStretch()

        self.selection_hint = QLabel("Select an item to enable actions")
        self.selection_hint.setProperty("role", "subtle")
        action_layout.addWidget(self.selection_hint, alignment=Qt.AlignVCenter)

        layout.addWidget(action_bar, stretch=0)

        self.tab_widget.addTab(manage_widget, "Manage")
    

        
    def select_appimage(self):
        """Open file dialog to select AppImage."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select AppImage",
            "",
            "AppImage files (*.AppImage);;All files (*)"
        )

        if file_path:
            self.appimage_path = file_path
            path_obj = Path(file_path)
            self._set_file_state(
                kind="appimage",
                filename=path_obj.name,
                meta=self._format_file_meta(path_obj),
                selected=True,
            )
            self.install_button.setEnabled(True)
            self.status_log.append(f"› Selected AppImage: {file_path}")
            self.logger.log_operation('info', f"Selected AppImage for installation: {file_path}")
    
    def install_appimage(self):
        """Start the installation process."""
        if not self.appimage_path:
            return
            
        # Disable buttons during installation
        self.install_button.setEnabled(False)
        self.select_button.setEnabled(False)
        # Swap button -> progress bar without shifting layout
        self.install_action_stack.setCurrentWidget(self.progress_bar)
        self.progress_bar.setValue(0)
        
        # Clear log
        self.status_log.clear()
        self.status_log.append("Starting installation...")
        
        # Start installer thread
        self.installer_thread = AppImageInstaller(self.appimage_path)
        self.installer_thread.status_update.connect(self.update_status)
        self.installer_thread.progress_update.connect(self.update_progress)
        self.installer_thread.finished_signal.connect(self.installation_finished)
        self.installer_thread.start()
    
    def update_status(self, message):
        """Update status log with new message."""
        self.status_log.append(message)
        self.status_log.ensureCursorVisible()
    
    def update_progress(self, value):
        """Update progress bar."""
        self.progress_bar.setValue(value)
    
    def installation_finished(self, success, message):
        """Handle installation completion."""
        # Re-enable buttons
        self.install_button.setEnabled(True)
        self.select_button.setEnabled(True)
        # Swap progress bar -> button
        self.install_action_stack.setCurrentWidget(self.install_button)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_log.append("✓ Installation completed successfully")

            self.appimage_path = None
            self._set_file_state(
                kind="appimage",
                filename="No AppImage selected",
                meta="Click \"Browse\" to pick a file",
                selected=False,
            )
            self.install_button.setEnabled(False)

            self.refresh_installed_apps()
        else:
            QMessageBox.critical(self, "Error", f"Installation failed: {message}")
            self.status_log.append(f"✗ Installation failed: {message}")

        self.installer_thread = None

    def select_deb_package(self):
        """Open file dialog to select .deb package."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select .deb Package",
            "",
            ".deb files (*.deb);;All files (*)"
        )

        if file_path:
            self.deb_path = file_path
            path_obj = Path(file_path)
            self._set_file_state(
                kind="deb",
                filename=path_obj.name,
                meta=self._format_file_meta(path_obj),
                selected=True,
            )
            self.deb_install_button.setEnabled(True)
            self.status_log.append(f"› Selected .deb package: {file_path}")
            self.logger.log_operation('info', f"Selected .deb package for installation: {file_path}")

    def _format_file_meta(self, path_obj: Path) -> str:
        """Build a 'parent · size MB' string for the dropzone meta line."""
        parent = str(path_obj.parent)
        home = str(Path.home())
        if parent.startswith(home):
            parent = "~" + parent[len(home):]
        try:
            size_mb = path_obj.stat().st_size / (1024 * 1024)
            return f"{parent} · {size_mb:.1f} MB"
        except OSError:
            return parent

    def _set_file_state(self, *, kind: str, filename: str, meta: str, selected: bool):
        """Update dropzone visuals for a selected/empty state without inline styles."""
        if kind == "deb":
            label = self.deb_file_label
            meta_label = self.deb_file_meta
            dropzone = self.deb_dropzone
        else:
            label = self.file_label
            meta_label = self.file_meta
            dropzone = self.dropzone

        label.setText(filename)
        meta_label.setText(meta)

        new_state = "active" if selected else "empty"
        label.setProperty("state", "" if selected else "empty")
        dropzone.setProperty("state", new_state)

        for w in (label, dropzone):
            w.style().unpolish(w)
            w.style().polish(w)

    def install_deb_package(self):
        """Start the .deb installation process."""
        if not self.deb_path:
            return

        # Disable buttons during installation
        self.deb_install_button.setEnabled(False)
        self.select_deb_button.setEnabled(False)
        # Swap button -> progress bar without shifting layout
        self.deb_install_action_stack.setCurrentWidget(self.deb_progress_bar)
        self.deb_progress_bar.setValue(0)

        # Clear log
        self.status_log.clear()
        self.status_log.append("Starting .deb installation...")

        # Start installer thread
        self.deb_installer_thread = DebInstaller(self.deb_path)
        self.deb_installer_thread.status_update.connect(self.update_deb_status)
        self.deb_installer_thread.progress_update.connect(self.update_deb_progress)
        self.deb_installer_thread.finished_signal.connect(self.deb_installation_finished)
        self.deb_installer_thread.start()

    def update_deb_status(self, message):
        """Update status log with new message for .deb installation."""
        self.status_log.append(message)
        self.status_log.ensureCursorVisible()

    def update_deb_progress(self, value):
        """Update progress bar for .deb installation."""
        self.deb_progress_bar.setValue(value)

    def deb_installation_finished(self, success, message):
        """Handle .deb installation completion."""
        # Re-enable buttons
        self.deb_install_button.setEnabled(True)
        self.select_deb_button.setEnabled(True)
        # Swap progress bar -> button
        self.deb_install_action_stack.setCurrentWidget(self.deb_install_button)

        if success:
            QMessageBox.information(self, "Success", message)
            self.status_log.append("✓ .deb installation completed successfully")

            self.deb_path = None
            self._set_file_state(
                kind="deb",
                filename="No .deb package selected",
                meta="Click \"Browse\" to pick a file",
                selected=False,
            )
            self.deb_install_button.setEnabled(False)

            self.refresh_installed_apps()
        else:
            QMessageBox.critical(self, "Error", f".deb installation failed: {message}")
            self.status_log.append(f"✗ .deb installation failed: {message}")

        # Log the installation result
        if success:
            # Extract package info for logging
            package_info = self.deb_installer_thread.get_package_info() if hasattr(self.deb_installer_thread, 'get_package_info') else None
            if package_info:
                package_name = package_info.get('Package', 'Unknown')
                version = package_info.get('Version', 'Unknown')
                self.logger.log_deb_installation(package_name, version, success=True)
            else:
                self.logger.log_operation('info', f".deb installation successful: {message}")
        else:
            self.logger.log_operation('error', f".deb installation failed: {message}")

        # Clean up thread
        self.deb_installer_thread = None

    def refresh_installed_apps(self):
        """Refresh the list of installed applications and packages."""
        try:
            self.apps_list.clear()
            installed_items = InstalledAppsManager.get_combined_installed_items()

            if not installed_items:
                item = QListWidgetItem("No installed items yet — install an AppImage or .deb to see it here.")
                item.setData(Qt.UserRole, None)
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                self.apps_list.addItem(item)
                self._update_count_badges(0, 0)
                self.status_log.append("· No installed items found")
                return

            appimage_count = 0
            deb_count = 0

            for item in installed_items:
                if item['type'] == 'appimage':
                    display_text = f"📦  {item['name']}  ·  {item['size']} MB  ·  AppImage"
                    appimage_count += 1
                else:
                    display_text = f"📋  {item['name']}  ·  v{item.get('version', 'N/A')}  ·  .deb"
                    deb_count += 1

                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.UserRole, item)
                self.apps_list.addItem(list_item)

            self._update_count_badges(appimage_count, deb_count)
            self.status_log.append(f"· Found {appimage_count} AppImage(s) and {deb_count} .deb package(s)")

        except Exception as e:
            self.status_log.append(f"✗ Error refreshing list: {str(e)}")

    def _update_count_badges(self, appimage_count: int, deb_count: int) -> None:
        """Refresh the count pills in the Manage tab header."""
        try:
            self.appimage_badge.setText(f"{appimage_count} AppImages")
            self.deb_badge.setText(f"{deb_count} .deb")
        except Exception:
            pass
    
    def on_app_selection_changed(self):
        """Handle app/package selection change."""
        current_item = self.apps_list.currentItem()
        if current_item and current_item.data(Qt.UserRole):
            item_data = current_item.data(Qt.UserRole)
            item_type = item_data.get('type')

            if item_type == 'appimage':
                self.launch_button.setEnabled(True)
                self.launch_button.setText("🚀  Launch")
                self.selection_hint.setText(f"Selected · {item_data.get('name', '')}")
            elif item_type == 'deb':
                self.launch_button.setEnabled(False)
                self.launch_button.setText("🚀  Launch (N/A)")
                self.selection_hint.setText(f"Selected .deb · {item_data.get('name', '')}")
            else:
                self.launch_button.setEnabled(False)
                self.launch_button.setText("🚀  Launch")
                self.selection_hint.setText("Select an item to enable actions")

            self.uninstall_button.setEnabled(True)
        else:
            self.launch_button.setEnabled(False)
            self.launch_button.setText("🚀  Launch")
            self.uninstall_button.setEnabled(False)
            self.selection_hint.setText("Select an item to enable actions")
    
    def launch_selected_app(self):
        """Launch the selected application with comprehensive logging."""
        current_item = self.apps_list.currentItem()
        if not current_item:
            return

        item_data = current_item.data(Qt.UserRole)
        if not item_data:
            return

        item_type = item_data.get('type')

        # Only launch AppImages, not .deb packages
        if item_type != 'appimage':
            QMessageBox.information(self, "Info", ".deb packages cannot be launched like applications.\n\n.deb packages provide system libraries or services that are automatically used by other applications.")
            return

        app_name = item_data['name']
        apprun_path = item_data['apprun']
        # Use both sandbox flags to fix sandbox issues: --no-sandbox --disable-setuid-sandbox
        command_with_sandbox = [apprun_path, '--no-sandbox', '--disable-setuid-sandbox']
        command_without_sandbox = [apprun_path]
        
        # Get the directory containing AppRun - critical for APPDIR resolution
        apprun_dir = os.path.dirname(os.path.abspath(apprun_path))
        
        try:
            self.status_log.append(f"Launching {app_name}...")
            self.logger.log_operation('info', f"Attempting to launch {app_name}")
            
            # Try with --no-sandbox first
            final_command = command_with_sandbox
            process = subprocess.Popen(
                command_with_sandbox,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=apprun_dir
            )
            
            # Give the process a moment to start and potentially fail immediately
            try:
                stdout, stderr = process.communicate(timeout=2)
                # If we get here, the process finished quickly
                if process.returncode != 0:
                    # Check if the error is about unknown sandbox flags
                    error_output = stderr or stdout or ""
                    if (("no-sandbox" in error_output.lower() and "unknown" in error_output.lower()) or
                        ("disable-setuid-sandbox" in error_output.lower() and "unknown" in error_output.lower())):
                        # Try without sandbox flags
                        self.status_log.append(f"Retrying {app_name} without sandbox flags...")
                        final_command = command_without_sandbox
                        
                        process = subprocess.Popen(
                            command_without_sandbox,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=apprun_dir
                        )
                        
                        try:
                            stdout, stderr = process.communicate(timeout=2)
                            if process.returncode != 0:
                                error_output = stderr or stdout or f"Process exited with code {process.returncode}"
                                self.logger.log_app_launch(app_name, final_command, success=False, error_output=error_output)
                                error_msg = f"Application failed to start.\nExit code: {process.returncode}\nError: {error_output}"
                                self.status_log.append(f"❌ {app_name} failed to launch")
                                QMessageBox.critical(self, "Launch Error", error_msg)
                                return
                            else:
                                # Success without --no-sandbox
                                self.logger.log_app_launch(app_name, final_command, success=True)
                                self.status_log.append(f"✅ {app_name} launched successfully!")
                                
                        except subprocess.TimeoutExpired:
                            # Process is still running - success
                            # Don't kill it! Just log success and let it continue running
                            self.logger.log_app_launch(app_name, final_command, success=True)
                            self.status_log.append(f"✅ {app_name} launched successfully!")
                    else:
                        # Different error, not related to --no-sandbox
                        self.logger.log_app_launch(app_name, final_command, success=False, error_output=error_output)
                        error_msg = f"Application failed to start.\nExit code: {process.returncode}\nError: {error_output}"
                        self.status_log.append(f"❌ {app_name} failed to launch")
                        QMessageBox.critical(self, "Launch Error", error_msg)
                        return
                else:
                    # Process completed successfully with --no-sandbox
                    self.logger.log_app_launch(app_name, final_command, success=True)
                    self.status_log.append(f"✅ {app_name} launched successfully!")
                    
            except subprocess.TimeoutExpired:
                # Process is still running after timeout - this is good for GUI apps
                # Don't kill it! Just log success and let it continue running
                self.logger.log_app_launch(app_name, final_command, success=True)
                self.status_log.append(f"✅ {app_name} launched successfully!")
            
        except FileNotFoundError:
            error_msg = f"AppRun file not found: {apprun_path}"
            self.logger.log_app_launch(app_name, command_with_sandbox, success=False, error_output=error_msg)
            self.status_log.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "Launch Error", error_msg)
            
        except PermissionError:
            error_msg = f"Permission denied executing: {apprun_path}"
            self.logger.log_app_launch(app_name, command_with_sandbox, success=False, error_output=error_msg)
            self.status_log.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "Launch Error", error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error launching {app_name}: {str(e)}"
            self.logger.log_app_launch(app_name, command_with_sandbox, success=False, error_output=error_msg)
            self.status_log.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "Launch Error", error_msg)
    
    def uninstall_selected_app(self):
        """Uninstall the selected application or package."""
        current_item = self.apps_list.currentItem()
        if not current_item:
            return

        item_data = current_item.data(Qt.UserRole)
        if not item_data:
            return

        item_name = item_data['name']
        item_type = item_data.get('type')

        # Prepare confirmation message based on item type
        if item_type == 'appimage':
            confirm_message = (
                f"Are you sure you want to uninstall '{item_name}'?\n\n"
                f"This will remove:\n"
                f"• Application files from ~/Applications/{item_name}\n"
                f"• Desktop entry from applications menu\n"
                f"• User configuration will be preserved"
            )
            final_confirm_text = f"Type the app name exactly to confirm: {item_name}"
        else:  # deb package
            confirm_message = (
                f"Are you sure you want to uninstall '{item_name}'?\n\n"
                f"This will remove the .deb package and its system files.\n"
                f"⚠️  Warning: This may affect other applications that depend on this package."
            )
            final_confirm_text = f"Type the package name exactly to confirm: {item_name}"

        # First confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            confirm_message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Second stricter confirmation
            text, ok = QInputDialog.getText(
                self,
                "Final Confirmation",
                final_confirm_text
            )

            if not ok or text.strip() != item_name:
                QMessageBox.information(self, "Cancelled", "Uninstall cancelled.")
                return

            try:
                self.status_log.append(f"Uninstalling {item_name}...")

                # Handle uninstallation based on item type
                if item_type == 'appimage':
                    result = InstalledAppsManager.uninstall_app(item_name)
                    success = result == True
                    error_msg = None if success else (result[1] if isinstance(result, tuple) else "Unknown error")
                else:  # deb package
                    success, error_msg = InstalledAppsManager.uninstall_deb_package(item_name)

                if success:
                    self.status_log.append(f"✅ {item_name} uninstalled successfully!")
                    QMessageBox.information(self, "Success", f"{item_name} has been uninstalled successfully!")

                    # Log the uninstallation
                    if item_type == 'deb':
                        self.logger.log_deb_uninstallation(item_name, success=True)

                    # Refresh the list
                    self.refresh_installed_apps()
                else:
                    error_msg = f"Failed to uninstall {item_name}" + (f": {error_msg}" if error_msg else "")
                    self.status_log.append(f"❌ {error_msg}")
                    QMessageBox.critical(self, "Uninstall Error", error_msg)

                    # Log the failed uninstallation
                    if item_type == 'deb':
                        self.logger.log_deb_uninstallation(item_name, success=False, error_output=error_msg)

            except Exception as e:
                error_msg = f"Failed to uninstall {item_name}: {str(e)}"
                self.status_log.append(f"❌ {error_msg}")
                QMessageBox.critical(self, "Uninstall Error", error_msg)

                # Log the failed uninstallation
                if item_type == 'deb':
                    self.logger.log_deb_uninstallation(item_name, success=False, error_output=error_msg)
    

    
    # Removed update_desktop_entries and check_desktop_entries_update methods per request


def main():
    """Main application entry point."""
    QApplication.setApplicationName("SquashMate")
    QApplication.setApplicationDisplayName("SquashMate")
    QApplication.setOrganizationName("SquashMate")
    QApplication.setApplicationVersion(__version__)
    QApplication.setDesktopFileName("SquashMate")

    app = QApplication(sys.argv)

    if Path(APP_ICON_PATH).exists():
        app.setWindowIcon(QIcon(APP_ICON_PATH))

    window = SquashMateGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()