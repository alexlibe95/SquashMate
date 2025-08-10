#!/bin/bash
# SquashMate Uninstallation Script
# Removes SquashMate from the system applications menu

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️  SquashMate Uninstallation Script${NC}"
echo "======================================"

# Remove desktop file
APPLICATIONS_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$APPLICATIONS_DIR/SquashMate.desktop"

if [ -f "$DESKTOP_FILE" ]; then
    echo -e "${YELLOW}Removing desktop entry...${NC}"
    rm "$DESKTOP_FILE"
    echo -e "${GREEN}✅ Desktop entry removed${NC}"
else
    echo -e "${YELLOW}⚠️  Desktop entry not found${NC}"
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    echo -e "\n${YELLOW}Updating desktop database...${NC}"
    update-desktop-database "$APPLICATIONS_DIR"
    echo -e "${GREEN}✅ Desktop database updated${NC}"
fi

# Remove launcher wrapper
LAUNCHER_WRAPPER="$HOME/.local/bin/squashmate_launcher.py"
if [ -f "$LAUNCHER_WRAPPER" ]; then
    echo -e "\n${YELLOW}Removing launcher wrapper...${NC}"
    rm "$LAUNCHER_WRAPPER"
    echo -e "${GREEN}✅ Launcher wrapper removed${NC}"
fi

echo -e "\n${GREEN}✅ SquashMate has been removed from the applications menu${NC}"
echo -e "${BLUE}Note: The SquashMate files are still in this directory.${NC}"
echo -e "${BLUE}You can still run SquashMate manually with ./launch.sh${NC}"

echo -e "\n${YELLOW}Would you like to completely remove SquashMate files? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    SQUASHMATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo -e "${RED}This will delete the entire SquashMate directory: $SQUASHMATE_DIR${NC}"
    echo -e "${YELLOW}Are you sure? (y/n)${NC}"
    read -r confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        cd ..
        rm -rf "$SQUASHMATE_DIR"
        echo -e "${GREEN}✅ SquashMate completely removed${NC}"
    else
        echo -e "${BLUE}Files kept in $SQUASHMATE_DIR${NC}"
    fi
fi

echo -e "\n${BLUE}Uninstallation complete! 👋${NC}"