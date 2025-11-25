"""Tests for Markdown storage (Ticket 1.2).

Tests cover:
- save_recording() creates proper Markdown file with YAML frontmatter
- load_recording() parses frontmatter and transcript correctly
- list_recordings() returns all .md files sorted chronologically
- Directory structure follows YYYY-MM pattern
- Error handling for malformed files
- Round-trip save/load preserves all data
"""

from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time


class TestSaveRecording:
    """Test save_recording() function."""

    @freeze_time("2025-11-25 14:30:00")
    def test_save_recording_creates_file_with_frontmatter(self, temp_storage_dir):
        """Test that save_recording creates a Markdown file with YAML frontmatter."""
        from recall.storage.markdown import save_recording
        from recall.storage.models import Recording

        recording = Recording(
            id="test-save-123",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 14, 30),
            transcript="This is the meeting transcript.",
            duration_seconds=3600,
            summary="Summary of the meeting.",
        )

        filepath = save_recording(recording, temp_storage_dir)

        assert filepath.exists()
        content = filepath.read_text()
        # Check frontmatter delimiters
        assert content.startswith("---\n")
        assert "\n---\n" in content
        # Check key fields are in frontmatter
        assert "id: test-save-123" in content
        assert "source: zoom" in content
        assert "duration_seconds: 3600" in content
        # Check transcript is in body (after second ---)
        parts = content.split("---")
        body = parts[2].strip()
        assert "This is the meeting transcript." in body

    def test_save_recording_creates_date_directory(self, temp_storage_dir):
        """Test that save_recording creates YYYY-MM directory structure."""
        from recall.storage.markdown import save_recording
        from recall.storage.models import Recording

        recording = Recording(
            id="date-dir-test",
            source="microphone",
            timestamp=datetime(2025, 3, 15, 9, 0),
            transcript="March recording.",
        )

        filepath = save_recording(recording, temp_storage_dir)

        # Should be in YYYY-MM subdirectory
        assert filepath.parent.name == "2025-03"
        assert filepath.parent.parent == temp_storage_dir

    def test_save_recording_filename_format(self, temp_storage_dir):
        """Test that save_recording uses correct filename format."""
        from recall.storage.markdown import save_recording
        from recall.storage.models import Recording

        recording = Recording(
            id="filename-test",
            source="youtube",
            timestamp=datetime(2025, 11, 25, 10, 45, 30),
            transcript="YouTube video transcript.",
        )

        filepath = save_recording(recording, temp_storage_dir)

        # Filename should be: {timestamp}_{source}.md
        assert filepath.name == "20251125_104530_youtube.md"
        assert filepath.suffix == ".md"

    def test_save_recording_all_fields_in_frontmatter(self, temp_storage_dir):
        """Test that all fields are properly serialized to frontmatter."""
        from recall.storage.markdown import save_recording
        from recall.storage.models import Recording

        recording = Recording(
            id="full-fields-test",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 14, 0),
            duration_seconds=1800,
            transcript="Full transcript here.",
            summary="Meeting summary.",
            participants=["Alice", "Bob"],
            tags=["meeting", "q4"],
            source_url=None,  # Should be excluded
            audio_path=Path("/audio/meeting.wav"),
        )

        filepath = save_recording(recording, temp_storage_dir)
        content = filepath.read_text()

        # All non-None fields should be present
        assert "id: full-fields-test" in content
        assert "source: zoom" in content
        assert "duration_seconds: 1800" in content
        assert "summary: Meeting summary." in content
        assert "Alice" in content
        assert "Bob" in content
        assert "meeting" in content
        assert "q4" in content
        assert "audio_path:" in content
        assert "/audio/meeting.wav" in content
        # source_url should NOT be present (it's None)
        assert "source_url" not in content


