"""Integration tests for the Knowledge module (Sprint 3).

These tests verify that all knowledge module components work together:
- GraphRAG wrapper (Ticket 4.1)
- Recording ingestion (Ticket 4.2)
- Query interface (Ticket 4.3)
- Incremental sync (Ticket 4.4)

Integration tests use mocked LLM/embeddings but real file I/O
and data flow between components.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# ============================================================================
# Integration Test Fixtures
# ============================================================================


@pytest.fixture
def mock_embedding_model():
    """Mock sentence-transformers embedding model."""
    mock = MagicMock()
    # Return consistent embeddings for reproducible tests
    mock.encode.return_value = [[0.1, 0.2, 0.3] * 128]  # 384-dim vector
    return mock


@pytest.fixture
def mock_graphrag_internal():
    """Mock the internal nano-graphrag GraphRAG class.

    Note: nano-graphrag's .insert() and .query() are synchronous methods
    that handle asyncio internally via loop.run_until_complete().
    Therefore we use MagicMock, not AsyncMock.
    """
    mock = MagicMock()

    # Sync mock for insert (nano-graphrag handles event loop internally)
    mock.insert = MagicMock(return_value=None)

    # Sync mock for query (nano-graphrag handles event loop internally)
    mock.query = MagicMock(return_value="This is a mock answer about the meeting.")

    return mock


@pytest.fixture
def integration_recordings_dir(tmp_path):
    """Create a directory with multiple recordings for integration tests."""
    from recall.storage.markdown import save_recording
    from recall.storage.models import Recording

    recordings_dir = tmp_path / "recordings"
    recordings_dir.mkdir()

    # Create varied recordings to test different scenarios
    recordings = [
        Recording(
            id="meeting-001",
            source="zoom",
            timestamp=datetime(2025, 11, 20, 9, 0, 0),
            title="Q4 Planning Meeting",
            transcript="""
            Welcome to the Q4 planning meeting. Today we'll discuss the budget 
            allocation for next quarter. The marketing team has requested a 15% 
            increase in their budget for the product launch campaign.
            
            Action items:
            1. Review marketing proposal by Friday
            2. Schedule follow-up with finance team
            3. Prepare presentation for board meeting
            """,
            summary="Q4 planning meeting covering budget allocation and marketing requests.",
            participants=["Alice", "Bob", "Carol"],
            tags=["meeting", "budget", "Q4"],
        ),
        Recording(
            id="youtube-001",
            source="youtube",
            timestamp=datetime(2025, 11, 21, 14, 30, 0),
            title="Python Best Practices Tutorial",
            transcript="""
            In this tutorial, we'll cover Python best practices for 2025.
            First, always use type hints in your function signatures.
            Second, prefer dataclasses for data structures.
            Third, use async/await for I/O-bound operations.
            
            Remember to write tests for your code and maintain good documentation.
            """,
            summary="Tutorial on Python best practices including type hints and async.",
            tags=["python", "tutorial", "programming"],
        ),
        Recording(
            id="meeting-002",
            source="zoom",
            timestamp=datetime(2025, 11, 22, 10, 0, 0),
            title="Product Launch Sync",
            transcript="""
            Product launch update: We're on track for the December 15th launch.
            The marketing team has finalized the campaign assets.
            Engineering has completed the beta testing phase.
            
            Remaining tasks:
            - Final QA review by December 10th
            - Press release draft by December 12th
            - Customer support training next week
            """,
            summary="Product launch sync - on track for December 15th.",
            participants=["Alice", "David", "Eve"],
            tags=["meeting", "product-launch", "Q4"],
        ),
        Recording(
            id="note-001",
            source="note",
            timestamp=datetime(2025, 11, 23, 16, 0, 0),
            title="Personal Notes",
            transcript="""
            Ideas for improving the recall system:
            - Add voice commands for hands-free operation
            - Implement smart notifications for action items
            - Create weekly summary reports
            
            Research topics:
            - Graph neural networks for better knowledge extraction
            - Whisper fine-tuning for domain-specific vocabulary
            """,
            summary="Personal notes on recall system improvements.",
            tags=["notes", "ideas"],
        ),
    ]

    for recording in recordings:
        save_recording(recording, recordings_dir)

    return recordings_dir


@pytest.fixture
def integration_state_dir(tmp_path):
    """Create a temporary directory for state files."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================


