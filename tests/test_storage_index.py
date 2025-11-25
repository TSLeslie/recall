"""Tests for SQLite search index (Ticket 1.3).

Tests cover:
- RecordingIndex initialization (file-based and in-memory)
- add_recording() indexes a recording
- remove_recording() removes from index
- search() performs full-text search on transcript/summary
- filter() filters by source, date range, tags
- rebuild_index() scans directory and rebuilds
- SearchResult structure
"""

from datetime import date, datetime
from pathlib import Path

import pytest


class TestRecordingIndexInit:
    """Test RecordingIndex initialization."""

    def test_index_creates_database_file(self, tmp_path):
        """Test that RecordingIndex creates the database file."""
        from recall.storage.index import RecordingIndex

        db_path = tmp_path / "test.db"
        index = RecordingIndex(db_path)

        assert db_path.exists()
        index.close()

    def test_index_in_memory(self):
        """Test that RecordingIndex works with in-memory database."""
        from recall.storage.index import RecordingIndex

        index = RecordingIndex(":memory:")
        # Should not raise any errors
        assert index is not None
        index.close()

    def test_index_creates_tables(self, tmp_path):
        """Test that RecordingIndex creates required tables."""
        from recall.storage.index import RecordingIndex

        db_path = tmp_path / "test.db"
        index = RecordingIndex(db_path)

        # Check tables exist by attempting a query
        # This tests the FTS5 table was created
        results = index.search("test")
        assert results == []
        index.close()


class TestAddRecording:
    """Test add_recording() method."""

    def test_add_recording_indexes_content(self, tmp_path):
        """Test that add_recording adds content to the index."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recording = Recording(
            id="add-test-1",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 14, 30),
            transcript="Discussing quarterly budget and revenue goals.",
            summary="Budget review meeting.",
            tags=["meeting", "budget"],
        )
        filepath = tmp_path / "2025-11" / "recording.md"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()

        index.add_recording(filepath, recording)

        # Should be searchable
        results = index.search("budget")
        assert len(results) == 1
        assert results[0].filepath == filepath
        index.close()

    def test_add_recording_updates_existing(self, tmp_path):
        """Test that add_recording updates if already indexed."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")
        filepath = tmp_path / "recording.md"
        filepath.touch()

        # Add first version
        recording1 = Recording(
            id="update-test",
            source="note",
            timestamp=datetime(2025, 11, 25, 10, 0),
            transcript="Original content about Python.",
        )
        index.add_recording(filepath, recording1)

        # Update with new content
        recording2 = Recording(
            id="update-test",
            source="note",
            timestamp=datetime(2025, 11, 25, 10, 0),
            transcript="Updated content about JavaScript.",
        )
        index.add_recording(filepath, recording2)

        # Should find updated content
        results = index.search("JavaScript")
        assert len(results) == 1

        # Should not find old content
        results = index.search("Python")
        assert len(results) == 0
        index.close()


class TestRemoveRecording:
    """Test remove_recording() method."""

    def test_remove_recording_removes_from_index(self, tmp_path):
        """Test that remove_recording removes content from index."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")
        filepath = tmp_path / "recording.md"
        filepath.touch()

        recording = Recording(
            id="remove-test",
            source="microphone",
            timestamp=datetime(2025, 11, 25, 15, 0),
            transcript="Voice memo about project deadline.",
        )
        index.add_recording(filepath, recording)

        # Verify it's indexed
        assert len(index.search("deadline")) == 1

        # Remove it
        index.remove_recording(filepath)

        # Should not be found
        assert len(index.search("deadline")) == 0
        index.close()

    def test_remove_nonexistent_does_not_raise(self, tmp_path):
        """Test that removing non-existent entry doesn't raise."""
        from recall.storage.index import RecordingIndex

        index = RecordingIndex(":memory:")
        filepath = tmp_path / "nonexistent.md"

        # Should not raise
        index.remove_recording(filepath)
        index.close()