class TestLoadRecording:
    """Test load_recording() function."""

    def test_load_recording_parses_frontmatter(self, temp_storage_dir):
        """Test that load_recording correctly parses YAML frontmatter."""
        from recall.storage.markdown import load_recording

        # Create a sample Markdown file
        md_content = """---
id: load-test-123
source: zoom
timestamp: '2025-11-25T14:30:00'
duration_seconds: 3600
summary: Test meeting summary.
participants:
  - Alice
  - Bob
tags:
  - meeting
  - test
---

This is the transcript content from the meeting.
It has multiple lines.
"""
        md_file = temp_storage_dir / "2025-11" / "test.md"
        md_file.parent.mkdir(parents=True, exist_ok=True)
        md_file.write_text(md_content)

        recording = load_recording(md_file)

        assert recording.id == "load-test-123"
        assert recording.source == "zoom"
        assert recording.timestamp == datetime(2025, 11, 25, 14, 30)
        assert recording.duration_seconds == 3600
        assert recording.summary == "Test meeting summary."
        assert recording.participants == ["Alice", "Bob"]
        assert recording.tags == ["meeting", "test"]
        assert "transcript content" in recording.transcript

    def test_load_recording_handles_minimal_frontmatter(self, temp_storage_dir):
        """Test that load_recording handles files with minimal frontmatter."""
        from recall.storage.markdown import load_recording

        md_content = """---
id: minimal-test
source: note
timestamp: '2025-11-25T08:00:00'
---

Just a simple note.
"""
        md_file = temp_storage_dir / "minimal.md"
        md_file.write_text(md_content)

        recording = load_recording(md_file)

        assert recording.id == "minimal-test"
        assert recording.source == "note"
        assert recording.transcript == "Just a simple note."
        assert recording.duration_seconds is None
        assert recording.summary is None
        assert recording.tags == []

    def test_load_recording_raises_for_missing_file(self, temp_storage_dir):
        """Test that load_recording raises FileNotFoundError for missing files."""
        from recall.storage.markdown import load_recording

        nonexistent = temp_storage_dir / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            load_recording(nonexistent)

    def test_load_recording_raises_for_malformed_frontmatter(self, temp_storage_dir):
        """Test that load_recording raises ValueError for malformed files."""
        from recall.storage.markdown import load_recording

        # Missing frontmatter delimiters
        md_content = """No frontmatter here, just plain text."""
        md_file = temp_storage_dir / "malformed.md"
        md_file.write_text(md_content)

        with pytest.raises(ValueError) as exc_info:
            load_recording(md_file)

        assert "frontmatter" in str(exc_info.value).lower()

    def test_load_recording_raises_for_invalid_yaml(self, temp_storage_dir):
        """Test that load_recording raises ValueError for invalid YAML."""
        from recall.storage.markdown import load_recording

        md_content = """---
id: bad-yaml
source: [this is not valid
timestamp: also broken
---

Some content.
"""
        md_file = temp_storage_dir / "bad_yaml.md"
        md_file.write_text(md_content)

        with pytest.raises(ValueError):
            load_recording(md_file)


