"""macOS Permissions handling for Recall.

This module provides:
- Permission type enumeration
- Permission status checking
- Permission request handling
- System Preferences integration
"""

import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable

# Check if running on macOS
MACOS_AVAILABLE = platform.system() == "Darwin"

# Try to import macOS-specific modules
if MACOS_AVAILABLE:
    try:
        import AVFoundation  # type: ignore  # noqa: F401

        AVFOUNDATION_AVAILABLE = True
    except ImportError:
        AVFOUNDATION_AVAILABLE = False
else:
    AVFOUNDATION_AVAILABLE = False


class PermissionType(Enum):
    """Types of permissions required by Recall."""

    MICROPHONE = "microphone"
    ACCESSIBILITY = "accessibility"
    SCREEN_RECORDING = "screen_recording"


class PermissionStatus(Enum):
    """Status of a permission."""

    GRANTED = "granted"
    DENIED = "denied"
    NOT_DETERMINED = "not_determined"
    RESTRICTED = "restricted"


@dataclass
class PermissionInfo:
    """Information about a permission."""

    permission_type: PermissionType
    status: PermissionStatus
    description: str
    required: bool
    instructions: str = ""


# System Preferences URL schemes for each permission
PREFERENCE_URLS = {
    PermissionType.MICROPHONE: "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone",
    PermissionType.ACCESSIBILITY: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
    PermissionType.SCREEN_RECORDING: "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
}

# Instructions for each permission type
PERMISSION_INSTRUCTIONS = {
    PermissionType.MICROPHONE: """To grant microphone access:
1. Open System Settings > Privacy & Security > Microphone
2. Find "Recall" in the list
3. Toggle the switch to enable microphone access
4. Restart Recall if needed""",
    PermissionType.ACCESSIBILITY: """To grant accessibility access:
1. Open System Settings > Privacy & Security > Accessibility
2. Click the '+' button to add an application
3. Navigate to Recall.app and add it
4. Toggle the switch to enable accessibility access
5. Restart Recall for changes to take effect""",
    PermissionType.SCREEN_RECORDING: """To grant screen recording access:
1. Open System Settings > Privacy & Security > Screen Recording
2. Find "Recall" in the list
3. Toggle the switch to enable screen recording
4. Restart Recall for changes to take effect

Note: Screen recording is only needed for capturing system audio.""",
}


def get_permission_instructions(permission_type: PermissionType) -> str:
    """Get instructions for granting a permission.

    Args:
        permission_type: Type of permission.

    Returns:
        Human-readable instructions for granting the permission.
    """
    return PERMISSION_INSTRUCTIONS.get(
        permission_type,
        f"Please grant {permission_type.value} permission in System Settings.",
    )


def get_preferences_url(permission_type: PermissionType) -> str:
    """Get the System Preferences URL for a permission.

    Args:
        permission_type: Type of permission.

    Returns:
        URL scheme to open the relevant System Preferences pane.
    """
    return PREFERENCE_URLS.get(
        permission_type,
        "x-apple.systempreferences:com.apple.preference.security?Privacy",
    )


