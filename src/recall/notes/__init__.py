"""Notes module for Recall.

This module provides quick note-taking capabilities:
- Text notes via create_note()
- Voice notes via record_voice_note()
- Note listing and management
"""

from .quick_note import append_to_note, create_note, list_notes
from .voice_note import (
    VoiceNoteError,
    record_voice_note,
    start_voice_note,
    stop_voice_note,
)

__all__ = [
    "create_note",
    "append_to_note",
    "list_notes",
    "record_voice_note",
    "start_voice_note",
    "stop_voice_note",
    "VoiceNoteError",
]
