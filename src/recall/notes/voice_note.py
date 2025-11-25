"""Voice Quick Notes for Recall.

This module provides voice note-taking functionality:
- record_voice_note() - record audio for fixed duration, transcribe, and save
- start_voice_note() / stop_voice_note() - variable length voice notes

Voice notes are recorded from the microphone, transcribed using Whisper,
and saved as Markdown files with source="note".
"""

from pathlib import Path
from typing import List, Optional

from recall.analyze import LlamaAnalyzer
from recall.capture.recorder import Recorder
from recall.config import get_default_config
from recall.storage.markdown import save_recording
from recall.storage.models import Recording
from recall.transcribe import transcribe

# Threshold for using LLM vs simple truncation for summary
SUMMARY_THRESHOLD_CHARS = 100

# Module-level state for start/stop workflow
_current_recorder: Optional[Recorder] = None
_current_base_dir: Optional[Path] = None
_current_retain_audio: bool = False
_current_whisper_model: str = "base"
_current_tags: Optional[List[str]] = None


class VoiceNoteError(Exception):
    """Error raised for voice note operations."""

    pass


def record_voice_note(
    duration_seconds: int = 60,
    base_dir: Optional[Path] = None,
    retain_audio: bool = False,
    whisper_model: str = "base",
    tags: Optional[List[str]] = None,
    model_path: Optional[str] = None,
) -> Recording:
    """Record a voice note with fixed duration.

    Records audio from the microphone for the specified duration,
    transcribes it using Whisper, generates a summary, and saves
    as a Markdown file.

    Args:
        duration_seconds: Recording duration in seconds (default: 60)
        base_dir: Base directory for notes storage (default: ~/.recall/notes/)
        retain_audio: Whether to keep the audio file (default: False)
        whisper_model: Whisper model size (default: "base")
        tags: Optional list of tags for categorization
        model_path: Path to LLM model for summary generation

    Returns:
        Recording instance representing the saved voice note
    """
    if base_dir is None:
        config = get_default_config()
        base_dir = config.storage_dir / "notes"

    # Create recorder and record audio
    recorder = Recorder(output_dir=base_dir / "audio")
    audio_path = recorder.record(duration_seconds=duration_seconds)

    # Transcribe audio
    result = transcribe(str(audio_path), model=whisper_model)
    transcript = result.get("text", "").strip()

    if not transcript:
        transcript = "[No speech detected]"

    # Generate summary
    summary = _generate_summary(transcript, model_path)

    # Create Recording
    recording = Recording.create_new(
        source="note",
        transcript=transcript,
        summary=summary,
        duration_seconds=duration_seconds,
        tags=tags or [],
        audio_path=audio_path if retain_audio else None,
    )

    # Save to Markdown file
    save_recording(recording, base_dir)

    # Clean up audio if not retaining
    if not retain_audio and audio_path.exists():
        audio_path.unlink()

    return recording


def start_voice_note(
    base_dir: Optional[Path] = None,
    retain_audio: bool = False,
    whisper_model: str = "base",
    tags: Optional[List[str]] = None,
) -> None:
    """Start recording a variable-length voice note.

    Call stop_voice_note() to stop recording, transcribe, and save.

    Args:
        base_dir: Base directory for notes storage (default: ~/.recall/notes/)
        retain_audio: Whether to keep the audio file (default: False)
        whisper_model: Whisper model size (default: "base")
        tags: Optional list of tags for categorization
    """
    global _current_recorder, _current_base_dir, _current_retain_audio
    global _current_whisper_model, _current_tags

    if base_dir is None:
        config = get_default_config()
        base_dir = config.storage_dir / "notes"

    _current_base_dir = base_dir
    _current_retain_audio = retain_audio
    _current_whisper_model = whisper_model
    _current_tags = tags

    # Create recorder and start recording
    _current_recorder = Recorder(output_dir=base_dir / "audio")
    _current_recorder.start_recording()


def stop_voice_note(model_path: Optional[str] = None) -> Recording:
    """Stop recording and save the voice note.

    Must be called after start_voice_note().

    Args:
        model_path: Path to LLM model for summary generation

    Returns:
        Recording instance representing the saved voice note

    Raises:
        VoiceNoteError: If no recording is in progress
    """
    global _current_recorder, _current_base_dir, _current_retain_audio
    global _current_whisper_model, _current_tags

    if _current_recorder is None:
        raise VoiceNoteError("No voice note recording in progress")

    # Stop recording
    audio_path = _current_recorder.stop_recording()

    # Transcribe audio
    result = transcribe(str(audio_path), model=_current_whisper_model)
    transcript = result.get("text", "").strip()

    if not transcript:
        transcript = "[No speech detected]"

    # Generate summary
    summary = _generate_summary(transcript, model_path)

    # Create Recording
    recording = Recording.create_new(
        source="note",
        transcript=transcript,
        summary=summary,
        tags=_current_tags or [],
        audio_path=audio_path if _current_retain_audio else None,
    )

    # Save to Markdown file
    save_recording(recording, _current_base_dir)

    # Clean up audio if not retaining
    if not _current_retain_audio and audio_path.exists():
        audio_path.unlink()

    # Reset state
    _current_recorder = None
    _current_base_dir = None
    _current_retain_audio = False
    _current_whisper_model = "base"
    _current_tags = None

    return recording


def _generate_summary(transcript: str, model_path: Optional[str] = None) -> str:
    """Generate a summary for voice note transcript.

    For short content (< SUMMARY_THRESHOLD_CHARS), uses the content itself.
    For longer content, uses LLM to generate a summary.

    Args:
        transcript: The voice note transcript
        model_path: Path to LLM model (optional, uses default if not provided)

    Returns:
        Summary string
    """
    if len(transcript) <= SUMMARY_THRESHOLD_CHARS:
        # Short content - use as-is for summary
        return transcript

    # Long content - try to use LLM
    if model_path is None:
        try:
            config = get_default_config()
            model_path = str(config.llm_model_path)
        except Exception:
            # No model available, fallback to truncation
            return transcript[:SUMMARY_THRESHOLD_CHARS] + "..."

    try:
        analyzer = LlamaAnalyzer(model_path, n_ctx=4096)
        summary_result = analyzer.generate_summary(transcript)
        return summary_result.brief
    except Exception:
        # LLM failed, fallback to truncation
        return transcript[:SUMMARY_THRESHOLD_CHARS] + "..."
