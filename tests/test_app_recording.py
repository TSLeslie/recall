"""Tests for Recording Controls (Ticket 7.2).

TDD tests for recording functionality in the menu bar app:
- Start/stop recording integration
- Recording duration display
- Processing state and notifications
- Integration with Recorder
"""

import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from recall.app.menubar import AppState, RecallMenuBar
from recall.app.recording import (
    RecordingController,
    RecordingStatus,
)

# ============================================================================
# Test: RecordingStatus Model
# ============================================================================


class TestRecordingStatus:
    """Tests for RecordingStatus model."""

    def test_status_has_state(self):
        """Test that status has state field."""
        status = RecordingStatus(
            state=AppState.IDLE,
            duration_seconds=0,
        )

        assert status.state == AppState.IDLE

    def test_status_has_duration(self):
        """Test that status has duration_seconds field."""
        status = RecordingStatus(
            state=AppState.RECORDING,
            duration_seconds=120,
        )

        assert status.duration_seconds == 120

    def test_status_has_optional_message(self):
        """Test that status has optional message field."""
        status = RecordingStatus(
            state=AppState.PROCESSING,
            duration_seconds=60,
            message="Transcribing...",
        )

        assert status.message == "Transcribing..."

    def test_status_has_optional_error(self):
        """Test that status has optional error field."""
        status = RecordingStatus(
            state=AppState.IDLE,
            duration_seconds=0,
            error="Microphone not found",
        )

        assert status.error == "Microphone not found"


# ============================================================================
# Test: RecordingController Initialization
# ============================================================================


class TestRecordingControllerInit:
    """Tests for RecordingController initialization."""

    def test_controller_initializes_with_idle_state(self):
        """Test that controller starts in IDLE state."""
        controller = RecordingController()

        assert controller.state == AppState.IDLE

    def test_controller_has_no_active_recording_initially(self):
        """Test that no recording is active initially."""
        controller = RecordingController()

        assert controller.active_recording is None

    def test_controller_accepts_output_directory(self):
        """Test that controller accepts output directory."""
        output_dir = Path("/tmp/recordings")
        controller = RecordingController(output_dir=output_dir)

        assert controller.output_dir == output_dir


# ============================================================================
# Test: Start Recording
# ============================================================================


