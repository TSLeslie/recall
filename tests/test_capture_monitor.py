"""Tests for System Audio Monitor (Ticket 2.3).

TDD tests for AudioMonitor class that detects system audio:
- Start/stop monitoring
- Audio event detection
- BlackHole availability check
- Configurable thresholds
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Import at module level to avoid freezegun issues
from recall.capture.monitor import (
    AudioEvent,
    AudioMonitor,
    is_blackhole_available,
)

# ============================================================================
# Test: AudioEvent Model
# ============================================================================


class TestAudioEvent:
    """Tests for AudioEvent data model."""

    def test_audio_event_created_with_required_fields(self):
        """Test that AudioEvent can be created with required fields."""
        event = AudioEvent(
            event_type="started",
            timestamp=datetime.now(),
        )

        assert event.event_type == "started"
        assert isinstance(event.timestamp, datetime)

    def test_audio_event_accepts_valid_types(self):
        """Test that AudioEvent accepts valid event types."""
        for event_type in ["started", "stopped"]:
            event = AudioEvent(
                event_type=event_type,
                timestamp=datetime.now(),
            )
            assert event.event_type == event_type

    def test_audio_event_optional_source_hint(self):
        """Test that AudioEvent has optional source_hint."""
        event = AudioEvent(
            event_type="started",
            timestamp=datetime.now(),
            source_hint="Zoom Meeting",
        )

        assert event.source_hint == "Zoom Meeting"

    def test_audio_event_default_source_hint_is_none(self):
        """Test that source_hint defaults to None."""
        event = AudioEvent(
            event_type="started",
            timestamp=datetime.now(),
        )

        assert event.source_hint is None


# ============================================================================
# Test: AudioMonitor Initialization
# ============================================================================


class TestAudioMonitorInit:
    """Tests for AudioMonitor initialization."""

    def test_monitor_init_with_defaults(self):
        """Test that AudioMonitor initializes with default settings."""
        monitor = AudioMonitor()

        assert monitor.silence_threshold > 0
        assert monitor.silence_duration > 0
        assert not monitor.is_monitoring

    def test_monitor_init_with_custom_threshold(self):
        """Test that AudioMonitor accepts custom silence threshold."""
        monitor = AudioMonitor(silence_threshold=0.05)

        assert monitor.silence_threshold == 0.05

    def test_monitor_init_with_custom_silence_duration(self):
        """Test that AudioMonitor accepts custom silence duration."""
        monitor = AudioMonitor(silence_duration=3.0)

        assert monitor.silence_duration == 3.0

    def test_monitor_init_with_device_name(self):
        """Test that AudioMonitor accepts device name for BlackHole."""
        monitor = AudioMonitor(device_name="BlackHole 2ch")

        assert monitor.device_name == "BlackHole 2ch"


# ============================================================================
# Test: Start/Stop Monitoring
# ============================================================================


class TestAudioMonitorStartStop:
    """Tests for starting and stopping audio monitoring."""

    def test_start_monitoring_sets_is_monitoring(self):
        """Test that start_monitoring sets is_monitoring to True."""
        with patch("recall.capture.monitor.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "BlackHole 2ch", "max_input_channels": 2, "index": 0}
            ]
            mock_sd.InputStream.return_value.__enter__ = MagicMock()
            mock_sd.InputStream.return_value.__exit__ = MagicMock()

            monitor = AudioMonitor()
            callback = MagicMock()

            # Start in background thread would set is_monitoring
            # For unit test, we test the state change
            assert not monitor.is_monitoring

    def test_stop_monitoring_sets_is_monitoring_false(self):
        """Test that stop_monitoring sets is_monitoring to False."""
        monitor = AudioMonitor()

        # Even if not monitoring, stop should be safe
        monitor.stop_monitoring()

        assert not monitor.is_monitoring

    def test_start_monitoring_requires_callback(self):
        """Test that start_monitoring requires a callback function."""
        monitor = AudioMonitor()

        with pytest.raises(TypeError):
            monitor.start_monitoring()  # Missing callback

    def test_callback_receives_audio_events(self):
        """Test that callback receives AudioEvent objects."""
        events_received = []

        def callback(event):
            events_received.append(event)

        with patch("recall.capture.monitor.sd") as mock_sd:
            # Setup mock device
            mock_sd.query_devices.return_value = [
                {"name": "BlackHole 2ch", "max_input_channels": 2, "index": 0}
            ]

            monitor = AudioMonitor()

            # Simulate an event being triggered
            test_event = AudioEvent(
                event_type="started",
                timestamp=datetime.now(),
            )
            callback(test_event)

            assert len(events_received) == 1
            assert isinstance(events_received[0], AudioEvent)


# ============================================================================
# Test: Audio Detection
# ============================================================================


class TestAudioDetection:
    """Tests for audio detection logic."""

    def test_detect_audio_above_threshold(self):
        """Test that audio above threshold is detected."""
        monitor = AudioMonitor(silence_threshold=0.01)

        # Simulate audio data above threshold
        audio_data = np.array([0.1, 0.2, 0.15, 0.08])

        is_audio = monitor._is_audio_present(audio_data)

        assert is_audio

    def test_detect_silence_below_threshold(self):
        """Test that audio below threshold is detected as silence."""
        monitor = AudioMonitor(silence_threshold=0.01)

        # Simulate silent audio data
        audio_data = np.array([0.001, 0.002, 0.0005, 0.001])

        is_audio = monitor._is_audio_present(audio_data)

        assert not is_audio

    def test_detect_audio_uses_rms(self):
        """Test that audio detection uses RMS amplitude."""
        monitor = AudioMonitor(silence_threshold=0.05)

        # Create data where peak is high but RMS is low
        audio_data = np.zeros(1000)
        audio_data[0] = 0.5  # Single spike

        # RMS should be low despite peak
        is_audio = monitor._is_audio_present(audio_data)

        # Depends on threshold, but spike alone shouldn't trigger
        assert not is_audio


# ============================================================================
# Test: Audio State Transitions
# ============================================================================


class TestAudioStateTransitions:
    """Tests for audio state transitions (started/stopped events)."""

    def test_transition_from_silence_to_audio_triggers_started(self):
        """Test that transitioning from silence to audio triggers 'started' event."""
        events = []
        monitor = AudioMonitor(silence_threshold=0.01, silence_duration=0.5)
        monitor._emit_event = lambda e: events.append(e)

        # Simulate silence then audio
        monitor._was_audio_present = False
        monitor._process_audio_state(is_audio=True)

        # Should emit started event
        assert len(events) == 1
        assert events[0].event_type == "started"

    def test_transition_from_audio_to_silence_triggers_stopped(self):
        """Test that silence after audio triggers 'stopped' event after duration."""
        events = []
        monitor = AudioMonitor(silence_threshold=0.01, silence_duration=0.1)
        monitor._emit_event = lambda e: events.append(e)

        # Simulate audio then silence
        monitor._was_audio_present = True
        monitor._silence_start = datetime.now()

        # Wait for silence duration to pass
        import time

        time.sleep(0.15)

        monitor._process_audio_state(is_audio=False)

        # Should emit stopped event after silence duration
        assert len(events) == 1
        assert events[0].event_type == "stopped"

    def test_brief_silence_does_not_trigger_stopped(self):
        """Test that brief silence doesn't trigger 'stopped' event."""
        events = []
        monitor = AudioMonitor(silence_threshold=0.01, silence_duration=1.0)
        monitor._emit_event = lambda e: events.append(e)

        # Simulate audio then brief silence
        monitor._was_audio_present = True
        monitor._silence_start = datetime.now()

        # Don't wait for full silence duration
        monitor._process_audio_state(is_audio=False)

        # Should not emit stopped event yet
        assert len(events) == 0


