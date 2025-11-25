"""Recording ingestion to GraphRAG (Ticket 4.2).

This module provides functions for adding recordings to the knowledge base:
- Chunking transcripts into manageable segments
- Including metadata with each chunk
- Bulk ingestion of multiple recordings
- Tracking ingested recordings to avoid duplicates
"""

import json
import logging
from pathlib import Path
from typing import Optional

from recall.knowledge.graphrag import RecallGraphRAG
from recall.storage.markdown import list_recordings, load_recording
from recall.storage.models import Recording

logger = logging.getLogger(__name__)

# Default chunk size in characters (roughly ~500 tokens)
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_OVERLAP = 200


def chunk_transcript(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split transcript into overlapping chunks.

    Chunks are split at word boundaries to preserve readability.
    Overlap ensures context is maintained between chunks.

    Args:
        text: The transcript text to chunk
        chunk_size: Target size for each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    words = text.split()
    current_chunk: list[str] = []
    current_length = 0

    for word in words:
        word_len = len(word) + 1  # +1 for space

        if current_length + word_len > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(" ".join(current_chunk))

            # Start new chunk with overlap
            # Keep last few words for context
            overlap_words = []
            overlap_length = 0
            for w in reversed(current_chunk):
                if overlap_length + len(w) + 1 > overlap:
                    break
                overlap_words.insert(0, w)
                overlap_length += len(w) + 1

            current_chunk = overlap_words
            current_length = overlap_length

        current_chunk.append(word)
        current_length += word_len

    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def ingest_recording(
    recording: Recording,
    graphrag: RecallGraphRAG,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> int:
    """Ingest a recording into the GraphRAG knowledge base.

    Chunks the transcript and inserts each chunk with metadata.

    Args:
        recording: The Recording to ingest
        graphrag: The GraphRAG instance to insert into
        chunk_size: Size of transcript chunks

    Returns:
        Number of chunks inserted
    """
    # Create metadata for this recording
    metadata = {
        "source": recording.source,
        "timestamp": recording.timestamp.isoformat(),
        "recording_id": recording.id,
    }

    if recording.title:
        metadata["title"] = recording.title
    if recording.summary:
        metadata["summary"] = recording.summary
    if recording.participants:
        metadata["participants"] = ", ".join(recording.participants)
    if recording.tags:
        metadata["tags"] = ", ".join(recording.tags)

    # Chunk and insert transcript
    chunks = chunk_transcript(recording.transcript, chunk_size=chunk_size)

    for i, chunk in enumerate(chunks):
        chunk_metadata = {**metadata, "chunk": f"{i + 1}/{len(chunks)}"}
        graphrag.insert(chunk, metadata=chunk_metadata)

    logger.info(f"Ingested recording {recording.id} ({len(chunks)} chunks)")
    return len(chunks)


def ingest_all(
    base_dir: Path,
    graphrag: RecallGraphRAG,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> int:
    """Ingest all recordings from a directory into GraphRAG.

    Args:
        base_dir: Base directory containing recordings
        graphrag: The GraphRAG instance to insert into
        chunk_size: Size of transcript chunks

    Returns:
        Number of recordings ingested
    """
    md_files = list_recordings(base_dir)
    count = 0

    for filepath in md_files:
        try:
            recording = load_recording(filepath)
            ingest_recording(recording, graphrag, chunk_size=chunk_size)
            count += 1
        except Exception as e:
            logger.error(f"Failed to ingest {filepath}: {e}")

    logger.info(f"Ingested {count} recordings from {base_dir}")
    return count


class KnowledgeIngestor:
    """Manages recording ingestion with state tracking.

    Tracks which recordings have been ingested to avoid duplicates
    and supports incremental sync.

    Example:
        >>> ingestor = KnowledgeIngestor(graphrag)
        >>> ingestor.sync_knowledge_base(Path("~/.recall/recordings"))
    """

    def __init__(
        self,
        graphrag: RecallGraphRAG,
        state_file: Optional[Path] = None,
    ):
        """Initialize the ingestor.

        Args:
            graphrag: The GraphRAG instance to use
            state_file: Path to state file for tracking ingested recordings
        """
        self.graphrag = graphrag
        self.state_file = state_file or Path.home() / ".recall" / "ingest_state.json"
        self._state: dict = self._load_state()

    def _load_state(self) -> dict:
        """Load ingestion state from file."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load state file: {e}")
        return {"ingested": {}}

    def _save_state(self) -> None:
        """Save ingestion state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state, indent=2))

    def is_ingested(self, recording_id: str) -> bool:
        """Check if a recording has been ingested.

        Args:
            recording_id: The recording ID to check

        Returns:
            True if already ingested
        """
        return recording_id in self._state.get("ingested", {})

    def ingest_recording(
        self,
        recording: Recording,
        filepath: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> bool:
        """Ingest a recording if not already ingested.

        Args:
            recording: The Recording to ingest
            filepath: Path to the recording file
            chunk_size: Size of transcript chunks

        Returns:
            True if ingested, False if skipped (already ingested)
        """
        if self.is_ingested(recording.id):
            logger.debug(f"Skipping already ingested recording: {recording.id}")
            return False

        chunks = ingest_recording(recording, self.graphrag, chunk_size=chunk_size)

        # Track as ingested
        self._state.setdefault("ingested", {})[recording.id] = {
            "filepath": str(filepath),
            "timestamp": recording.timestamp.isoformat(),
            "chunks": chunks,
        }
        self._save_state()

        return True

    def sync_knowledge_base(self, base_dir: Path) -> tuple[int, int]:
        """Sync the knowledge base with recordings directory.

        Adds new recordings and detects removed ones.

        Args:
            base_dir: Base directory containing recordings

        Returns:
            Tuple of (added_count, removed_count)
        """
        md_files = list_recordings(base_dir)
        current_files = {str(f) for f in md_files}

        added = 0
        removed = 0

        # Add new recordings
        for filepath in md_files:
            try:
                recording = load_recording(filepath)
                if self.ingest_recording(recording, filepath):
                    added += 1
            except Exception as e:
                logger.error(f"Failed to sync {filepath}: {e}")

        # Detect removed recordings
        ingested = self._state.get("ingested", {})
        to_remove = []

        for rec_id, info in ingested.items():
            if info.get("filepath") not in current_files:
                to_remove.append(rec_id)
                removed += 1

        # Remove from state
        for rec_id in to_remove:
            del self._state["ingested"][rec_id]

        if to_remove:
            self._save_state()

        logger.info(f"Sync complete: {added} added, {removed} removed")
        return added, removed
