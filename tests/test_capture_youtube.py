"""Tests for YouTube audio extraction (Ticket 2.2).

Tests cover:
- download_audio() function for extracting audio from YouTube
- YouTubeResult model with video metadata
- Audio format conversion to WAV (16kHz mono for Whisper)
- Error handling for invalid URLs, unavailable videos
- Progress callback support
"""

from datetime import datetime
from pathlib import Path

import pytest


class TestYouTubeResult:
    """Test YouTubeResult model."""

    def test_youtube_result_has_required_fields(self):
        """Test that YouTubeResult has all required fields."""
        from recall.capture.youtube import YouTubeResult

        result = YouTubeResult(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            duration_seconds=300,
            uploader="Test Channel",
            audio_path=Path("/path/to/audio.wav"),
        )

        assert result.video_id == "dQw4w9WgXcQ"
        assert result.title == "Test Video"
        assert result.duration_seconds == 300
        assert result.uploader == "Test Channel"
        assert result.audio_path == Path("/path/to/audio.wav")

    def test_youtube_result_optional_fields(self):
        """Test that YouTubeResult has optional fields with defaults."""
        from recall.capture.youtube import YouTubeResult

        result = YouTubeResult(
            video_id="abc123",
            title="Test",
            duration_seconds=60,
            uploader="Channel",
            audio_path=Path("/audio.wav"),
        )

        # Optional fields should have None or default values
        assert result.upload_date is None
        assert result.description is None
        assert result.thumbnail_url is None

    def test_youtube_result_with_all_fields(self):
        """Test YouTubeResult with all optional fields populated."""
        from recall.capture.youtube import YouTubeResult

        result = YouTubeResult(
            video_id="abc123",
            title="Full Video",
            duration_seconds=600,
            uploader="Full Channel",
            audio_path=Path("/audio.wav"),
            upload_date=datetime(2025, 11, 25),
            description="This is a test video description.",
            thumbnail_url="https://example.com/thumb.jpg",
        )

        assert result.upload_date == datetime(2025, 11, 25)
        assert result.description == "This is a test video description."
        assert result.thumbnail_url == "https://example.com/thumb.jpg"


class TestDownloadAudio:
    """Test download_audio() function."""

    def test_download_audio_returns_youtube_result(self, temp_storage_dir, mock_ytdlp):
        """Test that download_audio returns YouTubeResult."""
        from recall.capture.youtube import YouTubeResult, download_audio

        result = download_audio(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            output_dir=temp_storage_dir,
        )

        assert isinstance(result, YouTubeResult)

    def test_download_audio_creates_wav_file(self, temp_storage_dir, mock_ytdlp):
        """Test that download_audio creates a WAV file."""
        from recall.capture.youtube import download_audio

        result = download_audio(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            output_dir=temp_storage_dir,
        )

        assert result.audio_path.exists()
        assert result.audio_path.suffix == ".wav"

    def test_download_audio_extracts_metadata(self, temp_storage_dir, mock_ytdlp):
        """Test that download_audio extracts video metadata."""
        from recall.capture.youtube import download_audio

        result = download_audio(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            output_dir=temp_storage_dir,
        )

        assert result.title == "Test Video Title"
        assert result.duration_seconds == 300
        assert result.uploader == "Test Channel"
        assert result.video_id == "dQw4w9WgXcQ"

    def test_download_audio_filename_format(self, temp_storage_dir, mock_ytdlp):
        """Test that filename follows youtube_{video_id}.wav format."""
        from recall.capture.youtube import download_audio

        result = download_audio(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            output_dir=temp_storage_dir,
        )

        assert result.audio_path.name.startswith("youtube_")
        assert "dQw4w9WgXcQ" in result.audio_path.name
        assert result.audio_path.name.endswith(".wav")

    def test_download_audio_calls_ytdlp_correctly(self, temp_storage_dir, mock_ytdlp):
        """Test that download_audio uses yt-dlp with correct options."""
        from recall.capture.youtube import download_audio

        download_audio(
            url="https://www.youtube.com/watch?v=test123",
            output_dir=temp_storage_dir,
        )

        # Verify yt-dlp was called (the mock is the YoutubeDL class itself)
        mock_ytdlp.assert_called_once()

    def test_download_audio_accepts_short_url(self, temp_storage_dir, mock_ytdlp):
        """Test that download_audio accepts youtu.be short URLs."""
        from recall.capture.youtube import YouTubeResult, download_audio

        result = download_audio(
            url="https://youtu.be/dQw4w9WgXcQ",
            output_dir=temp_storage_dir,
        )

        assert isinstance(result, YouTubeResult)

    def test_download_audio_creates_output_dir(self, tmp_path, mock_ytdlp):
        """Test that download_audio creates output directory if missing."""
        from recall.capture.youtube import download_audio

        new_dir = tmp_path / "youtube" / "downloads"
        download_audio(
            url="https://www.youtube.com/watch?v=test123",
            output_dir=new_dir,
        )

        assert new_dir.exists()


