"""Tests for Menu Bar App (Ticket 7.1).

TDD tests for the basic menu bar application:
- App initialization and state
- Menu item creation
- Status indicator changes
- Menu callbacks
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Import at module level
from recall.app.menubar import (
    AppState,
    MenuItem,
    RecallMenuBar,
)

# ============================================================================
# Test: AppState Enum
# ============================================================================


class TestAppState:
    """Tests for AppState enum."""

    def test_idle_state_exists(self):
        """Test that IDLE state exists."""
        assert AppState.IDLE.value == "idle"

    def test_recording_state_exists(self):
        """Test that RECORDING state exists."""
        assert AppState.RECORDING.value == "recording"

    def test_processing_state_exists(self):
        """Test that PROCESSING state exists."""
        assert AppState.PROCESSING.value == "processing"

    def test_state_icons(self):
        """Test that each state has an associated icon."""
        assert AppState.IDLE.icon == "🎤"
        assert AppState.RECORDING.icon == "🔴"
        assert AppState.PROCESSING.icon == "⚙️"


# ============================================================================
# Test: MenuItem Model
# ============================================================================


class TestMenuItem:
    """Tests for MenuItem model."""

    def test_menu_item_created_with_required_fields(self):
        """Test that MenuItem can be created with required fields."""
        item = MenuItem(
            title="Start Recording",
            callback="on_start_recording",
        )

        assert item.title == "Start Recording"
        assert item.callback == "on_start_recording"

    def test_menu_item_has_optional_key(self):
        """Test that MenuItem has optional keyboard shortcut."""
        item = MenuItem(
            title="Start Recording",
            callback="on_start_recording",
            key="r",
        )

        assert item.key == "r"

    def test_menu_item_default_enabled(self):
        """Test that MenuItem is enabled by default."""
        item = MenuItem(
            title="Start Recording",
            callback="on_start_recording",
        )

        assert item.enabled is True

    def test_menu_item_separator(self):
        """Test that separator MenuItem can be created."""
        item = MenuItem.separator()

        assert item.is_separator is True


# ============================================================================
# Test: RecallMenuBar Initialization
# ============================================================================


class TestRecallMenuBarInit:
    """Tests for RecallMenuBar initialization."""

    def test_menu_bar_initializes_with_idle_state(self):
        """Test that menu bar starts in IDLE state."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            assert app.state == AppState.IDLE

    def test_menu_bar_has_app_name(self):
        """Test that menu bar has correct app name."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            assert app.name == "Recall"

    def test_menu_bar_initial_icon(self):
        """Test that menu bar shows idle icon initially."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            assert app.icon == AppState.IDLE.icon


# ============================================================================
# Test: Menu Items
# ============================================================================


class TestRecallMenuBarMenuItems:
    """Tests for menu items in RecallMenuBar."""

    def test_menu_has_start_recording_item(self):
        """Test that menu has Start Recording item."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            titles = [item.title for item in items if not item.is_separator]
            assert "Start Recording" in titles

    def test_menu_has_quick_note_item(self):
        """Test that menu has Quick Note item."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            titles = [item.title for item in items if not item.is_separator]
            assert "Quick Note..." in titles

    def test_menu_has_voice_note_item(self):
        """Test that menu has Voice Note item."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            titles = [item.title for item in items if not item.is_separator]
            assert "Voice Note" in titles

    def test_menu_has_search_item(self):
        """Test that menu has Search item."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            titles = [item.title for item in items if not item.is_separator]
            assert "Search..." in titles

    def test_menu_has_open_library_item(self):
        """Test that menu has Open Library item."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            titles = [item.title for item in items if not item.is_separator]
            assert "Open Library" in titles

    def test_menu_has_settings_item(self):
        """Test that menu has Settings item."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            titles = [item.title for item in items if not item.is_separator]
            assert "Settings..." in titles

    def test_menu_has_quit_item(self):
        """Test that menu has Quit item."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            titles = [item.title for item in items if not item.is_separator]
            assert "Quit" in titles

    def test_menu_has_separators(self):
        """Test that menu has separators."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()

            separators = [item for item in items if item.is_separator]
            assert len(separators) >= 2


# ============================================================================
# Test: State Changes
# ============================================================================


