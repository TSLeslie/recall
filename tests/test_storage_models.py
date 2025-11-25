"""Tests for Recording data model (Ticket 1.1).

Tests cover:
- Model creation with required fields
- Model creation with all optional fields
- Validation of source field (must be allowed value)
- Auto-generation of ID and timestamp via create_new()
- Serialization to/from dict for YAML frontmatter
- Type validation and constraints
"""

from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest
from freezegun import freeze_time


class TestRecordingModel:
    """Test Recording Pydantic model."""

    def test_recording_creation_with_required_fields(self):
        """Test that Recording can be created with minimum required fields."""
        from recall.storage.models import Recording

        recording = Recording(
            id="test-id-123",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 14, 30),
            transcript="This is the transcript content.",
        )

        assert recording.id == "test-id-123"
        assert recording.source == "zoom"
        assert recording.timestamp == datetime(2025, 11, 25, 14, 30)
        assert recording.transcript == "This is the transcript content."

    def test_recording_creation_with_all_fields(self):
        """Test that Recording can be created with all optional fields."""
        from recall.storage.models import Recording

        recording = Recording(
            id="full-recording-456",
            source="youtube",
            timestamp=datetime(2025, 11, 25, 10, 0),
            duration_seconds=1800,
            transcript="Full transcript with all details.",
            summary="A comprehensive summary.",
            participants=["Alice", "Bob", "Charlie"],
            tags=["meeting", "q4", "budget"],
            source_url="https://youtube.com/watch?v=abc123",
            audio_path=Path("/path/to/audio.wav"),
        )

        assert recording.id == "full-recording-456"
        assert recording.source == "youtube"
        assert recording.duration_seconds == 1800
        assert recording.summary == "A comprehensive summary."
        assert recording.participants == ["Alice", "Bob", "Charlie"]
        assert recording.tags == ["meeting", "q4", "budget"]
        assert recording.source_url == "https://youtube.com/watch?v=abc123"
        assert recording.audio_path == Path("/path/to/audio.wav")

    def test_recording_default_values(self):
        """Test that optional fields have correct defaults."""
        from recall.storage.models import Recording

        recording = Recording(
            id="defaults-test",
            source="microphone",
            timestamp=datetime(2025, 11, 25, 9, 0),
            transcript="Simple transcript.",
        )

        assert recording.duration_seconds is None
        assert recording.summary is None
        assert recording.participants is None
        assert recording.tags == []
        assert recording.source_url is None
        assert recording.audio_path is None

    @pytest.mark.parametrize(
        "source",
        ["zoom", "youtube", "microphone", "system", "note"],
    )
    def test_recording_accepts_valid_sources(self, source):
        """Test that all valid source values are accepted."""
        from recall.storage.models import Recording

        recording = Recording(
            id="source-test",
            source=source,
            timestamp=datetime(2025, 11, 25, 12, 0),
            transcript="Test transcript.",
        )

        assert recording.source == source

    def test_recording_rejects_invalid_source(self):
        """Test that invalid source values raise validation error."""
        from pydantic import ValidationError

        from recall.storage.models import Recording

        with pytest.raises(ValidationError) as exc_info:
            Recording(
                id="invalid-source",
                source="invalid_source",
                timestamp=datetime(2025, 11, 25, 12, 0),
                transcript="Test transcript.",
            )

        assert "source" in str(exc_info.value).lower()

    def test_recording_rejects_empty_transcript(self):
        """Test that empty transcript raises validation error."""
        from pydantic import ValidationError

        from recall.storage.models import Recording

        with pytest.raises(ValidationError):
            Recording(
                id="empty-transcript",
                source="microphone",
                timestamp=datetime(2025, 11, 25, 12, 0),
                transcript="",
            )


class TestRecordingCreateNew:
    """Test Recording.create_new() factory method."""

    @freeze_time("2025-11-25 14:30:00")
    def test_create_new_generates_uuid(self):
        """Test that create_new generates a valid UUID for id."""
        from recall.storage.models import Recording

        recording = Recording.create_new(
            source="microphone",
            transcript="Auto-generated ID test.",
        )

        # Verify id is a valid UUID
        uuid_obj = UUID(recording.id)
        assert str(uuid_obj) == recording.id

    @freeze_time("2025-11-25 14:30:00")
    def test_create_new_sets_current_timestamp(self):
        """Test that create_new sets timestamp to current time."""
        from recall.storage.models import Recording

        recording = Recording.create_new(
            source="zoom",
            transcript="Timestamp test.",
        )

        assert recording.timestamp == datetime(2025, 11, 25, 14, 30, 0)

    @freeze_time("2025-11-25 09:15:30")
    def test_create_new_with_optional_fields(self):
        """Test that create_new accepts optional fields."""
        from recall.storage.models import Recording

        recording = Recording.create_new(
            source="youtube",
            transcript="YouTube video transcript.",
            duration_seconds=600,
            summary="Video summary here.",
            participants=["Speaker 1"],
            tags=["tutorial", "python"],
            source_url="https://youtube.com/watch?v=xyz789",
        )

        assert recording.source == "youtube"
        assert recording.transcript == "YouTube video transcript."
        assert recording.duration_seconds == 600
        assert recording.summary == "Video summary here."
        assert recording.participants == ["Speaker 1"]
        assert recording.tags == ["tutorial", "python"]
        assert recording.source_url == "https://youtube.com/watch?v=xyz789"
        assert recording.timestamp == datetime(2025, 11, 25, 9, 15, 30)


