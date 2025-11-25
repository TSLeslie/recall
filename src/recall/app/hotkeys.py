"""Global Hotkeys for Recall Menu Bar App.

This module provides:
- Global keyboard shortcuts using pynput
- Hotkey configuration
- Conflict detection
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

# Check if pynput is available
try:
    from pynput import keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False

logger = logging.getLogger(__name__)


# Modifier key mappings for display
MODIFIER_DISPLAY = {
    "cmd": "⌘",
    "super": "⌘",
    "ctrl": "⌃",
    "alt": "⌥",
    "option": "⌥",
    "shift": "⇧",
}


@dataclass
class HotkeyConfig:
    """Configuration for global hotkeys.

    Attributes:
        enabled: Whether hotkeys are enabled.
        toggle_recording: Hotkey for start/stop recording.
        quick_note: Hotkey for quick text note.
        voice_note: Hotkey for voice note.
        open_search: Hotkey for opening search.
    """

    enabled: bool = True
    toggle_recording: str = "<cmd>+<shift>+r"
    quick_note: str = "<cmd>+<shift>+n"
    voice_note: str = "<cmd>+<shift>+v"
    open_search: str = "<cmd>+<shift>+s"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HotkeyConfig":
        """Create config from a dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            HotkeyConfig instance.
        """
        return cls(
            enabled=data.get("enabled", True),
            toggle_recording=data.get("toggle_recording", "<cmd>+<shift>+r"),
            quick_note=data.get("quick_note", "<cmd>+<shift>+n"),
            voice_note=data.get("voice_note", "<cmd>+<shift>+v"),
            open_search=data.get("open_search", "<cmd>+<shift>+s"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "enabled": self.enabled,
            "toggle_recording": self.toggle_recording,
            "quick_note": self.quick_note,
            "voice_note": self.voice_note,
            "open_search": self.open_search,
        }

    def get_all_hotkeys(self) -> Dict[str, str]:
        """Get all configured hotkeys.

        Returns:
            Dictionary mapping action names to hotkey strings.
        """
        return {
            "toggle_recording": self.toggle_recording,
            "quick_note": self.quick_note,
            "voice_note": self.voice_note,
            "open_search": self.open_search,
        }


class HotkeyManager:
    """Manages global hotkey registration and callbacks.

    This class handles:
    - Registering hotkeys with the system
    - Dispatching callbacks when hotkeys are pressed
    - Starting/stopping the listener
    """

    def __init__(self, config: HotkeyConfig) -> None:
        """Initialize the hotkey manager.

        Args:
            config: Hotkey configuration.
        """
        self.config = config
        self._listener = None
        self._is_listening = False

        # Callbacks for each action
        self.on_toggle_recording: Optional[Callable[[], None]] = None
        self.on_quick_note: Optional[Callable[[], None]] = None
        self.on_voice_note: Optional[Callable[[], None]] = None
        self.on_open_search: Optional[Callable[[], None]] = None

    @property
    def is_listening(self) -> bool:
        """Check if currently listening for hotkeys."""
        return self._is_listening

    def start_listening(self) -> None:
        """Start listening for global hotkeys."""
        if not self.config.enabled:
            logger.info("Hotkeys are disabled, not starting listener")
            return

        if not PYNPUT_AVAILABLE:
            logger.warning("pynput not available, hotkeys disabled")
            return

        # Build hotkey mappings
        hotkeys = {
            self.config.toggle_recording: self._handle_toggle_recording,
            self.config.quick_note: self._handle_quick_note,
            self.config.voice_note: self._handle_voice_note,
            self.config.open_search: self._handle_open_search,
        }

        self._listener = keyboard.GlobalHotKeys(hotkeys)
        self._listener.start()
        self._is_listening = True
        logger.info("Started hotkey listener")

    def stop_listening(self) -> None:
        """Stop listening for global hotkeys."""
        if self._listener:
            self._listener.stop()
            self._listener = None

        self._is_listening = False
        logger.info("Stopped hotkey listener")

    def _handle_toggle_recording(self) -> None:
        """Handle toggle recording hotkey."""
        logger.debug("Toggle recording hotkey pressed")
        if self.on_toggle_recording:
            self.on_toggle_recording()

    def _handle_quick_note(self) -> None:
        """Handle quick note hotkey."""
        logger.debug("Quick note hotkey pressed")
        if self.on_quick_note:
            self.on_quick_note()

    def _handle_voice_note(self) -> None:
        """Handle voice note hotkey."""
        logger.debug("Voice note hotkey pressed")
        if self.on_voice_note:
            self.on_voice_note()

    def _handle_open_search(self) -> None:
        """Handle open search hotkey."""
        logger.debug("Open search hotkey pressed")
        if self.on_open_search:
            self.on_open_search()


def parse_hotkey(hotkey_str: str) -> Dict[str, Any]:
    """Parse a hotkey string into components.

    Args:
        hotkey_str: Hotkey string like "<cmd>+<shift>+r"

    Returns:
        Dictionary with 'modifiers' list and 'key' string.
    """
    parts = hotkey_str.lower().split("+")
    modifiers = []
    key = ""

    for part in parts:
        # Remove angle brackets
        clean = part.strip("<>")

        if clean in ("cmd", "super", "ctrl", "alt", "option", "shift"):
            modifiers.append(clean)
        else:
            key = clean

    return {
        "modifiers": modifiers,
        "key": key,
    }


def format_hotkey_display(hotkey_str: str) -> str:
    """Format a hotkey string for display.

    Args:
        hotkey_str: Hotkey string like "<cmd>+<shift>+r"

    Returns:
        Display string like "⌘⇧R"
    """
    parsed = parse_hotkey(hotkey_str)
    parts = []

    for mod in parsed["modifiers"]:
        symbol = MODIFIER_DISPLAY.get(mod, mod.capitalize())
        parts.append(symbol)

    if parsed["key"]:
        parts.append(parsed["key"].upper())

    return "".join(parts)


def detect_conflicts(config: HotkeyConfig) -> List[Dict[str, Any]]:
    """Detect conflicting hotkey assignments.

    Args:
        config: Hotkey configuration to check.

    Returns:
        List of conflict descriptions.
    """
    conflicts = []
    hotkeys = config.get_all_hotkeys()

    # Check for internal conflicts (same hotkey for multiple actions)
    seen = {}
    for action, hotkey in hotkeys.items():
        normalized = hotkey.lower()
        if normalized in seen:
            conflicts.append(
                {
                    "type": "internal",
                    "hotkey": hotkey,
                    "actions": [seen[normalized], action],
                    "message": f"Hotkey {hotkey} is assigned to both {seen[normalized]} and {action}",
                }
            )
        else:
            seen[normalized] = action

    return conflicts
