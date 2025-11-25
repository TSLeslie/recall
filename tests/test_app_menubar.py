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
