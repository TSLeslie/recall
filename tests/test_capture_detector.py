"""Tests for Application Detector (Ticket 2.4).

TDD tests for detecting running audio applications:
- Meeting apps (Zoom, Teams, Google Meet, etc.)
- Media apps (YouTube, Spotify, VLC, etc.)
- Browser detection with tab context
"""

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

# Import at module level to avoid freezegun issues
from recall.capture.detector import (
    AudioApp,
    AudioAppCategory,
    get_active_audio_app,
    get_running_audio_apps,
    is_meeting_app_running,
)

# ============================================================================
# Test: AudioApp Model
# ============================================================================


class TestAudioApp:
    """Tests for AudioApp data model."""

    def test_audio_app_created_with_required_fields(self):
        """Test that AudioApp can be created with required fields."""
        app = AudioApp(
            name="Zoom",
            process_name="zoom.us",
            category=AudioAppCategory.MEETING,
        )

        assert app.name == "Zoom"
        assert app.process_name == "zoom.us"
        assert app.category == AudioAppCategory.MEETING

    def test_audio_app_has_optional_pid(self):
        """Test that AudioApp has optional PID field."""
        app = AudioApp(
            name="Zoom",
            process_name="zoom.us",
            category=AudioAppCategory.MEETING,
            pid=12345,
        )

        assert app.pid == 12345

    def test_audio_app_default_pid_is_none(self):
        """Test that PID defaults to None."""
        app = AudioApp(
            name="Zoom",
            process_name="zoom.us",
            category=AudioAppCategory.MEETING,
        )

        assert app.pid is None

    def test_audio_app_has_optional_window_title(self):
        """Test that AudioApp has optional window_title field."""
        app = AudioApp(
            name="Chrome",
            process_name="Google Chrome",
            category=AudioAppCategory.BROWSER,
            window_title="YouTube - Watch Video",
        )

        assert app.window_title == "YouTube - Watch Video"


# ============================================================================
# Test: AudioAppCategory Enum
# ============================================================================


class TestAudioAppCategory:
    """Tests for AudioAppCategory enum."""

    def test_meeting_category_exists(self):
        """Test that MEETING category exists."""
        assert AudioAppCategory.MEETING.value == "meeting"

    def test_media_category_exists(self):
        """Test that MEDIA category exists."""
        assert AudioAppCategory.MEDIA.value == "media"

    def test_browser_category_exists(self):
        """Test that BROWSER category exists."""
        assert AudioAppCategory.BROWSER.value == "browser"

    def test_other_category_exists(self):
        """Test that OTHER category exists."""
        assert AudioAppCategory.OTHER.value == "other"


# ============================================================================
# Test: get_running_audio_apps
# ============================================================================


