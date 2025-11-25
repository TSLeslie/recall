"""Tests for Ticket 8.2: macOS Permissions Handling.

This module tests:
- Microphone permission checking and requesting
- Accessibility permission for global hotkeys
- Screen recording permission for system audio
- Permission status tracking
"""

from unittest.mock import patch

# ============================================================================
# Test: PermissionType Enum
# ============================================================================


class TestPermissionType:
    """Tests for PermissionType enumeration."""

    def test_permission_types_exist(self):
        """Test that all required permission types are defined."""
        from recall.app.permissions import PermissionType

        assert hasattr(PermissionType, "MICROPHONE")
        assert hasattr(PermissionType, "ACCESSIBILITY")
        assert hasattr(PermissionType, "SCREEN_RECORDING")

    def test_permission_type_values(self):
        """Test permission type values are strings."""
        from recall.app.permissions import PermissionType

        assert PermissionType.MICROPHONE.value == "microphone"
        assert PermissionType.ACCESSIBILITY.value == "accessibility"
        assert PermissionType.SCREEN_RECORDING.value == "screen_recording"


# ============================================================================
# Test: PermissionStatus
# ============================================================================


class TestPermissionStatus:
    """Tests for PermissionStatus enumeration."""

    def test_permission_status_values(self):
        """Test permission status values."""
        from recall.app.permissions import PermissionStatus

        assert hasattr(PermissionStatus, "GRANTED")
        assert hasattr(PermissionStatus, "DENIED")
        assert hasattr(PermissionStatus, "NOT_DETERMINED")
        assert hasattr(PermissionStatus, "RESTRICTED")


# ============================================================================
# Test: PermissionInfo
# ============================================================================


class TestPermissionInfo:
    """Tests for PermissionInfo dataclass."""

    def test_permission_info_structure(self):
        """Test PermissionInfo dataclass structure."""
        from recall.app.permissions import PermissionInfo, PermissionStatus, PermissionType

        info = PermissionInfo(
            permission_type=PermissionType.MICROPHONE,
            status=PermissionStatus.GRANTED,
            description="Microphone access for audio recording",
            required=True,
        )

        assert info.permission_type == PermissionType.MICROPHONE
        assert info.status == PermissionStatus.GRANTED
        assert info.required is True

    def test_permission_info_optional_fields(self):
        """Test PermissionInfo optional fields."""
        from recall.app.permissions import PermissionInfo, PermissionStatus, PermissionType

        info = PermissionInfo(
            permission_type=PermissionType.ACCESSIBILITY,
            status=PermissionStatus.NOT_DETERMINED,
            description="Test",
            required=True,
            instructions="Go to System Preferences...",
        )

        assert info.instructions == "Go to System Preferences..."


# ============================================================================
# Test: PermissionManager
# ============================================================================


class TestPermissionManager:
    """Tests for PermissionManager class."""

    def test_permission_manager_init(self):
        """Test PermissionManager initialization."""
        from recall.app.permissions import PermissionManager

        manager = PermissionManager()

        assert manager is not None

    def test_get_all_permissions(self):
        """Test getting all required permissions."""
        from recall.app.permissions import PermissionManager

        manager = PermissionManager()
        permissions = manager.get_all_permissions()

        assert len(permissions) >= 3
        perm_types = [p.permission_type.value for p in permissions]
        assert "microphone" in perm_types
        assert "accessibility" in perm_types
        assert "screen_recording" in perm_types

    def test_check_microphone_permission_on_non_macos(self):
        """Test microphone permission check returns NOT_DETERMINED on non-macOS."""
        from recall.app.permissions import PermissionManager, PermissionStatus, PermissionType

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()
            status = manager.check_permission(PermissionType.MICROPHONE)

            # On non-macOS, should return NOT_DETERMINED
            assert status == PermissionStatus.NOT_DETERMINED

    def test_check_accessibility_permission_on_non_macos(self):
        """Test accessibility permission check on non-macOS."""
        from recall.app.permissions import PermissionManager, PermissionStatus, PermissionType

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()
            status = manager.check_permission(PermissionType.ACCESSIBILITY)

            assert status == PermissionStatus.NOT_DETERMINED

    def test_check_screen_recording_permission_on_non_macos(self):
        """Test screen recording permission check on non-macOS."""
        from recall.app.permissions import PermissionManager, PermissionStatus, PermissionType

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()
            status = manager.check_permission(PermissionType.SCREEN_RECORDING)

            assert status == PermissionStatus.NOT_DETERMINED

    def test_get_missing_permissions(self):
        """Test getting missing required permissions."""
        from recall.app.permissions import PermissionManager, PermissionStatus

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()
            missing = manager.get_missing_permissions()

            # On non-macOS all permissions are NOT_DETERMINED
            assert len(missing) >= 2  # At least microphone and accessibility

    def test_all_permissions_granted(self):
        """Test checking if all required permissions are granted."""
        from recall.app.permissions import PermissionManager

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()

            # On non-macOS, not all permissions granted
            assert manager.all_permissions_granted() is False


# ============================================================================
# Test: Permission Request
# ============================================================================