class TestRecordingControllerStart:
    """Tests for starting recording."""

    def test_start_recording_changes_state(self):
        """Test that start_recording changes state to RECORDING."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            controller = RecordingController()

            controller.start_recording()

            assert controller.state == AppState.RECORDING

    def test_start_recording_creates_recorder(self):
        """Test that start_recording creates a Recorder instance."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            controller = RecordingController()

            controller.start_recording()

            MockRecorder.assert_called_once()

    def test_start_recording_calls_recorder_start(self):
        """Test that start_recording calls recorder.start_recording()."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            mock_recorder = MagicMock()
            MockRecorder.return_value = mock_recorder

            controller = RecordingController()
            controller.start_recording()

            mock_recorder.start_recording.assert_called_once()

    def test_start_recording_tracks_start_time(self):
        """Test that start_recording records the start time."""
        with patch("recall.app.recording.Recorder"):
            controller = RecordingController()

            controller.start_recording()

            assert controller.recording_start_time is not None

    def test_start_recording_returns_status(self):
        """Test that start_recording returns RecordingStatus."""
        with patch("recall.app.recording.Recorder"):
            controller = RecordingController()

            status = controller.start_recording()

            assert isinstance(status, RecordingStatus)
            assert status.state == AppState.RECORDING


# ============================================================================
# Test: Stop Recording
# ============================================================================


class TestRecordingControllerStop:
    """Tests for stopping recording."""

    def test_stop_recording_changes_state_to_processing(self):
        """Test that stop_recording changes state to PROCESSING."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            mock_recorder = MagicMock()
            mock_recorder.stop_recording.return_value = Path("/tmp/audio.wav")
            MockRecorder.return_value = mock_recorder

            controller = RecordingController()
            controller.start_recording()
            controller.stop_recording()

            assert controller.state == AppState.PROCESSING

    def test_stop_recording_calls_recorder_stop(self):
        """Test that stop_recording calls recorder.stop_recording()."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            mock_recorder = MagicMock()
            mock_recorder.stop_recording.return_value = Path("/tmp/audio.wav")
            MockRecorder.return_value = mock_recorder

            controller = RecordingController()
            controller.start_recording()
            controller.stop_recording()

            mock_recorder.stop_recording.assert_called_once()

    def test_stop_recording_returns_audio_path(self):
        """Test that stop_recording returns the audio file path."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            mock_recorder = MagicMock()
            mock_recorder.stop_recording.return_value = Path("/tmp/audio.wav")
            MockRecorder.return_value = mock_recorder

            controller = RecordingController()
            controller.start_recording()
            status = controller.stop_recording()

            assert status.audio_path == Path("/tmp/audio.wav")

    def test_stop_recording_calculates_duration(self):
        """Test that stop_recording calculates recording duration."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            mock_recorder = MagicMock()
            mock_recorder.stop_recording.return_value = Path("/tmp/audio.wav")
            MockRecorder.return_value = mock_recorder

            controller = RecordingController()
            controller.start_recording()
            time.sleep(0.1)  # Small delay
            status = controller.stop_recording()

            assert status.duration_seconds >= 0


# ============================================================================
# Test: Recording Duration
# ============================================================================


class TestRecordingControllerDuration:
    """Tests for recording duration tracking."""

    def test_get_duration_returns_none_when_not_recording(self):
        """Test that get_duration returns None when not recording."""
        controller = RecordingController()

        assert controller.get_duration() is None

    def test_get_duration_returns_elapsed_time(self):
        """Test that get_duration returns elapsed time while recording."""
        with patch("recall.app.recording.Recorder"):
            controller = RecordingController()
            controller.start_recording()
            time.sleep(0.1)

            duration = controller.get_duration()

            assert duration is not None
            assert duration >= 0.1

    def test_get_formatted_duration(self):
        """Test that get_formatted_duration returns MM:SS format."""
        with patch("recall.app.recording.Recorder"):
            controller = RecordingController()
            controller.start_recording()
            controller._recording_start_time = time.time() - 65  # 1:05

            formatted = controller.get_formatted_duration()

            assert formatted == "01:05"


# ============================================================================
# Test: Process Recording
# ============================================================================


class TestRecordingControllerProcess:
    """Tests for processing recordings through the pipeline."""

    def test_process_recording_triggers_pipeline(self):
        """Test that process_recording triggers the ingestion pipeline."""
        with patch("recall.app.recording.ingest_audio") as mock_ingest:
            mock_ingest.return_value = MagicMock()

            controller = RecordingController()
            audio_path = Path("/tmp/audio.wav")

            controller.process_recording(audio_path)

            mock_ingest.assert_called_once()

    def test_process_recording_sets_idle_on_completion(self):
        """Test that process_recording sets state to IDLE on completion."""
        with patch("recall.app.recording.ingest_audio") as mock_ingest:
            mock_ingest.return_value = MagicMock()

            controller = RecordingController()
            controller._state = AppState.PROCESSING
            audio_path = Path("/tmp/audio.wav")

            controller.process_recording(audio_path)

            assert controller.state == AppState.IDLE

    def test_process_recording_with_callback(self):
        """Test that process_recording calls completion callback."""
        with patch("recall.app.recording.ingest_audio") as mock_ingest:
            mock_recording = MagicMock()
            mock_ingest.return_value = mock_recording

            callback = MagicMock()
            controller = RecordingController()
            audio_path = Path("/tmp/audio.wav")

            controller.process_recording(audio_path, on_complete=callback)

            callback.assert_called_once_with(mock_recording)


# ============================================================================
# Test: Error Handling
# ============================================================================


class TestRecordingControllerErrors:
    """Tests for error handling in RecordingController."""

    def test_start_recording_handles_device_error(self):
        """Test that start_recording handles device not found."""
        with patch("recall.app.recording.Recorder") as MockRecorder:
            from recall.capture.recorder import DeviceNotFoundError

            MockRecorder.side_effect = DeviceNotFoundError("No microphone")

            controller = RecordingController()
            status = controller.start_recording()

            assert status.error is not None
            assert controller.state == AppState.IDLE

    def test_stop_recording_handles_no_active_recording(self):
        """Test that stop_recording handles no active recording."""
        controller = RecordingController()

        status = controller.stop_recording()

        assert status.error is not None
        assert "No active recording" in status.error


# ============================================================================
# Test: Integration with MenuBar
# ============================================================================


class TestRecordingControllerMenuBarIntegration:
    """Tests for integration between RecordingController and RecallMenuBar."""

    def test_menubar_uses_recording_controller(self):
        """Test that RecallMenuBar uses RecordingController."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            assert hasattr(app, "recording_controller")
            assert isinstance(app.recording_controller, RecordingController)

    def test_menubar_start_recording_delegates_to_controller(self):
        """Test that menubar start_recording delegates to controller."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                app.on_start_recording(None)

                assert app.recording_controller.state == AppState.RECORDING
