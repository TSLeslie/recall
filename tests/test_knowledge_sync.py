"""Tests for Incremental Knowledge Updates (Ticket 4.4).

Tests the KnowledgeSync class for tracking sync state,
detecting changes, and incrementally updating the knowledge base.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_graphrag():
    """Mock RecallGraphRAG for sync testing."""
    mock = MagicMock()
    mock.insert = MagicMock()
    mock.query = MagicMock()
    return mock


@pytest.fixture
def temp_recordings_dir(tmp_path):
    """Create a temp directory with sample recordings."""
    from recall.storage.markdown import save_recording
    from recall.storage.models import Recording

    recordings_dir = tmp_path / "recordings"
    recordings_dir.mkdir()

    # Create sample recordings
    for i in range(3):
        recording = Recording(
            id=f"rec-{i}",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 10 + i, 0, 0),
            transcript=f"Recording {i} transcript content.",
            title=f"Meeting {i}",
        )
        save_recording(recording, recordings_dir)

    return recordings_dir


@pytest.fixture
def sync_state_file(tmp_path):
    """Temporary sync state file."""
    return tmp_path / "sync_state.json"


# ============================================================================
# KnowledgeSync Initialization Tests
# ============================================================================


class TestKnowledgeSyncInit:
    """Tests for KnowledgeSync initialization."""

    def test_knowledge_sync_creates_state_file_dir(self, tmp_path, mock_graphrag):
        """Test that sync creates state file directory."""
        from recall.knowledge.sync import KnowledgeSync

        state_file = tmp_path / "subdir" / "state.json"
        sync = KnowledgeSync(mock_graphrag, state_file=state_file)

        # Just instantiating should be fine, dir created on save
        assert sync is not None

    def test_knowledge_sync_loads_existing_state(self, sync_state_file, mock_graphrag):
        """Test that existing state is loaded."""
        from recall.knowledge.sync import KnowledgeSync

        # Create existing state
        state = {
            "last_sync": "2025-11-25T12:00:00",
            "file_hashes": {"/path/to/file.md": "abc123"},
        }
        sync_state_file.parent.mkdir(parents=True, exist_ok=True)
        sync_state_file.write_text(json.dumps(state))

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        assert sync.last_sync is not None
        assert len(sync.file_hashes) == 1


# ============================================================================
# Change Detection Tests
# ============================================================================


class TestChangeDetection:
    """Tests for detecting file changes."""

    def test_get_pending_changes_detects_new_files(
        self, temp_recordings_dir, sync_state_file, mock_graphrag
    ):
        """Test that new files are detected."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)
        changes = sync.get_pending_changes(temp_recordings_dir)

        assert len(changes.new) == 3  # All files are new
        assert len(changes.modified) == 0
        assert len(changes.deleted) == 0

    def test_get_pending_changes_detects_modified_files(
        self, temp_recordings_dir, sync_state_file, mock_graphrag
    ):
        """Test that modified files are detected."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        # First sync to establish baseline
        sync.sync(temp_recordings_dir)

        # Modify a file
        md_files = list(temp_recordings_dir.rglob("*.md"))
        if md_files:
            content = md_files[0].read_text()
            md_files[0].write_text(content + "\n\nAdditional content.")

        changes = sync.get_pending_changes(temp_recordings_dir)

        assert len(changes.modified) == 1
        assert len(changes.new) == 0

    def test_get_pending_changes_detects_deleted_files(
        self, temp_recordings_dir, sync_state_file, mock_graphrag
    ):
        """Test that deleted files are detected."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        # First sync to establish baseline
        sync.sync(temp_recordings_dir)

        # Delete a file
        md_files = list(temp_recordings_dir.rglob("*.md"))
        if md_files:
            md_files[0].unlink()

        changes = sync.get_pending_changes(temp_recordings_dir)

        assert len(changes.deleted) == 1
        assert len(changes.new) == 0


# ============================================================================
# ChangeSet Model Tests
# ============================================================================


class TestChangeSetModel:
    """Tests for the ChangeSet model."""

    def test_changeset_has_all_fields(self):
        """Test that ChangeSet has new, modified, deleted fields."""
        from recall.knowledge.sync import ChangeSet

        changes = ChangeSet(
            new=[Path("/new/file.md")],
            modified=[Path("/modified/file.md")],
            deleted=[Path("/deleted/file.md")],
        )

        assert len(changes.new) == 1
        assert len(changes.modified) == 1
        assert len(changes.deleted) == 1

    def test_changeset_empty_by_default(self):
        """Test that ChangeSet can be empty."""
        from recall.knowledge.sync import ChangeSet

        changes = ChangeSet()

        assert changes.new == []
        assert changes.modified == []
        assert changes.deleted == []

    def test_changeset_has_changes_property(self):
        """Test has_changes property."""
        from recall.knowledge.sync import ChangeSet

        empty = ChangeSet()
        assert not empty.has_changes

        with_new = ChangeSet(new=[Path("/file.md")])
        assert with_new.has_changes


# ============================================================================
# Sync Process Tests
# ============================================================================


