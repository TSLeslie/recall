"""SQLite-based search index for Recall recordings.

This module provides fast full-text search and filtering capabilities
using SQLite's FTS5 extension. The index stores metadata and searchable
content from recordings for quick retrieval.

Features:
- Full-text search on transcript and summary
- Filtering by source, date range, tags
- Relevance-ranked results
- Rebuild from Markdown files
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Union

from .markdown import list_recordings, load_recording
from .models import Recording


@dataclass
class SearchResult:
    """Result from a search or filter query.

    Attributes:
        filepath: Path to the recording's Markdown file
        source: Recording source type (zoom, youtube, etc.)
        timestamp: When the recording was created
        summary_snippet: Brief excerpt from summary or transcript
        relevance_score: Search relevance score (higher = more relevant)
    """

    filepath: Path
    source: str
    timestamp: datetime
    summary_snippet: str
    relevance_score: float


class RecordingIndex:
    """SQLite-based index for searching and filtering recordings.

    Uses FTS5 for full-text search on transcript and summary content.
    Stores metadata for filtering by source, date, and tags.

    Args:
        db_path: Path to SQLite database file, or ":memory:" for in-memory

    Example:
        >>> index = RecordingIndex(":memory:")
        >>> index.add_recording(filepath, recording)
        >>> results = index.search("budget meeting")
        >>> index.close()
    """

    def __init__(self, db_path: Union[str, Path]):
        """Initialize the index, creating tables if needed."""
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create the required database tables."""
        cursor = self._conn.cursor()

        # Main recordings table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recordings (
                filepath TEXT PRIMARY KEY,
                id TEXT NOT NULL,
                source TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                transcript TEXT,
                summary TEXT,
                tags TEXT
            )
        """
        )

        # FTS5 virtual table for full-text search (standalone, not content table)
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS recordings_fts USING fts5(
                filepath,
                transcript,
                summary
            )
        """
        )

        self._conn.commit()

    def add_recording(self, filepath: Path, recording: Recording) -> None:
        """Add or update a recording in the index.

        Args:
            filepath: Path to the recording's Markdown file
            recording: The Recording object to index
        """
        cursor = self._conn.cursor()
        filepath_str = str(filepath)

        # Check if exists (for update)
        cursor.execute("SELECT 1 FROM recordings WHERE filepath = ?", (filepath_str,))
        existing = cursor.fetchone()

        if existing:
            # Remove old FTS entry
            cursor.execute("DELETE FROM recordings_fts WHERE filepath = ?", (filepath_str,))

            # Update main record
            cursor.execute(
                """
                UPDATE recordings SET
                    id = ?,
                    source = ?,
                    timestamp = ?,
                    transcript = ?,
                    summary = ?,
                    tags = ?
                WHERE filepath = ?
            """,
                (
                    recording.id,
                    recording.source,
                    recording.timestamp.isoformat(),
                    recording.transcript,
                    recording.summary,
                    json.dumps(recording.tags),
                    filepath_str,
                ),
            )
        else:
            # Insert new record
            cursor.execute(
                """
                INSERT INTO recordings (filepath, id, source, timestamp, transcript, summary, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    filepath_str,
                    recording.id,
                    recording.source,
                    recording.timestamp.isoformat(),
                    recording.transcript,
                    recording.summary,
                    json.dumps(recording.tags),
                ),
            )

        # Add FTS entry
        cursor.execute(
            "INSERT INTO recordings_fts(filepath, transcript, summary) VALUES(?, ?, ?)",
            (filepath_str, recording.transcript, recording.summary or ""),
        )

        self._conn.commit()

    def remove_recording(self, filepath: Path) -> None:
        """Remove a recording from the index.

        Args:
            filepath: Path to the recording's Markdown file
        """
        cursor = self._conn.cursor()
        filepath_str = str(filepath)

        # Remove from FTS
        cursor.execute("DELETE FROM recordings_fts WHERE filepath = ?", (filepath_str,))

        # Remove from main table
        cursor.execute("DELETE FROM recordings WHERE filepath = ?", (filepath_str,))

        self._conn.commit()

    def search(self, query: str) -> List[SearchResult]:
        """Search recordings by full-text query.

        Searches transcript and summary fields using FTS5.

        Args:
            query: Search query string

        Returns:
            List of SearchResult objects, ranked by relevance
        """
        if not query or not query.strip():
            return []

        cursor = self._conn.cursor()

        # FTS5 search with ranking
        cursor.execute(
            """
            SELECT
                r.filepath,
                r.source,
                r.timestamp,
                r.summary,
                r.transcript,
                bm25(recordings_fts) as rank
            FROM recordings_fts fts
            JOIN recordings r ON fts.filepath = r.filepath
            WHERE recordings_fts MATCH ?
            ORDER BY rank
        """,
            (query,),
        )

        results = []
        for row in cursor.fetchall():
            # Create snippet from summary or transcript
            summary = row["summary"] or ""
            transcript = row["transcript"] or ""
            snippet = summary if summary else transcript[:200]

            results.append(
                SearchResult(
                    filepath=Path(row["filepath"]),
                    source=row["source"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    summary_snippet=snippet,
                    relevance_score=abs(row["rank"]),  # BM25 returns negative scores
                )
            )

        return results

    def filter(
        self,
        source: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tags: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Filter recordings by metadata criteria.

        Args:
            source: Filter by source type (zoom, youtube, etc.)
            start_date: Include recordings on or after this date
            end_date: Include recordings on or before this date
            tags: Include recordings that have ALL specified tags

        Returns:
            List of SearchResult objects matching the criteria
        """
        cursor = self._conn.cursor()

        # Build dynamic query
        conditions = []
        params = []

        if source:
            conditions.append("source = ?")
            params.append(source)

        if start_date:
            conditions.append("date(timestamp) >= ?")
            params.append(start_date.isoformat())

        if end_date:
            conditions.append("date(timestamp) <= ?")
            params.append(end_date.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor.execute(
            f"""
            SELECT filepath, source, timestamp, summary, tags
            FROM recordings
            WHERE {where_clause}
            ORDER BY timestamp DESC
        """,
            params,
        )

        results = []
        for row in cursor.fetchall():
            # Filter by tags if specified
            if tags:
                row_tags = json.loads(row["tags"]) if row["tags"] else []
                if not all(tag in row_tags for tag in tags):
                    continue

            results.append(
                SearchResult(
                    filepath=Path(row["filepath"]),
                    source=row["source"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    summary_snippet=row["summary"] or "",
                    relevance_score=1.0,  # No ranking for filter results
                )
            )

        return results

    def rebuild_index(self, base_dir: Path) -> None:
        """Rebuild the index from Markdown files in a directory.

        Clears existing entries and re-indexes all recordings found.

        Args:
            base_dir: Base directory containing recording Markdown files
        """
        cursor = self._conn.cursor()

        # Clear existing data
        cursor.execute("DELETE FROM recordings")
        cursor.execute("DELETE FROM recordings_fts")
        self._conn.commit()

        # Re-index all files
        for filepath in list_recordings(base_dir):
            try:
                recording = load_recording(filepath)
                self.add_recording(filepath, recording)
            except (ValueError, KeyError) as e:
                # Skip malformed files
                print(f"Warning: Skipping {filepath}: {e}")

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