class TestPermissionRequest:
    """Tests for permission request functionality."""

    def test_request_microphone_permission(self):
        """Test requesting microphone permission."""
        from recall.app.permissions import PermissionManager, PermissionType

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()

            # Should not raise on non-macOS
            result = manager.request_permission(PermissionType.MICROPHONE)
            assert result is not None

    def test_open_system_preferences_accessibility(self):
        """Test opening System Preferences for accessibility."""
        from recall.app.permissions import PermissionManager, PermissionType

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()

            # Should return False on non-macOS (can't open preferences)
            result = manager.open_system_preferences(PermissionType.ACCESSIBILITY)
            assert result is False

    def test_open_system_preferences_microphone(self):
        """Test opening System Preferences for microphone."""
        from recall.app.permissions import PermissionManager, PermissionType

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()

            result = manager.open_system_preferences(PermissionType.MICROPHONE)
            assert result is False


# ============================================================================
# Test: Permission Instructions
# ============================================================================


class TestPermissionInstructions:
    """Tests for permission instruction text."""

    def test_get_microphone_instructions(self):
        """Test getting microphone permission instructions."""
        from recall.app.permissions import PermissionType, get_permission_instructions

        instructions = get_permission_instructions(PermissionType.MICROPHONE)

        assert "microphone" in instructions.lower()
        assert "system" in instructions.lower() or "settings" in instructions.lower()

    def test_get_accessibility_instructions(self):
        """Test getting accessibility permission instructions."""
        from recall.app.permissions import PermissionType, get_permission_instructions

        instructions = get_permission_instructions(PermissionType.ACCESSIBILITY)

        assert "accessibility" in instructions.lower()

    def test_get_screen_recording_instructions(self):
        """Test getting screen recording permission instructions."""
        from recall.app.permissions import PermissionType, get_permission_instructions

        instructions = get_permission_instructions(PermissionType.SCREEN_RECORDING)

        assert "screen" in instructions.lower() or "recording" in instructions.lower()


# ============================================================================
# Test: Permission URL Schemes
# ============================================================================


class TestPermissionURLSchemes:
    """Tests for System Preferences URL schemes."""

    def test_get_preferences_url_microphone(self):
        """Test getting preferences URL for microphone."""
        from recall.app.permissions import PermissionType, get_preferences_url

        url = get_preferences_url(PermissionType.MICROPHONE)

        assert "x-apple.systempreferences" in url or "privacy" in url.lower()

    def test_get_preferences_url_accessibility(self):
        """Test getting preferences URL for accessibility."""
        from recall.app.permissions import PermissionType, get_preferences_url

        url = get_preferences_url(PermissionType.ACCESSIBILITY)

        assert "accessibility" in url.lower()

    def test_get_preferences_url_screen_recording(self):
        """Test getting preferences URL for screen recording."""
        from recall.app.permissions import PermissionType, get_preferences_url

        url = get_preferences_url(PermissionType.SCREEN_RECORDING)

        assert "screenrecording" in url.lower() or "screen" in url.lower()


# ============================================================================
# Test: Permission Callback
# ============================================================================


class TestPermissionCallback:
    """Tests for permission change callbacks."""

    def test_add_permission_callback(self):
        """Test adding a callback for permission changes."""
        from recall.app.permissions import PermissionManager, PermissionType

        manager = PermissionManager()
        callback_called = []

        def on_change(perm_type, status):
            callback_called.append((perm_type, status))

        manager.add_callback(on_change)

        assert len(manager._callbacks) == 1

    def test_remove_permission_callback(self):
        """Test removing a callback."""
        from recall.app.permissions import PermissionManager

        manager = PermissionManager()

        def on_change(perm_type, status):
            pass

        manager.add_callback(on_change)
        manager.remove_callback(on_change)

        assert len(manager._callbacks) == 0


# ============================================================================
# Test: Permission Summary
# ============================================================================


class TestPermissionSummary:
    """Tests for permission summary functionality."""

    def test_get_permission_summary(self):
        """Test getting a summary of all permissions."""
        from recall.app.permissions import PermissionManager

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()
            summary = manager.get_permission_summary()

            assert "microphone" in summary.lower()
            assert "accessibility" in summary.lower()

    def test_permission_summary_format(self):
        """Test permission summary format."""
        from recall.app.permissions import PermissionManager

        with patch("recall.app.permissions.MACOS_AVAILABLE", False):
            manager = PermissionManager()
            summary = manager.get_permission_summary()

            # Should be a multi-line string or dict
            assert len(summary) > 50  # Reasonable length


# ============================================================================
# Test: Required vs Optional Permissions
# ============================================================================


class TestRequiredPermissions:
    """Tests for required vs optional permission handling."""

    def test_microphone_is_required(self):
        """Test that microphone permission is required."""
        from recall.app.permissions import PermissionManager, PermissionType

        manager = PermissionManager()
        permissions = manager.get_all_permissions()

        mic_perm = next(p for p in permissions if p.permission_type == PermissionType.MICROPHONE)
        assert mic_perm.required is True

    def test_accessibility_required_for_hotkeys(self):
        """Test that accessibility is required for global hotkeys."""
        from recall.app.permissions import PermissionManager, PermissionType

        manager = PermissionManager()
        permissions = manager.get_all_permissions()

        acc_perm = next(p for p in permissions if p.permission_type == PermissionType.ACCESSIBILITY)
        assert acc_perm.required is True

    def test_screen_recording_optional(self):
        """Test that screen recording is optional (only for system audio)."""
        from recall.app.permissions import PermissionManager, PermissionType

        manager = PermissionManager()
        permissions = manager.get_all_permissions()

        sr_perm = next(
            p for p in permissions if p.permission_type == PermissionType.SCREEN_RECORDING
        )
        # Screen recording is optional - only needed for system audio capture
        assert sr_perm.required is False
