"""Installer and Setup for Recall macOS app.

This module provides:
- DMG installer configuration
- First-run wizard
- App launcher logic
- Documentation generation
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

# Default paths
DEFAULT_CONFIG_DIR = Path.home() / ".recall"


class LaunchMode(Enum):
    """Launch modes for the application."""

    NORMAL = "normal"
    FIRST_RUN_WIZARD = "first_run_wizard"
    MODEL_DOWNLOAD = "model_download"


@dataclass
class InstallerConfig:
    """Configuration for DMG installer."""

    app_name: str = "Recall"
    dmg_name: str = "Recall-Installer.dmg"
    volume_name: str = "Recall Installer"
    background_image: Optional[str] = None
    window_width: int = 600
    window_height: int = 400
    icon_size: int = 128


@dataclass
class WizardPage:
    """A page in the first-run wizard."""

    name: str
    title: str
    description: str
    can_skip: bool = False
    action: Optional[Callable[[], bool]] = None


class DMGBuilder:
    """Builds DMG installer for macOS."""

    def __init__(self, config: Optional[InstallerConfig] = None):
        """Initialize DMG builder.

        Args:
            config: Optional installer configuration.
        """
        self.config = config or InstallerConfig()

    def get_dmg_spec(self) -> dict:
        """Get DMG specification dictionary.

        Returns:
            Dictionary with DMG creation settings.
        """
        return {
            "volume_name": self.config.volume_name,
            "format": "UDBZ",  # Compressed DMG
            "size": "500M",
            "window": {
                "width": self.config.window_width,
                "height": self.config.window_height,
            },
            "icon_size": self.config.icon_size,
            "contents": [
                {"x": 150, "y": 200, "type": "file", "path": "dist/Recall.app"},
                {
                    "x": 450,
                    "y": 200,
                    "type": "link",
                    "path": "/Applications",
                },
            ],
            "symlinks": {"Applications": "/Applications"},
            "background": self.config.background_image,
        }


class FirstRunWizard:
    """First-run setup wizard."""

    DEFAULT_PAGES = [
        WizardPage(
            name="welcome",
            title="Welcome to Recall",
            description="""Welcome to Recall - Your Local AI Note-Taking System!

Recall captures, transcribes, and summarizes audio from:
• Zoom calls and meetings
• YouTube videos
• System audio
• Microphone recordings

All processing happens locally on your Mac. Your data stays private.""",
            can_skip=False,
        ),
        WizardPage(
            name="model_download",
            title="Download AI Models",
            description="""Recall uses local AI models for transcription and summarization.

Required models:
• Whisper Base (~145 MB) - Speech recognition
• Qwen2.5-3B (~2 GB) - Summarization

These will be downloaded to ~/.recall/models/""",
            can_skip=False,
        ),
        WizardPage(
            name="permissions",
            title="Grant Permissions",
            description="""Recall needs some permissions to work:

Required:
• Microphone - Record audio
• Accessibility - Global hotkeys

Optional:
• Screen Recording - Capture system audio""",
            can_skip=False,
        ),
        WizardPage(
            name="complete",
            title="Setup Complete!",
            description="""You're all set! Recall is ready to use.

Quick tips:
• Click the menu bar icon to start recording
• Use ⌘⇧R to toggle recording
• Access preferences with ⌘,

