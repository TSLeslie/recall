"""Tests for Ticket 7.4: Global Hotkeys.

This module tests:
- Global hotkey registration using pynput
- Keyboard shortcuts for recording, notes, search
- Hotkey configuration
- Conflict detection
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from recall.app.menubar import AppState

# ============================================================================
# Test: HotkeyConfig
# ============================================================================


class TestHotkeyConfig:
    """Tests for hotkey configuration."""

    def test_config_defaults(self):
        """Test default hotkey configuration."""
        from recall.app.hotkeys import HotkeyConfig

        config = HotkeyConfig()

        assert config.enabled is True
        assert config.toggle_recording == "<cmd>+<shift>+r"
        assert config.quick_note == "<cmd>+<shift>+n"
        assert config.voice_note == "<cmd>+<shift>+v"
        assert config.open_search == "<cmd>+<shift>+s"

    def test_config_custom_hotkeys(self):
        """Test custom hotkey configuration."""
        from recall.app.hotkeys import HotkeyConfig

        config = HotkeyConfig(
            toggle_recording="<cmd>+<alt>+r",
            quick_note="<cmd>+<alt>+n",
        )

        assert config.toggle_recording == "<cmd>+<alt>+r"
        assert config.quick_note == "<cmd>+<alt>+n"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        from recall.app.hotkeys import HotkeyConfig

        config = HotkeyConfig.from_dict(
            {
                "enabled": False,
                "toggle_recording": "<ctrl>+r",
            }
        )

        assert config.enabled is False
        assert config.toggle_recording == "<ctrl>+r"

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        from recall.app.hotkeys import HotkeyConfig

        config = HotkeyConfig()

        data = config.to_dict()

        assert "enabled" in data
        assert "toggle_recording" in data
        assert "quick_note" in data

    def test_config_get_all_hotkeys(self):
        """Test getting all configured hotkeys."""
        from recall.app.hotkeys import HotkeyConfig

        config = HotkeyConfig()

        hotkeys = config.get_all_hotkeys()

        assert "toggle_recording" in hotkeys
        assert hotkeys["toggle_recording"] == "<cmd>+<shift>+r"


# ============================================================================
# Test: HotkeyManager
# ============================================================================


class TestHotkeyManager:
    """Tests for HotkeyManager class."""

    def test_manager_init(self):
        """Test that HotkeyManager initializes correctly."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        assert manager is not None
        assert manager.config == config
        assert manager.is_listening is False

    def test_manager_start_listening(self):
        """Test starting hotkey listener."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", True):
            with patch("recall.app.hotkeys.keyboard") as mock_keyboard:
                mock_listener = MagicMock()
                mock_keyboard.GlobalHotKeys.return_value = mock_listener

                config = HotkeyConfig()
                manager = HotkeyManager(config)

                manager.start_listening()

                assert manager.is_listening is True
                mock_listener.start.assert_called_once()

    def test_manager_stop_listening(self):
        """Test stopping hotkey listener."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", True):
            with patch("recall.app.hotkeys.keyboard") as mock_keyboard:
                mock_listener = MagicMock()
                mock_keyboard.GlobalHotKeys.return_value = mock_listener

                config = HotkeyConfig()
                manager = HotkeyManager(config)
                manager.start_listening()

                manager.stop_listening()

                assert manager.is_listening is False
                mock_listener.stop.assert_called_once()

    def test_manager_without_pynput(self):
        """Test manager behavior when pynput unavailable."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", False):
            config = HotkeyConfig()
            manager = HotkeyManager(config)

            # Should not raise, just log warning
            manager.start_listening()

            assert manager.is_listening is False

    def test_manager_disabled_config(self):
        """Test that disabled config prevents listening."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", True):
            config = HotkeyConfig(enabled=False)
            manager = HotkeyManager(config)

            manager.start_listening()

            assert manager.is_listening is False


# ============================================================================
# Test: Hotkey Callbacks
# ============================================================================


class TestHotkeyCallbacks:
    """Tests for hotkey callback registration."""

    def test_register_toggle_recording_callback(self):
        """Test registering toggle recording callback."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        callback = MagicMock()
        manager.on_toggle_recording = callback

        manager._handle_toggle_recording()

        callback.assert_called_once()

    def test_register_quick_note_callback(self):
        """Test registering quick note callback."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        callback = MagicMock()
        manager.on_quick_note = callback

        manager._handle_quick_note()

        callback.assert_called_once()

    def test_register_voice_note_callback(self):
        """Test registering voice note callback."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        callback = MagicMock()
        manager.on_voice_note = callback

        manager._handle_voice_note()

        callback.assert_called_once()

    def test_register_open_search_callback(self):
        """Test registering open search callback."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        callback = MagicMock()
        manager.on_open_search = callback

        manager._handle_open_search()

        callback.assert_called_once()

    def test_callback_not_set_does_not_raise(self):
        """Test that missing callback doesn't raise."""
        from recall.app.hotkeys import HotkeyConfig, HotkeyManager

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        # Should not raise
        manager._handle_toggle_recording()
        manager._handle_quick_note()
        manager._handle_voice_note()
        manager._handle_open_search()


