"""Data models for Recall recordings and notes.

This module defines the core data structures used throughout Recall:
- Recording: The primary model for audio transcriptions and notes
"""

from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

# Valid source types for recordings
SourceType = Literal["zoom", "youtube", "microphone", "system", "note"]


class Recording(BaseModel):
    """A recording with transcript, metadata, and optional summary.

    This is the core data model for Recall. Each recording represents
    a transcribed audio source (meeting, video, voice note) or a text note.

    Attributes:
        id: Unique identifier (UUID format)
        source: Where the recording came from (zoom, youtube, etc.)
        timestamp: When the recording was created
        transcript: The full text content
        title: Optional title for the recording
        duration_seconds: Length of audio in seconds (if applicable)
        summary: AI-generated summary (if processed)
        participants: List of participant names (if detected)
        tags: User-defined or auto-generated tags
        source_url: Original URL for YouTube videos
        audio_path: Path to retained audio file (if kept)
    """

    id: str = Field(..., description="Unique identifier (UUID)")
    source: SourceType = Field(..., description="Recording source type")
    timestamp: datetime = Field(..., description="When recording was created")
    transcript: str = Field(..., min_length=1, description="Full transcript text")
    title: Optional[str] = Field(None, description="Recording title")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Audio duration")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    participants: Optional[List[str]] = Field(None, description="Participant names")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    source_url: Optional[str] = Field(None, description="Source URL (e.g., YouTube)")
    audio_path: Optional[Path] = Field(None, description="Path to audio file")

    @field_validator("transcript")
    @classmethod
    def transcript_not_empty(cls, v: str) -> str:
        """Ensure transcript is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("transcript cannot be empty")
        return v

    @classmethod
    def create_new(
        cls,
        source: SourceType,
        transcript: str,
        title: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        summary: Optional[str] = None,
        participants: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        source_url: Optional[str] = None,
        audio_path: Optional[Path] = None,
    ) -> "Recording":
        """Create a new Recording with auto-generated ID and current timestamp.

        This is the preferred way to create new recordings, as it handles
        ID generation and timestamp setting automatically.

        Args:
            source: Recording source type
            transcript: Full transcript text
            title: Optional title for the recording
            duration_seconds: Audio duration in seconds
            summary: AI-generated summary
            participants: List of participant names
            tags: Tags for categorization
            source_url: Original URL (for YouTube)
            audio_path: Path to retained audio file

        Returns:
            A new Recording instance with generated ID and current timestamp
        """
        return cls(
            id=str(uuid4()),
            source=source,
            timestamp=datetime.now(),
            transcript=transcript,
            title=title,
            duration_seconds=duration_seconds,
            summary=summary,
            participants=participants,
            tags=tags or [],
            source_url=source_url,
            audio_path=audio_path,
        )

    def to_frontmatter_dict(self) -> dict:
        """Convert Recording to a dict suitable for YAML frontmatter.

        The transcript is excluded (it goes in the Markdown body).
        None values are excluded for cleaner YAML output.
        Paths are converted to strings.
        Timestamps are converted to ISO format strings.

        Returns:
            Dictionary ready for YAML serialization
        """
        result = {
            "id": self.id,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }

        # Add optional fields only if they have values
        if self.title is not None:
            result["title"] = self.title
        if self.duration_seconds is not None:
            result["duration_seconds"] = self.duration_seconds
        if self.summary is not None:
            result["summary"] = self.summary
        if self.participants is not None:
            result["participants"] = self.participants
        if self.tags:  # Only include non-empty tags list
            result["tags"] = self.tags
        if self.source_url is not None:
            result["source_url"] = self.source_url
        if self.audio_path is not None:
            result["audio_path"] = str(self.audio_path)

        return result

    @classmethod
    def from_frontmatter_dict(cls, frontmatter: dict, transcript: str) -> "Recording":
        """Create a Recording from YAML frontmatter dict and transcript body.

        Args:
            frontmatter: Dictionary parsed from YAML frontmatter
            transcript: The Markdown body content (the transcript)

        Returns:
            Recording instance populated from the frontmatter and transcript
        """
        # Parse timestamp from ISO format string
        timestamp = frontmatter.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # Parse audio_path from string to Path
        audio_path = frontmatter.get("audio_path")
        if audio_path is not None:
            audio_path = Path(audio_path)

        return cls(
            id=frontmatter["id"],
            source=frontmatter["source"],
            timestamp=timestamp,
            transcript=transcript,
            title=frontmatter.get("title"),
            duration_seconds=frontmatter.get("duration_seconds"),
            summary=frontmatter.get("summary"),
            participants=frontmatter.get("participants"),
            tags=frontmatter.get("tags", []),
            source_url=frontmatter.get("source_url"),
            audio_path=audio_path,
        )
