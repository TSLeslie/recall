#!/bin/bash
# Build Recall.app using py2app
#
# Usage: ./scripts/build_app.sh
#
# Prerequisites:
# - Python 3.11+
# - py2app installed
# - All dependencies installed

set -e

echo "=================================================="
echo "Building Recall.app"
echo "=================================================="

# Check we're in the right directory
if [ ! -f "setup_app.py" ]; then
    echo "Error: setup_app.py not found. Run from project root."
    exit 1
fi

# Check for py2app
if ! python -c "import py2app" 2>/dev/null; then
    echo "Installing py2app..."
    pip install py2app
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Create resources directory if needed
mkdir -p resources

# Create placeholder icon if needed
if [ ! -f "resources/recall.icns" ]; then
    echo "Note: No icon file found. Using placeholder."
    touch resources/recall.icns
fi

# Build the app
echo "Building app bundle..."
python setup_app.py py2app

# Check if build succeeded
if [ -d "dist/Recall.app" ]; then
    echo ""
    echo "=================================================="
    echo "Build complete!"
    echo "=================================================="
    echo ""
    echo "App bundle: dist/Recall.app"
    echo ""
    echo "To test:"
    echo "  open dist/Recall.app"
    echo ""
    echo "To create DMG:"
    echo "  ./scripts/create_dmg.sh"
else
    echo "Error: Build failed - dist/Recall.app not found"
    exit 1
fi