class TestDownloadAudioErrors:
    """Test error handling for download_audio."""

    def test_download_audio_invalid_url_raises_error(self, temp_storage_dir, mock_ytdlp):
        """Test that invalid URL raises YouTubeError."""
        from recall.capture.youtube import YouTubeError, download_audio

        # Configure mock to raise error - the mock is the YoutubeDL class directly
        mock_ytdlp.return_value.__enter__.return_value.extract_info.side_effect = Exception(
            "Invalid URL"
        )

        with pytest.raises(YouTubeError) as exc_info:
            download_audio(
                url="https://invalid-url.com/video",
                output_dir=temp_storage_dir,
            )

        assert "download" in str(exc_info.value).lower() or "url" in str(exc_info.value).lower()

    def test_download_audio_unavailable_video_raises_error(self, temp_storage_dir, mock_ytdlp):
        """Test that unavailable video raises YouTubeError."""
        from recall.capture.youtube import YouTubeError, download_audio

        # Configure mock to raise error for unavailable video
        mock_ytdlp.return_value.__enter__.return_value.extract_info.side_effect = Exception(
            "Video unavailable"
        )

        with pytest.raises(YouTubeError):
            download_audio(
                url="https://www.youtube.com/watch?v=unavailable",
                output_dir=temp_storage_dir,
            )


class TestWAVConversion:
    """Test WAV conversion for Whisper compatibility."""

    def test_download_audio_wav_is_16khz(self, temp_storage_dir, mock_ytdlp):
        """Test that output WAV is 16kHz sample rate."""
        import wave

        from recall.capture.youtube import download_audio

        result = download_audio(
            url="https://www.youtube.com/watch?v=test",
            output_dir=temp_storage_dir,
        )

        with wave.open(str(result.audio_path), "rb") as wav:
            assert wav.getframerate() == 16000

    def test_download_audio_wav_is_mono(self, temp_storage_dir, mock_ytdlp):
        """Test that output WAV is mono."""
        import wave

        from recall.capture.youtube import download_audio

        result = download_audio(
            url="https://www.youtube.com/watch?v=test",
            output_dir=temp_storage_dir,
        )

        with wave.open(str(result.audio_path), "rb") as wav:
            assert wav.getnchannels() == 1


class TestProgressCallback:
    """Test progress callback support."""

    def test_download_audio_accepts_progress_callback(self, temp_storage_dir, mock_ytdlp):
        """Test that download_audio accepts optional progress callback."""
        from recall.capture.youtube import download_audio

        progress_calls = []

        def progress_callback(d):
            progress_calls.append(d)

        # Should not raise
        download_audio(
            url="https://www.youtube.com/watch?v=test",
            output_dir=temp_storage_dir,
            progress_callback=progress_callback,
        )

        # Callback should have been set up - check that YoutubeDL was called with options
        mock_ytdlp.assert_called()
