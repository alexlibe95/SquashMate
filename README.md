# SquashMate - AppImage Installation Manager

A simple and elegant desktop application for managing AppImage installations on Linux systems.

Note: This app was primarily created to make it very easy to update Cursor to new versions (and it works great for any AppImage).

## Features

### Installation Management
- **Easy AppImage Selection**: Browse and select AppImage files with a clean file picker
- **Automatic Installation**: Extracts and installs AppImages to `~/Applications/`
- **Desktop Integration**: Creates `.desktop` files for launcher integration
- **Progress Tracking**: Real-time status updates and progress indication
- **Version Management**: Handles app updates while preserving user configurations

### Installed Apps Management
- **Applications List**: View all installed AppImages with sizes
- **Launch Applications**: Launch installed apps directly from SquashMate
- **Uninstall Applications**: Remove apps with confirmation dialogs
- **Refresh Functionality**: Update the installed apps list on demand
- **Configuration Preservation**: User settings are kept during uninstallation

### Logging & Debugging
- **Background Logging (no in-app viewer)**: Operations and launches are logged under `~/.local/share/squashmate/`
- **Application Launch Logs**: Individual logs per app (helpful if a launch fails)
- **Desktop Launch Logging**: Launches from the applications menu are also logged via a wrapper
- **Launch Wrapper**: `~/.local/bin/squashmate_launcher.py` captures errors when apps start from desktop entries
- **Error Debugging**: Failed launches capture stderr output for troubleshooting


### User Interface
- **Tabbed Interface**: Separate tabs for installation and management
- **Modern UI**: Clean, minimal interface built with PyQt5
- **Status Logging**: Real-time status updates and comprehensive logging

## Requirements

- Python 3.6+
- PyQt5
- Linux (Ubuntu/Debian compatible)

## Installation

1. Clone or download this repository
2. Install PyQt5 dependency:
   ```bash
   sudo apt install python3-pyqt5
   ```
3. Make scripts executable (already done):
   ```bash
   chmod +x squashmate.py launch.sh
   ```
4. Run the application:
   ```bash
   ./launch.sh
   # or directly:
   python3 squashmate.py
   ```

### Quick Install & Run
```bash
git clone <repository-url>
cd SquashMate
./install_squashmate.sh
```

This will:
- Install PyQt5 dependency
- Add SquashMate to your applications menu
- Create a desktop entry with icon
- Make SquashMate accessible via "Show Apps"

### Manual Installation
If you prefer to run without installing to the system:
```bash
sudo apt install python3-pyqt5
./launch.sh
```

## Usage

### Accessing SquashMate
- **From Applications Menu**: Search for "SquashMate" in Ubuntu's "Show Apps"
- **From Terminal**: Run `./launch.sh` in the SquashMate directory
- **Categories**: Found under System > Utilities in the applications menu

### Installing AppImages
1. Go to the **"Install AppImage"** tab
2. Click "Select AppImage" to choose an AppImage file
3. Click "Install/Update Application" to begin installation
4. Monitor progress in the status log
5. The installed application will be available in your system's application launcher

### Managing Installed Applications
1. Go to the **"Manage Installed"** tab
2. View all installed AppImages with their sizes
3. Select an application to:
   - **Launch**: Run the application directly
   - **Uninstall**: Remove the application (with confirmation)
4. Use **Refresh** to update the list after manual changes

Tip: Uninstall requires a second, stricter confirmation where you type the app name to avoid accidental removal.


### Log Locations (view with any text editor)
- **Main Log**: `~/.local/share/squashmate/squashmate.log`
- **App Logs**: `~/.local/share/squashmate/apps/<AppName>.log`
- **Launch Wrapper**: `~/.local/bin/squashmate_launcher.py`

### Troubleshooting Desktop Launches
If apps installed with SquashMate don't launch from Ubuntu's dashboard:
1. Check the log files directly at `~/.local/share/squashmate/apps/<AppName>.log`
2. Desktop launches are marked as "Desktop Launch" in logs
3. Common issues include missing dependencies or permission problems

### Uninstalling SquashMate
Run the uninstall script:
```bash
./uninstall_squashmate.sh
```

## How It Works

1. **Extraction**: Uses the AppImage's built-in `--appimage-extract` command
2. **Installation**: Moves extracted files to `~/Applications/<AppName>/`
3. **Desktop Entry**: Creates a `.desktop` file with launcher wrapper for error logging
4. **Launch Wrapper**: Installs `~/.local/bin/squashmate_launcher.py` for desktop launches
5. **Permissions**: Sets proper executable permissions for all components
6. **Logging**: All launches (from SquashMate and desktop) are logged with errors

Note on .desktop files: Use `install_squashmate.sh` to create a correct desktop entry for your machine. The repository version uses relative paths for safety.

## Future Enhancements

The codebase is designed to be modular, making it easy to add support for:
- Other package formats (Flatpak, Snap, etc.)
- Custom installation directories
- Advanced configuration options
- Batch installations

## License

This project is open source and available under the MIT License.