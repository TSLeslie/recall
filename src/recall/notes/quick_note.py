"""Text Quick Notes for Recall.

This module provides text note-taking functionality:
- create_note() - create and save text notes
- append_to_note() - add content to existing notes
- list_notes() - retrieve all notes

Notes are stored as Markdown files with YAML frontmatter,
just like recordings, but with source="note".
"""

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from recall.analyze import LlamaAnalyzer
from recall.config import get_default_config
from recall.storage.index import RecordingIndex
from recall.storage.markdown import list_recordings, load_recording, save_recording
from recall.storage.models import Recording

if TYPE_CHECKING:
    from recall.knowledge.graphrag import RecallGraphRAG

# Threshold for using LLM vs simple truncation for summary
SUMMARY_THRESHOLD_CHARS = 100


def create_note(
    content: str,
    base_dir: Optional[Path] = None,
    tags: Optional[List[str]] = None,
    title: Optional[str] = None,
    index_db: Optional[Path] = None,
    model_path: Optional[str] = None,
    graphrag: Optional["RecallGraphRAG"] = None,
) -> Recording:
    """Create a text note and save it.

    Creates a Recording with source="note", saves it as a Markdown file,
    and optionally indexes it for searching.

    Args:
        content: The note content/text
        base_dir: Base directory for notes storage (default: ~/.recall/notes/)
        tags: Optional list of tags for categorization
        title: Optional title for the note
        index_db: Path to SQLite index database (None to skip indexing)
        model_path: Path to LLM model for summary generation (optional)
        graphrag: Optional RecallGraphRAG instance for knowledge base ingestion

    Returns:
        Recording instance representing the saved note
    """
    if base_dir is None:
        config = get_default_config()
        base_dir = config.storage_dir / "notes"

    # Generate summary
    summary = _generate_summary(content, model_path)

    # Create Recording with source="note"
    recording = Recording.create_new(
        source="note",
        transcript=content,
        title=title,
        summary=summary,
        tags=tags or [],
    )

    # Save to Markdown file
    filepath = save_recording(recording, base_dir)

    # Optionally index for search
    if index_db is not None:
        index = RecordingIndex(str(index_db))
        index.add_recording(filepath, recording)

    # Optionally ingest to GraphRAG knowledge base
    if graphrag is not None:
        _ingest_to_graphrag(recording, graphrag)

    return recording


def _ingest_to_graphrag(recording: Recording, graphrag: "RecallGraphRAG") -> None:
    """Ingest a note into the GraphRAG knowledge base.

    Args:
        recording: The Recording to ingest
        graphrag: The RecallGraphRAG instance
    """
    # Format note content with metadata for ingestion
    metadata_lines = [
        f"Source: {recording.source}",
        f"Timestamp: {recording.timestamp.isoformat()}",
    ]
    if recording.title:
        metadata_lines.append(f"Title: {recording.title}")
    if recording.tags:
        metadata_lines.append(f"Tags: {', '.join(recording.tags)}")
    if recording.summary:
        metadata_lines.append(f"Summary: {recording.summary}")

    formatted_text = "\n".join(metadata_lines) + "\n\n" + recording.transcript
    graphrag.insert(formatted_text)


def _generate_summary(content: str, model_path: Optional[str] = None) -> str:
    """Generate a summary for note content.

    For short content (< SUMMARY_THRESHOLD_CHARS), uses the content itself.
    For longer content, uses LLM to generate a summary.

    Args:
        content: The note content
        model_path: Path to LLM model (optional, uses default if not provided)

    Returns:
        Summary string
    """
    if len(content) <= SUMMARY_THRESHOLD_CHARS:
        # Short content - use as-is for summary
        return content

    # Long content - try to use LLM
    if model_path is None:
        try:
            config = get_default_config()
            model_path = str(config.llm_model_path)
        except Exception:
            # No model available, fallback to truncation
            return content[:SUMMARY_THRESHOLD_CHARS] + "..."

    try:
        analyzer = LlamaAnalyzer(model_path, n_ctx=4096)
        summary_result = analyzer.generate_summary(content)
        return summary_result.brief
    except Exception:
        # LLM failed, fallback to truncation
        return content[:SUMMARY_THRESHOLD_CHARS] + "..."


def append_to_note(filepath: Path, content: str) -> Recording:
    """Append content to an existing note.

    Loads the note, appends the new content to the transcript,
    and saves the updated note back to the same file.

    Args:
        filepath: Path to the existing note Markdown file
        content: Content to append

    Returns:
        Updated Recording instance

    Raises:
        FileNotFoundError: If the note file doesn't exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Note file not found: {filepath}")

    # Load existing note
    recording = load_recording(filepath)

    # Create updated recording with appended content
    updated = Recording(
        id=recording.id,
        source=recording.source,
        timestamp=recording.timestamp,
        transcript=recording.transcript + content,
        title=recording.title,
        duration_seconds=recording.duration_seconds,
        summary=recording.summary,
        participants=recording.participants,
        tags=recording.tags,
        source_url=recording.source_url,
        audio_path=recording.audio_path,
    )

    # Save back to same location
    # We need to rewrite the file with updated content
    _save_to_existing_path(updated, filepath)

    return updated


def _save_to_existing_path(recording: Recording, filepath: Path) -> None:
    """Save a recording to a specific filepath.

    Unlike save_recording which generates the path from timestamp,
    this writes directly to the given path.

    Args:
        recording: The Recording to save
        filepath: Exact path to write to
    """
    import yaml

    # Build file content
    frontmatter = recording.to_frontmatter_dict()
    frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    content = f"---\n{frontmatter_yaml}---\n\n{recording.transcript}\n"

    # Write file
    filepath.write_text(content)


def list_notes(base_dir: Optional[Path] = None, limit: Optional[int] = None) -> List[Recording]:
    """List all notes in the notes directory.

    Args:
        base_dir: Base directory for notes (default: ~/.recall/notes/)
        limit: Maximum number of notes to return (default: all)

    Returns:
        List of Recording objects for all notes, sorted chronologically (newest first)
    """
    if base_dir is None:
        config = get_default_config()
        base_dir = config.storage_dir / "notes"

    if not base_dir.exists():
        return []

    # Get all markdown files
    md_files = list_recordings(base_dir)

    # Load each as a Recording
    notes = []
    for filepath in md_files:
        try:
            recording = load_recording(filepath)
            notes.append(recording)
        except (ValueError, FileNotFoundError):
            # Skip malformed files
            continue

    # Sort by timestamp descending (newest first)
    notes.sort(key=lambda n: n.timestamp, reverse=True)

    # Apply limit if specified
    if limit is not None:
        notes = notes[:limit]

    return notes