class TestSyncProcess:
    """Tests for the sync process."""

    def test_sync_processes_new_files(self, temp_recordings_dir, sync_state_file, mock_graphrag):
        """Test that sync processes new files."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)
        result = sync.sync(temp_recordings_dir)

        assert result.added == 3
        assert mock_graphrag.insert.called

    def test_sync_updates_last_sync_timestamp(
        self, temp_recordings_dir, sync_state_file, mock_graphrag
    ):
        """Test that sync updates last_sync timestamp."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)
        before = sync.last_sync

        sync.sync(temp_recordings_dir)

        assert sync.last_sync is not None
        if before:
            assert sync.last_sync >= before

    def test_sync_saves_state(self, temp_recordings_dir, sync_state_file, mock_graphrag):
        """Test that sync persists state to file."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)
        sync.sync(temp_recordings_dir)

        assert sync_state_file.exists()
        state = json.loads(sync_state_file.read_text())
        assert "last_sync" in state
        assert "file_hashes" in state

    def test_sync_only_processes_changes(self, temp_recordings_dir, sync_state_file, mock_graphrag):
        """Test that subsequent syncs only process changes."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        # First sync
        result1 = sync.sync(temp_recordings_dir)
        assert result1.added == 3

        # Second sync (no changes)
        result2 = sync.sync(temp_recordings_dir)
        assert result2.added == 0


# ============================================================================
# Force Rebuild Tests
# ============================================================================


class TestForceRebuild:
    """Tests for force_rebuild functionality."""

    def test_force_rebuild_reprocesses_all(
        self, temp_recordings_dir, sync_state_file, mock_graphrag
    ):
        """Test that force_rebuild reprocesses all files."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        # First sync
        sync.sync(temp_recordings_dir)
        initial_calls = mock_graphrag.insert.call_count

        # Force rebuild
        result = sync.force_rebuild(temp_recordings_dir)

        assert result.added == 3
        assert mock_graphrag.insert.call_count > initial_calls

    def test_force_rebuild_clears_state(self, temp_recordings_dir, sync_state_file, mock_graphrag):
        """Test that force_rebuild clears existing state."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        # First sync
        sync.sync(temp_recordings_dir)
        assert len(sync.file_hashes) == 3

        # Force rebuild clears and rebuilds
        sync.force_rebuild(temp_recordings_dir)

        # State should be rebuilt (same count since same files)
        assert len(sync.file_hashes) == 3


# ============================================================================
# SyncResult Model Tests
# ============================================================================


class TestSyncResultModel:
    """Tests for SyncResult model."""

    def test_sync_result_has_all_fields(self):
        """Test that SyncResult has all tracking fields."""
        from recall.knowledge.sync import SyncResult

        result = SyncResult(
            added=5,
            modified=2,
            deleted=1,
            errors=0,
        )

        assert result.added == 5
        assert result.modified == 2
        assert result.deleted == 1
        assert result.errors == 0

    def test_sync_result_total_property(self):
        """Test total changes property."""
        from recall.knowledge.sync import SyncResult

        result = SyncResult(added=5, modified=2, deleted=1, errors=0)

        assert result.total == 8  # 5 + 2 + 1


# ============================================================================
# File Hashing Tests
# ============================================================================


class TestFileHashing:
    """Tests for file content hashing."""

    def test_compute_file_hash(self, temp_recordings_dir):
        """Test that file hash is computed correctly."""
        from recall.knowledge.sync import compute_file_hash

        md_files = list(temp_recordings_dir.rglob("*.md"))
        if md_files:
            hash1 = compute_file_hash(md_files[0])

            assert hash1 is not None
            assert len(hash1) == 64  # SHA256 hex

    def test_hash_changes_with_content(self, temp_recordings_dir):
        """Test that hash changes when content changes."""
        from recall.knowledge.sync import compute_file_hash

        md_files = list(temp_recordings_dir.rglob("*.md"))
        if md_files:
            hash1 = compute_file_hash(md_files[0])

            # Modify file
            content = md_files[0].read_text()
            md_files[0].write_text(content + "\nNew content")

            hash2 = compute_file_hash(md_files[0])

            assert hash1 != hash2


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling during sync."""

    def test_sync_handles_corrupted_state_file(self, sync_state_file, mock_graphrag):
        """Test that corrupted state file is handled gracefully."""
        from recall.knowledge.sync import KnowledgeSync

        # Create corrupted state file
        sync_state_file.parent.mkdir(parents=True, exist_ok=True)
        sync_state_file.write_text("not valid json {{{")

        # Should not raise, just use empty state
        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        assert sync.last_sync is None
        assert sync.file_hashes == {}

    def test_sync_handles_ingest_error(self, temp_recordings_dir, sync_state_file, mock_graphrag):
        """Test that ingest errors are tracked."""
        from recall.knowledge.sync import KnowledgeSync

        # Make graphrag.insert raise an exception
        mock_graphrag.insert.side_effect = Exception("Ingest failed")

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)
        result = sync.sync(temp_recordings_dir)

        # All files should be errors
        assert result.errors == 3
        assert result.added == 0

    def test_sync_handles_modified_file_error(
        self, temp_recordings_dir, sync_state_file, mock_graphrag
    ):
        """Test that errors on modified files are tracked."""
        from recall.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync(mock_graphrag, state_file=sync_state_file)

        # First sync succeeds
        sync.sync(temp_recordings_dir)

        # Modify a file
        md_files = list(temp_recordings_dir.rglob("*.md"))
        if md_files:
            content = md_files[0].read_text()
            md_files[0].write_text(content + "\n\nNew content.")

        # Make next ingest fail
        mock_graphrag.insert.side_effect = Exception("Re-ingest failed")

        result = sync.sync(temp_recordings_dir)

        assert result.errors == 1
        assert result.modified == 0