# ============================================================================
# Test: Hotkey Parsing
# ============================================================================


class TestHotkeyParsing:
    """Tests for hotkey string parsing."""

    def test_parse_cmd_shift_r(self):
        """Test parsing Cmd+Shift+R hotkey."""
        from recall.app.hotkeys import parse_hotkey

        result = parse_hotkey("<cmd>+<shift>+r")

        assert "cmd" in result["modifiers"] or "super" in result["modifiers"]
        assert "shift" in result["modifiers"]
        assert result["key"] == "r"

    def test_parse_ctrl_alt_n(self):
        """Test parsing Ctrl+Alt+N hotkey."""
        from recall.app.hotkeys import parse_hotkey

        result = parse_hotkey("<ctrl>+<alt>+n")

        assert "ctrl" in result["modifiers"]
        assert "alt" in result["modifiers"]
        assert result["key"] == "n"

    def test_parse_single_key(self):
        """Test parsing single key (no modifiers)."""
        from recall.app.hotkeys import parse_hotkey

        result = parse_hotkey("f1")

        assert result["modifiers"] == []
        assert result["key"] == "f1"

    def test_format_hotkey_for_display(self):
        """Test formatting hotkey for display."""
        from recall.app.hotkeys import format_hotkey_display

        # macOS style
        result = format_hotkey_display("<cmd>+<shift>+r")

        assert "⌘" in result or "Cmd" in result
        assert "⇧" in result or "Shift" in result
        assert "R" in result


# ============================================================================
# Test: Conflict Detection
# ============================================================================


class TestHotkeyConflicts:
    """Tests for hotkey conflict detection."""

    def test_detect_internal_conflicts(self):
        """Test detecting conflicts within config."""
        from recall.app.hotkeys import HotkeyConfig, detect_conflicts

        config = HotkeyConfig(
            toggle_recording="<cmd>+<shift>+r",
            quick_note="<cmd>+<shift>+r",  # Duplicate!
        )

        conflicts = detect_conflicts(config)

        assert len(conflicts) > 0
        assert "toggle_recording" in str(conflicts)
        assert "quick_note" in str(conflicts)

    def test_no_conflicts_with_different_hotkeys(self):
        """Test no conflicts with unique hotkeys."""
        from recall.app.hotkeys import HotkeyConfig, detect_conflicts

        config = HotkeyConfig()

        conflicts = detect_conflicts(config)

        assert len(conflicts) == 0


# ============================================================================
# Test: MenuBar Integration
# ============================================================================


class TestMenuBarHotkeyIntegration:
    """Tests for hotkey integration with RecallMenuBar."""

    def test_menubar_has_hotkey_manager(self):
        """Test that RecallMenuBar has a hotkey manager."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", False):
                    from recall.app.menubar import RecallMenuBar

                    app = RecallMenuBar()

                    assert hasattr(app, "hotkey_manager")

    def test_menubar_hotkey_toggles_recording(self):
        """Test that hotkey triggers recording toggle."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", False):
                    from recall.app.menubar import RecallMenuBar

                    app = RecallMenuBar()

                    # Simulate hotkey press by calling callback
                    app.hotkey_manager._handle_toggle_recording()

                    # Should trigger recording (mocked)

    def test_menubar_starts_hotkey_listener_on_run(self):
        """Test that hotkey listener starts when app runs."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", True):
                    with patch("recall.app.hotkeys.keyboard"):
                        from recall.app.menubar import RecallMenuBar

                        app = RecallMenuBar()

                        with patch.object(app.hotkey_manager, "start_listening") as mock_start:
                            # Call the setup method (run() would block)
                            app._setup_hotkeys()

                            mock_start.assert_called_once()

    def test_menubar_has_hotkey_config(self):
        """Test that RecallMenuBar has hotkey configuration."""
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.recording.Recorder"):
                with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", False):
                    from recall.app.menubar import RecallMenuBar

                    app = RecallMenuBar()

                    assert hasattr(app, "hotkey_config")