class TestListRecordings:
    """Test list_recordings() function."""

    def test_list_recordings_returns_all_markdown_files(self, temp_storage_dir):
        """Test that list_recordings finds all .md files recursively."""
        from recall.storage.markdown import list_recordings

        # Create several files in different directories
        (temp_storage_dir / "2025-01").mkdir()
        (temp_storage_dir / "2025-01" / "recording1.md").write_text("content1")
        (temp_storage_dir / "2025-01" / "recording2.md").write_text("content2")
        (temp_storage_dir / "2025-02").mkdir()
        (temp_storage_dir / "2025-02" / "recording3.md").write_text("content3")

        recordings = list_recordings(temp_storage_dir)

        assert len(recordings) == 3
        filenames = [p.name for p in recordings]
        assert "recording1.md" in filenames
        assert "recording2.md" in filenames
        assert "recording3.md" in filenames

    def test_list_recordings_sorted_chronologically(self, temp_storage_dir):
        """Test that list_recordings returns files sorted by filename."""
        from recall.storage.markdown import list_recordings

        # Create files with timestamp-based names
        (temp_storage_dir / "2025-01").mkdir()
        (temp_storage_dir / "2025-01" / "20250115_100000_zoom.md").write_text("a")
        (temp_storage_dir / "2025-01" / "20250101_090000_mic.md").write_text("b")
        (temp_storage_dir / "2025-02").mkdir()
        (temp_storage_dir / "2025-02" / "20250210_140000_note.md").write_text("c")

        recordings = list_recordings(temp_storage_dir)

        # Should be sorted: Jan 1 < Jan 15 < Feb 10
        assert recordings[0].name == "20250101_090000_mic.md"
        assert recordings[1].name == "20250115_100000_zoom.md"
        assert recordings[2].name == "20250210_140000_note.md"

    def test_list_recordings_ignores_non_markdown_files(self, temp_storage_dir):
        """Test that list_recordings ignores non-.md files."""
        from recall.storage.markdown import list_recordings

        (temp_storage_dir / "recording.md").write_text("valid")
        (temp_storage_dir / "audio.wav").write_text("ignored")
        (temp_storage_dir / "notes.txt").write_text("ignored")
        (temp_storage_dir / "index.db").write_text("ignored")

        recordings = list_recordings(temp_storage_dir)

        assert len(recordings) == 1
        assert recordings[0].name == "recording.md"

    def test_list_recordings_empty_directory(self, temp_storage_dir):
        """Test that list_recordings returns empty list for empty directory."""
        from recall.storage.markdown import list_recordings

        recordings = list_recordings(temp_storage_dir)

        assert recordings == []


class TestSaveLoadRoundTrip:
    """Test that save and load produce consistent results."""

    def test_round_trip_preserves_all_data(self, temp_storage_dir):
        """Test that saving then loading a recording preserves all fields."""
        from recall.storage.markdown import load_recording, save_recording
        from recall.storage.models import Recording

        original = Recording(
            id="round-trip-test",
            source="youtube",
            timestamp=datetime(2025, 11, 25, 16, 0),
            duration_seconds=1200,
            transcript="Full video transcript with multiple sentences. This is the second line.",
            summary="Video about Python programming.",
            participants=["Speaker One"],
            tags=["python", "tutorial"],
            source_url="https://youtube.com/watch?v=test123",
            audio_path=Path("/audio/youtube_test.wav"),
        )

        # Save
        filepath = save_recording(original, temp_storage_dir)

        # Load
        loaded = load_recording(filepath)

        # Compare all fields
        assert loaded.id == original.id
        assert loaded.source == original.source
        assert loaded.timestamp == original.timestamp
        assert loaded.duration_seconds == original.duration_seconds
        assert loaded.transcript.strip() == original.transcript.strip()
        assert loaded.summary == original.summary
        assert loaded.participants == original.participants
        assert loaded.tags == original.tags
        assert loaded.source_url == original.source_url
        assert loaded.audio_path == original.audio_path

    def test_round_trip_with_multiline_transcript(self, temp_storage_dir):
        """Test round-trip with multiline transcript content."""
        from recall.storage.markdown import load_recording, save_recording
        from recall.storage.models import Recording

        multiline_transcript = """First paragraph of the transcript.
It continues on multiple lines.

Second paragraph with more content.
And even more details here.

## A Markdown Heading

- Bullet point one
- Bullet point two
"""

        original = Recording(
            id="multiline-test",
            source="note",
            timestamp=datetime(2025, 11, 25, 12, 0),
            transcript=multiline_transcript,
        )

        filepath = save_recording(original, temp_storage_dir)
        loaded = load_recording(filepath)

        # Transcript should be preserved (maybe with minor whitespace changes)
        assert "First paragraph" in loaded.transcript
        assert "Second paragraph" in loaded.transcript
        assert "## A Markdown Heading" in loaded.transcript
        assert "Bullet point one" in loaded.transcript
