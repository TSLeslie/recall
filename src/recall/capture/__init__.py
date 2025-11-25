"""Audio capture module for Recall.

This module provides components for capturing audio from various sources:
- Microphone recording
- System audio capture (via BlackHole on macOS)
- YouTube audio extraction
- Application detection
"""

from recall.capture.detector import (
    AudioApp,
    AudioAppCategory,
    get_active_audio_app,
    get_running_audio_apps,
    is_meeting_app_running,
)
from recall.capture.monitor import (
    AudioEvent,
    AudioMonitor,
    is_blackhole_available,
)
from recall.capture.recorder import (
    AudioDevice,
    DeviceNotFoundError,
    Recorder,
    RecordingError,
)
from recall.capture.youtube import (
    YouTubeError,
    YouTubeResult,
    download_audio,
)

__all__ = [
    "AudioApp",
    "AudioAppCategory",
    "AudioEvent",
    "AudioMonitor",
    "get_active_audio_app",
    "get_running_audio_apps",
    "is_blackhole_available",
    "is_meeting_app_running",
    "Recorder",
    "AudioDevice",
    "RecordingError",
    "DeviceNotFoundError",
    "YouTubeResult",
    "YouTubeError",
    "download_audio",
]
