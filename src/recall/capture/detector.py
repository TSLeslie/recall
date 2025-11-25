"""Application Detector for identifying running audio applications.

This module detects running applications that might be producing audio,
such as meeting apps (Zoom, Teams), media apps (Spotify, VLC),
and browsers (Chrome, Firefox).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import psutil


class AudioAppCategory(Enum):
    """Categories of audio applications."""

    MEETING = "meeting"
    MEDIA = "media"
    BROWSER = "browser"
    OTHER = "other"


@dataclass
class AudioApp:
    """Represents a detected audio application.

    Attributes:
        name: Display name of the application
        process_name: System process name
        category: Category of the application
        pid: Process ID (optional)
        window_title: Window title if available (optional)
    """

    name: str
    process_name: str
    category: AudioAppCategory
    pid: Optional[int] = None
    window_title: Optional[str] = None


# Known audio applications mapping
# Format: process_name -> (display_name, category)
KNOWN_APPS: Dict[str, tuple] = {
    # Meeting apps
    "zoom.us": ("Zoom", AudioAppCategory.MEETING),
    "Microsoft Teams": ("Microsoft Teams", AudioAppCategory.MEETING),
    "Slack": ("Slack", AudioAppCategory.MEETING),
    "Discord": ("Discord", AudioAppCategory.MEETING),
    "Webex": ("Webex", AudioAppCategory.MEETING),
    "Skype": ("Skype", AudioAppCategory.MEETING),
    "FaceTime": ("FaceTime", AudioAppCategory.MEETING),
    "Google Meet": ("Google Meet", AudioAppCategory.MEETING),
    # Media apps
    "Spotify": ("Spotify", AudioAppCategory.MEDIA),
    "VLC": ("VLC", AudioAppCategory.MEDIA),
    "Music": ("Apple Music", AudioAppCategory.MEDIA),
    "iTunes": ("iTunes", AudioAppCategory.MEDIA),
    "QuickTime Player": ("QuickTime", AudioAppCategory.MEDIA),
    "Audacity": ("Audacity", AudioAppCategory.MEDIA),
    "mpv": ("mpv", AudioAppCategory.MEDIA),
    # Browsers
    "Google Chrome": ("Chrome", AudioAppCategory.BROWSER),
    "Firefox": ("Firefox", AudioAppCategory.BROWSER),
    "Safari": ("Safari", AudioAppCategory.BROWSER),
    "Arc": ("Arc", AudioAppCategory.BROWSER),
    "Brave Browser": ("Brave", AudioAppCategory.BROWSER),
    "Microsoft Edge": ("Edge", AudioAppCategory.BROWSER),
    "Opera": ("Opera", AudioAppCategory.BROWSER),
}


def get_running_audio_apps() -> List[AudioApp]:
    """Get list of running audio applications.

    Scans running processes and identifies known audio applications
    such as meeting apps, media players, and browsers.

    Returns:
        List of AudioApp objects for detected audio applications.
    """
    audio_apps: List[AudioApp] = []

    try:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                info = proc.info
                if info is None:
                    continue

                process_name = info.get("name", "")
                if not process_name:
                    continue

                if process_name in KNOWN_APPS:
                    display_name, category = KNOWN_APPS[process_name]
                    audio_apps.append(
                        AudioApp(
                            name=display_name,
                            process_name=process_name,
                            category=category,
                            pid=info.get("pid"),
                        )
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    return audio_apps


def is_meeting_app_running() -> bool:
    """Check if any meeting application is currently running.

    Returns:
        True if a meeting app (Zoom, Teams, etc.) is running.
    """
    apps = get_running_audio_apps()
    return any(app.category == AudioAppCategory.MEETING for app in apps)


def get_active_audio_app() -> Optional[AudioApp]:
    """Get the most likely active audio application.

    Returns the first meeting app if running, otherwise the first
    media app. Meeting apps take priority as they typically
    produce the most important audio content.

    Returns:
        The most relevant AudioApp, or None if no audio apps found.
    """
    apps = get_running_audio_apps()

    if not apps:
        return None

    # Meeting apps take priority
    for app in apps:
        if app.category == AudioAppCategory.MEETING:
            return app

    # Return first media or browser app
    for app in apps:
        if app.category in (AudioAppCategory.MEDIA, AudioAppCategory.BROWSER):
            return app

    # Return any app
    return apps[0] if apps else None