class TestGetRunningAudioApps:
    """Tests for get_running_audio_apps function."""

    def test_returns_empty_list_when_no_audio_apps(self):
        """Test that empty list is returned when no audio apps running."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_psutil.process_iter.return_value = []

            result = get_running_audio_apps()

            assert result == []

    def test_detects_zoom_process(self):
        """Test that Zoom process is detected as meeting app."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = {
                "pid": 1234,
                "name": "zoom.us",
            }
            mock_psutil.process_iter.return_value = [mock_process]

            result = get_running_audio_apps()

            assert len(result) == 1
            assert result[0].name == "Zoom"
            assert result[0].category == AudioAppCategory.MEETING

    def test_detects_teams_process(self):
        """Test that Microsoft Teams process is detected."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = {
                "pid": 5678,
                "name": "Microsoft Teams",
            }
            mock_psutil.process_iter.return_value = [mock_process]

            result = get_running_audio_apps()

            assert len(result) == 1
            assert result[0].name == "Microsoft Teams"
            assert result[0].category == AudioAppCategory.MEETING

    def test_detects_spotify_process(self):
        """Test that Spotify process is detected as media app."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = {
                "pid": 9999,
                "name": "Spotify",
            }
            mock_psutil.process_iter.return_value = [mock_process]

            result = get_running_audio_apps()

            assert len(result) == 1
            assert result[0].name == "Spotify"
            assert result[0].category == AudioAppCategory.MEDIA

    def test_detects_vlc_process(self):
        """Test that VLC process is detected as media app."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = {
                "pid": 1111,
                "name": "VLC",
            }
            mock_psutil.process_iter.return_value = [mock_process]

            result = get_running_audio_apps()

            assert len(result) == 1
            assert result[0].name == "VLC"
            assert result[0].category == AudioAppCategory.MEDIA

    def test_detects_chrome_browser(self):
        """Test that Chrome browser is detected."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = {
                "pid": 2222,
                "name": "Google Chrome",
            }
            mock_psutil.process_iter.return_value = [mock_process]

            result = get_running_audio_apps()

            assert len(result) == 1
            assert result[0].name == "Chrome"
            assert result[0].category == AudioAppCategory.BROWSER

    def test_detects_multiple_apps(self):
        """Test that multiple audio apps are detected."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_zoom = MagicMock()
            mock_zoom.info = {"pid": 1111, "name": "zoom.us"}

            mock_spotify = MagicMock()
            mock_spotify.info = {"pid": 2222, "name": "Spotify"}

            mock_psutil.process_iter.return_value = [mock_zoom, mock_spotify]

            result = get_running_audio_apps()

            assert len(result) == 2
            categories = {app.category for app in result}
            assert AudioAppCategory.MEETING in categories
            assert AudioAppCategory.MEDIA in categories

    def test_ignores_non_audio_apps(self):
        """Test that non-audio apps are ignored."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = {
                "pid": 3333,
                "name": "TextEdit",
            }
            mock_psutil.process_iter.return_value = [mock_process]

            result = get_running_audio_apps()

            assert result == []

    def test_handles_process_access_error(self):
        """Test that access errors are handled gracefully."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = None  # Simulate access denied

            mock_psutil.process_iter.return_value = [mock_process]
            mock_psutil.NoSuchProcess = Exception
            mock_psutil.AccessDenied = Exception

            result = get_running_audio_apps()

            assert result == []


# ============================================================================
# Test: is_meeting_app_running
# ============================================================================


class TestIsMeetingAppRunning:
    """Tests for is_meeting_app_running helper function."""

    def test_returns_true_when_zoom_running(self):
        """Test that returns True when Zoom is running."""
        with patch("recall.capture.detector.get_running_audio_apps") as mock_get:
            mock_get.return_value = [
                AudioApp(
                    name="Zoom",
                    process_name="zoom.us",
                    category=AudioAppCategory.MEETING,
                )
            ]

            assert is_meeting_app_running()

    def test_returns_true_when_teams_running(self):
        """Test that returns True when Teams is running."""
        with patch("recall.capture.detector.get_running_audio_apps") as mock_get:
            mock_get.return_value = [
                AudioApp(
                    name="Microsoft Teams",
                    process_name="Microsoft Teams",
                    category=AudioAppCategory.MEETING,
                )
            ]

            assert is_meeting_app_running()

    def test_returns_false_when_no_meeting_app(self):
        """Test that returns False when no meeting app is running."""
        with patch("recall.capture.detector.get_running_audio_apps") as mock_get:
            mock_get.return_value = [
                AudioApp(
                    name="Spotify",
                    process_name="Spotify",
                    category=AudioAppCategory.MEDIA,
                )
            ]

            assert not is_meeting_app_running()

    def test_returns_false_when_no_apps(self):
        """Test that returns False when no audio apps are running."""
        with patch("recall.capture.detector.get_running_audio_apps") as mock_get:
            mock_get.return_value = []

            assert not is_meeting_app_running()


# ============================================================================
# Test: get_active_audio_app
# ============================================================================


class TestGetActiveAudioApp:
    """Tests for get_active_audio_app function."""

    def test_returns_meeting_app_first_if_running(self):
        """Test that meeting app takes priority over media."""
        with patch("recall.capture.detector.get_running_audio_apps") as mock_get:
            mock_get.return_value = [
                AudioApp(
                    name="Spotify",
                    process_name="Spotify",
                    category=AudioAppCategory.MEDIA,
                ),
                AudioApp(
                    name="Zoom",
                    process_name="zoom.us",
                    category=AudioAppCategory.MEETING,
                ),
            ]

            result = get_active_audio_app()

            assert result is not None
            assert result.name == "Zoom"
            assert result.category == AudioAppCategory.MEETING

    def test_returns_media_app_if_no_meeting(self):
        """Test that media app is returned if no meeting app."""
        with patch("recall.capture.detector.get_running_audio_apps") as mock_get:
            mock_get.return_value = [
                AudioApp(
                    name="Spotify",
                    process_name="Spotify",
                    category=AudioAppCategory.MEDIA,
                ),
            ]

            result = get_active_audio_app()

            assert result is not None
            assert result.name == "Spotify"
            assert result.category == AudioAppCategory.MEDIA

    def test_returns_none_if_no_apps(self):
        """Test that None is returned if no audio apps."""
        with patch("recall.capture.detector.get_running_audio_apps") as mock_get:
            mock_get.return_value = []

            result = get_active_audio_app()

            assert result is None


# ============================================================================
# Test: Known Apps Detection
# ============================================================================


class TestKnownAppsDetection:
    """Tests for detection of known audio applications."""

    @pytest.mark.parametrize(
        "process_name,expected_name,expected_category",
        [
            ("zoom.us", "Zoom", AudioAppCategory.MEETING),
            ("Microsoft Teams", "Microsoft Teams", AudioAppCategory.MEETING),
            ("Slack", "Slack", AudioAppCategory.MEETING),
            ("Discord", "Discord", AudioAppCategory.MEETING),
            ("Webex", "Webex", AudioAppCategory.MEETING),
            ("Spotify", "Spotify", AudioAppCategory.MEDIA),
            ("VLC", "VLC", AudioAppCategory.MEDIA),
            ("Music", "Apple Music", AudioAppCategory.MEDIA),
            ("Google Chrome", "Chrome", AudioAppCategory.BROWSER),
            ("Firefox", "Firefox", AudioAppCategory.BROWSER),
            ("Safari", "Safari", AudioAppCategory.BROWSER),
            ("Arc", "Arc", AudioAppCategory.BROWSER),
        ],
    )
    def test_known_app_detection(self, process_name, expected_name, expected_category):
        """Test that known apps are detected correctly."""
        with patch("recall.capture.detector.psutil") as mock_psutil:
            mock_process = MagicMock()
            mock_process.info = {
                "pid": 9999,
                "name": process_name,
            }
            mock_psutil.process_iter.return_value = [mock_process]

            result = get_running_audio_apps()

            assert len(result) == 1
            assert result[0].name == expected_name
            assert result[0].category == expected_category
