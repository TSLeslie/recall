"""Audio transcription using Whisper AI."""

import whisper
from typing import Optional, Dict, Any
from pathlib import Path


def transcribe(
    audio_path: str,
    model: str = "base",
    language: Optional[str] = None,
    task: str = "transcribe",
    **kwargs
) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI's Whisper model.

    Args:
        audio_path: Path to the audio file
        model: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        language: Language code (e.g., 'en', 'es'). None for auto-detection
        task: Either 'transcribe' or 'translate'
        **kwargs: Additional arguments passed to whisper.transcribe()

    Returns:
        Dictionary containing transcription results with keys:
        - text: Full transcription text
        - segments: List of timestamped segments
        - language: Detected language
    """
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Load the Whisper model
    print(f"Loading Whisper {model} model...")
    whisper_model = whisper.load_model(model)

    # Transcribe the audio
    print(f"Transcribing {audio_path}...")
    result = whisper_model.transcribe(
        audio_path,
        language=language,
        task=task,
        **kwargs
    )

    return result


def transcribe_with_timestamps(
    audio_path: str,
    model: str = "base",
    **kwargs
) -> Dict[str, Any]:
    """
    Transcribe audio with detailed timestamp information.

    Args:
        audio_path: Path to the audio file
        model: Whisper model size
        **kwargs: Additional arguments

    Returns:
        Dictionary with transcription and detailed timestamps
    """
    result = transcribe(audio_path, model=model, **kwargs)

    # Format segments with cleaner timestamp info
    formatted_segments = []
    for segment in result.get("segments", []):
        formatted_segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip(),
            "confidence": segment.get("no_speech_prob", 0.0)
        })

    return {
        "text": result["text"],
        "language": result.get("language", "unknown"),
        "segments": formatted_segments
    }