class TestSearch:
    """Test search() full-text search method."""

    def test_search_finds_matching_transcript(self, tmp_path):
        """Test that search finds content in transcript."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recordings = [
            Recording(
                id="search-1",
                source="zoom",
                timestamp=datetime(2025, 11, 20, 10, 0),
                transcript="Meeting about Python programming and web development.",
                summary="Python discussion",
            ),
            Recording(
                id="search-2",
                source="youtube",
                timestamp=datetime(2025, 11, 21, 14, 0),
                transcript="Tutorial on JavaScript frameworks.",
                summary="JS tutorial",
            ),
        ]

        for i, rec in enumerate(recordings):
            fp = tmp_path / f"rec{i}.md"
            fp.touch()
            index.add_recording(fp, rec)

        # Search for Python
        results = index.search("Python")
        assert len(results) == 1
        assert "search-1" in str(results[0].filepath) or results[0].source == "zoom"

        # Search for JavaScript
        results = index.search("JavaScript")
        assert len(results) == 1
        index.close()

    def test_search_finds_matching_summary(self, tmp_path):
        """Test that search finds content in summary."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recording = Recording(
            id="summary-search",
            source="note",
            timestamp=datetime(2025, 11, 25, 9, 0),
            transcript="Generic content here.",
            summary="Important quarterly review meeting",
        )
        filepath = tmp_path / "rec.md"
        filepath.touch()
        index.add_recording(filepath, recording)

        results = index.search("quarterly")
        assert len(results) == 1
        index.close()

    def test_search_returns_search_result_with_all_fields(self, tmp_path):
        """Test that SearchResult has all required fields."""
        from recall.storage.index import RecordingIndex, SearchResult
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recording = Recording(
            id="fields-test",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 14, 0),
            transcript="Testing search result fields.",
            summary="Test summary for fields.",
        )
        filepath = tmp_path / "test.md"
        filepath.touch()
        index.add_recording(filepath, recording)

        results = index.search("testing")
        assert len(results) == 1

        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.filepath == filepath
        assert result.source == "zoom"
        assert result.timestamp == datetime(2025, 11, 25, 14, 0)
        assert "Test summary" in result.summary_snippet or "Testing" in result.summary_snippet
        assert isinstance(result.relevance_score, float)
        index.close()

    def test_search_empty_query_returns_empty(self, tmp_path):
        """Test that empty search query returns empty results."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recording = Recording(
            id="empty-search",
            source="note",
            timestamp=datetime(2025, 11, 25, 10, 0),
            transcript="Some content.",
        )
        filepath = tmp_path / "rec.md"
        filepath.touch()
        index.add_recording(filepath, recording)

        results = index.search("")
        assert results == []
        index.close()


class TestFilter:
    """Test filter() method for filtering by source, date, tags."""

    def test_filter_by_source(self, tmp_path):
        """Test filtering recordings by source."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recordings = [
            Recording(
                id="f1",
                source="zoom",
                timestamp=datetime(2025, 11, 20, 10, 0),
                transcript="Zoom meeting.",
            ),
            Recording(
                id="f2",
                source="youtube",
                timestamp=datetime(2025, 11, 21, 10, 0),
                transcript="YouTube video.",
            ),
            Recording(
                id="f3",
                source="zoom",
                timestamp=datetime(2025, 11, 22, 10, 0),
                transcript="Another zoom.",
            ),
        ]

        for i, rec in enumerate(recordings):
            fp = tmp_path / f"rec{i}.md"
            fp.touch()
            index.add_recording(fp, rec)

        results = index.filter(source="zoom")
        assert len(results) == 2

        results = index.filter(source="youtube")
        assert len(results) == 1
        index.close()

    def test_filter_by_date_range(self, tmp_path):
        """Test filtering recordings by date range."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recordings = [
            Recording(
                id="d1",
                source="note",
                timestamp=datetime(2025, 10, 15, 10, 0),
                transcript="October note.",
            ),
            Recording(
                id="d2",
                source="note",
                timestamp=datetime(2025, 11, 15, 10, 0),
                transcript="November note.",
            ),
            Recording(
                id="d3",
                source="note",
                timestamp=datetime(2025, 12, 15, 10, 0),
                transcript="December note.",
            ),
        ]

        for i, rec in enumerate(recordings):
            fp = tmp_path / f"rec{i}.md"
            fp.touch()
            index.add_recording(fp, rec)

        # Only November
        results = index.filter(start_date=date(2025, 11, 1), end_date=date(2025, 11, 30))
        assert len(results) == 1

        # November and later
        results = index.filter(start_date=date(2025, 11, 1))
        assert len(results) == 2

        # Up to November
        results = index.filter(end_date=date(2025, 11, 30))
        assert len(results) == 2
        index.close()

    def test_filter_by_tags(self, tmp_path):
        """Test filtering recordings by tags."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recordings = [
            Recording(
                id="t1",
                source="note",
                timestamp=datetime(2025, 11, 20, 10, 0),
                transcript="Note one.",
                tags=["meeting", "important"],
            ),
            Recording(
                id="t2",
                source="note",
                timestamp=datetime(2025, 11, 21, 10, 0),
                transcript="Note two.",
                tags=["personal"],
            ),
            Recording(
                id="t3",
                source="note",
                timestamp=datetime(2025, 11, 22, 10, 0),
                transcript="Note three.",
                tags=["meeting"],
            ),
        ]

        for i, rec in enumerate(recordings):
            fp = tmp_path / f"rec{i}.md"
            fp.touch()
            index.add_recording(fp, rec)

        results = index.filter(tags=["meeting"])
        assert len(results) == 2

        results = index.filter(tags=["important"])
        assert len(results) == 1

        results = index.filter(tags=["meeting", "important"])
        assert len(results) == 1  # Must have both
        index.close()

    def test_filter_combined(self, tmp_path):
        """Test combining multiple filter criteria."""
        from recall.storage.index import RecordingIndex
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        recordings = [
            Recording(
                id="c1",
                source="zoom",
                timestamp=datetime(2025, 11, 20, 10, 0),
                transcript="Meeting.",
                tags=["work"],
            ),
            Recording(
                id="c2",
                source="zoom",
                timestamp=datetime(2025, 11, 25, 10, 0),
                transcript="Another meeting.",
                tags=["work"],
            ),
            Recording(
                id="c3",
                source="note",
                timestamp=datetime(2025, 11, 25, 10, 0),
                transcript="Note.",
                tags=["work"],
            ),
        ]

        for i, rec in enumerate(recordings):
            fp = tmp_path / f"rec{i}.md"
            fp.touch()
            index.add_recording(fp, rec)

        # Zoom meetings after Nov 22
        results = index.filter(source="zoom", start_date=date(2025, 11, 22))
        assert len(results) == 1
        index.close()


