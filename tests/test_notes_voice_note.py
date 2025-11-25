"""Tests for Voice Quick Notes (Ticket 5.2).

TDD tests for src/recall/notes/voice_note.py covering:
- record_voice_note() - record and transcribe voice notes
- start_voice_note() / stop_voice_note() - variable length voice notes
- Audio file retention options
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from freezegun import freeze_time

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def notes_dir(tmp_path):
    """Create a temporary notes directory."""
    notes_path = tmp_path / "notes"
    notes_path.mkdir()
    return notes_path


@pytest.fixture
def mock_recorder():
    """Mock the Recorder class for audio capture."""
    with patch("recall.notes.voice_note.Recorder") as mock:
        mock_instance = MagicMock()
        mock_instance.is_recording = False

        # Setup for fixed-duration recording
        def mock_record(duration_seconds):
            audio_path = Path("/tmp/test_recording.wav")
            return audio_path

        mock_instance.record.side_effect = mock_record

        # Setup for start/stop recording
        mock_instance.start_recording.return_value = None
        mock_instance.stop_recording.return_value = Path("/tmp/test_recording.wav")

        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_transcribe():
    """Mock Whisper transcription."""
    with patch("recall.notes.voice_note.transcribe") as mock:
        mock.return_value = {
            "text": "This is a transcribed voice note.",
            "language": "en",
            "segments": [{"start": 0.0, "end": 2.5, "text": "This is a transcribed voice note."}],
        }
        yield mock


@pytest.fixture
def mock_llm():
    """Mock LLM for summary generation."""
    with patch("recall.notes.voice_note.LlamaAnalyzer") as mock:
        mock_instance = MagicMock()
        mock_instance.generate_summary.return_value = MagicMock(
            brief="Voice note about testing.",
            key_points=["Testing voice notes"],
            action_items=[],
            participants=[],
            topics=["voice", "testing"],
        )
        mock.return_value = mock_instance
        yield mock_instance


# ============================================================================
# Test: record_voice_note()
# ============================================================================


class TestRecordVoiceNote:
    """Tests for the record_voice_note function."""

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_returns_recording(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that record_voice_note returns a Recording instance."""
        from recall.notes.voice_note import record_voice_note
        from recall.storage.models import Recording

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
        )

        assert isinstance(result, Recording)

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_sets_source_to_note(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that voice notes have source='note'."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
        )

        # Voice notes should also use source="note" for consistency
        assert result.source == "note"

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_transcribes_audio(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that audio is transcribed using Whisper."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
        )

        # Transcribe should have been called
        mock_transcribe.assert_called_once()
        assert result.transcript == "This is a transcribed voice note."

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_generates_summary(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that summary is generated from transcription."""
        from recall.notes.voice_note import record_voice_note

        # Make transcript long enough to trigger LLM summarization
        mock_transcribe.return_value["text"] = "A" * 200

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
        )

        # LLM should have been called for summary
        mock_llm.generate_summary.assert_called_once()

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_saves_to_file(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that voice note is saved as Markdown file."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
        )

        # Check file was created
        expected_dir = notes_dir / "2025-11"
        assert expected_dir.exists()

        md_files = list(expected_dir.glob("*.md"))
        assert len(md_files) == 1

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_default_duration(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that default duration is 60 seconds."""
        from recall.notes.voice_note import record_voice_note

        record_voice_note(base_dir=notes_dir)

        # Should have recorded for 60 seconds (default)
        mock_recorder.record.assert_called_once_with(duration_seconds=60)

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_custom_duration(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that custom duration is respected."""
        from recall.notes.voice_note import record_voice_note

        record_voice_note(duration_seconds=30, base_dir=notes_dir)

        mock_recorder.record.assert_called_once_with(duration_seconds=30)

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_retains_audio_when_requested(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that audio file path is saved when retain_audio=True."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
            retain_audio=True,
        )

        # audio_path should be set
        assert result.audio_path is not None

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_deletes_audio_by_default(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that audio is deleted when retain_audio=False (default)."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
            retain_audio=False,
        )

        # audio_path should be None (not retained)
        assert result.audio_path is None

    @freeze_time("2025-11-25 14:30:00")
    def test_record_voice_note_whisper_model_configurable(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that Whisper model can be configured."""
        from recall.notes.voice_note import record_voice_note

        record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
            whisper_model="small",
        )

        # Transcribe should have been called with the specified model
        call_args = mock_transcribe.call_args
        assert call_args.kwargs.get("model") == "small" or call_args.args[1] == "small"


# ============================================================================
# Test: start_voice_note() / stop_voice_note()
# ============================================================================


class TestStartStopVoiceNote:
    """Tests for variable-length voice note recording."""

    @freeze_time("2025-11-25 14:30:00")
    def test_start_voice_note_begins_recording(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that start_voice_note begins microphone recording."""
        from recall.notes.voice_note import start_voice_note

        start_voice_note(base_dir=notes_dir)

        mock_recorder.start_recording.assert_called_once()

    @freeze_time("2025-11-25 14:30:00")
    def test_stop_voice_note_returns_recording(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that stop_voice_note returns a Recording."""
        from recall.notes.voice_note import start_voice_note, stop_voice_note
        from recall.storage.models import Recording

        start_voice_note(base_dir=notes_dir)
        result = stop_voice_note()

        assert isinstance(result, Recording)

    @freeze_time("2025-11-25 14:30:00")
    def test_stop_voice_note_transcribes_audio(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that stop_voice_note transcribes the recorded audio."""
        from recall.notes.voice_note import start_voice_note, stop_voice_note

        start_voice_note(base_dir=notes_dir)
        result = stop_voice_note()

        mock_transcribe.assert_called_once()
        assert result.transcript == "This is a transcribed voice note."

    @freeze_time("2025-11-25 14:30:00")
    def test_stop_voice_note_saves_to_file(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that stop_voice_note saves the note as Markdown."""
        from recall.notes.voice_note import start_voice_note, stop_voice_note

        start_voice_note(base_dir=notes_dir)
        stop_voice_note()

        # Check file was created
        expected_dir = notes_dir / "2025-11"
        assert expected_dir.exists()

        md_files = list(expected_dir.glob("*.md"))
        assert len(md_files) == 1

    def test_stop_voice_note_raises_when_not_recording(
        self, notes_dir, mock_recorder, mock_transcribe
    ):
        """Test that stop_voice_note raises error if not recording."""
        from recall.notes.voice_note import VoiceNoteError, stop_voice_note

        with pytest.raises(VoiceNoteError):
            stop_voice_note()


# ============================================================================
# Test: Voice notes saved to correct location
# ============================================================================


class TestVoiceNoteStorage:
    """Tests for voice note file storage."""

    @freeze_time("2025-11-25 14:30:00")
    def test_voice_note_saved_to_notes_directory(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that voice notes are saved to ~/.recall/notes/ structure."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
        )

        # Should be in YYYY-MM subdirectory
        expected_dir = notes_dir / "2025-11"
        md_files = list(expected_dir.glob("*.md"))
        assert len(md_files) == 1
        assert "_note.md" in md_files[0].name

    @freeze_time("2025-11-25 14:30:00")
    def test_voice_note_file_contains_transcript(
        self, notes_dir, mock_recorder, mock_transcribe, mock_llm
    ):
        """Test that saved file contains the transcription."""
        from recall.notes.voice_note import record_voice_note

        record_voice_note(duration_seconds=10, base_dir=notes_dir)

        md_files = list(notes_dir.rglob("*.md"))
        assert len(md_files) == 1

        file_content = md_files[0].read_text()
        assert "This is a transcribed voice note." in file_content

    @freeze_time("2025-11-25 14:30:00")
    def test_voice_note_with_tags(self, notes_dir, mock_recorder, mock_transcribe, mock_llm):
        """Test that tags can be added to voice notes."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=10,
            base_dir=notes_dir,
            tags=["voice", "meeting"],
        )

        assert result.tags == ["voice", "meeting"]

    @freeze_time("2025-11-25 14:30:00")
    def test_voice_note_duration_stored(self, notes_dir, mock_recorder, mock_transcribe, mock_llm):
        """Test that recording duration is stored in the note."""
        from recall.notes.voice_note import record_voice_note

        result = record_voice_note(
            duration_seconds=45,
            base_dir=notes_dir,
        )

        assert result.duration_seconds == 45
