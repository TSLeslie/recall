"""End-to-End Integration Tests for Sprint 6: macOS Menu Bar App.

These tests verify the complete integration of all menu bar components
working together as they would in a real application.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from recall.app.hotkeys import (
    HotkeyConfig,
    HotkeyManager,
    detect_conflicts,
    format_hotkey_display,
)
from recall.app.menubar import AppState, MenuItem, RecallMenuBar
from recall.app.notifications import (
    AutoRecordingConfig,
    AutoRecordingTrigger,
    NotificationManager,
)
from recall.app.recording import RecordingController, RecordingStatus

# ============================================================================
# Test: Complete App Initialization
# ============================================================================


class TestMenuBarAppInitialization:
    """Test that the menu bar app initializes all components correctly."""

    def test_app_initializes_all_components(self):
        """Test that RecallMenuBar creates all required components."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                # Core components
                assert app.name == "Recall"
                assert app.state == AppState.IDLE
                assert app.icon == "🎤"

                # Recording controller
                assert isinstance(app.recording_controller, RecordingController)

                # Notification manager
                assert isinstance(app.notification_manager, NotificationManager)
                assert app.notification_manager.enabled is True

                # Auto-recording config
                assert isinstance(app.auto_recording_config, AutoRecordingConfig)

                # Hotkey manager and config
                assert isinstance(app.hotkey_config, HotkeyConfig)
                assert isinstance(app.hotkey_manager, HotkeyManager)

    def test_app_with_custom_output_dir(self, tmp_path):
        """Test that custom output directory is passed to recording controller."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar(output_dir=tmp_path)

                assert app.recording_controller.output_dir == tmp_path


# ============================================================================
# Test: Recording Workflow E2E
# ============================================================================


class TestRecordingWorkflowE2E:
    """End-to-end tests for the recording workflow."""

    def test_complete_recording_cycle(self):
        """Test complete recording cycle: start -> record -> stop -> process."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder") as mock_recorder:
                # Configure mock
                mock_instance = MagicMock()
                mock_instance.stop_recording.return_value = Path("/tmp/test.wav")
                mock_recorder.return_value = mock_instance

                app = RecallMenuBar()

                # Initial state
                assert app.state == AppState.IDLE
                assert app.is_recording is False
                assert app.recording_duration is None

                # Start recording
                app.on_start_recording(None)
                assert app.state == AppState.RECORDING
                assert app.is_recording is True
                assert app.recording_controller.state == AppState.RECORDING

                # Duration should be tracked
                time.sleep(0.1)
                assert app.recording_duration is not None
                assert app.recording_duration >= 0

                # Stop recording
                app.on_stop_recording(None)
                assert app.state == AppState.PROCESSING
                assert app.is_processing is True

    def test_recording_via_hotkey(self):
        """Test recording via hotkey toggle."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder") as mock_recorder:
                mock_instance = MagicMock()
                mock_instance.stop_recording.return_value = Path("/tmp/test.wav")
                mock_recorder.return_value = mock_instance

                app = RecallMenuBar()

                # Toggle ON via hotkey
                assert app.state == AppState.IDLE
                app.hotkey_manager._handle_toggle_recording()
                assert app.state == AppState.RECORDING

                # Toggle OFF via hotkey
                app.hotkey_manager._handle_toggle_recording()
                assert app.state == AppState.PROCESSING

    def test_menu_items_change_with_state(self):
        """Test that menu items update based on app state."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                # Idle state - should show "Start Recording"
                items = app.get_menu_items()
                recording_item = items[0]
                assert recording_item.title == "Start Recording"
                assert recording_item.enabled is True

                # Recording state - should show "Stop Recording"
                app.set_state(AppState.RECORDING)
                items = app.get_menu_items()
                recording_item = items[0]
                assert recording_item.title == "Stop Recording"

                # Processing state - should show "Processing..." (disabled)
                app.set_state(AppState.PROCESSING)
                items = app.get_menu_items()
                recording_item = items[0]
                assert recording_item.title == "Processing..."
                assert recording_item.enabled is False


