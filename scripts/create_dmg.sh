#!/bin/bash
# Create DMG installer for Recall
#
# Usage: ./scripts/create_dmg.sh
#
# Prerequisites:
# - Recall.app built in dist/
# - hdiutil (included in macOS)

set -e

echo "=================================================="
echo "Creating Recall DMG Installer"
echo "=================================================="

# Configuration
APP_NAME="Recall"
DMG_NAME="Recall-Installer.dmg"
VOLUME_NAME="Recall Installer"
APP_PATH="dist/${APP_NAME}.app"

# Check app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH not found."
    echo "Run ./scripts/build_app.sh first."
    exit 1
fi

# Clean previous DMG
if [ -f "$DMG_NAME" ]; then
    echo "Removing previous DMG..."
    rm -f "$DMG_NAME"
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy app to temp directory
echo "Copying app..."
cp -R "$APP_PATH" "$TEMP_DIR/"

# Create Applications symlink
ln -s /Applications "$TEMP_DIR/Applications"

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$TEMP_DIR" \
    -ov -format UDBZ \
    "$DMG_NAME"

# Clean up
rm -rf "$TEMP_DIR"

# Show result
if [ -f "$DMG_NAME" ]; then
    echo ""
    echo "=================================================="
    echo "DMG created successfully!"
    echo "=================================================="
    echo ""
    echo "File: $DMG_NAME"
    echo "Size: $(du -h "$DMG_NAME" | cut -f1)"
    echo ""
    echo "To test:"
    echo "  open $DMG_NAME"
    echo ""
    echo "To sign (requires Developer ID):"
    echo "  codesign --sign 'Developer ID Application: Your Name' $DMG_NAME"
else
    echo "Error: DMG creation failed"
    exit 1
fi