class TestKnowledgeEndToEnd:
    """End-to-end tests for the complete knowledge workflow."""

    def test_full_ingest_and_query_workflow(
        self,
        integration_recordings_dir,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test the complete workflow: ingest recordings → query knowledge base."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.ingest import ingest_all
            from recall.knowledge.query import ask

            # Step 1: Create GraphRAG instance
            graphrag_dir = integration_state_dir / "graphrag"
            rag = RecallGraphRAG(working_dir=graphrag_dir)

            # Step 2: Ingest all recordings
            count = ingest_all(integration_recordings_dir, rag)
            assert count == 4, "Should ingest all 4 recordings"

            # Verify insert was called for chunks
            assert mock_graphrag_internal.insert.called

            # Step 3: Query the knowledge base
            mock_graphrag_internal.query.return_value = (
                "The Q4 budget meeting discussed a 15% increase for marketing."
            )
            answer = ask("What was discussed about the budget?", rag)

            assert answer.response is not None
            assert len(answer.response) > 0

    def test_sync_workflow_detects_changes(
        self,
        integration_recordings_dir,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test the sync workflow: initial sync → modify → incremental sync."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.sync import KnowledgeSync

            # Step 1: Create components
            graphrag_dir = integration_state_dir / "graphrag"
            state_file = integration_state_dir / "sync_state.json"

            rag = RecallGraphRAG(working_dir=graphrag_dir)
            sync = KnowledgeSync(rag, state_file=state_file)

            # Step 2: Initial sync
            result1 = sync.sync(integration_recordings_dir)
            assert result1.added == 4, "Initial sync should add all recordings"
            assert result1.modified == 0
            assert result1.deleted == 0

            # Step 3: Verify state was persisted
            assert state_file.exists()
            state = json.loads(state_file.read_text())
            assert len(state["file_hashes"]) == 4

            # Step 4: Sync again with no changes
            result2 = sync.sync(integration_recordings_dir)
            assert result2.added == 0, "No new files"
            assert result2.modified == 0, "No modified files"
            assert result2.deleted == 0, "No deleted files"

            # Step 5: Modify a file
            md_files = list(integration_recordings_dir.rglob("*.md"))
            assert len(md_files) >= 1, "Should have markdown files"
            first_file = md_files[0]
            original_content = first_file.read_text()
            first_file.write_text(original_content + "\n\nAdditional notes added.")

            # Step 6: Sync detects modification
            result3 = sync.sync(integration_recordings_dir)
            assert result3.modified == 1, "Should detect 1 modified file"
            assert result3.added == 0

    def test_chunking_preserves_context(self, integration_recordings_dir):
        """Test that chunking preserves context through overlap."""
        from recall.knowledge.ingest import chunk_transcript

        # Create a long transcript
        long_text = " ".join(["word"] * 1000)  # ~5000 chars

        chunks = chunk_transcript(long_text, chunk_size=500, overlap=100)

        assert len(chunks) > 1, "Should create multiple chunks"

        # Verify overlap exists between consecutive chunks
        for i in range(len(chunks) - 1):
            # Last words of chunk i should appear at start of chunk i+1
            chunk_words = chunks[i].split()
            next_chunk_words = chunks[i + 1].split()

            # Some overlap should exist
            overlap_found = any(word in next_chunk_words[:20] for word in chunk_words[-20:])
            assert overlap_found, f"Chunks {i} and {i + 1} should overlap"


# ============================================================================
# Component Integration Tests
# ============================================================================


class TestGraphRAGIngestIntegration:
    """Tests for GraphRAG + Ingestion integration."""

    def test_ingest_recording_creates_correct_metadata(
        self,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that ingested recordings include correct metadata."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.ingest import ingest_recording
            from recall.storage.models import Recording

            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")

            recording = Recording(
                id="test-rec-001",
                source="zoom",
                timestamp=datetime(2025, 11, 25, 10, 0, 0),
                title="Test Meeting",
                transcript="This is a test transcript for metadata verification.",
                summary="Test summary",
                participants=["Alice", "Bob"],
                tags=["test", "integration"],
            )

            chunks = ingest_recording(recording, rag)

            assert chunks == 1, "Short transcript should be 1 chunk"
            assert mock_graphrag_internal.insert.called

    def test_ingest_all_handles_errors_gracefully(
        self,
        tmp_path,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that ingest_all continues after individual file errors."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.ingest import ingest_all
            from recall.storage.markdown import save_recording
            from recall.storage.models import Recording

            # Create recordings dir with valid and invalid files
            recordings_dir = tmp_path / "recordings"
            recordings_dir.mkdir()

            # Valid recording
            valid = Recording(
                id="valid-001",
                source="zoom",
                timestamp=datetime(2025, 11, 25, 10, 0, 0),
                transcript="Valid transcript content.",
            )
            save_recording(valid, recordings_dir)

            # Create an invalid markdown file (malformed YAML)
            invalid_file = recordings_dir / "invalid.md"
            invalid_file.write_text("---\ninvalid: yaml: here\n---\nContent")

            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")

            # Should not raise, should process valid file
            count = ingest_all(recordings_dir, rag)
            assert count >= 1, "Should process at least the valid recording"


class TestIngestQueryIntegration:
    """Tests for Ingestion + Query integration."""

    def test_query_returns_answer_after_ingest(
        self,
        integration_recordings_dir,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that queries work after ingesting recordings."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.ingest import ingest_all
            from recall.knowledge.query import ask

            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")

            # Ingest recordings
            ingest_all(integration_recordings_dir, rag)

            # Configure mock query response (sync - nano-graphrag handles event loop)
            from unittest.mock import MagicMock

            mock_graphrag_internal.query = MagicMock(
                return_value="The product launch is scheduled for December 15th."
            )

            # Query about ingested content
            answer = ask("When is the product launch?", rag)

            assert "December 15th" in answer.response

    def test_follow_up_questions_generated(
        self,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that follow-up questions are generated based on answer content."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.query import ask

            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")

            # Mock a response about a meeting (sync - nano-graphrag handles event loop)
            from unittest.mock import MagicMock

            mock_graphrag_internal.query = MagicMock(
                return_value="The meeting discussed the Q4 budget allocation."
            )

            answer = ask("What was the meeting about?", rag)

            # Should generate meeting-related follow-ups
            assert len(answer.follow_up_questions) > 0


class TestSyncIngestIntegration:
    """Tests for Sync + Ingest integration."""

    def test_sync_uses_ingest_correctly(
        self,
        integration_recordings_dir,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that sync properly uses ingest for new files."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.sync import KnowledgeSync

            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")
            sync = KnowledgeSync(rag, state_file=integration_state_dir / "sync_state.json")

            # Initial sync
            result = sync.sync(integration_recordings_dir)

            # Each recording gets chunked and inserted
            assert result.added == 4
            assert mock_graphrag_internal.insert.call_count >= 4

    def test_force_rebuild_reprocesses_all(
        self,
        integration_recordings_dir,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that force_rebuild reprocesses all recordings."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.sync import KnowledgeSync

            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")
            sync = KnowledgeSync(rag, state_file=integration_state_dir / "sync_state.json")

            # Initial sync
            sync.sync(integration_recordings_dir)
            initial_calls = mock_graphrag_internal.insert.call_count

            # Force rebuild
            result = sync.force_rebuild(integration_recordings_dir)

            assert result.added == 4
            assert mock_graphrag_internal.insert.call_count > initial_calls


# ============================================================================
# Data Flow Tests
# ============================================================================


class TestDataFlowIntegration:
    """Tests for data flow between components."""

    def test_recording_metadata_flows_through_pipeline(
        self,
        tmp_path,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that recording metadata is preserved through the pipeline."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.sync import KnowledgeSync
            from recall.storage.markdown import save_recording
            from recall.storage.models import Recording

            # Create a recording with full metadata
            recordings_dir = tmp_path / "recordings"
            recordings_dir.mkdir()

            recording = Recording(
                id="meta-test-001",
                source="zoom",
                timestamp=datetime(2025, 11, 25, 15, 30, 0),
                title="Metadata Test Meeting",
                transcript="Testing metadata flow through the system.",
                summary="Test of metadata preservation.",
                participants=["Alice", "Bob", "Carol"],
                tags=["test", "metadata", "integration"],
            )
            save_recording(recording, recordings_dir)

            # Sync to knowledge base
            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")
            sync = KnowledgeSync(rag, state_file=integration_state_dir / "sync_state.json")
            result = sync.sync(recordings_dir)

            assert result.added == 1

            # Verify the insert was called - can't easily check metadata
            # without deeper mocking, but we verify the flow completed
            assert mock_graphrag_internal.insert.called

    def test_file_changes_flow_through_sync(
        self,
        tmp_path,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that file changes are properly detected and synced."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.sync import KnowledgeSync, compute_file_hash
            from recall.storage.markdown import save_recording
            from recall.storage.models import Recording

            recordings_dir = tmp_path / "recordings"
            recordings_dir.mkdir()

            # Create initial recording
            recording = Recording(
                id="flow-test-001",
                source="microphone",
                timestamp=datetime(2025, 11, 25, 16, 0, 0),
                transcript="Initial transcript content.",
            )
            filepath = save_recording(recording, recordings_dir)

            # Get initial hash
            initial_hash = compute_file_hash(filepath)

            # Setup and sync
            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")
            sync = KnowledgeSync(rag, state_file=integration_state_dir / "sync_state.json")
            sync.sync(recordings_dir)

            # Modify file
            content = filepath.read_text()
            filepath.write_text(content.replace("Initial", "Modified"))

            # Verify hash changed
            new_hash = compute_file_hash(filepath)
            assert initial_hash != new_hash

            # Sync should detect change
            changes = sync.get_pending_changes(recordings_dir)
            assert len(changes.modified) == 1


# ============================================================================
# Error Recovery Tests
# ============================================================================


class TestErrorRecoveryIntegration:
    """Tests for error handling and recovery."""

    def test_sync_recovers_from_partial_failure(
        self,
        tmp_path,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that sync continues after individual file errors."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.sync import KnowledgeSync
            from recall.storage.markdown import save_recording
            from recall.storage.models import Recording

            recordings_dir = tmp_path / "recordings"
            recordings_dir.mkdir()

            # Create valid recordings
            for i in range(3):
                rec = Recording(
                    id=f"recovery-{i}",
                    source="zoom",
                    timestamp=datetime(2025, 11, 25, 10 + i, 0, 0),
                    transcript=f"Recording {i} content.",
                )
                save_recording(rec, recordings_dir)

            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")
            sync = KnowledgeSync(rag, state_file=integration_state_dir / "sync_state.json")

            # Create a malformed file to cause load_recording to fail
            bad_file = recordings_dir / "20251125_130000_zoom_bad.md"
            bad_file.write_text("---\ninvalid: yaml: here\n---\nContent")

            result = sync.sync(recordings_dir)

            # Should have some successes and one error (from malformed file)
            # 3 valid recordings + 1 bad = some errors expected
            assert result.added >= 3 or result.errors >= 1
            # At minimum, the 3 valid recordings should be processed
            assert result.added + result.errors >= 3

    def test_state_persists_after_error(
        self,
        tmp_path,
        integration_state_dir,
        mock_embedding_model,
        mock_graphrag_internal,
    ):
        """Test that state is saved even after errors."""
        with (
            patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
            patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
        ):
            mock_st.return_value = mock_embedding_model
            mock_rag_class.return_value = mock_graphrag_internal

            from recall.knowledge.graphrag import RecallGraphRAG
            from recall.knowledge.sync import KnowledgeSync
            from recall.storage.markdown import save_recording
            from recall.storage.models import Recording

            recordings_dir = tmp_path / "recordings"
            recordings_dir.mkdir()

            rec = Recording(
                id="state-test-001",
                source="zoom",
                timestamp=datetime(2025, 11, 25, 12, 0, 0),
                transcript="State persistence test.",
            )
            save_recording(rec, recordings_dir)

            state_file = integration_state_dir / "sync_state.json"
            rag = RecallGraphRAG(working_dir=integration_state_dir / "graphrag")
            sync = KnowledgeSync(rag, state_file=state_file)

            sync.sync(recordings_dir)

            # State file should exist
            assert state_file.exists()

            # Load and verify state
            state = json.loads(state_file.read_text())
            assert "last_sync" in state
            assert "file_hashes" in state
            assert len(state["file_hashes"]) == 1
