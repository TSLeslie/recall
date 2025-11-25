"""Incremental Knowledge Updates (Ticket 4.4).

This module provides the KnowledgeSync class for tracking sync state,
detecting changes, and incrementally updating the knowledge base.

Features:
- File hash tracking for change detection
- Incremental sync (only process changed files)
- Force rebuild for full re-indexing
- State persistence across sessions
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from recall.knowledge.graphrag import RecallGraphRAG
from recall.knowledge.ingest import ingest_recording
from recall.storage.markdown import list_recordings, load_recording

logger = logging.getLogger(__name__)

# Default state file location
DEFAULT_STATE_FILE = Path.home() / ".recall" / "sync_state.json"


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file's contents.

    Args:
        filepath: Path to the file

    Returns:
        Hex string of the SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


@dataclass
class ChangeSet:
    """Set of changes detected in the recordings directory.

    Attributes:
        new: List of new files
        modified: List of modified files
        deleted: List of deleted files
    """

    new: list[Path] = field(default_factory=list)
    modified: list[Path] = field(default_factory=list)
    deleted: list[Path] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.new or self.modified or self.deleted)


@dataclass
class SyncResult:
    """Result of a sync operation.

    Attributes:
        added: Number of files added
        modified: Number of files updated
        deleted: Number of files removed
        errors: Number of errors encountered
    """

    added: int = 0
    modified: int = 0
    deleted: int = 0
    errors: int = 0

    @property
    def total(self) -> int:
        """Total number of changes processed."""
        return self.added + self.modified + self.deleted


class KnowledgeSync:
    """Manages incremental synchronization of recordings to knowledge base.

    Tracks file hashes to detect changes and only processes modified files.
    State is persisted to a JSON file for continuity across sessions.

    Example:
        >>> sync = KnowledgeSync(graphrag)
        >>> result = sync.sync(Path("~/.recall/recordings"))
        >>> print(f"Added {result.added}, modified {result.modified}")
    """

    def __init__(
        self,
        graphrag: RecallGraphRAG,
        state_file: Optional[Path] = None,
    ):
        """Initialize KnowledgeSync.

        Args:
            graphrag: The GraphRAG instance to sync to
            state_file: Path to state file for persistence
        """
        self.graphrag = graphrag
        self.state_file = state_file or DEFAULT_STATE_FILE

        # Load or initialize state
        self._state = self._load_state()

    @property
    def last_sync(self) -> Optional[datetime]:
        """Get the timestamp of the last sync."""
        ts = self._state.get("last_sync")
        if ts:
            return datetime.fromisoformat(ts)
        return None

    @property
    def file_hashes(self) -> dict[str, str]:
        """Get the current file hash map."""
        return self._state.get("file_hashes", {})

    def _load_state(self) -> dict:
        """Load state from file."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load sync state: {e}")
        return {"last_sync": None, "file_hashes": {}}

    def _save_state(self) -> None:
        """Save state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state, indent=2))

    def get_pending_changes(self, base_dir: Path) -> ChangeSet:
        """Detect pending changes in the recordings directory.

        Compares current files against stored hashes to identify
        new, modified, and deleted files.

        Args:
            base_dir: Base directory to scan for recordings

        Returns:
            ChangeSet with lists of changed files
        """
        changes = ChangeSet()
        current_files = {str(f): f for f in list_recordings(base_dir)}
        stored_hashes = self.file_hashes

        # Check for new and modified files
        for filepath_str, filepath in current_files.items():
            current_hash = compute_file_hash(filepath)

            if filepath_str not in stored_hashes:
                changes.new.append(filepath)
            elif stored_hashes[filepath_str] != current_hash:
                changes.modified.append(filepath)

        # Check for deleted files
        for filepath_str in stored_hashes:
            if filepath_str not in current_files:
                changes.deleted.append(Path(filepath_str))

        return changes

    def sync(self, base_dir: Path) -> SyncResult:
        """Synchronize recordings to the knowledge base.

        Only processes files that have changed since the last sync.

        Args:
            base_dir: Base directory containing recordings

        Returns:
            SyncResult with counts of processed files
        """
        changes = self.get_pending_changes(base_dir)
        result = SyncResult()

        # Process new files
        for filepath in changes.new:
            try:
                recording = load_recording(filepath)
                ingest_recording(recording, self.graphrag)
                self._state.setdefault("file_hashes", {})[str(filepath)] = compute_file_hash(
                    filepath
                )
                result.added += 1
            except Exception as e:
                logger.error(f"Failed to process new file {filepath}: {e}")
                result.errors += 1

        # Process modified files
        for filepath in changes.modified:
            try:
                recording = load_recording(filepath)
                ingest_recording(recording, self.graphrag)
                self._state["file_hashes"][str(filepath)] = compute_file_hash(filepath)
                result.modified += 1
            except Exception as e:
                logger.error(f"Failed to process modified file {filepath}: {e}")
                result.errors += 1

        # Handle deleted files
        for filepath in changes.deleted:
            filepath_str = str(filepath)
            if filepath_str in self._state.get("file_hashes", {}):
                del self._state["file_hashes"][filepath_str]
            result.deleted += 1

        # Update sync timestamp and save state
        self._state["last_sync"] = datetime.now().isoformat()
        self._save_state()

        logger.info(
            f"Sync complete: {result.added} added, {result.modified} modified, "
            f"{result.deleted} deleted, {result.errors} errors"
        )

        return result

    def force_rebuild(self, base_dir: Path) -> SyncResult:
        """Force a full rebuild of the knowledge base.

        Ignores existing state and reprocesses all files.

        Args:
            base_dir: Base directory containing recordings

        Returns:
            SyncResult with counts of processed files
        """
        # Clear existing state
        self._state = {"last_sync": None, "file_hashes": {}}

        # Run full sync
        return self.sync(base_dir)
