#!/usr/bin/env bash
# Build Linux release artifacts for SquashMate and copy them to website downloads.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$PROJECT_DIR/VERSION"

if [[ ! -f "$VERSION_FILE" ]]; then
  echo "ERROR: VERSION file not found at $VERSION_FILE"
  exit 1
fi

VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
if [[ -z "$VERSION" ]]; then
  echo "ERROR: VERSION is empty. Update $VERSION_FILE first."
  exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "ERROR: dpkg-deb is required (install with: sudo apt install dpkg-dev)"
  exit 1
fi

APP_NAME="squashmate"
DEB_NAME="squashmate_${VERSION}_all.deb"
TAR_NAME="squashmate-${VERSION}-linux.tar.gz"
MANIFEST_NAME="latest.json"

DIST_DIR="$PROJECT_DIR/dist"
BUILD_DIR="$DIST_DIR/.build"
DEB_STAGING="$BUILD_DIR/${APP_NAME}_${VERSION}"
TAR_STAGING="$BUILD_DIR/squashmate-${VERSION}-linux"

WEBSITE_DIR="${WEBSITE_DIR:-/home/alex/Desktop/Projects/squashMate-website}"
WEBSITE_DOWNLOADS_DIR="${WEBSITE_DOWNLOADS_DIR:-$WEBSITE_DIR/public/downloads}"

echo "==> Building SquashMate v${VERSION}"
echo "==> Project dir: $PROJECT_DIR"
echo "==> Website dir: $WEBSITE_DIR"

rm -rf "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR"

###############################################################################
# Build .deb package
###############################################################################

mkdir -p \
  "$DEB_STAGING/DEBIAN" \
  "$DEB_STAGING/opt/squashmate" \
  "$DEB_STAGING/usr/bin" \
  "$DEB_STAGING/usr/share/applications" \
  "$DEB_STAGING/usr/share/icons/hicolor/512x512/apps"

cat > "$DEB_STAGING/DEBIAN/control" <<EOF
Package: squashmate
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Maintainer: SquashMate Team <squashmate@local>
Depends: python3, python3-pyqt5, policykit-1
Description: SquashMate AppImage and .deb manager
 A desktop utility that installs, updates, and manages AppImages and .deb packages.
EOF

cat > "$DEB_STAGING/DEBIAN/postinst" <<'EOF'
#!/usr/bin/env bash
set -e

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -t -f /usr/share/icons/hicolor || true
fi
EOF
chmod 755 "$DEB_STAGING/DEBIAN/postinst"

cat > "$DEB_STAGING/DEBIAN/prerm" <<'EOF'
#!/usr/bin/env bash
set -e

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -t -f /usr/share/icons/hicolor || true
fi
EOF
chmod 755 "$DEB_STAGING/DEBIAN/prerm"

install -m 755 "$PROJECT_DIR/launch.sh" "$DEB_STAGING/opt/squashmate/launch.sh"
install -m 755 "$PROJECT_DIR/squashmate.py" "$DEB_STAGING/opt/squashmate/squashmate.py"
install -m 755 "$PROJECT_DIR/squashmate_launcher.py" "$DEB_STAGING/opt/squashmate/squashmate_launcher.py"
install -m 755 "$PROJECT_DIR/install_squashmate.sh" "$DEB_STAGING/opt/squashmate/install_squashmate.sh"
install -m 755 "$PROJECT_DIR/uninstall_squashmate.sh" "$DEB_STAGING/opt/squashmate/uninstall_squashmate.sh"
install -m 644 "$PROJECT_DIR/README.md" "$DEB_STAGING/opt/squashmate/README.md"
install -m 644 "$PROJECT_DIR/requirements.txt" "$DEB_STAGING/opt/squashmate/requirements.txt"
install -m 644 "$PROJECT_DIR/VERSION" "$DEB_STAGING/opt/squashmate/VERSION"
install -m 644 "$PROJECT_DIR/squashmate_icon.png" "$DEB_STAGING/opt/squashmate/squashmate_icon.png"
install -m 644 "$PROJECT_DIR/squashmate_icon.png" "$DEB_STAGING/usr/share/icons/hicolor/512x512/apps/squashmate.png"

