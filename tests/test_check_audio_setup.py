"""Tests for Audio Setup Verification Script (Ticket 2.5).

TDD tests for the check_audio_setup.py script:
- Device detection
- BlackHole availability check
- Setup recommendations
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the path so we can import from scripts
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import at module level to avoid freezegun issues
from scripts.check_audio_setup import (
    AudioSetupStatus,
    check_audio_setup,
    check_blackhole_device,
    get_setup_recommendations,
)

# ============================================================================
# Test: AudioSetupStatus Model
# ============================================================================


class TestAudioSetupStatus:
    """Tests for AudioSetupStatus data model."""

    def test_status_created_with_all_fields(self):
        """Test that AudioSetupStatus has all required fields."""
        status = AudioSetupStatus(
            blackhole_found=True,
            blackhole_device_id=3,
            blackhole_channels=2,
            is_ready=True,
            message="System audio capture is ready!",
        )

        assert status.blackhole_found is True
        assert status.blackhole_device_id == 3
        assert status.blackhole_channels == 2
        assert status.is_ready is True

    def test_status_not_ready_when_blackhole_missing(self):
        """Test that status is not ready when BlackHole is missing."""
        status = AudioSetupStatus(
            blackhole_found=False,
            blackhole_device_id=None,
            blackhole_channels=0,
            is_ready=False,
            message="BlackHole not found",
        )

        assert status.is_ready is False
        assert status.blackhole_found is False


# ============================================================================
# Test: check_blackhole_device
# ============================================================================


class TestCheckBlackholeDevice:
    """Tests for check_blackhole_device function."""

    def test_returns_device_info_when_blackhole_present(self):
        """Test that device info is returned when BlackHole is installed."""
        with patch("scripts.check_audio_setup.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "Built-in Microphone", "max_input_channels": 1, "index": 0},
                {"name": "BlackHole 2ch", "max_input_channels": 2, "index": 1},
            ]

            device_id, channels = check_blackhole_device()

            assert device_id == 1
            assert channels == 2

    def test_returns_none_when_blackhole_absent(self):
        """Test that None is returned when BlackHole is not installed."""
        with patch("scripts.check_audio_setup.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "Built-in Microphone", "max_input_channels": 1, "index": 0},
                {"name": "Built-in Output", "max_input_channels": 0, "index": 1},
            ]

            device_id, channels = check_blackhole_device()

            assert device_id is None
            assert channels == 0

    def test_handles_sounddevice_error(self):
        """Test that errors are handled gracefully."""
        with patch("scripts.check_audio_setup.sd") as mock_sd:
            mock_sd.query_devices.side_effect = Exception("No audio devices")

            device_id, channels = check_blackhole_device()

            assert device_id is None
            assert channels == 0

    def test_detects_blackhole_16ch_variant(self):
        """Test that other BlackHole variants are detected."""
        with patch("scripts.check_audio_setup.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "BlackHole 16ch", "max_input_channels": 16, "index": 2},
            ]

            device_id, channels = check_blackhole_device()

            assert device_id == 2
            assert channels == 16


# ============================================================================
# Test: check_audio_setup
# ============================================================================


class TestCheckAudioSetup:
    """Tests for check_audio_setup function."""

    def test_returns_ready_status_when_blackhole_present(self):
        """Test that ready status is returned when BlackHole is available."""
        with patch("scripts.check_audio_setup.check_blackhole_device") as mock_check:
            mock_check.return_value = (3, 2)

            status = check_audio_setup()

            assert status.is_ready is True
            assert status.blackhole_found is True
            assert status.blackhole_device_id == 3
            assert status.blackhole_channels == 2

    def test_returns_not_ready_when_blackhole_missing(self):
        """Test that not-ready status is returned when BlackHole is missing."""
        with patch("scripts.check_audio_setup.check_blackhole_device") as mock_check:
            mock_check.return_value = (None, 0)

            status = check_audio_setup()

            assert status.is_ready is False
            assert status.blackhole_found is False

    def test_status_message_indicates_success(self):
        """Test that success message is included when ready."""
        with patch("scripts.check_audio_setup.check_blackhole_device") as mock_check:
            mock_check.return_value = (3, 2)

            status = check_audio_setup()

            assert "ready" in status.message.lower()

    def test_status_message_indicates_missing(self):
        """Test that missing message is included when not ready."""
        with patch("scripts.check_audio_setup.check_blackhole_device") as mock_check:
            mock_check.return_value = (None, 0)

            status = check_audio_setup()

            assert "not found" in status.message.lower() or "missing" in status.message.lower()


# ============================================================================
# Test: get_setup_recommendations
# ============================================================================


class TestGetSetupRecommendations:
    """Tests for get_setup_recommendations function."""

    def test_returns_install_recommendation_when_missing(self):
        """Test that install recommendation is returned when BlackHole missing."""
        status = AudioSetupStatus(
            blackhole_found=False,
            blackhole_device_id=None,
            blackhole_channels=0,
            is_ready=False,
            message="Not found",
        )

        recommendations = get_setup_recommendations(status)

        # Should recommend installation
        assert len(recommendations) > 0
        assert any("install" in r.lower() for r in recommendations)

    def test_returns_usage_tips_when_ready(self):
        """Test that usage tips are returned when setup is ready."""
        status = AudioSetupStatus(
            blackhole_found=True,
            blackhole_device_id=3,
            blackhole_channels=2,
            is_ready=True,
            message="Ready",
        )

        recommendations = get_setup_recommendations(status)

        # Should have some tips
        assert len(recommendations) > 0

    def test_recommendations_are_strings(self):
        """Test that recommendations are all strings."""
        status = AudioSetupStatus(
            blackhole_found=False,
            blackhole_device_id=None,
            blackhole_channels=0,
            is_ready=False,
            message="Not found",
        )

        recommendations = get_setup_recommendations(status)

        assert all(isinstance(r, str) for r in recommendations)