Enjoy using Recall!""",
            can_skip=False,
        ),
    ]

    def __init__(self):
        """Initialize first-run wizard."""
        self._pages = [WizardPage(**p.__dict__) for p in self.DEFAULT_PAGES]

    def get_pages(self) -> list[WizardPage]:
        """Get wizard pages.

        Returns:
            List of WizardPage objects.
        """
        return self._pages


class AppLauncher:
    """Handles app launch logic and first-run detection."""

    SETUP_COMPLETE_FILE = ".setup_complete"
    CONFIG_FILE = "config.json"

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        project_dir: Optional[Path] = None,
    ):
        """Initialize app launcher.

        Args:
            config_dir: Configuration directory path.
            project_dir: Project directory to search for models.
        """
        from recall.app.bundle import ModelManager

        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_file = self.config_dir / self.SETUP_COMPLETE_FILE
        self._config_file = self.config_dir / self.CONFIG_FILE
        self._project_dir = project_dir

        # Load config if exists
        self._config = self._load_config()

        # Initialize model manager with search paths
        search_paths = []
        if self._config.get("models_path"):
            custom_path = Path(self._config["models_path"])
            if custom_path.exists():
                search_paths.append(custom_path)

        self.model_manager = ModelManager(
            search_paths=search_paths if search_paths else None,
            project_dir=project_dir,
        )

    def _load_config(self) -> dict:
        """Load configuration from file.

        Returns:
            Configuration dictionary.
        """
        if self._config_file.exists():
            try:
                return json.loads(self._config_file.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        self._config_file.write_text(json.dumps(self._config, indent=2))

    def is_first_run(self) -> bool:
        """Check if this is the first run.

        Returns:
            True if setup has not been completed.
        """
        return not self._setup_file.exists()

    def mark_first_run_complete(self) -> None:
        """Mark first run as complete."""
        self._setup_file.write_text(json.dumps({"version": "0.1.0", "setup_complete": True}))

    def find_existing_models(self) -> list:
        """Find existing models in search paths.

        Returns:
            List of found ModelInfo objects.
        """
        return self.model_manager.discover_existing_models()

    def get_missing_models(self) -> list:
        """Get list of missing models.

        Returns:
            List of missing ModelInfo objects.
        """
        return self.model_manager.get_missing_models()

    def set_models_path(self, path: Path) -> None:
        """Set custom models path and save to config.

        Args:
            path: Path to models directory.
        """
        self._config["models_path"] = str(path)
        self._save_config()
        self.model_manager.add_search_path(path)

    def get_launch_mode(self) -> LaunchMode:
        """Get the appropriate launch mode.

        Returns:
            LaunchMode indicating how app should start.
        """
        if self.is_first_run():
            return LaunchMode.FIRST_RUN_WIZARD
        return LaunchMode.NORMAL


def get_installer_version() -> str:
    """Get installer version.

    Returns:
        Version string.
    """
    return "0.1.0"


def get_minimum_macos_version() -> str:
    """Get minimum macOS version required.

    Returns:
        Minimum macOS version string.
    """
    return "12.0"


def generate_build_script() -> str:
    """Generate the build script for py2app.

    Returns:
        Shell script content.
    """
    return """#!/bin/bash
# Build Recall.app using py2app
#
# Usage: ./scripts/build_app.sh
#
# Prerequisites:
# - Python 3.11+
# - py2app installed
# - All dependencies installed

set -e

echo "Building Recall.app..."

# Clean previous builds
rm -rf build dist

# Install dependencies
pip install -r requirements.txt
pip install py2app

# Build the app
python setup_app.py py2app

echo "Build complete! App is in dist/Recall.app"
"""


def generate_dmg_script() -> str:
    """Generate the DMG creation script.

    Returns:
        Shell script content.
    """
    return """#!/bin/bash
# Create DMG installer for Recall
#
# Usage: ./scripts/create_dmg.sh
#
# Prerequisites:
# - Recall.app built in dist/
# - create-dmg installed (brew install create-dmg)

set -e

echo "Creating DMG installer..."

# Variables
APP_NAME="Recall"
DMG_NAME="Recall-Installer.dmg"
VOLUME_NAME="Recall Installer"

# Clean previous DMG
rm -f "$DMG_NAME"

# Create DMG using hdiutil
hdiutil create -volname "$VOLUME_NAME" \\
    -srcfolder "dist/$APP_NAME.app" \\
    -ov -format UDBZ \\
    "$DMG_NAME"

