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
        self._voice_note_active: bool = False

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
        # Voice Note toggle
        if self._voice_note_active:
            items.append(
                MenuItem(
                    title="Stop Voice Note",
                    callback="on_voice_note",
                    key="v",
                )
            )
        else:
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
        """Handle Quick Note action.

        Shows a text input dialog and saves the note using create_note().
        """
        if not RUMPS_AVAILABLE:
            # Mock mode - just log
            return

        window = rumps.Window(
            message="Enter your note:",
            title="Quick Note",
            default_text="",
            ok="Save",
            cancel="Cancel",
            dimensions=(320, 160),
        )
        response = window.run()

        if response.clicked:
            text = response.text.strip()
            if not text:
                rumps.alert(
                    title="Empty Note",
                    message="Please enter some text for your note.",
                )
                return

            try:
                from recall.notes.quick_note import create_note

                create_note(content=text)
                self.notification_manager.send(
                    title="Note Saved",
                    message="Quick note saved successfully.",
                )
            except Exception as e:
                self.notification_manager.notify_error(
                    f"Failed to save note: {e}"
                )

    def on_voice_note(self, sender) -> None:
        """Handle Voice Note action.

        Toggles voice note recording. On first click, starts recording.
        On second click, stops recording, transcribes, and saves.
        """
        if self._voice_note_active:
            # Stop recording
            self._stop_voice_note()
        else:
            # Start recording
            self._start_voice_note()

    def _start_voice_note(self) -> None:
        """Start voice note recording."""
        try:
            from recall.notes.voice_note import start_voice_note

            start_voice_note()
            self._voice_note_active = True
            self._icon = "🎙️"

            if RUMPS_AVAILABLE and self._rumps_app:
                self._rumps_app.title = self._icon
                self._update_rumps_menu()

            self.notification_manager.send(
                title="Voice Note",
                message="Recording started. Click 'Stop Voice Note' when done.",
            )
        except Exception as e:
            self.notification_manager.notify_error(f"Failed to start voice note: {e}")

    def _stop_voice_note(self) -> None:
        """Stop voice note recording and save."""
        try:
            from recall.notes.voice_note import stop_voice_note

            recording = stop_voice_note()
            self._voice_note_active = False
            self._icon = self._state.icon

            if RUMPS_AVAILABLE and self._rumps_app:
                self._rumps_app.title = self._icon
                self._update_rumps_menu()

            duration = recording.duration_seconds or 0
            self.notification_manager.send(
                title="Voice Note Saved",
                message=f"Voice note saved ({duration} seconds)",
            )
        except Exception as e:
            self._voice_note_active = False
            self._icon = self._state.icon
            if RUMPS_AVAILABLE and self._rumps_app:
                self._rumps_app.title = self._icon
                self._update_rumps_menu()
            self.notification_manager.notify_error(f"Failed to save voice note: {e}")

    def on_search(self, sender) -> None:
        """Handle Search action.

        Shows a search input dialog and displays results from the SQLite index.
        """
        if not RUMPS_AVAILABLE:
            # Mock mode - just log
            return

        window = rumps.Window(
            message="Search your notes and recordings:",
            title="Search Recall",
            default_text="",
            ok="Search",
            cancel="Cancel",
            dimensions=(320, 40),
        )
        response = window.run()

        if response.clicked:
            query = response.text.strip()
            if not query:
                rumps.alert(
                    title="Empty Search",
                    message="Please enter a search query.",
                )
                return

            try:
                results = self._perform_search(query)
                self._display_search_results(query, results)
            except Exception as e:
                self.notification_manager.notify_error(f"Search failed: {e}")

    def _perform_search(self, query: str):
        """Perform search using RecordingIndex.

        Args:
            query: Search query string

        Returns:
            List of SearchResult objects
        """
        from recall.config import RecallConfig
        from recall.storage.index import RecordingIndex

        config = RecallConfig.load()
        index_path = config.storage_dir / "index.db"

        if not index_path.exists():
            return []

        with RecordingIndex(str(index_path)) as index:
            return index.search(query)

    def _display_search_results(self, query: str, results) -> None:
        """Display search results in an alert dialog.

        Args:
            query: The search query
            results: List of SearchResult objects
        """
        if not results:
            rumps.alert(
                title="No Results",
                message=f'No matches found for "{query}"',
            )
            return

        # Format results for display (top 5)
        result_lines = []
        for i, result in enumerate(results[:5], 1):
            filename = result.filepath.name
            date_str = result.timestamp.strftime("%Y-%m-%d")
            snippet_text = result.summary_snippet or ""
            snippet = (snippet_text[:50] + "...") if len(snippet_text) > 50 else snippet_text
            result_lines.append(f"{i}. {filename}\n   {date_str} - {snippet}")

        message = "\n\n".join(result_lines)

        if len(results) > 5:
            message += f"\n\n... and {len(results) - 5} more results"

        rumps.alert(
            title=f'Search Results for "{query}"',
            message=message,
        )

    def on_open_library(self, sender) -> None:
        """Handle Open Library action.

        Opens Finder at the recordings directory. Creates the directory
        if it doesn't exist.
        """
        import subprocess

        from recall.config import RecallConfig

        try:
            config = RecallConfig.load()
            recordings_path = config.storage_dir / "recordings"
            recordings_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(["open", str(recordings_path)], check=True)
        except subprocess.CalledProcessError as e:
            self.notification_manager.notify_error(
                f"Failed to open library: {e}"
            )
        except Exception as e:
            self.notification_manager.notify_error(
                f"Error opening library: {e}"
            )

    def on_settings(self, sender) -> None:
        """Handle Settings action.

        Shows a settings dialog that allows viewing and modifying key settings.
        Settings are persisted to config.json.
        """
        if not RUMPS_AVAILABLE:
            # Mock mode - just log
            return

        from recall.config import RecallConfig

        try:
            config = RecallConfig.load()
            self._show_settings_dialog(config)
        except Exception as e:
            self.notification_manager.notify_error(f"Failed to load settings: {e}")

    def _show_settings_dialog(self, config) -> None:
        """Show the settings dialog.

        Args:
            config: Current RecallConfig instance
        """
        # Display current settings in a formatted text
        current_settings = (
            f"Current Settings:\n\n"
            f"audio_source: {config.default_audio_source}\n"
            f"whisper_model: {config.whisper_model}\n"
            f"retain_audio: {config.retain_audio}\n"
            f"auto_recording: {config.auto_recording_enabled}\n\n"
            f"Edit the values above (key: value format) or leave as-is."
        )

        window = rumps.Window(
            message="Modify settings below:",
            title="Recall Settings",
            default_text=current_settings,
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 200),
        )
        response = window.run()

        if response.clicked:
            self._parse_and_save_settings(response.text, config)

    def _parse_and_save_settings(self, text: str, config) -> None:
        """Parse settings from text and save.

        Args:
            text: Settings text in key: value format
            config: Current RecallConfig instance
        """
        try:
            # Parse settings from text
            for line in text.split("\n"):
                line = line.strip()
                if ":" not in line or line.startswith("Current") or line.startswith("Edit"):
                    continue

                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "audio_source":
                    if value in ["microphone", "system", "both"]:
                        config.default_audio_source = value
                    else:
                        rumps.alert(
                            title="Invalid Value",
                            message="audio_source must be: microphone, system, or both",
                        )
                        return
                elif key == "whisper_model":
                    if value in ["tiny", "base", "small", "medium", "large"]:
                        config.whisper_model = value
                    else:
                        rumps.alert(
                            title="Invalid Value",
                            message="whisper_model must be: tiny, base, small, medium, or large",
                        )
                        return
                elif key == "retain_audio":
                    config.retain_audio = value.lower() in ["true", "yes", "1"]
                elif key == "auto_recording":
                    config.auto_recording_enabled = value.lower() in ["true", "yes", "1"]

            # Save config
            config.save()
            self.notification_manager.send(
                title="Settings Saved",
                message="Your settings have been saved.",
            )
        except Exception as e:
            self.notification_manager.notify_error(f"Failed to save settings: {e}")

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
