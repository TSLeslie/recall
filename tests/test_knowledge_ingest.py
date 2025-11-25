"""Tests for Recording Ingestion to GraphRAG (Ticket 4.2).

Tests the functionality for adding recordings to the knowledge base,
including chunking, metadata handling, and bulk ingestion.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_graphrag(mocker):
    """Mock RecallGraphRAG for testing ingestion."""
    mock = mocker.patch("recall.knowledge.ingest.RecallGraphRAG")
    mock_instance = MagicMock()
    mock.return_value = mock_instance
    mock_instance.insert = MagicMock()
    mock_instance.query = MagicMock()
    return mock_instance


@pytest.fixture
def sample_recording():
    """Create a sample Recording for testing."""
    from recall.storage.models import Recording

    return Recording(
        id="test-recording-123",
        source="zoom",
        timestamp=datetime(2025, 11, 25, 14, 30, 0),
        transcript="This is a test transcript about machine learning and AI. "
        "We discussed the Q4 budget review and upcoming product launches. "
        "Action items include reviewing the proposal by Friday.",
        title="Q4 Planning Meeting",
        summary="Meeting covered Q4 budget and product launches.",
        duration_seconds=3600,
        tags=["meeting", "q4", "planning"],
        participants=["Alice", "Bob", "Charlie"],
    )


@pytest.fixture
def long_transcript():
    """Create a long transcript that needs chunking."""
    # Create a transcript with ~2000 words
    paragraph = (
        "This is a paragraph about machine learning and artificial intelligence. "
        "We discussed various topics including neural networks, deep learning, "
        "natural language processing, and computer vision. The team agreed to "
        "focus on improving model accuracy and reducing inference time. "
    )
    return paragraph * 50  # ~2000 words


@pytest.fixture
def temp_recordings_dir(tmp_path):
    """Create a temp directory with sample recordings."""
    from recall.storage.markdown import save_recording
    from recall.storage.models import Recording

    recordings_dir = tmp_path / "recordings"
    recordings_dir.mkdir()

    # Create a few sample recordings
    for i in range(3):
        recording = Recording(
            id=f"rec-{i}",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 10 + i, 0, 0),
            transcript=f"Recording {i} transcript content about topic {i}.",
            title=f"Meeting {i}",
            summary=f"Summary of meeting {i}.",
        )
        save_recording(recording, recordings_dir)

    return recordings_dir


# ============================================================================
# ingest_recording Tests
# ============================================================================


class TestIngestRecording:
    """Tests for ingest_recording function."""

    def test_ingest_recording_calls_graphrag_insert(self, sample_recording, mock_graphrag):
        """Test that ingest_recording inserts into GraphRAG."""
        from recall.knowledge.ingest import ingest_recording

        ingest_recording(sample_recording, mock_graphrag)

        # Should have called insert at least once
        assert mock_graphrag.insert.called

    def test_ingest_recording_includes_transcript(self, sample_recording, mock_graphrag):
        """Test that transcript content is inserted."""
        from recall.knowledge.ingest import ingest_recording

        ingest_recording(sample_recording, mock_graphrag)

        # Check that insert was called with transcript content
        calls = mock_graphrag.insert.call_args_list
        inserted_text = "".join(call[0][0] for call in calls)
        assert "machine learning" in inserted_text

    def test_ingest_recording_includes_metadata(self, sample_recording, mock_graphrag):
        """Test that metadata is included in insertion."""
        from recall.knowledge.ingest import ingest_recording

        ingest_recording(sample_recording, mock_graphrag)

        # Check that metadata was passed
        calls = mock_graphrag.insert.call_args_list
        for call in calls:
            if len(call) > 1 and "metadata" in call[1]:
                metadata = call[1]["metadata"]
                assert "source" in metadata or "zoom" in str(call)
                break


class TestChunking:
    """Tests for transcript chunking."""

    def test_chunk_transcript_splits_long_text(self, long_transcript):
        """Test that long transcripts are split into chunks."""
        from recall.knowledge.ingest import chunk_transcript

        chunks = chunk_transcript(long_transcript, chunk_size=500)

        assert len(chunks) > 1
        for chunk in chunks:
            # Each chunk should be around the target size (with some tolerance)
            assert len(chunk) <= 600  # Allow some overflow for word boundaries

    def test_chunk_transcript_preserves_content(self, long_transcript):
        """Test that chunking preserves all content."""
        from recall.knowledge.ingest import chunk_transcript

        chunks = chunk_transcript(long_transcript, chunk_size=500)

        # Rejoin should contain original words (overlap may duplicate some)
        original_words = set(long_transcript.split())
        chunked_words = set()
        for chunk in chunks:
            chunked_words.update(chunk.split())

        # All original words should be in chunks
        assert original_words.issubset(chunked_words)

    def test_chunk_transcript_with_overlap(self, long_transcript):
        """Test that chunks have overlapping content."""
        from recall.knowledge.ingest import chunk_transcript

        chunks = chunk_transcript(long_transcript, chunk_size=500, overlap=100)

        # Check that consecutive chunks have some overlap
        if len(chunks) > 1:
            chunk1_words = set(chunks[0].split()[-20:])  # Last 20 words
            chunk2_words = set(chunks[1].split()[:20])  # First 20 words
            # Should have some common words
            common = chunk1_words & chunk2_words
            assert len(common) > 0

    def test_chunk_transcript_short_text_single_chunk(self):
        """Test that short text returns single chunk."""
        from recall.knowledge.ingest import chunk_transcript

        short_text = "This is a short transcript."
        chunks = chunk_transcript(short_text, chunk_size=500)

        assert len(chunks) == 1
        assert chunks[0] == short_text


# ============================================================================
# ingest_all Tests
# ============================================================================


class TestIngestAll:
    """Tests for bulk ingestion of recordings."""

    def test_ingest_all_processes_all_recordings(self, temp_recordings_dir, mock_graphrag):
        """Test that ingest_all processes all recordings in directory."""
        from recall.knowledge.ingest import ingest_all

        count = ingest_all(temp_recordings_dir, mock_graphrag)

        assert count == 3  # We created 3 recordings
        assert mock_graphrag.insert.called

    def test_ingest_all_returns_count(self, temp_recordings_dir, mock_graphrag):
        """Test that ingest_all returns number of ingested recordings."""
        from recall.knowledge.ingest import ingest_all

        count = ingest_all(temp_recordings_dir, mock_graphrag)

        assert isinstance(count, int)
        assert count >= 0

    def test_ingest_all_empty_directory(self, tmp_path, mock_graphrag):
        """Test ingest_all with empty directory."""
        from recall.knowledge.ingest import ingest_all

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        count = ingest_all(empty_dir, mock_graphrag)

        assert count == 0


# ============================================================================
# Duplicate Prevention Tests
# ============================================================================


class TestDuplicatePrevention:
    """Tests for avoiding duplicate ingestion."""

    def test_ingest_recording_tracks_ingested(self, sample_recording, mock_graphrag, tmp_path):
        """Test that ingested recordings are tracked."""
        from recall.knowledge.ingest import KnowledgeIngestor

        ingestor = KnowledgeIngestor(mock_graphrag, state_file=tmp_path / "state.json")

        ingestor.ingest_recording(sample_recording, Path("/test/recording.md"))

        assert ingestor.is_ingested(sample_recording.id)

    def test_ingest_recording_skips_duplicates(self, sample_recording, mock_graphrag, tmp_path):
        """Test that duplicate recordings are skipped."""
        from recall.knowledge.ingest import KnowledgeIngestor

        ingestor = KnowledgeIngestor(mock_graphrag, state_file=tmp_path / "state.json")

        # Ingest twice
        ingestor.ingest_recording(sample_recording, Path("/test/recording.md"))
        call_count_1 = mock_graphrag.insert.call_count

        ingestor.ingest_recording(sample_recording, Path("/test/recording.md"))
        call_count_2 = mock_graphrag.insert.call_count

        # Second call should not add more inserts
        assert call_count_2 == call_count_1


# ============================================================================
# sync_knowledge_base Tests
# ============================================================================


class TestSyncKnowledgeBase:
    """Tests for sync_knowledge_base function."""

    def test_sync_adds_new_recordings(self, temp_recordings_dir, mock_graphrag, tmp_path):
        """Test that sync adds new recordings."""
        from recall.knowledge.ingest import KnowledgeIngestor

        ingestor = KnowledgeIngestor(mock_graphrag, state_file=tmp_path / "state.json")

        added, removed = ingestor.sync_knowledge_base(temp_recordings_dir)

        assert added == 3  # 3 new recordings
        assert removed == 0

    def test_sync_detects_removed_recordings(self, temp_recordings_dir, mock_graphrag, tmp_path):
        """Test that sync detects removed recordings."""
        from recall.knowledge.ingest import KnowledgeIngestor

        ingestor = KnowledgeIngestor(mock_graphrag, state_file=tmp_path / "state.json")

        # First sync
        ingestor.sync_knowledge_base(temp_recordings_dir)

        # Remove a recording file
        md_files = list(temp_recordings_dir.rglob("*.md"))
        if md_files:
            md_files[0].unlink()

        # Second sync
        added, removed = ingestor.sync_knowledge_base(temp_recordings_dir)

        assert removed == 1
        assert added == 0

    def test_sync_is_idempotent(self, temp_recordings_dir, mock_graphrag, tmp_path):
        """Test that running sync twice doesn't duplicate."""
        from recall.knowledge.ingest import KnowledgeIngestor

        ingestor = KnowledgeIngestor(mock_graphrag, state_file=tmp_path / "state.json")

        # First sync
        added1, _ = ingestor.sync_knowledge_base(temp_recordings_dir)

        # Second sync
        added2, _ = ingestor.sync_knowledge_base(temp_recordings_dir)

        assert added1 == 3
        assert added2 == 0  # No new additions
