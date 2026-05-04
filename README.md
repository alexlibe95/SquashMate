# SquashMate

**SquashMate** is a Linux desktop app (PyQt5) that makes AppImage and `.deb` installation easier, with built-in logging, desktop integration, and safe uninstall flows.

It was built to remove repetitive package-management friction for tools that are commonly shipped as AppImages or `.deb` files.

---

## Highlights

- Install or update AppImages into `~/Applications/<AppName>/`
- Install `.deb` files with privilege escalation (`pkexec`) and dependency fix-up
- Generate desktop entries for AppImages automatically
- Launch AppImages from inside SquashMate
- Uninstall AppImages and `.deb` packages with double confirmation
- Capture detailed logs for installs, uninstalls, and launch failures

---

## Current Scope

SquashMate currently focuses on:

- **AppImage lifecycle**: install, update, list, launch, uninstall
- **`.deb` lifecycle**: install, list installed packages, uninstall
- **Desktop UX**: launcher integration and persistent logs

It does **not** currently manage Flatpak, Snap, RPM, or repository browsing.

---

## Tech Stack

- Python 3
- PyQt5
- Linux desktop tooling (`dpkg`, `apt-get`, `pkexec`, `update-desktop-database`)

---

## Requirements

### Runtime

- Linux (tested on Ubuntu/Debian-style systems)
- Python 3.8+ recommended
- `python3-pyqt5`

### For `.deb` install/uninstall in GUI

- `pkexec` (usually provided by `policykit-1`)

Install requirements:

```bash
sudo apt update
sudo apt install -y python3-pyqt5 policykit-1
```

---

## Quick Start

```bash
git clone <repository-url>
cd SquashMate
chmod +x launch.sh squashmate.py
./launch.sh
```

---

## Optional System Integration

Install a desktop launcher entry and wrapper:

```bash
chmod +x install_squashmate.sh
./install_squashmate.sh
```

This script:

- Ensures `python3-pyqt5` is present
- Creates `~/.local/share/applications/SquashMate.desktop`
- Installs `~/.local/bin/squashmate_launcher.py`
- Updates desktop database (if available)

Uninstall integration:

```bash
chmod +x uninstall_squashmate.sh
./uninstall_squashmate.sh
```

---

## Usage

### 1) Install AppImage

1. Open the **Install AppImage** tab
2. Select an `.AppImage` file
3. Click **Install/Update Application**

What SquashMate does:

- Extracts using `--appimage-extract`
- Installs to `~/Applications/<AppName>/`
- Creates desktop entry in `~/.local/share/applications/`
- Sets execute permissions
- Installs/updates launcher wrapper in `~/.local/bin/`

### 2) Install `.deb`

1. Open the **Install .deb** tab
2. Select a `.deb` file
3. Click **Install .deb Package**
4. Approve authentication prompt when requested

Install flow:

- Validates package with `dpkg --info`
- Installs via `dpkg -i`
- Runs `apt-get install -f -y` for dependency resolution
- Verifies installed state via `dpkg -l`

### 3) Manage Installed Items

In **Manage Installed**:

- `📦` items are AppImages (launch + uninstall supported)
- `📋` items are installed `.deb` packages (uninstall supported)
- Uninstall requires a second typed confirmation to reduce accidental removals

---

## Logging & Diagnostics

SquashMate keeps logs under:

- Main log: `~/.local/share/squashmate/squashmate.log`
- App launch logs: `~/.local/share/squashmate/apps/<AppName>.log`
- `.deb` install/uninstall log: `~/.local/share/squashmate/deb_packages.log`
- Desktop wrapper: `~/.local/bin/squashmate_launcher.py`

Desktop launches are marked as **Desktop Launch** in per-app logs.

---

## Known Limitations

- `.deb` listing shows installed packages from the system package database, which can be large on some systems.
- `.deb` operations rely on host tools (`dpkg`, `apt-get`, `pkexec`) and desktop authentication configuration.
- Fallback terminal-based `.deb` install path assumes a GNOME terminal environment.

---

## Project Structure

- `squashmate.py` - main GUI and install/uninstall logic
- `squashmate_launcher.py` - AppImage launch wrapper used by desktop entries
- `install_squashmate.sh` - desktop integration installer
- `uninstall_squashmate.sh` - desktop integration remover
- `launch.sh` - convenience runner
- `test_launcher.py` - launcher wrapper smoke test
- `VERSION` - single source of truth for the app version

---

## Releasing a New Version

The app version lives in a single file: `VERSION` at the project root. To ship a new release:

1. Edit `VERSION` (e.g. `1.0.0` → `1.1.0`).
2. Commit and tag the release.

That value is automatically picked up by:

- The window header version pill (`v1.0.0`).
- `QApplication.setApplicationVersion(...)` (used by Qt for `--version` and dialogs).
- `install_squashmate.sh`, which prints the version during install.

No code edits are required to bump versions.

---

## Improvements Applied (Latest Update)

- Fixed `.deb` install success detection so both installation steps must succeed before reporting success.
- Improved AppImage extraction reliability by always restoring original working directory and cleaning temporary extraction data on failure.
- Hardened manual command examples for paths containing spaces by shell-quoting `.deb` paths.
- Refreshed this README for website/use-case clarity and accurate current behavior.

---

## Website Readiness Notes

If you are building a project website, this README now supports:

- Clear product value proposition
- Accurate feature and scope breakdown
- Operational flow suitable for docs pages
- Explicit limitations and environment assumptions

You can reuse sections directly for:

- Landing page (`Highlights`, `Current Scope`)
- Docs (`Quick Start`, `Usage`, `Logging`, `Known Limitations`)
- Changelog (`Improvements Applied`)

---

## Roadmap Ideas

- Filter/search in installed `.deb` package list
- Track only SquashMate-managed `.deb` installs as an optional mode
- Add exportable diagnostic bundle for support issues
- Add optional dark theme and accessibility tuning
- Add release packaging (`.deb`/AppImage) for SquashMate itself

---

## License

MIT (recommended). Add a `LICENSE` file if not already included.