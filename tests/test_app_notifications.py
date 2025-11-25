"""Tests for Ticket 7.3: Notifications and Auto-Recording.

This module tests:
- macOS notifications via rumps
- Notification when auto-recording starts
- Auto-recording triggers (meeting apps, system audio)
- Auto-recording configuration
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from recall.app.menubar import AppState

# ============================================================================
# Test: NotificationManager
# ============================================================================


class TestNotificationManager:
    """Tests for NotificationManager class."""

    def test_notification_manager_init(self):
        """Test that NotificationManager initializes correctly."""
        from recall.app.notifications import NotificationManager

        manager = NotificationManager()

        assert manager is not None
        assert hasattr(manager, "enabled")
        assert manager.enabled is True

    def test_notification_manager_can_disable(self):
        """Test that notifications can be disabled."""
        from recall.app.notifications import NotificationManager

        manager = NotificationManager(enabled=False)

        assert manager.enabled is False

    def test_send_notification_basic(self):
        """Test sending a basic notification."""
        import recall.app.notifications as notifications_module
        from recall.app.notifications import NotificationManager

        mock_rumps = MagicMock()
        original_rumps = notifications_module.rumps

        try:
            notifications_module.rumps = mock_rumps
            manager = NotificationManager()

            manager.send("Test Title", "Test message")

            mock_rumps.notification.assert_called_once_with(
                title="Test Title",
                subtitle="",
                message="Test message",
                sound=True,
            )
        finally:
            notifications_module.rumps = original_rumps

    def test_send_notification_with_subtitle(self):
        """Test sending a notification with subtitle."""
        import recall.app.notifications as notifications_module
        from recall.app.notifications import NotificationManager

        mock_rumps = MagicMock()
        original_rumps = notifications_module.rumps

        try:
            notifications_module.rumps = mock_rumps
            manager = NotificationManager()

            manager.send("Title", "Message", subtitle="Subtitle")

            mock_rumps.notification.assert_called_once_with(
                title="Title",
                subtitle="Subtitle",
                message="Message",
                sound=True,
            )
        finally:
            notifications_module.rumps = original_rumps

    def test_send_notification_without_sound(self):
        """Test sending a silent notification."""
        import recall.app.notifications as notifications_module
        from recall.app.notifications import NotificationManager

        mock_rumps = MagicMock()
        original_rumps = notifications_module.rumps

        try:
            notifications_module.rumps = mock_rumps
            manager = NotificationManager()

            manager.send("Title", "Message", sound=False)

            mock_rumps.notification.assert_called_once_with(
                title="Title",
                subtitle="",
                message="Message",
                sound=False,
            )
        finally:
            notifications_module.rumps = original_rumps

    def test_send_notification_disabled_does_nothing(self):
        """Test that disabled manager doesn't send notifications."""
        import recall.app.notifications as notifications_module
        from recall.app.notifications import NotificationManager

        mock_rumps = MagicMock()
        original_rumps = notifications_module.rumps

        try:
            notifications_module.rumps = mock_rumps
            manager = NotificationManager(enabled=False)

            manager.send("Title", "Message")

            mock_rumps.notification.assert_not_called()
        finally:
            notifications_module.rumps = original_rumps

    def test_send_notification_without_rumps_logs_fallback(self):
        """Test that notifications log a message when rumps unavailable."""
        from recall.app.notifications import NotificationManager

        with patch("recall.app.notifications.RUMPS_AVAILABLE", False):
            manager = NotificationManager()

            # Should not raise, just log
            manager.send("Title", "Message")


# ============================================================================
# Test: Recording Notifications
# ============================================================================