# ============================================================================
# Test: Notification Integration E2E
# ============================================================================


class TestNotificationIntegrationE2E:
    """End-to-end tests for notification integration."""

    def test_notification_manager_with_app(self):
        """Test that notification manager is properly integrated."""
        import recall.app.notifications as notifications_module

        # Save and mock rumps
        original_rumps = notifications_module.rumps
        notifications_module.rumps = None

        try:
            with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
                with patch("recall.app.recording.Recorder"):
                    app = RecallMenuBar()

                    # Manager should be ready to send notifications
                    assert app.notification_manager.enabled is True

                    # Test sending via manager (will log since rumps unavailable)
                    app.notification_manager.notify_recording_started("microphone")
                    app.notification_manager.notify_recording_saved("Test", 60)
        finally:
            notifications_module.rumps = original_rumps

    def test_auto_recording_config_defaults(self):
        """Test auto-recording config has sensible defaults."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                config = app.auto_recording_config

                # Should be disabled by default for privacy
                assert config.enabled is False

                # But detection should be ready when enabled
                assert config.detect_meeting_apps is True
                assert config.detect_system_audio is True

                # Common meeting apps should be whitelisted
                assert config.is_app_whitelisted("zoom.us")
                assert config.is_app_whitelisted("Microsoft Teams")


# ============================================================================
# Test: Hotkey Integration E2E
# ============================================================================


class TestHotkeyIntegrationE2E:
    """End-to-end tests for hotkey integration."""

    def test_hotkey_callbacks_connected(self):
        """Test that hotkey callbacks are properly connected to app."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                # Callbacks should be set
                assert app.hotkey_manager.on_toggle_recording is not None
                assert app.hotkey_manager.on_quick_note is not None
                assert app.hotkey_manager.on_voice_note is not None
                assert app.hotkey_manager.on_open_search is not None

    def test_default_hotkey_config(self):
        """Test default hotkey configuration."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                config = app.hotkey_config

                assert config.enabled is True
                assert config.toggle_recording == "<cmd>+<shift>+r"
                assert config.quick_note == "<cmd>+<shift>+n"
                assert config.voice_note == "<cmd>+<shift>+v"
                assert config.open_search == "<cmd>+<shift>+s"

    def test_no_default_hotkey_conflicts(self):
        """Test that default hotkeys have no conflicts."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                conflicts = detect_conflicts(app.hotkey_config)
                assert len(conflicts) == 0

    def test_hotkey_display_formatting(self):
        """Test hotkey display formatting for menu items."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                # Format for display
                display = format_hotkey_display(app.hotkey_config.toggle_recording)
                assert "⌘" in display or "Cmd" in display
                assert "⇧" in display or "Shift" in display
                assert "R" in display


# ============================================================================
# Test: State Transitions E2E
# ============================================================================


class TestStateTransitionsE2E:
    """End-to-end tests for state transitions."""

    def test_icon_updates_with_state(self):
        """Test that icon updates correctly with each state."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                # Idle
                assert app.icon == "🎤"

                # Recording
                app.set_state(AppState.RECORDING)
                assert app.icon == "🔴"

                # Processing
                app.set_state(AppState.PROCESSING)
                assert app.icon == "⚙️"

                # Back to Idle
                app.set_state(AppState.IDLE)
                assert app.icon == "🎤"

    def test_quit_workflow(self):
        """Test quit workflow."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                assert app._quit_requested is False

                app.on_quit(None)

                assert app._quit_requested is True


# ============================================================================
# Test: Component Interaction E2E
# ============================================================================


class TestComponentInteractionE2E:
    """End-to-end tests for component interactions."""

    def test_auto_recording_trigger_setup(self):
        """Test auto-recording trigger can be set up."""
        config = AutoRecordingConfig(enabled=True)
        trigger = AutoRecordingTrigger(config)

        triggered_events = []
        trigger.on_trigger = lambda event: triggered_events.append(event)

        # Simulate meeting app detection
        trigger._on_app_detected("zoom.us")
        assert len(triggered_events) == 1
        assert triggered_events[0]["source"] == "meeting_app"
        assert triggered_events[0]["app_name"] == "zoom.us"

        # Simulate system audio detection
        trigger._on_audio_detected("BlackHole")
        assert len(triggered_events) == 2
        assert triggered_events[1]["source"] == "system_audio"

    def test_auto_recording_respects_whitelist(self):
        """Test that auto-recording respects app whitelist."""
        config = AutoRecordingConfig(enabled=True)
        trigger = AutoRecordingTrigger(config)

        triggered_events = []
        trigger.on_trigger = lambda event: triggered_events.append(event)

        # Whitelisted app should trigger
        trigger._on_app_detected("zoom.us")
        assert len(triggered_events) == 1

        # Non-whitelisted app should not trigger
        trigger._on_app_detected("Safari")
        assert len(triggered_events) == 1  # Still 1

    def test_recording_status_flow(self):
        """Test RecordingStatus through the workflow."""
        with patch("recall.app.recording.Recorder") as mock_recorder:
            mock_instance = MagicMock()
            mock_instance.stop_recording.return_value = Path("/tmp/test.wav")
            mock_recorder.return_value = mock_instance

            controller = RecordingController()

            # Start recording
            status = controller.start_recording()
            assert status.state == AppState.RECORDING
            assert status.message == "Recording started"
            assert status.error is None

            # Stop recording
            status = controller.stop_recording()
            assert status.state == AppState.PROCESSING
            assert status.audio_path == Path("/tmp/test.wav")


# ============================================================================
# Test: Full User Scenario
# ============================================================================


class TestFullUserScenario:
    """Test complete user scenarios end-to-end."""

    def test_user_records_meeting_scenario(self):
        """Simulate a user recording a meeting from start to finish."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder") as mock_recorder:
                mock_instance = MagicMock()
                mock_instance.stop_recording.return_value = Path("/tmp/meeting_2025-11-25.wav")
                mock_recorder.return_value = mock_instance

                # 1. User launches app
                app = RecallMenuBar()
                assert app.state == AppState.IDLE

                # 2. User checks menu - sees "Start Recording"
                items = app.get_menu_items()
                assert any(item.title == "Start Recording" for item in items)

                # 3. User presses Cmd+Shift+R to start recording
                app.hotkey_manager._handle_toggle_recording()
                assert app.state == AppState.RECORDING
                assert app.icon == "🔴"

                # 4. User checks menu - sees "Stop Recording"
                items = app.get_menu_items()
                assert any(item.title == "Stop Recording" for item in items)

                # 5. Recording happens for a while
                time.sleep(0.1)
                duration = app.recording_duration
                assert duration is not None
                assert duration > 0

                # 6. User presses Cmd+Shift+R to stop
                app.hotkey_manager._handle_toggle_recording()
                assert app.state == AppState.PROCESSING
                assert app.icon == "⚙️"

                # 7. Menu shows "Processing..." (disabled)
                items = app.get_menu_items()
                processing_item = next(item for item in items if item.title == "Processing...")
                assert processing_item.enabled is False

    def test_user_configures_auto_recording(self):
        """Simulate user configuring auto-recording settings."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                # 1. Check default - auto-recording is off
                assert app.auto_recording_config.enabled is False

                # 2. User enables auto-recording
                app.auto_recording_config.enabled = True

                # 3. User adds a custom app to whitelist
                app.auto_recording_config.add_to_whitelist("Discord")
                assert app.auto_recording_config.is_app_whitelisted("Discord")

                # 4. User removes an app from whitelist
                app.auto_recording_config.remove_from_whitelist("Skype")
                assert not app.auto_recording_config.is_app_whitelisted("Skype")

                # 5. Configuration can be exported for saving
                config_dict = app.auto_recording_config.to_dict()
                assert config_dict["enabled"] is True
                assert "Discord" in config_dict["app_whitelist"]
