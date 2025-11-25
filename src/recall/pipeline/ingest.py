"""Audio ingestion pipeline for Recall.

Orchestrates the process of:
1. Transcribing audio with Whisper
2. Generating structured summary with LLM
3. Saving as Markdown with metadata
"""

import wave
from pathlib import Path
from typing import Callable, Optional

from recall.analyze import generate_summary
from recall.config import DEFAULT_LLAMA_MODEL, get_model_path
from recall.pipeline.progress import ProgressEvent
from recall.storage.markdown import save_recording
from recall.storage.models import Recording
from recall.transcribe import transcribe


class IngestError(Exception):
    """Error raised when ingestion pipeline fails."""

    pass


def ingest_audio(
    audio_path: Path,
    source: str,
    storage_dir: Path,
    title: Optional[str] = None,
    tags: Optional[list[str]] = None,
    participants: Optional[list[str]] = None,
    skip_summary: bool = False,
    progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
) -> Recording:
    """Ingest audio file through transcription and summarization pipeline.

    This function orchestrates the full ingestion pipeline:
    1. Validates audio file exists
    2. Transcribes audio with Whisper
    3. Generates structured summary with LLM (unless skip_summary=True)
    4. Creates Recording model with metadata
    5. Saves to Markdown file

    Args:
        audio_path: Path to audio file (WAV, MP3, etc.).
        source: Source type ("microphone", "youtube", "zoom", etc.).
        storage_dir: Directory to save the Markdown transcript.
        title: Optional title for the recording.
        tags: Optional list of tags.
        participants: Optional list of participant names.
        skip_summary: If True, skip LLM summarization.
        progress_callback: Optional callback for progress events.

    Returns:
        Recording object with all metadata populated.

    Raises:
        IngestError: If any step in the pipeline fails.

    Example:
        >>> result = ingest_audio(
        ...     audio_path=Path("./meeting.wav"),
        ...     source="zoom",
        ...     storage_dir=Path("./transcripts"),
        ...     participants=["Alice", "Bob"]
        ... )
        >>> print(result.summary)
        'Meeting discussed Q4 roadmap...'
    """

    def _report_progress(stage: str, progress: float, message: str) -> None:
        """Report progress if callback is provided."""
        if progress_callback:
            event = ProgressEvent(stage=stage, progress=progress, message=message)
            progress_callback(event)

    audio_path = Path(audio_path)
    storage_dir = Path(storage_dir)

    # Report starting
    _report_progress("starting", 0.0, "Starting ingestion pipeline")

    # Validate audio file exists
    if not audio_path.exists():
        raise IngestError(f"Audio file not found: {audio_path}")

    # Get audio duration
    try:
        duration_seconds = _get_audio_duration(audio_path)
    except Exception:
        duration_seconds = 0

    # Step 1: Transcribe with Whisper
    _report_progress("transcribing", 0.1, "Transcribing audio with Whisper")
    try:
        transcription_result = transcribe(str(audio_path))
        transcript_text = transcription_result["text"]
    except Exception as e:
        raise IngestError(f"Transcription failed: {e}") from e

    # Step 2: Generate summary with LLM (optional)
    summary_text = "No summary generated"
    if not skip_summary:
        _report_progress("summarizing", 0.5, "Generating summary with LLM")
        try:
            # Get model path from config
            model_path = get_model_path(DEFAULT_LLAMA_MODEL)
            if model_path is None:
                raise IngestError(f"LLM model not found: {DEFAULT_LLAMA_MODEL}")

            summary_result = generate_summary(transcript_text, str(model_path))
            # Format summary from structured result
            summary_parts = [summary_result.brief]
            if summary_result.key_points:
                summary_parts.append("\n\nKey Points:")
                for point in summary_result.key_points:
                    summary_parts.append(f"- {point}")
            if summary_result.action_items:
                summary_parts.append("\n\nAction Items:")
                for item in summary_result.action_items:
                    summary_parts.append(f"- {item}")
            summary_text = "\n".join(summary_parts)
        except IngestError:
            raise
        except Exception:
            # If summary fails, continue with basic info
            summary_text = "Summary generation failed"

    # Step 3: Create Recording model
    recording = Recording.create_new(
        source=source,
        transcript=transcript_text,
        title=title,
        summary=summary_text,
        duration_seconds=duration_seconds,
        tags=tags or [],
        participants=participants or [],
    )

    # Step 4: Save to Markdown
    _report_progress("saving", 0.8, "Saving recording to Markdown")
    try:
        save_recording(recording, storage_dir)
    except Exception as e:
        raise IngestError(f"Failed to save recording: {e}") from e

    # Report completion
    _report_progress("completed", 1.0, "Ingestion completed successfully")

    return recording


def _get_audio_duration(audio_path: Path) -> int:
    """Get duration of audio file in seconds.

    Args:
        audio_path: Path to audio file.

    Returns:
        Duration in seconds.
    """
    with wave.open(str(audio_path), "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        duration = frames / float(rate)
        return int(duration)