cat > "$DEB_STAGING/usr/share/applications/SquashMate.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Name=SquashMate
GenericName=AppImage & .deb Manager
Comment=Install, manage, and launch AppImages and .deb packages
Exec=squashmate
Icon=squashmate
Type=Application
Categories=System;PackageManager;Utility;
Terminal=false
StartupNotify=true
StartupWMClass=SquashMate
Keywords=AppImage;Install;Package;Manager;Deb;
MimeType=application/x-appimage;application/vnd.debian.binary-package;
EOF
chmod 644 "$DEB_STAGING/usr/share/applications/SquashMate.desktop"

cat > "$DEB_STAGING/usr/bin/squashmate" <<'EOF'
#!/usr/bin/env bash
exec /opt/squashmate/launch.sh "$@"
EOF
chmod 755 "$DEB_STAGING/usr/bin/squashmate"

dpkg-deb --build --root-owner-group "$DEB_STAGING" "$DIST_DIR/$DEB_NAME"
echo "✓ Built $DIST_DIR/$DEB_NAME"

###############################################################################
# Build tar.gz portable bundle
###############################################################################

mkdir -p "$TAR_STAGING"
install -m 755 "$PROJECT_DIR/launch.sh" "$TAR_STAGING/launch.sh"
install -m 755 "$PROJECT_DIR/squashmate.py" "$TAR_STAGING/squashmate.py"
install -m 755 "$PROJECT_DIR/squashmate_launcher.py" "$TAR_STAGING/squashmate_launcher.py"
install -m 755 "$PROJECT_DIR/install_squashmate.sh" "$TAR_STAGING/install_squashmate.sh"
install -m 755 "$PROJECT_DIR/uninstall_squashmate.sh" "$TAR_STAGING/uninstall_squashmate.sh"
install -m 644 "$PROJECT_DIR/README.md" "$TAR_STAGING/README.md"
install -m 644 "$PROJECT_DIR/requirements.txt" "$TAR_STAGING/requirements.txt"
install -m 644 "$PROJECT_DIR/VERSION" "$TAR_STAGING/VERSION"
install -m 644 "$PROJECT_DIR/squashmate_icon.png" "$TAR_STAGING/squashmate_icon.png"
cp "$PROJECT_DIR/SquashMate.desktop" "$TAR_STAGING/SquashMate.desktop"

tar -C "$BUILD_DIR" -czf "$DIST_DIR/$TAR_NAME" "squashmate-${VERSION}-linux"
echo "✓ Built $DIST_DIR/$TAR_NAME"

###############################################################################
# Build manifest
###############################################################################

DEB_SHA256=""
if command -v sha256sum >/dev/null 2>&1; then
  DEB_SHA256="$(sha256sum "$DIST_DIR/$DEB_NAME" | awk '{print $1}')"
fi

cat > "$DIST_DIR/$MANIFEST_NAME" <<EOF
{
  "app": "SquashMate",
  "version": "${VERSION}",
  "generatedAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "artifacts": {
    "deb": {
      "file": "${DEB_NAME}",
      "path": "/downloads/${DEB_NAME}",
      "sha256": "${DEB_SHA256}"
    }
  }
}
EOF
echo "✓ Built $DIST_DIR/$MANIFEST_NAME"

###############################################################################
# Copy artifacts to website
###############################################################################

if [[ -d "$WEBSITE_DIR" ]]; then
  mkdir -p "$WEBSITE_DOWNLOADS_DIR"
  # Website only ships the installable .deb + latest.json manifest
  rm -f "$WEBSITE_DOWNLOADS_DIR"/*.tar.gz 2>/dev/null || true
  cp "$DIST_DIR/$DEB_NAME" "$WEBSITE_DOWNLOADS_DIR/"
  cp "$DIST_DIR/$MANIFEST_NAME" "$WEBSITE_DOWNLOADS_DIR/"
  echo "✓ Copied artifacts to $WEBSITE_DOWNLOADS_DIR"
else
  echo "⚠ Website directory not found: $WEBSITE_DIR"
  echo "  Artifacts are still available in: $DIST_DIR"
fi

echo
echo "Release artifacts ready:"
echo "  - $DIST_DIR/$DEB_NAME"
echo "  - $DIST_DIR/$TAR_NAME"
echo "  - $DIST_DIR/$MANIFEST_NAME"
