"""Tests for progress callbacks (Ticket 3.2).

Tests cover:
- ProgressEvent model for reporting pipeline progress
- Progress callback in ingest_audio()
- Progress stages: transcribing, summarizing, saving
- Progress percentage reporting
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_transcribe(mocker):
    """Mock the transcribe function for pipeline tests."""
    mock = mocker.patch("recall.pipeline.ingest.transcribe")
    mock.return_value = {
        "text": "This is a test transcription from the meeting.",
        "segments": [{"start": 0.0, "end": 2.5, "text": "This is a test transcription."}],
        "language": "en",
    }
    return mock


@pytest.fixture
def mock_generate_summary(mocker):
    """Mock the generate_summary function for pipeline tests."""
    mock = mocker.patch("recall.pipeline.ingest.generate_summary")
    # Return a mock SummaryResult object
    mock_result = MagicMock()
    mock_result.brief = "Test meeting summary."
    mock_result.key_points = ["Point 1", "Point 2"]
    mock_result.action_items = ["Action 1"]
    mock_result.participants = []
    mock_result.topics = ["meeting"]
    mock.return_value = mock_result
    return mock


class TestProgressEvent:
    """Test ProgressEvent model."""

    def test_progress_event_has_required_fields(self):
        """Test that ProgressEvent has all required fields."""
        from recall.pipeline.progress import ProgressEvent

        event = ProgressEvent(
            stage="transcribing",
            progress=0.5,
            message="Processing audio...",
        )

        assert event.stage == "transcribing"
        assert event.progress == 0.5
        assert event.message == "Processing audio..."

    def test_progress_event_valid_stages(self):
        """Test that ProgressEvent accepts valid stages."""
        from recall.pipeline.progress import ProgressEvent

        valid_stages = ["starting", "transcribing", "summarizing", "saving", "completed"]
        for stage in valid_stages:
            event = ProgressEvent(stage=stage, progress=0.0, message="test")
            assert event.stage == stage

    def test_progress_event_progress_range(self):
        """Test that progress is between 0 and 1."""
        from recall.pipeline.progress import ProgressEvent

        event = ProgressEvent(stage="transcribing", progress=0.0, message="start")
        assert event.progress == 0.0

        event = ProgressEvent(stage="completed", progress=1.0, message="done")
        assert event.progress == 1.0

    def test_progress_event_optional_details(self):
        """Test that ProgressEvent accepts optional details."""
        from recall.pipeline.progress import ProgressEvent

        event = ProgressEvent(
            stage="transcribing",
            progress=0.5,
            message="Processing",
            details={"elapsed_seconds": 10, "eta_seconds": 10},
        )

        assert event.details is not None
        assert event.details["elapsed_seconds"] == 10


class TestIngestWithProgress:
    """Test ingest_audio() with progress callback."""

    def test_ingest_audio_accepts_progress_callback(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio accepts progress_callback parameter."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        # Should not raise
        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
        )

        # Should have received progress events
        assert len(progress_events) > 0

    def test_ingest_audio_reports_starting_event(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio reports starting event."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
        )

        stages = [e.stage for e in progress_events]
        assert "starting" in stages

    def test_ingest_audio_reports_transcribing_event(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio reports transcribing event."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
        )

        stages = [e.stage for e in progress_events]
        assert "transcribing" in stages

    def test_ingest_audio_reports_summarizing_event(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio reports summarizing event when not skipped."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
            skip_summary=False,
        )

        stages = [e.stage for e in progress_events]
        assert "summarizing" in stages

    def test_ingest_audio_skips_summarizing_event_when_skip_summary(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio skips summarizing event when skip_summary=True."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
            skip_summary=True,
        )

        stages = [e.stage for e in progress_events]
        assert "summarizing" not in stages

    def test_ingest_audio_reports_saving_event(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio reports saving event."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
        )

        stages = [e.stage for e in progress_events]
        assert "saving" in stages

    def test_ingest_audio_reports_completed_event(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio reports completed event."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
        )

        stages = [e.stage for e in progress_events]
        assert "completed" in stages
        # Completed should be the last event
        assert progress_events[-1].stage == "completed"
        assert progress_events[-1].progress == 1.0

    def test_ingest_audio_progress_increases(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that progress increases monotonically."""
        from recall.pipeline.ingest import ingest_audio

        progress_events = []

        def on_progress(event):
            progress_events.append(event)

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            progress_callback=on_progress,
        )

        progress_values = [e.progress for e in progress_events]
        # Progress should be non-decreasing
        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i - 1]

    def test_ingest_audio_works_without_progress_callback(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio still works without progress callback."""
        from recall.pipeline.ingest import ingest_audio

        # Should not raise
        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            # No progress_callback
        )

        assert result is not None
        assert result.transcript is not None
