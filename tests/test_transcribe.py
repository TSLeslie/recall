"""Tests for transcription functionality."""

import pytest
from pathlib import Path
from recall.transcribe import transcribe


def test_transcribe_file_not_found():
    """Test that transcribe raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        transcribe("nonexistent_audio.mp3")


def test_transcribe_invalid_model():
    """Test that invalid model names are handled."""
    # This test would need a sample audio file
    # For now, it's a placeholder
    pass


# Add more tests as needed with actual audio files
