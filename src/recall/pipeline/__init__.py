"""Pipeline module for Recall.

This module provides the audio ingestion pipeline that orchestrates:
- Whisper transcription
- LLM summarization
- Markdown storage
"""

from recall.pipeline.ingest import IngestError, ingest_audio
from recall.pipeline.progress import ProgressEvent

__all__ = [
    "ingest_audio",
    "IngestError",
    "ProgressEvent",
]
