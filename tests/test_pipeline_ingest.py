"""Tests for audio ingestion pipeline (Ticket 3.1).

Tests cover:
- ingest_audio() function orchestrating transcribe → summarize → save
- Integration with Whisper, LLM analysis, and Markdown storage
- Recording metadata population
- Error handling for pipeline failures
"""

from datetime import datetime
from pathlib import Path
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


class TestIngestAudio:
    """Test ingest_audio() function."""

    def test_ingest_audio_returns_recording(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio returns a Recording object."""
        from recall.pipeline.ingest import ingest_audio
        from recall.storage.models import Recording

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
        )

        assert isinstance(result, Recording)

    def test_ingest_audio_transcribes_audio(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio calls Whisper transcription."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
        )

        # Should have transcript from mocked Whisper
        assert result.transcript is not None
        assert len(result.transcript) > 0

    def test_ingest_audio_generates_summary(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio generates LLM summary."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
        )

        # Should have summary from mocked LLM
        assert result.summary is not None
        assert len(result.summary) > 0

    def test_ingest_audio_saves_recording(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio saves recording as Markdown file."""
        from recall.pipeline.ingest import ingest_audio

        ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
        )

        # Should have created a Markdown file
        md_files = list(temp_storage_dir.rglob("*.md"))
        assert len(md_files) >= 1

    def test_ingest_audio_sets_source(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio sets the correct source."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="youtube",
            storage_dir=temp_storage_dir,
        )

        assert result.source == "youtube"

    def test_ingest_audio_sets_timestamp(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio sets timestamp."""
        from recall.pipeline.ingest import ingest_audio

        before = datetime.now()
        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
        )
        after = datetime.now()

        assert before <= result.timestamp <= after


class TestIngestAudioMetadata:
    """Test metadata handling in ingest_audio."""

    def test_ingest_audio_accepts_title(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio accepts optional title."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            title="Test Meeting",
        )

        assert result.title == "Test Meeting"

    def test_ingest_audio_accepts_tags(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio accepts optional tags."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            tags=["meeting", "important"],
        )

        assert "meeting" in result.tags
        assert "important" in result.tags

    def test_ingest_audio_accepts_participants(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio accepts optional participants."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="zoom",
            storage_dir=temp_storage_dir,
            participants=["Alice", "Bob"],
        )

        assert "Alice" in result.participants
        assert "Bob" in result.participants

    def test_ingest_audio_calculates_duration(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingest_audio calculates audio duration."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
        )

        # Sample audio is 1 second
        assert result.duration_seconds > 0


class TestIngestAudioErrors:
    """Test error handling in ingest_audio."""

    def test_ingest_audio_missing_file_raises_error(
        self, temp_storage_dir, mock_transcribe, mock_generate_summary
    ):
        """Test that missing audio file raises error."""
        from recall.pipeline.ingest import IngestError, ingest_audio

        with pytest.raises(IngestError):
            ingest_audio(
                audio_path=Path("/nonexistent/audio.wav"),
                source="microphone",
                storage_dir=temp_storage_dir,
            )

    def test_ingest_audio_transcription_error_raises(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that transcription error raises IngestError."""
        from recall.pipeline.ingest import IngestError, ingest_audio

        # Make transcribe fail
        mock_transcribe.side_effect = Exception("Transcription failed")

        with pytest.raises(IngestError) as exc_info:
            ingest_audio(
                audio_path=sample_audio_path,
                source="microphone",
                storage_dir=temp_storage_dir,
            )

        assert "transcri" in str(exc_info.value).lower()


class TestIngestYouTube:
    """Test YouTube-specific ingestion."""

    def test_ingest_youtube_uses_video_title(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that YouTube ingest uses video title if provided."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="youtube",
            storage_dir=temp_storage_dir,
            title="YouTube Video Title",
        )

        assert result.title == "YouTube Video Title"


class TestIngestPipelineIntegration:
    """Test full pipeline integration."""

    def test_ingest_pipeline_creates_searchable_recording(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that ingested recording can be loaded back."""
        from recall.pipeline.ingest import ingest_audio
        from recall.storage.markdown import load_recording

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
        )

        # Find the saved file
        md_files = list(temp_storage_dir.rglob("*.md"))
        assert len(md_files) >= 1

        # Load it back
        loaded = load_recording(md_files[0])
        assert loaded.transcript == result.transcript
        assert loaded.source == result.source

    def test_ingest_skip_summary_option(
        self, temp_storage_dir, sample_audio_path, mock_transcribe, mock_generate_summary
    ):
        """Test that summary generation can be skipped."""
        from recall.pipeline.ingest import ingest_audio

        result = ingest_audio(
            audio_path=sample_audio_path,
            source="microphone",
            storage_dir=temp_storage_dir,
            skip_summary=True,
        )

        # Summary should be minimal or default
        assert result.summary in [None, "", "No summary generated"]
        # LLM should not have been called
        mock_generate_summary.assert_not_called()