class TestRecordingSerialization:
    """Test Recording serialization to/from dict for YAML frontmatter."""

    def test_to_frontmatter_dict(self):
        """Test that Recording serializes to dict suitable for YAML frontmatter."""
        from recall.storage.models import Recording

        recording = Recording(
            id="serialize-test",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 14, 30),
            duration_seconds=3600,
            transcript="Meeting transcript.",
            summary="Meeting summary.",
            participants=["Alice", "Bob"],
            tags=["meeting"],
            source_url=None,
            audio_path=Path("/audio/meeting.wav"),
        )

        frontmatter = recording.to_frontmatter_dict()

        assert frontmatter["id"] == "serialize-test"
        assert frontmatter["source"] == "zoom"
        assert frontmatter["timestamp"] == "2025-11-25T14:30:00"
        assert frontmatter["duration_seconds"] == 3600
        assert frontmatter["summary"] == "Meeting summary."
        assert frontmatter["participants"] == ["Alice", "Bob"]
        assert frontmatter["tags"] == ["meeting"]
        # transcript should NOT be in frontmatter (goes in body)
        assert "transcript" not in frontmatter
        # None values should be excluded
        assert "source_url" not in frontmatter
        # Path should be serialized as string
        assert frontmatter["audio_path"] == "/audio/meeting.wav"

    def test_from_frontmatter_dict(self):
        """Test that Recording can be created from frontmatter dict + transcript."""
        from recall.storage.models import Recording

        frontmatter = {
            "id": "deserialize-test",
            "source": "youtube",
            "timestamp": "2025-11-25T10:00:00",
            "duration_seconds": 1200,
            "summary": "Video summary.",
            "participants": ["Speaker"],
            "tags": ["video", "tutorial"],
            "source_url": "https://youtube.com/watch?v=test",
            "audio_path": "/audio/video.wav",
        }
        transcript = "This is the video transcript content."

        recording = Recording.from_frontmatter_dict(frontmatter, transcript)

        assert recording.id == "deserialize-test"
        assert recording.source == "youtube"
        assert recording.timestamp == datetime(2025, 11, 25, 10, 0)
        assert recording.duration_seconds == 1200
        assert recording.transcript == transcript
        assert recording.summary == "Video summary."
        assert recording.participants == ["Speaker"]
        assert recording.tags == ["video", "tutorial"]
        assert recording.source_url == "https://youtube.com/watch?v=test"
        assert recording.audio_path == Path("/audio/video.wav")

    def test_serialization_round_trip(self):
        """Test that Recording survives serialization round-trip."""
        from recall.storage.models import Recording

        original = Recording(
            id="round-trip-test",
            source="system",
            timestamp=datetime(2025, 11, 25, 16, 45),
            duration_seconds=900,
            transcript="System audio transcript.",
            summary="System audio summary.",
            participants=None,
            tags=["system", "audio"],
            source_url=None,
            audio_path=None,
        )

        # Serialize to frontmatter dict
        frontmatter = original.to_frontmatter_dict()
        transcript = original.transcript

        # Deserialize back
        restored = Recording.from_frontmatter_dict(frontmatter, transcript)

        # Compare all fields
        assert restored.id == original.id
        assert restored.source == original.source
        assert restored.timestamp == original.timestamp
        assert restored.duration_seconds == original.duration_seconds
        assert restored.transcript == original.transcript
        assert restored.summary == original.summary
        assert restored.participants == original.participants
        assert restored.tags == original.tags
        assert restored.source_url == original.source_url
        assert restored.audio_path == original.audio_path

    def test_from_frontmatter_dict_handles_missing_optional_fields(self):
        """Test that from_frontmatter_dict handles missing optional fields."""
        from recall.storage.models import Recording

        frontmatter = {
            "id": "minimal-test",
            "source": "note",
            "timestamp": "2025-11-25T08:00:00",
        }
        transcript = "Just a simple note."

        recording = Recording.from_frontmatter_dict(frontmatter, transcript)

        assert recording.id == "minimal-test"
        assert recording.source == "note"
        assert recording.transcript == transcript
        assert recording.duration_seconds is None
        assert recording.summary is None
        assert recording.participants is None
        assert recording.tags == []
        assert recording.source_url is None
        assert recording.audio_path is None