echo "DMG created: $DMG_NAME"

# Optionally sign the DMG (requires Apple Developer ID)
# codesign --sign "Developer ID Application: Your Name" "$DMG_NAME"

echo "Done!"
"""


def generate_install_docs() -> str:
    """Generate installation documentation.

    Returns:
        Markdown documentation content.
    """
    return """# Installing Recall

## System Requirements

- **macOS 12.0 (Monterey)** or later
- **Apple Silicon (M1/M2/M3)** or Intel Mac
- **4GB RAM** minimum (8GB recommended)
- **5GB disk space** for app and AI models

## Installation Steps

1. **Download the Installer**
   - Download `Recall-Installer.dmg` from the releases page

2. **Open the DMG**
   - Double-click the downloaded DMG file
   - A new Finder window will open

3. **Install the App**
   - Drag `Recall.app` to the Applications folder
   - Wait for the copy to complete

4. **First Launch**
   - Open Recall from Applications or Spotlight
   - Follow the setup wizard to:
     - Download AI models
     - Grant required permissions

5. **Grant Permissions**
   - Microphone access (required)
   - Accessibility access (for global hotkeys)
   - Screen recording (optional, for system audio)

## Uninstalling

1. Quit Recall if running
2. Drag Recall.app from Applications to Trash
3. Remove data (optional): `rm -rf ~/.recall`

## Troubleshooting

### App won't open
- Right-click and select "Open" to bypass Gatekeeper
- Check System Preferences > Security & Privacy

### Models not downloading
- Check internet connection
- Try manual download from releases page
- Place models in `~/.recall/models/`

### Permissions issues
- Open System Preferences > Security & Privacy
- Find Recall in the list and enable it
- Restart Recall after granting permissions

## Support

For issues and feature requests, visit:
https://github.com/your-username/recall/issues
"""


def generate_permissions_docs() -> str:
    """Generate permissions documentation.

    Returns:
        Markdown documentation content.
    """
    return """# Recall Permissions Guide

Recall requires certain macOS permissions to function properly.

## Required Permissions

### Microphone Access

**Why needed:** Record audio from your microphone for transcription.

**How to grant:**
1. Open System Settings > Privacy & Security > Microphone
2. Find "Recall" in the list
3. Toggle the switch to enable

### Accessibility Access

**Why needed:** Register global keyboard shortcuts that work system-wide.

**How to grant:**
1. Open System Settings > Privacy & Security > Accessibility
2. Click the lock icon to make changes
3. Click "+" and add Recall.app
4. Ensure the checkbox is enabled
5. Restart Recall

## Optional Permissions

### Screen Recording

**Why needed:** Capture system audio (from Zoom, YouTube, etc.)

**Note:** This is only needed if you want to capture audio from other apps. Microphone recording works without this permission.

**How to grant:**
1. Open System Settings > Privacy & Security > Screen Recording
2. Find "Recall" in the list
3. Toggle the switch to enable
4. Restart Recall

## Permission Status

You can check your permission status by:
1. Clicking the Recall menu bar icon
2. Selecting "Preferences"
3. Viewing the "Permissions" tab

## Troubleshooting

### "Recall is not permitted to record"
Grant microphone permission in System Settings.

### Global hotkeys not working
Grant accessibility permission and restart Recall.

### Can't capture Zoom/YouTube audio
Grant screen recording permission and restart Recall.

## Privacy Note

Recall processes all audio locally on your Mac. No data is sent to external servers. Your recordings and transcripts are stored in `~/.recall/` and remain completely private.
"""


# Exports
__all__ = [
    "InstallerConfig",
    "WizardPage",
    "DMGBuilder",
    "FirstRunWizard",
    "AppLauncher",
    "LaunchMode",
    "get_installer_version",
    "get_minimum_macos_version",
    "generate_build_script",
    "generate_dmg_script",
    "generate_install_docs",
    "generate_permissions_docs",
]
