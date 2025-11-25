"""YouTube audio extraction module for Recall.

Provides functions for downloading and converting YouTube audio to WAV format
optimized for Whisper transcription.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import yt_dlp


class YouTubeError(Exception):
    """Error raised when YouTube operations fail."""

    pass


@dataclass
class YouTubeResult:
    """Result from downloading YouTube audio.

    Attributes:
        video_id: YouTube video ID.
        title: Video title.
        duration_seconds: Video duration in seconds.
        uploader: Channel name.
        audio_path: Path to downloaded WAV file.
        upload_date: Video upload date (optional).
        description: Video description (optional).
        thumbnail_url: URL to video thumbnail (optional).
    """

    video_id: str
    title: str
    duration_seconds: int
    uploader: str
    audio_path: Path
    upload_date: Optional[datetime] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


def download_audio(
    url: str,
    output_dir: Path,
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> YouTubeResult:
    """Download audio from YouTube video and convert to WAV.

    Downloads audio from a YouTube video URL, converts it to 16kHz mono WAV
    format suitable for Whisper transcription.

    Args:
        url: YouTube video URL (supports youtube.com and youtu.be).
        output_dir: Directory to save the audio file.
        progress_callback: Optional callback for download progress.

    Returns:
        YouTubeResult with video metadata and path to audio file.

    Raises:
        YouTubeError: If download or conversion fails.

    Example:
        >>> result = download_audio(
        ...     url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ...     output_dir=Path("./downloads")
        ... )
        >>> print(result.title)
        'Never Gonna Give You Up'
    """
    # Create output directory if needed
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Configure yt-dlp options
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "outtmpl": str(output_dir / "youtube_%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }

    # Add progress callback if provided
    if progress_callback:
        ydl_opts["progress_hooks"] = [progress_callback]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info = ydl.extract_info(url, download=True)

            # Get the output path
            video_id = info["id"]
            audio_path = output_dir / f"youtube_{video_id}.wav"

            # Parse upload date if available
            upload_date = None
            if info.get("upload_date"):
                try:
                    upload_date = datetime.strptime(info["upload_date"], "%Y%m%d")
                except ValueError:
                    pass

            # Convert to 16kHz mono if needed
            _convert_to_whisper_format(audio_path)

            return YouTubeResult(
                video_id=video_id,
                title=info.get("title", "Unknown"),
                duration_seconds=info.get("duration", 0),
                uploader=info.get("uploader", "Unknown"),
                audio_path=audio_path,
                upload_date=upload_date,
                description=info.get("description"),
                thumbnail_url=info.get("thumbnail"),
            )

    except Exception as e:
        raise YouTubeError(f"Failed to download audio from URL: {e}") from e


def _convert_to_whisper_format(audio_path: Path) -> None:
    """Convert audio file to 16kHz mono WAV format.

    Whisper works best with 16kHz mono audio. This function converts
    the downloaded audio to this format.

    Args:
        audio_path: Path to audio file to convert.
    """
    import subprocess

    temp_path = audio_path.with_suffix(".temp.wav")

    try:
        # Use ffmpeg to convert to 16kHz mono
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(audio_path),
                "-ar",
                "16000",  # 16kHz sample rate
                "-ac",
                "1",  # Mono
                "-y",  # Overwrite output
                str(temp_path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and temp_path.exists():
            # Replace original with converted file
            temp_path.replace(audio_path)
        else:
            # If conversion fails, keep original
            if temp_path.exists():
                temp_path.unlink()

    except FileNotFoundError:
        # ffmpeg not available, keep original file
        pass