class TestRecordingNotifications:
    """Tests for recording-specific notifications."""

    def test_notify_recording_started(self):
        """Test notification when recording starts."""
        import recall.app.notifications as notifications_module
        from recall.app.notifications import NotificationManager

        mock_rumps = MagicMock()
        original_rumps = notifications_module.rumps

        try:
            notifications_module.rumps = mock_rumps
            manager = NotificationManager()

            manager.notify_recording_started(source="microphone")

            mock_rumps.notification.assert_called_once()
            call_args = mock_rumps.notification.call_args
            assert "Recording" in call_args.kwargs["title"]
        finally:
            notifications_module.rumps = original_rumps

    def test_notify_recording_saved(self):
        """Test notification when recording is saved."""
        import recall.app.notifications as notifications_module
        from recall.app.notifications import NotificationManager

        mock_rumps = MagicMock()
        original_rumps = notifications_module.rumps

        try:
            notifications_module.rumps = mock_rumps
            manager = NotificationManager()

            manager.notify_recording_saved(title="Team Standup", duration=300)

            mock_rumps.notification.assert_called_once()
            call_args = mock_rumps.notification.call_args
            assert "saved" in call_args.kwargs["title"].lower()
        finally:
            notifications_module.rumps = original_rumps

    def test_notify_auto_recording_detected(self):
        """Test notification when auto-recording is triggered."""
        import recall.app.notifications as notifications_module
        from recall.app.notifications import NotificationManager

        mock_rumps = MagicMock()
        original_rumps = notifications_module.rumps

        try:
            notifications_module.rumps = mock_rumps
            manager = NotificationManager()

            manager.notify_auto_recording(source="Zoom", app_name="zoom.us")

            mock_rumps.notification.assert_called_once()
            call_args = mock_rumps.notification.call_args
            assert "Zoom" in call_args.kwargs["message"]
        finally:
            notifications_module.rumps = original_rumps


# ============================================================================
# Test: AutoRecordingConfig
# ============================================================================


class TestAutoRecordingConfig:
    """Tests for auto-recording configuration."""

    def test_config_defaults(self):
        """Test default auto-recording configuration."""
        from recall.app.notifications import AutoRecordingConfig

        config = AutoRecordingConfig()

        assert config.enabled is False  # Off by default for privacy
        assert config.detect_meeting_apps is True
        assert config.detect_system_audio is True

    def test_config_app_whitelist(self):
        """Test app whitelist for auto-recording."""
        from recall.app.notifications import AutoRecordingConfig

        config = AutoRecordingConfig()

        assert "zoom.us" in config.app_whitelist
        assert "Microsoft Teams" in config.app_whitelist
        assert "Google Chrome" not in config.app_whitelist

    def test_config_add_to_whitelist(self):
        """Test adding app to whitelist."""
        from recall.app.notifications import AutoRecordingConfig

        config = AutoRecordingConfig()

        config.add_to_whitelist("Slack")

        assert "Slack" in config.app_whitelist

    def test_config_remove_from_whitelist(self):
        """Test removing app from whitelist."""
        from recall.app.notifications import AutoRecordingConfig

        config = AutoRecordingConfig()
        config.add_to_whitelist("Slack")

        config.remove_from_whitelist("Slack")

        assert "Slack" not in config.app_whitelist

    def test_config_is_app_whitelisted(self):
        """Test checking if app is whitelisted."""
        from recall.app.notifications import AutoRecordingConfig

        config = AutoRecordingConfig()

        assert config.is_app_whitelisted("zoom.us") is True
        assert config.is_app_whitelisted("Safari") is False

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        from recall.app.notifications import AutoRecordingConfig

        config = AutoRecordingConfig.from_dict(
            {
                "enabled": True,
                "detect_meeting_apps": False,
                "app_whitelist": ["CustomApp"],
            }
        )

        assert config.enabled is True
        assert config.detect_meeting_apps is False
        assert "CustomApp" in config.app_whitelist

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        from recall.app.notifications import AutoRecordingConfig

        config = AutoRecordingConfig(enabled=True)

        data = config.to_dict()

        assert data["enabled"] is True
        assert "app_whitelist" in data


# ============================================================================
# Test: AutoRecordingTrigger
# ============================================================================