class PermissionManager:
    """Manages macOS permissions for Recall."""

    # Permission definitions
    PERMISSIONS = [
        PermissionInfo(
            permission_type=PermissionType.MICROPHONE,
            status=PermissionStatus.NOT_DETERMINED,
            description="Microphone access for audio recording",
            required=True,
            instructions=PERMISSION_INSTRUCTIONS[PermissionType.MICROPHONE],
        ),
        PermissionInfo(
            permission_type=PermissionType.ACCESSIBILITY,
            status=PermissionStatus.NOT_DETERMINED,
            description="Accessibility access for global hotkeys",
            required=True,
            instructions=PERMISSION_INSTRUCTIONS[PermissionType.ACCESSIBILITY],
        ),
        PermissionInfo(
            permission_type=PermissionType.SCREEN_RECORDING,
            status=PermissionStatus.NOT_DETERMINED,
            description="Screen recording access for system audio capture",
            required=False,  # Only needed for system audio
            instructions=PERMISSION_INSTRUCTIONS[PermissionType.SCREEN_RECORDING],
        ),
    ]

    def __init__(self):
        """Initialize permission manager."""
        self._callbacks: list[Callable[[PermissionType, PermissionStatus], None]] = []
        self._cached_status: dict[PermissionType, PermissionStatus] = {}

    def get_all_permissions(self) -> list[PermissionInfo]:
        """Get all permission info with current status.

        Returns:
            List of PermissionInfo with current status.
        """
        permissions = []
        for perm in self.PERMISSIONS:
            status = self.check_permission(perm.permission_type)
            permissions.append(
                PermissionInfo(
                    permission_type=perm.permission_type,
                    status=status,
                    description=perm.description,
                    required=perm.required,
                    instructions=perm.instructions,
                )
            )
        return permissions

    def check_permission(self, permission_type: PermissionType) -> PermissionStatus:
        """Check the status of a permission.

        Args:
            permission_type: Type of permission to check.

        Returns:
            Current status of the permission.
        """
        if not MACOS_AVAILABLE:
            return PermissionStatus.NOT_DETERMINED

        if permission_type == PermissionType.MICROPHONE:
            return self._check_microphone_permission()
        elif permission_type == PermissionType.ACCESSIBILITY:
            return self._check_accessibility_permission()
        elif permission_type == PermissionType.SCREEN_RECORDING:
            return self._check_screen_recording_permission()

        return PermissionStatus.NOT_DETERMINED

    def _check_microphone_permission(self) -> PermissionStatus:
        """Check microphone permission on macOS.

        Returns:
            Permission status.
        """
        if not AVFOUNDATION_AVAILABLE:
            return PermissionStatus.NOT_DETERMINED

        try:
            import AVFoundation  # type: ignore

            auth_status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
                AVFoundation.AVMediaTypeAudio
            )

            # Map AVFoundation status to our enum
            status_map = {
                0: PermissionStatus.NOT_DETERMINED,  # AVAuthorizationStatusNotDetermined
                1: PermissionStatus.RESTRICTED,  # AVAuthorizationStatusRestricted
                2: PermissionStatus.DENIED,  # AVAuthorizationStatusDenied
                3: PermissionStatus.GRANTED,  # AVAuthorizationStatusAuthorized
            }
            return status_map.get(auth_status, PermissionStatus.NOT_DETERMINED)
        except Exception:
            return PermissionStatus.NOT_DETERMINED

    def _check_accessibility_permission(self) -> PermissionStatus:
        """Check accessibility permission on macOS.

        Returns:
            Permission status.
        """
        try:
            import Quartz  # type: ignore

            # Check if we have accessibility permissions
            trusted = Quartz.AXIsProcessTrustedWithOptions(
                {Quartz.kAXTrustedCheckOptionPrompt: False}
            )
            return PermissionStatus.GRANTED if trusted else PermissionStatus.DENIED
        except Exception:
            return PermissionStatus.NOT_DETERMINED

    def _check_screen_recording_permission(self) -> PermissionStatus:
        """Check screen recording permission on macOS.

        Returns:
            Permission status.
        """
        try:
            import Quartz  # type: ignore

            # Try to capture a small region - this will fail if no permission
            display_id = Quartz.CGMainDisplayID()
            image = Quartz.CGDisplayCreateImage(display_id)
            if image is not None:
                return PermissionStatus.GRANTED
            return PermissionStatus.DENIED
        except Exception:
            return PermissionStatus.NOT_DETERMINED

    def request_permission(self, permission_type: PermissionType) -> PermissionStatus:
        """Request a permission from the user.

        Args:
            permission_type: Type of permission to request.

        Returns:
            New status of the permission.
        """
        if not MACOS_AVAILABLE:
            return PermissionStatus.NOT_DETERMINED

        if permission_type == PermissionType.MICROPHONE:
            return self._request_microphone_permission()
        elif permission_type == PermissionType.ACCESSIBILITY:
            return self._request_accessibility_permission()
        elif permission_type == PermissionType.SCREEN_RECORDING:
            # Screen recording doesn't have a direct request API
            self.open_system_preferences(permission_type)
            return PermissionStatus.NOT_DETERMINED

        return PermissionStatus.NOT_DETERMINED

    def _request_microphone_permission(self) -> PermissionStatus:
        """Request microphone permission.

        Returns:
            New permission status.
        """
        if not AVFOUNDATION_AVAILABLE:
            return PermissionStatus.NOT_DETERMINED

        try:
            import AVFoundation  # type: ignore

            # This will trigger the permission dialog
            result = [PermissionStatus.NOT_DETERMINED]

            def handler(granted: bool) -> None:
                result[0] = PermissionStatus.GRANTED if granted else PermissionStatus.DENIED

            AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                AVFoundation.AVMediaTypeAudio, handler
            )

            return result[0]
        except Exception:
            return PermissionStatus.NOT_DETERMINED

    def _request_accessibility_permission(self) -> PermissionStatus:
        """Request accessibility permission (opens System Preferences).

        Returns:
            Current permission status.
        """
        try:
            import Quartz  # type: ignore

            # This will show a prompt to the user
            Quartz.AXIsProcessTrustedWithOptions({Quartz.kAXTrustedCheckOptionPrompt: True})
            return self._check_accessibility_permission()
        except Exception:
            return PermissionStatus.NOT_DETERMINED

    def open_system_preferences(self, permission_type: PermissionType) -> bool:
        """Open System Preferences to the relevant pane.

        Args:
            permission_type: Type of permission to open preferences for.

        Returns:
            True if successfully opened, False otherwise.
        """
        if not MACOS_AVAILABLE:
            return False

        url = get_preferences_url(permission_type)
        try:
            subprocess.run(["open", url], check=True)
            return True
        except Exception:
            return False

    def get_missing_permissions(self) -> list[PermissionInfo]:
        """Get list of required permissions that are not granted.

        Returns:
            List of missing required permissions.
        """
        missing = []
        for perm in self.get_all_permissions():
            if perm.required and perm.status != PermissionStatus.GRANTED:
                missing.append(perm)
        return missing

    def all_permissions_granted(self) -> bool:
        """Check if all required permissions are granted.

        Returns:
            True if all required permissions are granted.
        """
        return len(self.get_missing_permissions()) == 0

    def add_callback(self, callback: Callable[[PermissionType, PermissionStatus], None]) -> None:
        """Add a callback for permission status changes.

        Args:
            callback: Function to call when permission status changes.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[PermissionType, PermissionStatus], None]) -> None:
        """Remove a callback.

        Args:
            callback: Previously added callback to remove.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, permission_type: PermissionType, status: PermissionStatus) -> None:
        """Notify all callbacks of a permission change.

        Args:
            permission_type: Type of permission that changed.
            status: New status.
        """
        for callback in self._callbacks:
            try:
                callback(permission_type, status)
            except Exception:
                pass  # Don't let callback errors break the manager

    def get_permission_summary(self) -> str:
        """Get a human-readable summary of all permissions.

        Returns:
            Multi-line string summarizing permission status.
        """
        lines = ["Permission Status:"]
        lines.append("-" * 40)

        for perm in self.get_all_permissions():
            status_icon = {
                PermissionStatus.GRANTED: "✓",
                PermissionStatus.DENIED: "✗",
                PermissionStatus.NOT_DETERMINED: "?",
                PermissionStatus.RESTRICTED: "⊘",
            }.get(perm.status, "?")

            required_text = "(required)" if perm.required else "(optional)"
            lines.append(
                f"{status_icon} {perm.permission_type.value}: {perm.status.value} {required_text}"
            )

        lines.append("-" * 40)
        if self.all_permissions_granted():
            lines.append("All required permissions granted.")
        else:
            missing = self.get_missing_permissions()
            lines.append(
                f"Missing {len(missing)} required permission(s): "
                + ", ".join(p.permission_type.value for p in missing)
            )

        return "\n".join(lines)


# Exports
__all__ = [
    "PermissionType",
    "PermissionStatus",
    "PermissionInfo",
    "PermissionManager",
    "get_permission_instructions",
    "get_preferences_url",
    "MACOS_AVAILABLE",
]
