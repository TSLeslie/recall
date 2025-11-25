"""Tests for Text Quick Notes (Ticket 5.1).

TDD tests for src/recall/notes/quick_note.py covering:
- create_note() - create text notes
- append_to_note() - add content to existing notes
- list_notes() - retrieve all notes
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

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
def mock_llm():
    """Mock LLM for summary generation."""
    with patch("recall.notes.quick_note.LlamaAnalyzer") as mock:
        mock_instance = MagicMock()
        mock_instance.generate_summary.return_value = MagicMock(
            brief="A quick note about testing.",
            key_points=["Testing is important"],
            action_items=[],
            participants=[],
            topics=["testing"],
        )
        mock.return_value = mock_instance
        yield mock_instance


# ============================================================================
# Test: create_note()
# ============================================================================


class TestCreateNote:
    """Tests for the create_note function."""

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_returns_recording(self, notes_dir, mock_llm):
        """Test that create_note returns a Recording instance."""
        from recall.notes.quick_note import create_note

        result = create_note(
            content="This is a test note about TDD.",
            base_dir=notes_dir,
        )

        # Should return a Recording
        from recall.storage.models import Recording

        assert isinstance(result, Recording)

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_sets_source_to_note(self, notes_dir, mock_llm):
        """Test that created notes have source='note'."""
        from recall.notes.quick_note import create_note

        result = create_note(
            content="My quick note.",
            base_dir=notes_dir,
        )

        assert result.source == "note"

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_saves_transcript(self, notes_dir, mock_llm):
        """Test that note content is saved as transcript."""
        from recall.notes.quick_note import create_note

        content = "This is the full content of my note."
        result = create_note(content=content, base_dir=notes_dir)

        assert result.transcript == content

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_with_tags(self, notes_dir, mock_llm):
        """Test that tags are preserved on the note."""
        from recall.notes.quick_note import create_note

        tags = ["work", "important", "meeting-notes"]
        result = create_note(
            content="Note with tags.",
            tags=tags,
            base_dir=notes_dir,
        )

        assert result.tags == tags

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_generates_uuid(self, notes_dir, mock_llm):
        """Test that each note gets a unique ID."""
        from recall.notes.quick_note import create_note

        note1 = create_note(content="First note", base_dir=notes_dir)
        note2 = create_note(content="Second note", base_dir=notes_dir)

        assert note1.id != note2.id
        # UUID format check
        assert len(note1.id) == 36  # Standard UUID length

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_sets_timestamp(self, notes_dir, mock_llm):
        """Test that timestamp is set to creation time."""
        from recall.notes.quick_note import create_note

        result = create_note(content="Timestamped note", base_dir=notes_dir)

        assert result.timestamp == datetime(2025, 11, 25, 14, 30, 0)

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_saves_to_file(self, notes_dir, mock_llm):
        """Test that note is saved as Markdown file."""
        from recall.notes.quick_note import create_note

        result = create_note(content="Note to save", base_dir=notes_dir)

        # Check file was created in YYYY-MM subdirectory
        expected_dir = notes_dir / "2025-11"
        assert expected_dir.exists()

        # Check file naming convention: {timestamp}_note.md
        md_files = list(expected_dir.glob("*.md"))
        assert len(md_files) == 1
        assert "_note.md" in md_files[0].name

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_file_contains_content(self, notes_dir, mock_llm):
        """Test that saved file contains the note content."""
        from recall.notes.quick_note import create_note

        content = "Important content to persist."
        create_note(content=content, base_dir=notes_dir)

        # Read the saved file
        md_files = list(notes_dir.rglob("*.md"))
        assert len(md_files) == 1

        file_content = md_files[0].read_text()
        assert content in file_content

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_generates_summary_for_long_content(self, notes_dir, mock_llm):
        """Test that summary is generated for content over 100 chars."""
        from recall.notes.quick_note import create_note

        long_content = "This is a very long note. " * 20  # Well over 100 chars
        result = create_note(content=long_content, base_dir=notes_dir)

        # LLM should have been called to generate summary
        mock_llm.generate_summary.assert_called_once()
        assert result.summary is not None

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_uses_first_100_chars_for_short_content(self, notes_dir, mock_llm):
        """Test that short notes use truncated content as summary."""
        from recall.notes.quick_note import create_note

        short_content = "Short note."  # Under 100 chars
        result = create_note(content=short_content, base_dir=notes_dir)

        # LLM should NOT be called for short content
        mock_llm.generate_summary.assert_not_called()
        # Summary should be the content itself (or first 100 chars)
        assert result.summary == short_content

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_with_title(self, notes_dir, mock_llm):
        """Test that optional title is preserved."""
        from recall.notes.quick_note import create_note

        result = create_note(
            content="Note with title",
            title="My Important Note",
            base_dir=notes_dir,
        )

        assert result.title == "My Important Note"


# ============================================================================
# Test: append_to_note()
# ============================================================================


class TestAppendToNote:
    """Tests for the append_to_note function."""

    @freeze_time("2025-11-25 14:30:00")
    def test_append_to_note_adds_content(self, notes_dir, mock_llm):
        """Test that append_to_note adds content to existing note."""
        from recall.notes.quick_note import append_to_note, create_note

        # Create initial note
        note = create_note(content="Initial content.", base_dir=notes_dir)

        # Get the filepath
        md_files = list(notes_dir.rglob("*.md"))
        filepath = md_files[0]

        # Append content
        updated = append_to_note(filepath=filepath, content="\n\nAppended content.")

        assert "Initial content." in updated.transcript
        assert "Appended content." in updated.transcript

    @freeze_time("2025-11-25 14:30:00")
    def test_append_to_note_preserves_metadata(self, notes_dir, mock_llm):
        """Test that appending preserves original metadata."""
        from recall.notes.quick_note import append_to_note, create_note

        # Create note with tags
        note = create_note(
            content="Original content.",
            tags=["important"],
            base_dir=notes_dir,
        )
        original_id = note.id
        original_timestamp = note.timestamp

        md_files = list(notes_dir.rglob("*.md"))
        filepath = md_files[0]

        # Append
        updated = append_to_note(filepath=filepath, content="\nMore content.")

        # ID and timestamp should be preserved
        assert updated.id == original_id
        assert updated.timestamp == original_timestamp
        assert updated.tags == ["important"]

    def test_append_to_note_raises_for_missing_file(self, notes_dir):
        """Test that append_to_note raises for non-existent file."""
        from recall.notes.quick_note import append_to_note

        with pytest.raises(FileNotFoundError):
            append_to_note(
                filepath=notes_dir / "nonexistent.md",
                content="Content to append",
            )

    @freeze_time("2025-11-25 14:30:00")
    def test_append_to_note_updates_file(self, notes_dir, mock_llm):
        """Test that the file is updated with appended content."""
        from recall.notes.quick_note import append_to_note, create_note

        create_note(content="Original.", base_dir=notes_dir)
        md_files = list(notes_dir.rglob("*.md"))
        filepath = md_files[0]

        append_to_note(filepath=filepath, content="\nAddition.")

        # Read file and verify
        file_content = filepath.read_text()
        assert "Original." in file_content
        assert "Addition." in file_content


# ============================================================================
# Test: list_notes()
# ============================================================================


class TestListNotes:
    """Tests for the list_notes function."""

    def test_list_notes_returns_all_notes(self, notes_dir, mock_llm):
        """Test that list_notes returns all notes in directory."""
        from recall.notes.quick_note import create_note, list_notes

        # Create multiple notes with different timestamps
        with freeze_time("2025-11-25 14:30:00"):
            create_note(content="First note", base_dir=notes_dir)
        with freeze_time("2025-11-25 14:31:00"):
            create_note(content="Second note", base_dir=notes_dir)
        with freeze_time("2025-11-25 14:32:00"):
            create_note(content="Third note", base_dir=notes_dir)

        notes = list_notes(base_dir=notes_dir)

        assert len(notes) == 3

    def test_list_notes_empty_directory(self, notes_dir):
        """Test that list_notes returns empty list for empty dir."""
        from recall.notes.quick_note import list_notes

        notes = list_notes(base_dir=notes_dir)

        assert notes == []

    @freeze_time("2025-11-25 14:30:00")
    def test_list_notes_returns_recording_objects(self, notes_dir, mock_llm):
        """Test that list_notes returns Recording objects."""
        from recall.notes.quick_note import create_note, list_notes
        from recall.storage.models import Recording

        create_note(content="A note", base_dir=notes_dir)

        notes = list_notes(base_dir=notes_dir)

        assert all(isinstance(n, Recording) for n in notes)

    def test_list_notes_sorted_chronologically(self, notes_dir, mock_llm):
        """Test that notes are sorted by timestamp (newest first)."""
        from recall.notes.quick_note import create_note, list_notes

        # Create notes with different timestamps
        with freeze_time("2025-11-25 14:30:00"):
            create_note(content="First", base_dir=notes_dir)
        with freeze_time("2025-11-25 14:31:00"):
            create_note(content="Second", base_dir=notes_dir)
        with freeze_time("2025-11-25 14:32:00"):
            create_note(content="Third", base_dir=notes_dir)

        notes = list_notes(base_dir=notes_dir)

        # Should be sorted by timestamp (newest first)
        assert len(notes) == 3
        # Verify order - newest first
        assert notes[0].transcript == "Third"
        assert notes[1].transcript == "Second"
        assert notes[2].transcript == "First"

    def test_list_notes_nonexistent_directory(self, tmp_path):
        """Test that list_notes handles non-existent directory."""
        from recall.notes.quick_note import list_notes

        notes = list_notes(base_dir=tmp_path / "nonexistent")

        assert notes == []


# ============================================================================
# Test: Notes are indexed
# ============================================================================


class TestNotesIndexed:
    """Tests for notes being searchable."""

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_indexes_in_sqlite(self, notes_dir, mock_llm):
        """Test that created notes are added to SQLite index."""
        from recall.notes.quick_note import create_note

        with patch("recall.notes.quick_note.RecordingIndex") as mock_index_class:
            mock_index = MagicMock()
            mock_index_class.return_value = mock_index

            note = create_note(
                content="Indexed note content",
                base_dir=notes_dir,
                index_db=notes_dir / "test_index.db",
            )

            # Index should have been called
            mock_index.add_recording.assert_called_once()

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_without_indexing(self, notes_dir, mock_llm):
        """Test that indexing can be disabled."""
        from recall.notes.quick_note import create_note

        # Should not raise when index_db is None
        note = create_note(
            content="Non-indexed note",
            base_dir=notes_dir,
            index_db=None,
        )

        assert note.transcript == "Non-indexed note"
