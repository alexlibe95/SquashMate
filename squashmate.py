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
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QTextEdit, QFileDialog, 
                            QMessageBox, QProgressBar, QFrame, QListWidget, QListWidgetItem,
                            QTabWidget, QSplitter, QGroupBox, QGridLayout, QInputDialog, QStackedLayout)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon


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
        try:
            # Change to temp directory for extraction
            original_dir = os.getcwd()
            temp_dir = tempfile.mkdtemp()
            os.chdir(temp_dir)
            
            # Make AppImage executable
            os.chmod(self.appimage_path, 0o755)
            
            # Extract AppImage
            result = subprocess.run([self.appimage_path, '--appimage-extract'], 
                                  capture_output=True, text=True, cwd=temp_dir)
            
            if result.returncode != 0:
                os.chdir(original_dir)
                return False
                
            self.extraction_dir = temp_dir
            os.chdir(original_dir)
            return True
            
        except Exception as e:
            self.status_update.emit(f"Extraction error: {str(e)}")
            return False
    
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
            result = subprocess.run(['which', 'pkexec'], capture_output=True, text=True)
            return result.returncode == 0
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
                        f"sudo dpkg -i {self.deb_path}\n"
                        f"sudo apt-get install -f\n\n"
                        f"Or using apt directly:\n"
                        f"sudo apt install {self.deb_path}")
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
            success = False
            for cmd in install_cmds:
                try:
                    self.status_update.emit(f"Running: {cmd}")
                    pkexec_cmd = ['pkexec', 'bash', '-c', cmd]
                    result = subprocess.run(pkexec_cmd, capture_output=True, text=True, timeout=120)

                    if result.returncode == 0:
                        self.status_update.emit("Command completed successfully")
                        success = True
                    else:
                        self.status_update.emit(f"Command failed: {result.stderr}")
                        break  # Stop if any command fails

                except subprocess.TimeoutExpired:
                    self.status_update.emit("Command timed out")
                    break
                except Exception as e:
                    self.status_update.emit(f"Command error: {str(e)}")
                    break

            if success:
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
            
            # Remove desktop file
            desktop_file = InstalledAppsManager.get_desktop_file(app_name)
            if desktop_file and os.path.exists(desktop_file):
                os.remove(desktop_file)
            
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

            return result.returncode == 0, result.stderr if result.returncode != 0 else None

        except Exception as e:
            return False, str(e)

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
        self.setWindowTitle("SquashMate - AppImage & Deb Package Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(700, 500)
        
        # Apply modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton.danger {
                background-color: #f44336;
            }
            QPushButton.danger:hover {
                background-color: #d32f2f;
            }
            QPushButton.danger:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4CAF50;
            }
        """)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("SquashMate")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E7D32; margin-bottom: 10px;")
        layout.addWidget(title)
        
        subtitle = QLabel("AppImage & Deb Package Manager")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Install tabs
        self.create_install_tab()
        self.create_deb_install_tab()

        # Manage tab
        self.create_manage_tab()
        

        
        # Status log (shared across tabs)
        log_label = QLabel("Status Log:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(120)
        self.status_log.append("Ready to install and manage AppImages...")
        layout.addWidget(self.status_log)
    
    def create_install_tab(self):
        """Create the installation tab."""
        install_widget = QWidget()
        layout = QVBoxLayout(install_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # File selection section
        file_section = QFrame()
        file_section.setFrameStyle(QFrame.Box)
        file_section.setStyleSheet("""
            QFrame { 
                background-color: #f8f9fa; 
                border-radius: 10px; 
                padding: 20px; 
                border: 2px solid #e9ecef;
                min-height: 80px;
            }
        """)
        file_layout = QVBoxLayout(file_section)
        file_layout.setSpacing(10)
        file_layout.setContentsMargins(10, 15, 10, 15)
        
        self.file_label = QLabel("No AppImage selected")
        self.file_label.setStyleSheet("""
            color: #6c757d; 
            font-style: italic; 
            font-size: 14px; 
            padding: 5px 0px;
            min-height: 20px;
        """)
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        self.select_button = QPushButton("Select AppImage")
        self.select_button.clicked.connect(self.select_appimage)
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 15px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        file_layout.addWidget(self.select_button)
        
        layout.addWidget(file_section)
        
        # Install action area (stacked: button <-> progress bar)
        self.install_button = QPushButton("Install/Update Application")
        self.install_button.clicked.connect(self.install_appimage)
        self.install_button.setEnabled(False)
        self.install_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 18px 20px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover:enabled {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
        """)

        self.install_action_container = QWidget()
        self.install_action_stack = QStackedLayout(self.install_action_container)

        # Page 1: Button
        self.install_action_stack.addWidget(self.install_button)

        # Page 2: Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setValue(0)
        self.install_action_stack.addWidget(self.progress_bar)
        self.install_action_stack.setCurrentWidget(self.install_button)

        layout.addWidget(self.install_action_container)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        self.tab_widget.addTab(install_widget, "Install AppImage")

    def create_deb_install_tab(self):
        """Create the .deb installation tab."""
        deb_install_widget = QWidget()
        layout = QVBoxLayout(deb_install_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # File selection section
        file_section = QFrame()
        file_section.setFrameStyle(QFrame.Box)
        file_section.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                border: 2px solid #e9ecef;
                min-height: 80px;
            }
        """)
        file_layout = QVBoxLayout(file_section)
        file_layout.setSpacing(10)
        file_layout.setContentsMargins(10, 15, 10, 15)

        self.deb_file_label = QLabel("No .deb package selected")
        self.deb_file_label.setStyleSheet("""
            color: #6c757d;
            font-style: italic;
            font-size: 14px;
            padding: 5px 0px;
            min-height: 20px;
        """)
        self.deb_file_label.setWordWrap(True)
        file_layout.addWidget(self.deb_file_label)

        self.select_deb_button = QPushButton("Select .deb Package")
        self.select_deb_button.clicked.connect(self.select_deb_package)
        self.select_deb_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 15px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        file_layout.addWidget(self.select_deb_button)

        layout.addWidget(file_section)

        # Install action area (stacked: button <-> progress bar)
        self.deb_install_button = QPushButton("Install .deb Package")
        self.deb_install_button.clicked.connect(self.install_deb_package)
        self.deb_install_button.setEnabled(False)
        self.deb_install_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 18px 20px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover:enabled {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
        """)

        self.deb_install_action_container = QWidget()
        self.deb_install_action_stack = QStackedLayout(self.deb_install_action_container)

        # Page 1: Button
        self.deb_install_action_stack.addWidget(self.deb_install_button)

        # Page 2: Progress bar
        self.deb_progress_bar = QProgressBar()
        self.deb_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #dc3545;
                border-radius: 3px;
            }
        """)
        self.deb_progress_bar.setValue(0)
        self.deb_install_action_stack.addWidget(self.deb_progress_bar)
        self.deb_install_action_stack.setCurrentWidget(self.deb_install_button)

        layout.addWidget(self.deb_install_action_container)

        # Add stretch to push everything to top
        layout.addStretch()

        self.tab_widget.addTab(deb_install_widget, "Install .deb")

    def create_manage_tab(self):
        """Create the management tab."""
        manage_widget = QWidget()
        layout = QVBoxLayout(manage_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        header_label = QLabel("Installed Applications:")
        header_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_installed_apps)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Installed apps list
        self.apps_list = QListWidget()
        self.apps_list.itemSelectionChanged.connect(self.on_app_selection_changed)
        layout.addWidget(self.apps_list)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.launch_button = QPushButton("Launch")
        self.launch_button.clicked.connect(self.launch_selected_app)
        self.launch_button.setEnabled(False)
        buttons_layout.addWidget(self.launch_button)
        
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.setProperty("class", "danger")
        self.uninstall_button.clicked.connect(self.uninstall_selected_app)
        self.uninstall_button.setEnabled(False)
        buttons_layout.addWidget(self.uninstall_button)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        self.tab_widget.addTab(manage_widget, "Manage Installed")
    

        
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
            self.file_label.setText(f"Selected: {Path(file_path).name}")
            self.file_label.setStyleSheet("""
                color: #28a745; 
                font-weight: bold; 
                font-size: 14px; 
                padding: 5px 0px;
                min-height: 20px;
            """)
            self.install_button.setEnabled(True)
            self.status_log.append(f"Selected AppImage: {file_path}")
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
        
        # Show result message
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_log.append("\n✅ Installation completed successfully!")
            
            # Reset the interface to initial state for next installation
            self.appimage_path = None
            self.file_label.setText("No AppImage selected")
            self.file_label.setStyleSheet("""
                color: #6c757d; 
                font-style: italic; 
                font-size: 14px; 
                padding: 5px 0px;
                min-height: 20px;
            """)
            self.install_button.setEnabled(False)
            
            # Refresh the installed apps list
            self.refresh_installed_apps()
        else:
            QMessageBox.critical(self, "Error", f"Installation failed: {message}")
            self.status_log.append(f"\n❌ Installation failed: {message}")
        
        # Clean up thread
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
            self.deb_file_label.setText(f"Selected: {Path(file_path).name}")
            self.deb_file_label.setStyleSheet("""
                color: #28a745;
                font-weight: bold;
                font-size: 14px;
                padding: 5px 0px;
                min-height: 20px;
            """)
            self.deb_install_button.setEnabled(True)
            self.status_log.append(f"Selected .deb package: {file_path}")
            self.logger.log_operation('info', f"Selected .deb package for installation: {file_path}")

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

        # Show result message
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_log.append("\n✅ .deb installation completed successfully!")

            # Reset the interface to initial state for next installation
            self.deb_path = None
            self.deb_file_label.setText("No .deb package selected")
            self.deb_file_label.setStyleSheet("""
                color: #6c757d;
                font-style: italic;
                font-size: 14px;
                padding: 5px 0px;
                min-height: 20px;
            """)
            self.deb_install_button.setEnabled(False)

            # Refresh the installed apps list
            self.refresh_installed_apps()
        else:
            QMessageBox.critical(self, "Error", f".deb installation failed: {message}")
            self.status_log.append(f"\n❌ .deb installation failed: {message}")

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
                item = QListWidgetItem("No applications or packages installed")
                item.setData(Qt.UserRole, None)
                self.apps_list.addItem(item)
                self.status_log.append("No installed applications or packages found.")
                return

            appimage_count = 0
            deb_count = 0

            for item in installed_items:
                # Create display text with item name, size, and type
                if item['type'] == 'appimage':
                    display_text = f"📦 {item['name']} ({item['size']} MB) [AppImage]"
                    appimage_count += 1
                else:  # deb package
                    display_text = f"📋 {item['name']} ({item.get('version', 'N/A')}) [.deb]"
                    deb_count += 1

                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.UserRole, item)
                self.apps_list.addItem(list_item)

            self.status_log.append(f"Found {appimage_count} AppImage(s) and {deb_count} .deb package(s).")

        except Exception as e:
            self.status_log.append(f"Error refreshing apps list: {str(e)}")
    
    def on_app_selection_changed(self):
        """Handle app/package selection change."""
        current_item = self.apps_list.currentItem()
        if current_item and current_item.data(Qt.UserRole):
            item_data = current_item.data(Qt.UserRole)
            item_type = item_data.get('type')

            # Enable/disable buttons based on item type
            if item_type == 'appimage':
                self.launch_button.setEnabled(True)
                self.launch_button.setText("Launch")
            elif item_type == 'deb':
                self.launch_button.setEnabled(False)  # .deb packages can't be "launched" like AppImages
                self.launch_button.setText("Launch (N/A)")
            else:
                self.launch_button.setEnabled(False)
                self.launch_button.setText("Launch")

            self.uninstall_button.setEnabled(True)
        else:
            self.launch_button.setEnabled(False)
            self.launch_button.setText("Launch")
            self.uninstall_button.setEnabled(False)
    
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
        command_with_sandbox = [apprun_path, '--no-sandbox']
        command_without_sandbox = [apprun_path]
        
        try:
            self.status_log.append(f"Launching {app_name}...")
            self.logger.log_operation('info', f"Attempting to launch {app_name}")
            
            # Try with --no-sandbox first
            final_command = command_with_sandbox
            process = subprocess.Popen(
                command_with_sandbox,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give the process a moment to start and potentially fail immediately
            try:
                stdout, stderr = process.communicate(timeout=2)
                # If we get here, the process finished quickly
                if process.returncode != 0:
                    # Check if the error is about unknown --no-sandbox option
                    error_output = stderr or stdout or ""
                    if "no-sandbox" in error_output.lower() and "unknown" in error_output.lower():
                        # Try without --no-sandbox
                        self.status_log.append(f"Retrying {app_name} without --no-sandbox flag...")
                        final_command = command_without_sandbox
                        
                        process = subprocess.Popen(
                            command_without_sandbox,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
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
                            process.kill()
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
                process.kill()  # Kill the subprocess since we're monitoring, the real app should continue
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
    app = QApplication(sys.argv)
    app.setApplicationName("SquashMate")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = SquashMateGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()