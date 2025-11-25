"""Recall App package for macOS menu bar application."""

from recall.app.bundle import (
    AppConfig,
    DownloadProgressEvent,
    FirstRunSetup,
    ModelInfo,
    ModelManager,
    SetupStep,
    generate_setup_py,
    get_app_version,
    get_bundle_info,
    get_py2app_options,
)
from recall.app.hotkeys import (
    HotkeyConfig,
    HotkeyManager,
    detect_conflicts,
    format_hotkey_display,
    parse_hotkey,
)
from recall.app.installer import (
    AppLauncher,
    DMGBuilder,
    FirstRunWizard,
    InstallerConfig,
    LaunchMode,
    WizardPage,
    generate_build_script,
    generate_dmg_script,
    generate_install_docs,
    generate_permissions_docs,
    get_installer_version,
    get_minimum_macos_version,
)
from recall.app.menubar import (
    AppState,
    MenuItem,
    RecallMenuBar,
)
from recall.app.notifications import (
    AutoRecordingConfig,
    AutoRecordingTrigger,
    NotificationManager,
)
from recall.app.permissions import (
    PermissionInfo,
    PermissionManager,
    PermissionStatus,
    PermissionType,
    get_permission_instructions,
    get_preferences_url,
)
from recall.app.recording import (
    RecordingController,
    RecordingStatus,
)

__all__ = [
    # Menu Bar
    "AppState",
    "MenuItem",
    "RecallMenuBar",
    # Recording
    "RecordingController",
    "RecordingStatus",
    # Notifications
    "NotificationManager",
    "AutoRecordingConfig",
    "AutoRecordingTrigger",
    # Hotkeys
    "HotkeyConfig",
    "HotkeyManager",
    "detect_conflicts",
    "format_hotkey_display",
    "parse_hotkey",
    # Bundle
    "AppConfig",
    "ModelInfo",
    "DownloadProgressEvent",
    "ModelManager",
    "SetupStep",
    "FirstRunSetup",
    "get_app_version",
    "get_bundle_info",
    "get_py2app_options",
    "generate_setup_py",
    # Permissions
    "PermissionType",
    "PermissionStatus",
    "PermissionInfo",
    "PermissionManager",
    "get_permission_instructions",
    "get_preferences_url",
    # Installer
    "InstallerConfig",
    "WizardPage",
    "DMGBuilder",
    "FirstRunWizard",
    "AppLauncher",
    "LaunchMode",
    "generate_build_script",
    "generate_dmg_script",
    "generate_install_docs",
    "generate_permissions_docs",
    "get_installer_version",
    "get_minimum_macos_version",
]
