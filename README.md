# SquashMate - AppImage & Deb Package Manager

A simple and elegant desktop application for managing AppImage installations and .deb package installations on Linux systems.

## Background

**Why SquashMate was created:**

I built SquashMate out of personal frustration with managing application updates on Linux. As a developer, I frequently use tools like **Cursor** (AI-powered code editor) and **Discord**, which often come as AppImages or .deb packages. The update process was always tedious:

- **AppImages**: Download, make executable, extract, create desktop entries manually
- **.deb packages**: Terminal commands, dependency resolution, permission issues

One day, after spending 30 minutes wrestling with Cursor and Discord updates, I decided to create a proper GUI tool that would handle all of this automatically. SquashMate started as a simple script to update Cursor, but quickly evolved into a comprehensive package manager that works with any AppImage or .deb package.

**The name "SquashMate":**
- "Squash" comes from the AppImage extraction process (squashfs filesystem)
- "Mate" because it's your friendly companion for package management

Now, what used to take 30+ minutes of terminal commands takes just a few clicks in a clean, intuitive interface. Whether you're updating Cursor, installing Discord, or managing any other Linux application, SquashMate makes it effortless.

## Features

### Installation Management
- **Easy AppImage Selection**: Browse and select AppImage files with a clean file picker
- **Easy .deb Package Selection**: Browse and select .deb package files with a clean file picker
- **Automatic AppImage Installation**: Extracts and installs AppImages to `~/Applications/`
- **Automatic .deb Installation**: Installs .deb packages using dpkg/apt with dependency resolution
- **Desktop Integration**: Creates `.desktop` files for AppImage launcher integration
- **Progress Tracking**: Real-time status updates and progress indication for both package types
- **Version Management**: Handles app updates while preserving user configurations
- **Dependency Resolution**: Automatically installs .deb package dependencies

### Installed Items Management
- **Unified Applications List**: View all installed AppImages and .deb packages in one place
- **Launch Applications**: Launch installed AppImages directly from SquashMate
- **Uninstall Applications/Packages**: Remove apps/packages with confirmation dialogs
- **Type Identification**: Clear visual indicators distinguish AppImages from .deb packages
- **Refresh Functionality**: Update the installed items list on demand
- **Configuration Preservation**: User settings are kept during AppImage uninstallation

### Logging & Debugging
- **Background Logging (no in-app viewer)**: Operations and launches are logged under `~/.local/share/squashmate/`
- **Application Launch Logs**: Individual logs per AppImage (helpful if a launch fails)
- **Package Installation Logs**: Detailed logs for .deb package installations and uninstallations
- **Desktop Launch Logging**: Launches from the applications menu are also logged via a wrapper
- **Launch Wrapper**: `~/.local/bin/squashmate_launcher.py` captures errors when apps start from desktop entries
- **Error Debugging**: Failed launches and installations capture stderr output for troubleshooting


### User Interface
- **Tabbed Interface**: Separate tabs for AppImage installation, .deb installation, and unified management
- **Modern UI**: Clean, minimal interface built with PyQt5
- **Status Logging**: Real-time status updates and comprehensive logging for all operations

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

### Installing .deb Packages
1. Go to the **"Install .deb"** tab
2. Click "Select .deb Package" to choose a .deb package file
3. Click "Install .deb Package" to begin installation
4. Monitor progress in the status log (includes dependency installation)
5. The installed package will be available system-wide

### Managing Installed Applications and Packages
1. Go to the **"Manage Installed"** tab
2. View all installed AppImages (📦) and .deb packages (📋) in a unified list
3. Select an item to:
   - **Launch**: Run AppImages directly (not available for .deb packages)
   - **Uninstall**: Remove the application/package (with confirmation)
4. Use **Refresh** to update the list after manual changes

Tip: Uninstall requires a second, stricter confirmation where you type the item name to avoid accidental removal.


### Log Locations (view with any text editor)
- **Main Log**: `~/.local/share/squashmate/squashmate.log`
- **App Logs**: `~/.local/share/squashmate/apps/<AppName>.log`
- **Package Logs**: `~/.local/share/squashmate/deb_packages.log`
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

### AppImage Installation:
1. **Extraction**: Uses the AppImage's built-in `--appimage-extract` command
2. **Installation**: Moves extracted files to `~/Applications/<AppName>/`
3. **Desktop Entry**: Creates a `.desktop` file with launcher wrapper for error logging
4. **Launch Wrapper**: Installs `~/.local/bin/squashmate_launcher.py` for desktop launches
5. **Permissions**: Sets proper executable permissions for all components
6. **Logging**: All launches (from SquashMate and desktop) are logged with errors

### .deb Package Installation:
1. **Validation**: Verifies the .deb file format and integrity
2. **Package Info**: Extracts package metadata (name, version, dependencies)
3. **Dependency Check**: Identifies and installs required dependencies using apt
4. **Installation**: Uses `dpkg -i` to install the package, with fallback dependency resolution
5. **Verification**: Confirms successful installation using `dpkg -l`
6. **Logging**: Records installation attempts, successes, and failures

Note on .desktop files: Use `install_squashmate.sh` to create a correct desktop entry for your machine. The repository version uses relative paths for safety.

## Future Enhancements

The codebase is designed to be modular, making it easy to add support for:
- Other package formats (Flatpak, Snap, etc.)
- Custom installation directories
- Advanced configuration options
- Batch installations
- Package search and download from repositories

## License

This project is open source and available under the MIT License.