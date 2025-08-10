#!/bin/bash
# SquashMate Installation Script
# Installs SquashMate to the system applications menu

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 SquashMate Installation Script${NC}"
echo "=================================="

# Get the current directory (where SquashMate is located)
SQUASHMATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${BLUE}SquashMate directory: ${SQUASHMATE_DIR}${NC}"

# Check if PyQt5 is installed
echo -e "\n${YELLOW}Checking dependencies...${NC}"
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo -e "${YELLOW}PyQt5 not found. Installing...${NC}"
    sudo apt update
    sudo apt install -y python3-pyqt5
    echo -e "${GREEN}✅ PyQt5 installed successfully${NC}"
else
    echo -e "${GREEN}✅ PyQt5 already installed${NC}"
fi

# Create directories if they don't exist
APPLICATIONS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPLICATIONS_DIR"

# Create the desktop file with absolute paths
echo -e "\n${YELLOW}Creating desktop entry...${NC}"
cat > "$APPLICATIONS_DIR/SquashMate.desktop" << EOF
[Desktop Entry]
Name=SquashMate
Comment=AppImage Installation Manager
Exec=$SQUASHMATE_DIR/launch.sh
Icon=$SQUASHMATE_DIR/squashmate_icon.svg
Type=Application
Categories=System;PackageManager;Utility;
Terminal=false
StartupNotify=true
Keywords=AppImage;Install;Package;Manager;
MimeType=application/x-appimage;
EOF

# Make the desktop file executable
chmod +x "$APPLICATIONS_DIR/SquashMate.desktop"

# Make sure the launch script is executable
chmod +x "$SQUASHMATE_DIR/launch.sh"
chmod +x "$SQUASHMATE_DIR/squashmate.py"

# Install the launcher wrapper for desktop entries
echo -e "\n${YELLOW}Installing launcher wrapper...${NC}"
mkdir -p "$HOME/.local/bin"
cp "$SQUASHMATE_DIR/squashmate_launcher.py" "$HOME/.local/bin/"
chmod +x "$HOME/.local/bin/squashmate_launcher.py"
echo -e "${GREEN}✅ Launcher wrapper installed${NC}"

echo -e "${GREEN}✅ Desktop entry created successfully${NC}"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    echo -e "\n${YELLOW}Updating desktop database...${NC}"
    update-desktop-database "$APPLICATIONS_DIR"
    echo -e "${GREEN}✅ Desktop database updated${NC}"
fi

# Success message
echo -e "\n${GREEN}🎉 SquashMate has been successfully installed!${NC}"
echo -e "${BLUE}You can now find SquashMate in your applications menu.${NC}"
echo -e "${BLUE}Search for 'SquashMate' or look in the System/Utilities category.${NC}"

# Optional: Ask if user wants to launch SquashMate now
echo -e "\n${YELLOW}Would you like to launch SquashMate now? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Launching SquashMate...${NC}"
    "$SQUASHMATE_DIR/launch.sh" &
    echo -e "${GREEN}✅ SquashMate launched!${NC}"
fi

echo -e "\n${BLUE}Installation complete! 🚀${NC}"