class TestRebuildIndex:
    """Test rebuild_index() method."""

    def test_rebuild_index_scans_directory(self, temp_storage_dir):
        """Test that rebuild_index scans and indexes all files."""
        from recall.storage.index import RecordingIndex
        from recall.storage.markdown import save_recording
        from recall.storage.models import Recording

        # Create some recordings using save_recording
        recordings = [
            Recording(
                id="r1",
                source="zoom",
                timestamp=datetime(2025, 11, 20, 10, 0),
                transcript="First meeting transcript.",
            ),
            Recording(
                id="r2",
                source="youtube",
                timestamp=datetime(2025, 11, 21, 14, 0),
                transcript="Second video transcript.",
            ),
        ]

        for rec in recordings:
            save_recording(rec, temp_storage_dir)

        # Create fresh index and rebuild
        index = RecordingIndex(":memory:")
        index.rebuild_index(temp_storage_dir)

        # Should find all recordings
        results = index.search("transcript")
        assert len(results) == 2

        results = index.search("meeting")
        assert len(results) == 1
        index.close()

    def test_rebuild_index_clears_old_entries(self, temp_storage_dir):
        """Test that rebuild_index removes old entries."""
        from recall.storage.index import RecordingIndex
        from recall.storage.markdown import save_recording
        from recall.storage.models import Recording

        index = RecordingIndex(":memory:")

        # Add a recording manually
        old_recording = Recording(
            id="old",
            source="note",
            timestamp=datetime(2025, 11, 19, 10, 0),
            transcript="Removed unique keyword xyzzy123.",
        )
        old_path = temp_storage_dir / "old.md"
        old_path.write_text("---\nid: old\n---\nRemoved content")
        index.add_recording(old_path, old_recording)

        # Save a new recording to disk
        new_recording = Recording(
            id="new",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 10, 0),
            transcript="New recording from file.",
        )
        save_recording(new_recording, temp_storage_dir)

        # Delete old file from disk
        old_path.unlink()

        # Rebuild should only have new entry
        index.rebuild_index(temp_storage_dir)

        # Old unique keyword should not be found
        results = index.search("xyzzy123")
        assert len(results) == 0

        # New content should be found
        results = index.search("recording")
        assert len(results) == 1
        index.close()