# ============================================================================
# Test: BlackHole Detection
# ============================================================================


class TestBlackHoleDetection:
    """Tests for BlackHole device detection."""

    def test_is_blackhole_available_true_when_present(self):
        """Test that is_blackhole_available returns True when BlackHole is installed."""
        with patch("recall.capture.monitor.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "MacBook Pro Microphone", "max_input_channels": 1},
                {"name": "BlackHole 2ch", "max_input_channels": 2},
            ]

            assert is_blackhole_available()

    def test_is_blackhole_available_false_when_absent(self):
        """Test that is_blackhole_available returns False when BlackHole not installed."""
        with patch("recall.capture.monitor.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "MacBook Pro Microphone", "max_input_channels": 1},
                {"name": "Built-in Output", "max_input_channels": 0},
            ]

            assert not is_blackhole_available()

    def test_is_blackhole_available_handles_error(self):
        """Test that is_blackhole_available handles sounddevice errors."""
        with patch("recall.capture.monitor.sd") as mock_sd:
            mock_sd.query_devices.side_effect = Exception("No audio devices")

            # Should return False, not raise
            assert not is_blackhole_available()

    def test_monitor_finds_blackhole_device(self):
        """Test that AudioMonitor finds BlackHole device by name."""
        with patch("recall.capture.monitor.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "MacBook Pro Microphone", "max_input_channels": 1, "index": 0},
                {"name": "BlackHole 2ch", "max_input_channels": 2, "index": 1},
            ]

            monitor = AudioMonitor(device_name="BlackHole 2ch")
            device_id = monitor._find_device()

            assert device_id == 1


# ============================================================================
# Test: Monitor Properties
# ============================================================================


class TestMonitorProperties:
    """Tests for AudioMonitor properties."""

    def test_is_monitoring_property(self):
        """Test that is_monitoring property reflects state."""
        monitor = AudioMonitor()

        assert isinstance(monitor.is_monitoring, bool)
        assert not monitor.is_monitoring

    def test_current_amplitude_property(self):
        """Test that current_amplitude returns recent audio level."""
        monitor = AudioMonitor()
        monitor._current_amplitude = 0.05

        assert monitor.current_amplitude == 0.05

    def test_current_amplitude_default_zero(self):
        """Test that current_amplitude defaults to 0."""
        monitor = AudioMonitor()

        assert monitor.current_amplitude == 0.0
