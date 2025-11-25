"""Recording Controller for Menu Bar App.

This module provides the recording functionality for the menu bar app,
integrating with the audio capture and ingestion pipeline.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from recall.app.menubar import AppState
from recall.capture.recorder import DeviceNotFoundError, Recorder
from recall.pipeline.ingest import ingest_audio


@dataclass
class RecordingStatus:
    """Status of a recording operation.

    Attributes:
        state: Current application state
        duration_seconds: Duration of recording in seconds
        message: Optional status message
        error: Optional error message
        audio_path: Path to recorded audio file (after stopping)
    """

    state: AppState
    duration_seconds: float = 0
    message: Optional[str] = None
    error: Optional[str] = None
    audio_path: Optional[Path] = None


class RecordingController:
    """Controller for managing recording operations.

    This class handles the recording lifecycle:
    - Starting/stopping recordings
    - Tracking duration
    - Processing through the ingestion pipeline

    Attributes:
        state: Current recording state
        output_dir: Directory for saving recordings
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize the recording controller.

        Args:
            output_dir: Directory for saving recordings.
                       Defaults to ~/.recall/recordings/
        """
        self.output_dir = output_dir or Path.home() / ".recall" / "recordings"
        self._state = AppState.IDLE
        self._recorder: Optional[Recorder] = None
        self._recording_start_time: Optional[float] = None

    @property
    def state(self) -> AppState:
        """Get the current recording state."""
        return self._state

    @property
    def active_recording(self) -> Optional[Recorder]:
        """Get the active recorder, if any."""
        return self._recorder

    @property
    def recording_start_time(self) -> Optional[float]:
        """Get the recording start timestamp."""
        return self._recording_start_time

    def start_recording(self) -> RecordingStatus:
        """Start a new recording.

        Returns:
            RecordingStatus with current state.
        """
        try:
            # Create recorder
            self._recorder = Recorder(output_dir=self.output_dir)
            self._recorder.start_recording()

            # Update state
            self._state = AppState.RECORDING
            self._recording_start_time = time.time()

            return RecordingStatus(
                state=self._state,
                duration_seconds=0,
                message="Recording started",
            )

        except DeviceNotFoundError as e:
            self._state = AppState.IDLE
            return RecordingStatus(
                state=self._state,
                duration_seconds=0,
                error=str(e),
            )
        except Exception as e:
            self._state = AppState.IDLE
            return RecordingStatus(
                state=self._state,
                duration_seconds=0,
                error=f"Failed to start recording: {e}",
            )

    def stop_recording(self) -> RecordingStatus:
        """Stop the current recording.

        Returns:
            RecordingStatus with audio path and duration.
        """
        if self._recorder is None:
            return RecordingStatus(
                state=self._state,
                duration_seconds=0,
                error="No active recording to stop",
            )

        try:
            # Stop recorder
            audio_path = self._recorder.stop_recording()

            # Calculate duration
            duration = self.get_duration() or 0

            # Update state
            self._state = AppState.PROCESSING

            # Clean up
            self._recorder = None

            return RecordingStatus(
                state=self._state,
                duration_seconds=duration,
                audio_path=audio_path,
                message="Recording stopped, processing...",
            )

        except Exception as e:
            self._state = AppState.IDLE
            self._recorder = None
            return RecordingStatus(
                state=self._state,
                duration_seconds=0,
                error=f"Failed to stop recording: {e}",
            )

    def get_duration(self) -> Optional[float]:
        """Get the current recording duration in seconds.

        Returns:
            Duration in seconds, or None if not recording.
        """
        if self._recording_start_time is None:
            return None
        return time.time() - self._recording_start_time

    def get_formatted_duration(self) -> str:
        """Get the recording duration formatted as MM:SS.

        Returns:
            Formatted duration string.
        """
        duration = self.get_duration()
        if duration is None:
            return "00:00"

        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def process_recording(
        self,
        audio_path: Path,
        on_complete: Optional[Callable] = None,
    ) -> RecordingStatus:
        """Process a recording through the ingestion pipeline.

        Args:
            audio_path: Path to the audio file
            on_complete: Optional callback called with the Recording

        Returns:
            RecordingStatus with result.
        """
        try:
            # Run ingestion pipeline
            recording = ingest_audio(
                audio_path=audio_path,
                source="microphone",
            )

            # Update state
            self._state = AppState.IDLE
            self._recording_start_time = None

            # Call completion callback
            if on_complete:
                on_complete(recording)

            return RecordingStatus(
                state=self._state,
                duration_seconds=0,
                message=f"Recording saved: {recording.title if hasattr(recording, 'title') else 'Untitled'}",
            )

        except Exception as e:
            self._state = AppState.IDLE
            return RecordingStatus(
                state=self._state,
                duration_seconds=0,
                error=f"Failed to process recording: {e}",
            )