class TestRecallMenuBarStateChanges:
    """Tests for state changes in RecallMenuBar."""

    def test_set_state_updates_state(self):
        """Test that set_state updates the state."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            app.set_state(AppState.RECORDING)

            assert app.state == AppState.RECORDING

    def test_set_state_updates_icon(self):
        """Test that set_state updates the icon."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            app.set_state(AppState.RECORDING)

            assert app.icon == AppState.RECORDING.icon

    def test_recording_state_changes_menu_text(self):
        """Test that recording state changes Start to Stop."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            app.set_state(AppState.RECORDING)

            items = app.get_menu_items()
            titles = [item.title for item in items if not item.is_separator]

            assert "Stop Recording" in titles
            assert "Start Recording" not in titles

    def test_processing_state_disables_recording_button(self):
        """Test that processing state disables recording button."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            app.set_state(AppState.PROCESSING)

            items = app.get_menu_items()
            # In processing state, the first item shows "Processing..."
            processing_item = items[0]

            assert "Processing" in processing_item.title
            assert processing_item.enabled is False


# ============================================================================
# Test: Callbacks
# ============================================================================


class TestRecallMenuBarCallbacks:
    """Tests for callback methods in RecallMenuBar."""

    def test_on_start_recording_changes_state(self):
        """Test that on_start_recording changes state to RECORDING."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                app.on_start_recording(None)

                assert app.state == AppState.RECORDING

    def test_on_stop_recording_changes_state_to_processing(self):
        """Test that on_stop_recording changes state to PROCESSING."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            app.set_state(AppState.RECORDING)

            app.on_stop_recording(None)

            assert app.state == AppState.PROCESSING

    def test_on_quit_sets_quit_flag(self):
        """Test that on_quit sets the quit flag."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            app.on_quit(None)

            assert app._quit_requested is True


# ============================================================================
# Test: Properties
# ============================================================================


class TestRecallMenuBarProperties:
    """Tests for properties in RecallMenuBar."""

    def test_is_recording_property(self):
        """Test that is_recording returns correct value."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            assert app.is_recording is False

            app.set_state(AppState.RECORDING)

            assert app.is_recording is True

    def test_is_processing_property(self):
        """Test that is_processing returns correct value."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()

            assert app.is_processing is False

            app.set_state(AppState.PROCESSING)

            assert app.is_processing is True

    def test_recording_duration_property(self):
        """Test that recording_duration returns elapsed time."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                app = RecallMenuBar()

                # Not recording
                assert app.recording_duration is None

                # Start recording
                app.on_start_recording(None)

                # Should have duration (via controller)
                assert app.recording_duration is not None
                assert app.recording_duration >= 0


# ============================================================================
# Test: Open Library (RECALL-002)
# ============================================================================


class TestRecallMenuBarOpenLibrary:
    """Tests for Open Library menu action."""

    def test_on_open_library_creates_directory(self, tmp_path):
        """Test that on_open_library creates recordings directory if missing."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.config.RecallConfig.load") as mock_load:
                from recall.config import RecallConfig

                mock_config = RecallConfig.default()
                mock_config.storage_dir = tmp_path
                mock_load.return_value = mock_config

                with patch("subprocess.run") as mock_run:
                    app = RecallMenuBar()
                    app.on_open_library(None)

                    recordings_path = tmp_path / "recordings"
                    assert recordings_path.exists()

    def test_on_open_library_calls_subprocess(self, tmp_path):
        """Test that on_open_library calls subprocess to open folder."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.config.RecallConfig.load") as mock_load:
                from recall.config import RecallConfig

                mock_config = RecallConfig.default()
                mock_config.storage_dir = tmp_path
                mock_load.return_value = mock_config

                with patch("subprocess.run") as mock_run:
                    app = RecallMenuBar()
                    app.on_open_library(None)

                    recordings_path = tmp_path / "recordings"
                    mock_run.assert_called_once_with(
                        ["open", str(recordings_path)],
                        check=True,
                    )

    def test_on_open_library_handles_subprocess_error(self, tmp_path):
        """Test that on_open_library handles subprocess errors."""
        import subprocess

        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.config.RecallConfig.load") as mock_load:
                from recall.config import RecallConfig

                mock_config = RecallConfig.default()
                mock_config.storage_dir = tmp_path
                mock_load.return_value = mock_config

                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = subprocess.CalledProcessError(1, "open")
                    app = RecallMenuBar()

                    # Should not raise, but notify error
                    with patch.object(
                        app.notification_manager, "notify_error"
                    ) as mock_notify:
                        app.on_open_library(None)
                        mock_notify.assert_called_once()


# ============================================================================
# Test: Quick Note (RECALL-003)
# ============================================================================


