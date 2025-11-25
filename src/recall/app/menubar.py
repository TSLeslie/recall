"""macOS Menu Bar Application for Recall.

This module provides a native macOS menu bar interface for Recall.
It uses the `rumps` library on macOS, with a fallback mock implementation
for testing on other platforms.

Usage on macOS:
    from recall.app.menubar import RecallMenuBar
    app = RecallMenuBar()
    app.run()
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

# Check if rumps is available (macOS only)
try:
    import rumps

    RUMPS_AVAILABLE = True
except ImportError:
    RUMPS_AVAILABLE = False


class AppState(Enum):
    """Application state for the menu bar.

    Each state has an associated icon that appears in the menu bar.
    """

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"

    @property
    def icon(self) -> str:
        """Get the menu bar icon for this state."""
        icons = {
            AppState.IDLE: "🎤",
            AppState.RECORDING: "🔴",
            AppState.PROCESSING: "⚙️",
        }
        return icons[self]


@dataclass
class MenuItem:
    """Represents a menu item in the menu bar dropdown.

    Attributes:
        title: Display text for the menu item
        callback: Name of the callback method to invoke
        key: Optional keyboard shortcut (single character)
        enabled: Whether the item is clickable
        is_separator: If True, this is a separator line
    """

    title: str = ""
    callback: Optional[str] = None
    key: Optional[str] = None
    enabled: bool = True
    is_separator: bool = False

    @classmethod
    def separator(cls) -> "MenuItem":
        """Create a separator menu item."""
        return cls(is_separator=True)


class RecallMenuBar:
    """macOS Menu Bar Application for Recall.

    This class provides the menu bar interface with:
    - Status indicator showing app state
    - Recording controls
    - Quick access to notes and search
    - Settings and quit options

    On non-macOS platforms, it runs in a mock mode for testing.
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize the menu bar application.

        Args:
            output_dir: Optional directory for recording output.
        """
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager
        from recall.app.notifications import (
            AutoRecordingConfig,
            NotificationManager,
        )
        from recall.app.recording import RecordingController

        self.name = "Recall"
        self._state = AppState.IDLE
        self._icon = AppState.IDLE.icon
        self._quit_requested = False
        self._recording_start_time: Optional[float] = None

        # Initialize recording controller
        self.recording_controller = RecordingController(output_dir=output_dir)

        # Initialize notification manager
        self.notification_manager = NotificationManager()

        # Initialize auto-recording configuration
        self.auto_recording_config = AutoRecordingConfig()

        # Initialize hotkey manager
        self.hotkey_config = HotkeyConfig()
        self.hotkey_manager = HotkeyManager(self.hotkey_config)
        self._setup_hotkey_callbacks()

        # Initialize rumps app if available
        if RUMPS_AVAILABLE:
            self._rumps_app = rumps.App(
                self.name,
                title=self._icon,
                quit_button=None,  # We'll add our own quit
            )
            self._setup_rumps_menu()
        else:
            self._rumps_app = None

    @property
    def state(self) -> AppState:
        """Get the current application state."""
        return self._state

    @property
    def icon(self) -> str:
        """Get the current menu bar icon."""
        return self._icon

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._state == AppState.RECORDING

    @property
    def is_processing(self) -> bool:
        """Check if currently processing."""
        return self._state == AppState.PROCESSING

    @property
    def recording_duration(self) -> Optional[float]:
        """Get the current recording duration in seconds."""
        # Use controller's duration if available
        if self.recording_controller:
            return self.recording_controller.get_duration()
        if self._recording_start_time is None:
            return None
        return time.time() - self._recording_start_time

    def set_state(self, state: AppState) -> None:
        """Set the application state and update UI.

        Args:
            state: The new application state
        """
        self._state = state
        self._icon = state.icon

        if RUMPS_AVAILABLE and self._rumps_app:
            self._rumps_app.title = self._icon
            self._update_rumps_menu()

    def get_menu_items(self) -> List[MenuItem]:
        """Get the list of menu items based on current state.

        Returns:
            List of MenuItem objects for the dropdown menu.
        """
        items = []

        # Recording toggle
        if self._state == AppState.RECORDING:
            items.append(
                MenuItem(
                    title="Stop Recording",
                    callback="on_stop_recording",
                    key="r",
                )
            )
        elif self._state == AppState.PROCESSING:
            items.append(
                MenuItem(
                    title="Processing...",
                    callback="on_start_recording",
                    enabled=False,
                )
            )
        else:
            items.append(
                MenuItem(
                    title="Start Recording",
                    callback="on_start_recording",
                    key="r",
                )
            )

        # Notes
        items.append(
            MenuItem(
                title="Quick Note...",
                callback="on_quick_note",
                key="n",
            )
        )
        items.append(
            MenuItem(
                title="Voice Note",
                callback="on_voice_note",
                key="v",
            )
        )

        items.append(MenuItem.separator())

        # Search and Library
        items.append(
            MenuItem(
                title="Search...",
                callback="on_search",
                key="s",
            )
        )
        items.append(
            MenuItem(
                title="Open Library",
                callback="on_open_library",
            )
        )

        items.append(MenuItem.separator())

        # Settings and Quit
        items.append(
            MenuItem(
                title="Settings...",
                callback="on_settings",
                key=",",
            )
        )
        items.append(
            MenuItem(
                title="Quit",
                callback="on_quit",
                key="q",
            )
        )

        return items

    # ========================================================================
    # Callback Methods
    # ========================================================================

    def on_start_recording(self, sender) -> None:
        """Handle Start Recording action."""
        status = self.recording_controller.start_recording()
        self.set_state(status.state)

    def on_stop_recording(self, sender) -> None:
        """Handle Stop Recording action."""
        self.set_state(AppState.PROCESSING)
        # TODO: Stop recorder and trigger ingestion pipeline
        # For now, just reset to idle after "processing"
        # In real implementation, this would be async

    def on_quick_note(self, sender) -> None:
        """Handle Quick Note action."""
        # TODO: Show text input dialog
        pass

    def on_voice_note(self, sender) -> None:
        """Handle Voice Note action."""
        # TODO: Start voice recording
        pass

    def on_search(self, sender) -> None:
        """Handle Search action."""
        # TODO: Show search dialog
        pass

    def on_open_library(self, sender) -> None:
        """Handle Open Library action."""
        # TODO: Open Finder to recordings folder
        pass

    def on_settings(self, sender) -> None:
        """Handle Settings action."""
        # TODO: Show settings dialog
        pass

    def on_quit(self, sender) -> None:
        """Handle Quit action."""
        self._quit_requested = True
        if RUMPS_AVAILABLE:
            rumps.quit_application()

    # ========================================================================
    # rumps Integration
    # ========================================================================

    def _setup_rumps_menu(self) -> None:
        """Set up the rumps menu items."""
        if not RUMPS_AVAILABLE or not self._rumps_app:
            return

        self._update_rumps_menu()

    def _setup_hotkey_callbacks(self) -> None:
        """Set up callbacks for hotkey events."""
        self.hotkey_manager.on_toggle_recording = self._toggle_recording
        self.hotkey_manager.on_quick_note = lambda: self.on_quick_note(None)
        self.hotkey_manager.on_voice_note = lambda: self.on_voice_note(None)
        self.hotkey_manager.on_open_search = lambda: self.on_search(None)

    def _setup_hotkeys(self) -> None:
        """Start the hotkey listener."""
        self.hotkey_manager.start_listening()

    def _toggle_recording(self) -> None:
        """Toggle recording state via hotkey."""
        if self._state == AppState.RECORDING:
            self.on_stop_recording(None)
        else:
            self.on_start_recording(None)

    def _update_rumps_menu(self) -> None:
        """Update the rumps menu to match current state."""
        if not RUMPS_AVAILABLE or not self._rumps_app:
            return

        menu_items = self.get_menu_items()
        self._rumps_app.menu.clear()

        for item in menu_items:
            if item.is_separator:
                self._rumps_app.menu.add(rumps.separator)
            else:
                callback = getattr(self, item.callback, None)
                rumps_item = rumps.MenuItem(
                    title=item.title,
                    callback=callback,
                    key=item.key or "",
                )
                if not item.enabled:
                    rumps_item.set_callback(None)
                self._rumps_app.menu.add(rumps_item)

    def run(self) -> None:
        """Run the menu bar application.

        On macOS, this starts the rumps event loop.
        On other platforms, this prints a warning.
        """
        if RUMPS_AVAILABLE and self._rumps_app:
            self._rumps_app.run()
        else:
            print("⚠️  Menu bar app requires macOS with rumps installed.")
            print("   Install on macOS: pip install rumps")
            print("   Running in mock mode for testing.")


def main() -> None:
    """Entry point for the menu bar application."""
    app = RecallMenuBar()
    app.run()


if __name__ == "__main__":
    main()
