"""Tests for Notes Integration with Knowledge Base (Ticket 5.3).

TDD tests for integrating notes with GraphRAG:
- Notes automatically ingested on creation
- Notes searchable via ask() and search()
- Notes appear in query source references
- sync_knowledge_base includes notes directory
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

# Import modules BEFORE freeze_time is active to avoid datetime binary incompatibility
# See: https://github.com/spulec/freezegun/issues/493
from recall.knowledge.ingest import ingest_all
from recall.knowledge.sync import KnowledgeSync
from recall.notes.quick_note import append_to_note, create_note
from recall.storage.markdown import save_recording
from recall.storage.models import Recording

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
def mock_graphrag():
    """Mock RecallGraphRAG for testing."""
    from dataclasses import dataclass, field

    @dataclass
    class MockQueryResult:
        answer: str = "The note mentioned TDD testing practices."
        sources: list = field(default_factory=list)
        confidence: float = 0.85

    mock = MagicMock()
    mock.insert.return_value = None
    mock.query.return_value = MockQueryResult()
    return mock


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
# Test: Notes automatically ingested on creation
# ============================================================================


class TestNotesAutoIngest:
    """Tests for automatic note ingestion to GraphRAG."""

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_with_graphrag_ingests(self, notes_dir, mock_graphrag, mock_llm):
        """Test that create_note with graphrag parameter ingests the note."""
        note = create_note(
            content="This is a test note about TDD practices.",
            base_dir=notes_dir,
            graphrag=mock_graphrag,
        )

        # GraphRAG insert should have been called
        mock_graphrag.insert.assert_called()

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_ingest_includes_metadata(self, notes_dir, mock_graphrag, mock_llm):
        """Test that ingested note includes metadata."""
        note = create_note(
            content="Important note about the budget meeting.",
            tags=["meeting", "budget"],
            base_dir=notes_dir,
            graphrag=mock_graphrag,
        )

        # Check that insert was called with content containing metadata
        call_args = mock_graphrag.insert.call_args
        # The first positional argument should contain the note content
        inserted_text = call_args[0][0] if call_args[0] else call_args[1].get("text", "")
        assert "budget meeting" in inserted_text.lower()

    @freeze_time("2025-11-25 14:30:00")
    def test_create_note_without_graphrag_skips_ingest(self, notes_dir, mock_llm):
        """Test that create_note without graphrag doesn't try to ingest."""
        # Should not raise even without graphrag
        note = create_note(
            content="Note without knowledge base integration.",
            base_dir=notes_dir,
        )

        assert note.transcript == "Note without knowledge base integration."


# ============================================================================
# Test: Notes searchable via query
# ============================================================================


class TestNotesSearchable:
    """Tests for searching notes through knowledge base."""

    @freeze_time("2025-11-25 14:30:00")
    def test_ask_with_ingested_note(self, notes_dir, mock_graphrag, mock_llm):
        """Test that ask() works with a note that was ingested to graphrag."""
        # Create a note with specific content - this ingests to mock_graphrag
        create_note(
            content="The quarterly budget meeting discussed a 15% increase.",
            base_dir=notes_dir,
            graphrag=mock_graphrag,
        )

        # Verify insert was called (note was ingested)
        mock_graphrag.insert.assert_called()

        # The ask() function would use mock_graphrag.query() which is mocked
        # We just verify the note was properly ingested
        call_args = mock_graphrag.insert.call_args
        inserted_text = call_args[0][0]
        assert "quarterly budget" in inserted_text.lower()

    @freeze_time("2025-11-25 14:30:00")
    def test_note_content_searchable_after_ingest(self, notes_dir, mock_graphrag, mock_llm):
        """Test that note content is available in graphrag after ingestion."""
        create_note(
            content="Python best practices include using type hints.",
            tags=["python", "programming"],
            base_dir=notes_dir,
            graphrag=mock_graphrag,
        )

        # Verify the note content was inserted
        assert mock_graphrag.insert.called
        call_args = mock_graphrag.insert.call_args
        inserted_text = call_args[0][0]
        assert "type hints" in inserted_text.lower()


# ============================================================================
# Test: Notes in source references
# ============================================================================


class TestNotesInSources:
    """Tests for notes appearing in query source references."""

    @freeze_time("2025-11-25 14:30:00")
    def test_ingest_note_preserves_source_info(self, notes_dir, mock_graphrag, mock_llm):
        """Test that ingested notes include source information."""
        note = create_note(
            content="Meeting notes from the product review.",
            title="Product Review Notes",
            base_dir=notes_dir,
            graphrag=mock_graphrag,
        )

        # The insert should include source="note"
        assert note.source == "note"
        mock_graphrag.insert.assert_called()


# ============================================================================
# Test: sync_knowledge_base includes notes
# ============================================================================


class TestSyncIncludesNotes:
    """Tests for sync_knowledge_base including notes directory."""

    def test_ingest_all_processes_notes(self, tmp_path, mock_graphrag):
        """Test that ingest_all processes notes in notes directory."""
        # Create some note-type recordings directly (bypassing create_note)
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Use different timestamps to avoid filename collision
        with freeze_time("2025-11-25 14:30:00"):
            note1 = Recording.create_new(source="note", transcript="First note content")
            save_recording(note1, notes_dir)

        with freeze_time("2025-11-25 14:30:01"):
            note2 = Recording.create_new(source="note", transcript="Second note content")
            save_recording(note2, notes_dir)

        # Ingest all notes
        count = ingest_all(notes_dir, mock_graphrag)

        # Should have processed the notes
        assert count == 2
        assert mock_graphrag.insert.call_count == 2

    def test_sync_detects_new_notes(self, tmp_path, mock_graphrag):
        """Test that KnowledgeSync detects new notes."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        state_file = tmp_path / "sync_state.json"

        # Create initial note directly
        with freeze_time("2025-11-25 14:30:00"):
            note = Recording.create_new(source="note", transcript="Initial note")
            save_recording(note, notes_dir)

        # Create sync (takes graphrag first, then state_file)
        sync = KnowledgeSync(mock_graphrag, state_file)
        changes = sync.get_pending_changes(notes_dir)

        # Should detect the new note
        assert len(changes.new) >= 1

    def test_sync_detects_modified_notes(self, tmp_path, mock_graphrag):
        """Test that KnowledgeSync detects modified notes."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        state_file = tmp_path / "sync_state.json"

        # Create note directly
        with freeze_time("2025-11-25 14:30:00"):
            note = Recording.create_new(source="note", transcript="Original content")
            filepath = save_recording(note, notes_dir)

        # Create sync and mark as synced
        sync = KnowledgeSync(mock_graphrag, state_file)
        sync.sync(notes_dir)

        # Modify the note by rewriting
        content = filepath.read_text()
        filepath.write_text(content.replace("Original", "Modified"))

        # Check for changes
        changes = sync.get_pending_changes(notes_dir)

        # Should detect the modification
        assert len(changes.modified) >= 1


# ============================================================================
# Test: Convenience function for note with knowledge base
# ============================================================================


class TestNoteWithKnowledgeBase:
    """Tests for convenience functions combining notes and knowledge base."""

    @freeze_time("2025-11-25 14:30:00")
    def test_create_indexed_note(self, notes_dir, mock_graphrag, mock_llm):
        """Test creating a note that is automatically indexed."""
        # create_note with graphrag parameter ingests the note
        create_note(
            content="Indexed note content",
            base_dir=notes_dir,
            graphrag=mock_graphrag,
        )

        # Should have been inserted into GraphRAG
        mock_graphrag.insert.assert_called()