class TestRecallMenuBarQuickNote:
    """Tests for Quick Note menu action."""

    def test_on_quick_note_returns_early_when_rumps_unavailable(self):
        """Test that on_quick_note returns early when rumps is not available."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            # Should not raise
            app.on_quick_note(None)

    def test_on_quick_note_shows_window(self):
        """Test that on_quick_note shows a rumps window."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = False  # User cancels
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    app.on_quick_note(None)

                    mock_rumps.Window.assert_called_once()

    def test_on_quick_note_saves_note_on_submit(self, tmp_path):
        """Test that on_quick_note saves note when user submits."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "Test note content"
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.notes.quick_note.create_note") as mock_create:
                        app = RecallMenuBar()
                        app.on_quick_note(None)

                        mock_create.assert_called_once_with(content="Test note content")

    def test_on_quick_note_shows_warning_for_empty_text(self):
        """Test that on_quick_note shows warning for empty text."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "   "  # Whitespace only
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    app.on_quick_note(None)

                    mock_rumps.alert.assert_called_once()

    def test_on_quick_note_notifies_on_success(self, tmp_path):
        """Test that on_quick_note shows notification on success."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "Test note"
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.notes.quick_note.create_note"):
                        app = RecallMenuBar()
                        with patch.object(
                            app.notification_manager, "send"
                        ) as mock_send:
                            app.on_quick_note(None)
                            mock_send.assert_called_once()

    def test_on_quick_note_handles_save_error(self):
        """Test that on_quick_note handles save errors gracefully."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "Test note"
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.notes.quick_note.create_note") as mock_create:
                        mock_create.side_effect = Exception("Save failed")
                        app = RecallMenuBar()
                        with patch.object(
                            app.notification_manager, "notify_error"
                        ) as mock_notify:
                            app.on_quick_note(None)
                            mock_notify.assert_called_once()


# ============================================================================
# Test: Voice Note (RECALL-004)
# ============================================================================