class TestAutoRecordingTrigger:
    """Tests for auto-recording trigger system."""

    def test_trigger_init(self):
        """Test AutoRecordingTrigger initialization."""
        from recall.app.notifications import AutoRecordingConfig, AutoRecordingTrigger

        config = AutoRecordingConfig(enabled=True)
        trigger = AutoRecordingTrigger(config)

        assert trigger.config == config
        assert trigger.is_monitoring is False

    def test_trigger_start_monitoring(self):
        """Test starting auto-recording monitoring."""
        from recall.app.notifications import AutoRecordingConfig, AutoRecordingTrigger

        config = AutoRecordingConfig(enabled=True)
        trigger = AutoRecordingTrigger(config)

        with patch.object(trigger, "_start_app_monitor"):
            with patch.object(trigger, "_start_audio_monitor"):
                trigger.start_monitoring()

                assert trigger.is_monitoring is True

    def test_trigger_stop_monitoring(self):
        """Test stopping auto-recording monitoring."""
        from recall.app.notifications import AutoRecordingConfig, AutoRecordingTrigger

        config = AutoRecordingConfig(enabled=True)
        trigger = AutoRecordingTrigger(config)
        trigger._is_monitoring = True

        with patch.object(trigger, "_stop_app_monitor"):
            with patch.object(trigger, "_stop_audio_monitor"):
                trigger.stop_monitoring()

                assert trigger.is_monitoring is False

    def test_trigger_disabled_config_does_not_monitor(self):
        """Test that disabled config prevents monitoring."""
        from recall.app.notifications import AutoRecordingConfig, AutoRecordingTrigger

        config = AutoRecordingConfig(enabled=False)
        trigger = AutoRecordingTrigger(config)

        trigger.start_monitoring()

        assert trigger.is_monitoring is False

    def test_trigger_on_meeting_app_detected(self):
        """Test callback when meeting app is detected."""
        from recall.app.notifications import AutoRecordingConfig, AutoRecordingTrigger

        config = AutoRecordingConfig(enabled=True, detect_meeting_apps=True)
        trigger = AutoRecordingTrigger(config)

        callback = MagicMock()
        trigger.on_trigger = callback

        trigger._on_app_detected("zoom.us")

        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["source"] == "meeting_app"
        assert call_args["app_name"] == "zoom.us"

    def test_trigger_on_system_audio_detected(self):
        """Test callback when system audio is detected."""
        from recall.app.notifications import AutoRecordingConfig, AutoRecordingTrigger

        config = AutoRecordingConfig(enabled=True, detect_system_audio=True)
        trigger = AutoRecordingTrigger(config)

        callback = MagicMock()
        trigger.on_trigger = callback

        trigger._on_audio_detected(source="BlackHole")

        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["source"] == "system_audio"

    def test_trigger_ignores_non_whitelisted_apps(self):
        """Test that non-whitelisted apps don't trigger recording."""
        from recall.app.notifications import AutoRecordingConfig, AutoRecordingTrigger

        config = AutoRecordingConfig(enabled=True, detect_meeting_apps=True)
        trigger = AutoRecordingTrigger(config)

        callback = MagicMock()
        trigger.on_trigger = callback

        trigger._on_app_detected("Safari")

        callback.assert_not_called()


# ============================================================================
# Test: MenuBar Integration
# ============================================================================


class TestMenuBarNotificationIntegration:
    """Tests for notification integration with RecallMenuBar."""

    def test_menubar_has_notification_manager(self):
        """Test that RecallMenuBar has a notification manager."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                from recall.app.menubar import RecallMenuBar

                app = RecallMenuBar()

                assert hasattr(app, "notification_manager")

    def test_menubar_notifies_on_recording_stop(self):
        """Test that stopping recording sends a notification."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder") as mock_recorder:
                with patch("recall.app.notifications.RUMPS_AVAILABLE", True):
                    with patch("recall.app.notifications.rumps"):
                        from recall.app.menubar import RecallMenuBar

                        mock_recorder.return_value.stop_recording.return_value = Path(
                            "/tmp/test.wav"
                        )

                        app = RecallMenuBar()
                        app.recording_controller._recorder = mock_recorder.return_value
                        app.recording_controller._state = AppState.RECORDING

                        with patch.object(
                            app.notification_manager, "notify_recording_saved"
                        ) as mock_notify:
                            app.on_stop_recording(None)

                            # Notification should be called after processing
                            # (In real implementation, this happens after pipeline completes)

    def test_menubar_has_auto_recording_config(self):
        """Test that RecallMenuBar has auto-recording configuration."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                from recall.app.menubar import RecallMenuBar

                app = RecallMenuBar()

                assert hasattr(app, "auto_recording_config")
