"""Notifications and Auto-Recording for Recall Menu Bar App.

This module provides:
- macOS notification support via rumps
- Auto-recording triggers for meeting apps and system audio
- Configuration for auto-recording behavior
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# Check if rumps is available (macOS only)
try:
    import rumps

    RUMPS_AVAILABLE = True
except ImportError:
    rumps = None  # type: ignore
    RUMPS_AVAILABLE = False

logger = logging.getLogger(__name__)


# Default meeting apps to whitelist for auto-recording
DEFAULT_MEETING_APPS = [
    "zoom.us",
    "Microsoft Teams",
    "Slack",
    "Discord",
    "Google Meet",
    "Webex",
    "Skype",
    "FaceTime",
]


class NotificationManager:
    """Manages macOS notifications for Recall.

    This class provides a unified interface for sending notifications,
    with special methods for recording-related events.
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the notification manager.

        Args:
            enabled: Whether notifications are enabled.
        """
        self.enabled = enabled

    def send(
        self,
        title: str,
        message: str,
        subtitle: str = "",
        sound: bool = True,
    ) -> None:
        """Send a notification.

        Args:
            title: The notification title.
            message: The notification body message.
            subtitle: Optional subtitle.
            sound: Whether to play a sound.
        """
        if not self.enabled:
            return

        if rumps is not None:
            rumps.notification(
                title=title,
                subtitle=subtitle,
                message=message,
                sound=sound,
            )
        else:
            # Log as fallback when rumps unavailable
            logger.info(f"Notification: {title} - {message}")

    def notify_recording_started(self, source: str = "microphone") -> None:
        """Send notification when recording starts.

        Args:
            source: The recording source (e.g., "microphone", "system").
        """
        self.send(
            title="Recording Started",
            message=f"Now recording from {source}",
        )

    def notify_recording_saved(
        self,
        title: str = "Recording",
        duration: int = 0,
    ) -> None:
        """Send notification when recording is saved.

        Args:
            title: The recording title.
            duration: Duration in seconds.
        """
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}:{seconds:02d}"

        self.send(
            title="Recording Saved",
            message=f"{title} ({duration_str})",
        )

    def notify_auto_recording(
        self,
        source: str,
        app_name: Optional[str] = None,
    ) -> None:
        """Send notification when auto-recording is triggered.

        Args:
            source: The detection source (e.g., "Zoom", "system_audio").
            app_name: The detected application name.
        """
        message = f"Recording detected audio from {source}"
        if app_name and app_name != source:
            message = f"Recording detected audio from {source} ({app_name})"

        self.send(
            title="Auto-Recording Started",
            message=message,
        )

    def notify_error(self, error: str) -> None:
        """Send notification for an error.

        Args:
            error: The error message.
        """
        self.send(
            title="Recall Error",
            message=error,
            sound=True,
        )


@dataclass
class AutoRecordingConfig:
    """Configuration for auto-recording triggers.

    Attributes:
        enabled: Whether auto-recording is enabled (off by default for privacy).
        detect_meeting_apps: Whether to detect meeting applications.
        detect_system_audio: Whether to detect system audio via BlackHole.
        app_whitelist: List of application names to trigger auto-recording.
    """

    enabled: bool = False
    detect_meeting_apps: bool = True
    detect_system_audio: bool = True
    app_whitelist: List[str] = field(default_factory=lambda: DEFAULT_MEETING_APPS.copy())

    def add_to_whitelist(self, app_name: str) -> None:
        """Add an application to the whitelist.

        Args:
            app_name: The application name to add.
        """
        if app_name not in self.app_whitelist:
            self.app_whitelist.append(app_name)

    def remove_from_whitelist(self, app_name: str) -> None:
        """Remove an application from the whitelist.

        Args:
            app_name: The application name to remove.
        """
        if app_name in self.app_whitelist:
            self.app_whitelist.remove(app_name)

    def is_app_whitelisted(self, app_name: str) -> bool:
        """Check if an application is whitelisted.

        Args:
            app_name: The application name to check.

        Returns:
            True if the app is in the whitelist.
        """
        return app_name in self.app_whitelist

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoRecordingConfig":
        """Create config from a dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            AutoRecordingConfig instance.
        """
        return cls(
            enabled=data.get("enabled", False),
            detect_meeting_apps=data.get("detect_meeting_apps", True),
            detect_system_audio=data.get("detect_system_audio", True),
            app_whitelist=data.get("app_whitelist", DEFAULT_MEETING_APPS.copy()),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "enabled": self.enabled,
            "detect_meeting_apps": self.detect_meeting_apps,
            "detect_system_audio": self.detect_system_audio,
            "app_whitelist": self.app_whitelist,
        }


class AutoRecordingTrigger:
    """Monitors for auto-recording trigger conditions.

    This class watches for:
    - Meeting applications starting (via ApplicationDetector)
    - System audio activity (via AudioMonitor)
    """

    def __init__(self, config: AutoRecordingConfig) -> None:
        """Initialize the auto-recording trigger.

        Args:
            config: Auto-recording configuration.
        """
        self.config = config
        self._is_monitoring = False
        self._app_monitor = None
        self._audio_monitor = None

        # Callback for when recording should start
        self.on_trigger: Optional[Callable[[Dict[str, Any]], None]] = None

    @property
    def is_monitoring(self) -> bool:
        """Check if currently monitoring for triggers."""
        return self._is_monitoring

    def start_monitoring(self) -> None:
        """Start monitoring for auto-recording triggers."""
        if not self.config.enabled:
            logger.info("Auto-recording is disabled, not starting monitors")
            return

        if self.config.detect_meeting_apps:
            self._start_app_monitor()

        if self.config.detect_system_audio:
            self._start_audio_monitor()

        self._is_monitoring = True
        logger.info("Started auto-recording monitors")

    def stop_monitoring(self) -> None:
        """Stop monitoring for auto-recording triggers."""
        if self.config.detect_meeting_apps:
            self._stop_app_monitor()

        if self.config.detect_system_audio:
            self._stop_audio_monitor()

        self._is_monitoring = False
        logger.info("Stopped auto-recording monitors")

    def _start_app_monitor(self) -> None:
        """Start the application monitor."""
        # Integration with recall.capture.detector.ApplicationDetector
        # would happen here in a full implementation
        pass

    def _stop_app_monitor(self) -> None:
        """Stop the application monitor."""
        pass

    def _start_audio_monitor(self) -> None:
        """Start the audio monitor."""
        # Integration with recall.capture.monitor.AudioMonitor
        # would happen here in a full implementation
        pass

    def _stop_audio_monitor(self) -> None:
        """Stop the audio monitor."""
        pass

    def _on_app_detected(self, app_name: str) -> None:
        """Handle detection of a meeting application.

        Args:
            app_name: The detected application name.
        """
        if not self.config.is_app_whitelisted(app_name):
            logger.debug(f"App {app_name} not in whitelist, ignoring")
            return

        if self.on_trigger:
            self.on_trigger(
                {
                    "source": "meeting_app",
                    "app_name": app_name,
                }
            )

    def _on_audio_detected(self, source: str = "BlackHole") -> None:
        """Handle detection of system audio.

        Args:
            source: The audio source name.
        """
        if self.on_trigger:
            self.on_trigger(
                {
                    "source": "system_audio",
                    "audio_source": source,
                }
            )