class TestRecallMenuBarVoiceNote:
    """Tests for Voice Note menu action."""

    def test_voice_note_initial_state(self):
        """Test that voice note is initially not active."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            assert app._voice_note_active is False

    def test_voice_note_menu_item_when_inactive(self):
        """Test that menu shows 'Voice Note' when not recording."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            items = app.get_menu_items()
            titles = [item.title for item in items if not item.is_separator]
            assert "Voice Note" in titles
            assert "Stop Voice Note" not in titles

    def test_voice_note_menu_item_when_active(self):
        """Test that menu shows 'Stop Voice Note' when recording."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            app._voice_note_active = True
            items = app.get_menu_items()
            titles = [item.title for item in items if not item.is_separator]
            assert "Stop Voice Note" in titles
            assert "Voice Note" not in titles

    def test_on_voice_note_starts_recording(self):
        """Test that on_voice_note starts recording when not active."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.start_voice_note") as mock_start:
                app = RecallMenuBar()
                app.on_voice_note(None)

                mock_start.assert_called_once()
                assert app._voice_note_active is True

    def test_on_voice_note_stops_recording(self):
        """Test that on_voice_note stops recording when active."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.stop_voice_note") as mock_stop:
                mock_recording = MagicMock()
                mock_recording.duration_seconds = 30
                mock_stop.return_value = mock_recording

                app = RecallMenuBar()
                app._voice_note_active = True
                app.on_voice_note(None)

                mock_stop.assert_called_once()
                assert app._voice_note_active is False

    def test_on_voice_note_changes_icon_when_recording(self):
        """Test that on_voice_note changes icon to microphone when recording."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.start_voice_note"):
                app = RecallMenuBar()
                app.on_voice_note(None)

                assert app._icon == "🎙️"

    def test_on_voice_note_restores_icon_when_stopped(self):
        """Test that on_voice_note restores icon when stopped."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.stop_voice_note") as mock_stop:
                mock_recording = MagicMock()
                mock_recording.duration_seconds = 30
                mock_stop.return_value = mock_recording

                app = RecallMenuBar()
                app._voice_note_active = True
                app._icon = "🎙️"
                app.on_voice_note(None)

                assert app._icon == app._state.icon

    def test_on_voice_note_handles_start_error(self):
        """Test that on_voice_note handles errors when starting."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.start_voice_note") as mock_start:
                mock_start.side_effect = Exception("Mic not available")

                app = RecallMenuBar()
                with patch.object(
                    app.notification_manager, "notify_error"
                ) as mock_notify:
                    app.on_voice_note(None)
                    mock_notify.assert_called_once()
                    assert app._voice_note_active is False

    def test_on_voice_note_handles_stop_error(self):
        """Test that on_voice_note handles errors when stopping."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.stop_voice_note") as mock_stop:
                mock_stop.side_effect = Exception("Transcription failed")

                app = RecallMenuBar()
                app._voice_note_active = True
                with patch.object(
                    app.notification_manager, "notify_error"
                ) as mock_notify:
                    app.on_voice_note(None)
                    mock_notify.assert_called_once()
                    assert app._voice_note_active is False

    def test_on_voice_note_notifies_on_start(self):
        """Test that on_voice_note sends notification when starting."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.start_voice_note"):
                app = RecallMenuBar()
                with patch.object(
                    app.notification_manager, "send"
                ) as mock_send:
                    app.on_voice_note(None)
                    mock_send.assert_called_once()

    def test_on_voice_note_notifies_on_save(self):
        """Test that on_voice_note sends notification when saved."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.notes.voice_note.stop_voice_note") as mock_stop:
                mock_recording = MagicMock()
                mock_recording.duration_seconds = 30
                mock_stop.return_value = mock_recording

                app = RecallMenuBar()
                app._voice_note_active = True
                with patch.object(
                    app.notification_manager, "send"
                ) as mock_send:
                    app.on_voice_note(None)
                    mock_send.assert_called_once()


# ============================================================================
# Test: Search (RECALL-005)
# ============================================================================


class TestRecallMenuBarSearch:
    """Tests for Search menu action."""

    def test_on_search_returns_early_when_rumps_unavailable(self):
        """Test that on_search returns early when rumps is not available."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            # Should not raise
            app.on_search(None)

    def test_on_search_shows_window(self):
        """Test that on_search shows a rumps window."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = False  # User cancels
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    app.on_search(None)

                    mock_rumps.Window.assert_called_once()

    def test_on_search_shows_warning_for_empty_query(self):
        """Test that on_search shows warning for empty query."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "   "  # Whitespace only
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    app.on_search(None)

                    mock_rumps.alert.assert_called_once()

    def test_on_search_performs_search(self, tmp_path):
        """Test that on_search performs search with query."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "test query"
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    with patch.object(app, "_perform_search") as mock_search:
                        mock_search.return_value = []
                        app.on_search(None)

                        mock_search.assert_called_once_with("test query")

    def test_on_search_displays_no_results_message(self, tmp_path):
        """Test that on_search shows message when no results found."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "nonexistent"
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    with patch.object(app, "_perform_search") as mock_search:
                        mock_search.return_value = []
                        app.on_search(None)

                        # Should call alert with "No Results"
                        mock_rumps.alert.assert_called_once()
                        call_args = mock_rumps.alert.call_args
                        assert "No Results" in str(call_args) or "No matches" in str(call_args)

    def test_on_search_displays_results(self, tmp_path):
        """Test that on_search displays results when found."""
        from datetime import datetime

        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "meeting"
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        # Create mock search results
        mock_result = MagicMock()
        mock_result.filepath = tmp_path / "test.md"
        mock_result.timestamp = datetime(2024, 1, 15, 10, 30)
        mock_result.summary_snippet = "Team meeting notes about Q1 planning"
        mock_result.source = "note"

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    with patch.object(app, "_perform_search") as mock_search:
                        mock_search.return_value = [mock_result]
                        app.on_search(None)

                        # Should call alert with results
                        mock_rumps.alert.assert_called_once()

    def test_on_search_handles_search_error(self):
        """Test that on_search handles search errors gracefully."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = "test"
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    app = RecallMenuBar()
                    with patch.object(app, "_perform_search") as mock_search:
                        mock_search.side_effect = Exception("Database error")
                        with patch.object(
                            app.notification_manager, "notify_error"
                        ) as mock_notify:
                            app.on_search(None)
                            mock_notify.assert_called_once()

    def test_perform_search_returns_empty_when_no_index(self, tmp_path):
        """Test that _perform_search returns empty list when index doesn't exist."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.config.RecallConfig.load") as mock_load:
                from recall.config import RecallConfig

                mock_config = RecallConfig.default()
                mock_config.storage_dir = tmp_path
                mock_load.return_value = mock_config

                app = RecallMenuBar()
                results = app._perform_search("test")

                assert results == []

    def test_perform_search_uses_recording_index(self, tmp_path):
        """Test that _perform_search uses RecordingIndex.search()."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.config.RecallConfig.load") as mock_load:
                from recall.config import RecallConfig

                mock_config = RecallConfig.default()
                mock_config.storage_dir = tmp_path
                mock_load.return_value = mock_config

                # Create a mock index file
                index_path = tmp_path / "index.db"
                index_path.touch()

                with patch("recall.storage.index.RecordingIndex") as mock_index_class:
                    mock_index = MagicMock()
                    mock_index.search.return_value = []
                    mock_index_class.return_value.__enter__.return_value = mock_index

                    app = RecallMenuBar()
                    app._perform_search("test query")

                    mock_index.search.assert_called_once_with("test query")



# ============================================================================
# Test: Settings (RECALL-006)
# ============================================================================


class TestRecallMenuBarSettings:
    """Tests for Settings menu action."""

    def test_on_settings_returns_early_when_rumps_unavailable(self):
        """Test that on_settings returns early when rumps is not available."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            app = RecallMenuBar()
            # Should not raise
            app.on_settings(None)

    def test_on_settings_loads_config(self, tmp_path):
        """Test that on_settings loads configuration."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = False  # User cancels
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.config.RecallConfig.load") as mock_load:
                        from recall.config import RecallConfig

                        mock_config = RecallConfig.default()
                        mock_config.storage_dir = tmp_path
                        mock_load.return_value = mock_config

                        app = RecallMenuBar()
                        app.on_settings(None)

                        mock_load.assert_called()

    def test_on_settings_shows_window(self, tmp_path):
        """Test that on_settings shows a rumps window."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = False  # User cancels
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.config.RecallConfig.load") as mock_load:
                        from recall.config import RecallConfig

                        mock_config = RecallConfig.default()
                        mock_config.storage_dir = tmp_path
                        mock_load.return_value = mock_config

                        app = RecallMenuBar()
                        app.on_settings(None)

                        mock_rumps.Window.assert_called_once()

    def test_on_settings_saves_config_on_submit(self, tmp_path):
        """Test that on_settings saves config when user submits."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = """Current Settings:

audio_source: system
whisper_model: small
retain_audio: true
auto_recording: false

Edit the values above (key: value format) or leave as-is."""
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.config.RecallConfig.load") as mock_load:
                        from recall.config import RecallConfig

                        mock_config = RecallConfig.default()
                        mock_config.storage_dir = tmp_path
                        mock_load.return_value = mock_config

                        with patch.object(mock_config, "save") as mock_save:
                            app = RecallMenuBar()
                            app.on_settings(None)

                            mock_save.assert_called_once()
                            assert mock_config.default_audio_source == "system"
                            assert mock_config.whisper_model == "small"
                            assert mock_config.retain_audio is True

    def test_on_settings_validates_audio_source(self, tmp_path):
        """Test that on_settings validates audio_source values."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = """audio_source: invalid_value"""
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.config.RecallConfig.load") as mock_load:
                        from recall.config import RecallConfig

                        mock_config = RecallConfig.default()
                        mock_config.storage_dir = tmp_path
                        mock_load.return_value = mock_config

                        app = RecallMenuBar()
                        app.on_settings(None)

                        # Should show alert for invalid value
                        mock_rumps.alert.assert_called()

    def test_on_settings_handles_load_error(self):
        """Test that on_settings handles config load errors."""
        mock_rumps = MagicMock()

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.config.RecallConfig.load") as mock_load:
                        mock_load.side_effect = Exception("Config file corrupt")

                        app = RecallMenuBar()
                        with patch.object(
                            app.notification_manager, "notify_error"
                        ) as mock_notify:
                            app.on_settings(None)
                            mock_notify.assert_called_once()

    def test_on_settings_notifies_on_save(self, tmp_path):
        """Test that on_settings shows notification when saved."""
        mock_rumps = MagicMock()
        mock_window = MagicMock()
        mock_response = MagicMock()
        mock_response.clicked = True
        mock_response.text = """audio_source: microphone"""
        mock_window.run.return_value = mock_response
        mock_rumps.Window.return_value = mock_window

        with patch.dict("sys.modules", {"rumps": mock_rumps}):
            with patch("recall.app.menubar.RUMPS_AVAILABLE", True):
                with patch("recall.app.menubar.rumps", mock_rumps, create=True):
                    with patch("recall.config.RecallConfig.load") as mock_load:
                        from recall.config import RecallConfig

                        mock_config = RecallConfig.default()
                        mock_config.storage_dir = tmp_path
                        mock_load.return_value = mock_config

                        with patch.object(mock_config, "save"):
                            app = RecallMenuBar()
                            with patch.object(
                                app.notification_manager, "send"
                            ) as mock_send:
                                app.on_settings(None)
                                mock_send.assert_called_once()

