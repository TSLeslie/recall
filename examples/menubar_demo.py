#!/usr/bin/env python3
"""Demo script for the Recall Menu Bar App (Sprint 6).

This script demonstrates all the menu bar app features:
- Recording controls
- Notifications
- Auto-recording configuration
- Global hotkeys

Since rumps and pynput are macOS-only, this demo runs in mock mode
and simulates the user interactions.
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_status(app) -> None:
    """Print current app status."""
    from recall.app.menubar import AppState

    state_icons = {
        AppState.IDLE: "🎤 Idle",
        AppState.RECORDING: "🔴 Recording",
        AppState.PROCESSING: "⚙️ Processing",
    }
    print(f"  Status: {state_icons.get(app.state, app.state)}")
    print(f"  Icon: {app.icon}")
    if app.recording_duration:
        print(f"  Duration: {app.recording_controller.get_formatted_duration()}")


def demo_menu_items(app) -> None:
    """Demonstrate menu item generation."""
    print_header("Menu Items (Current State)")

    items = app.get_menu_items()
    for item in items:
        if item.is_separator:
            print("  ─────────────────────")
        else:
            key_hint = f" ({item.key})" if item.key else ""
            enabled = "" if item.enabled else " [disabled]"
            print(f"  • {item.title}{key_hint}{enabled}")


def demo_recording_workflow() -> None:
    """Demonstrate the recording workflow."""
    print_header("Recording Workflow Demo")

    # Mock the Recorder to avoid needing actual audio devices
    with patch("recall.app.recording.Recorder") as mock_recorder:
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            # Configure mock
            mock_instance = MagicMock()
            mock_instance.stop_recording.return_value = Path("/tmp/demo_recording.wav")
            mock_recorder.return_value = mock_instance

            from recall.app.menubar import RecallMenuBar

            app = RecallMenuBar()

            print("1. Initial State:")
            print_status(app)
            demo_menu_items(app)

            print("\n2. Starting Recording...")
            app.on_start_recording(None)
            time.sleep(0.1)  # Simulate some recording time
            print_status(app)

            print("\n3. Menu changes during recording:")
            demo_menu_items(app)

            print("\n4. Stopping Recording...")
            app.on_stop_recording(None)
            print_status(app)

            print("\n5. Back to Idle:")
            app.set_state(app.state.__class__.IDLE)
            print_status(app)


def demo_notifications() -> None:
    """Demonstrate the notification system."""
    print_header("Notification System Demo")

    from recall.app.notifications import NotificationManager

    # Create manager (will use logging fallback since rumps unavailable)
    manager = NotificationManager()

    print("Sending notifications (logged since rumps not available):\n")

    print("  → Recording Started notification:")
    manager.notify_recording_started(source="microphone")

    print("\n  → Recording Saved notification:")
    manager.notify_recording_saved(title="Team Standup Meeting", duration=1847)

    print("\n  → Auto-Recording Detected notification:")
    manager.notify_auto_recording(source="Zoom", app_name="zoom.us")

    print("\n  → Error notification:")
    manager.notify_error("Failed to access microphone")


def demo_auto_recording_config() -> None:
    """Demonstrate auto-recording configuration."""
    print_header("Auto-Recording Configuration Demo")

    from recall.app.notifications import AutoRecordingConfig

    config = AutoRecordingConfig()

    print("Default Configuration:")
    print(f"  Enabled: {config.enabled}")
    print(f"  Detect Meeting Apps: {config.detect_meeting_apps}")
    print(f"  Detect System Audio: {config.detect_system_audio}")
    print(f"  Whitelisted Apps: {len(config.app_whitelist)}")

    print("\nWhitelisted Meeting Apps:")
    for app_name in config.app_whitelist:
        print(f"  • {app_name}")

    print("\nChecking app whitelist:")
    test_apps = ["zoom.us", "Safari", "Microsoft Teams", "Firefox"]
    for app_name in test_apps:
        status = "✓" if config.is_app_whitelisted(app_name) else "✗"
        print(f"  {status} {app_name}")

    print("\nAdding custom app to whitelist:")
    config.add_to_whitelist("OBS Studio")
    print(f"  Added 'OBS Studio': {config.is_app_whitelisted('OBS Studio')}")

    print("\nConfiguration as dict (for saving):")
    data = config.to_dict()
    print(f"  {data}")


def demo_hotkeys() -> None:
    """Demonstrate hotkey configuration."""
    print_header("Global Hotkeys Demo")

    from recall.app.hotkeys import (
        HotkeyConfig,
        HotkeyManager,
        detect_conflicts,
        format_hotkey_display,
        parse_hotkey,
    )

    config = HotkeyConfig()

    print("Default Hotkey Configuration:")
    print(f"  Enabled: {config.enabled}")

    print("\nConfigured Hotkeys:")
    hotkeys = config.get_all_hotkeys()
    for action, hotkey in hotkeys.items():
        display = format_hotkey_display(hotkey)
        print(f"  {action:20} : {hotkey:20} → {display}")

    print("\nParsing hotkey '<cmd>+<shift>+r':")
    parsed = parse_hotkey("<cmd>+<shift>+r")
    print(f"  Modifiers: {parsed['modifiers']}")
    print(f"  Key: {parsed['key']}")

    print("\nConflict Detection (no conflicts):")
    conflicts = detect_conflicts(config)
    print(f"  Conflicts found: {len(conflicts)}")

    print("\nConflict Detection (with duplicate):")
    bad_config = HotkeyConfig(
        toggle_recording="<cmd>+<shift>+r",
        quick_note="<cmd>+<shift>+r",  # Duplicate!
    )
    conflicts = detect_conflicts(bad_config)
    if conflicts:
        print(f"  ⚠️  {conflicts[0]['message']}")

    print("\nHotkey Manager (mock mode):")
    with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", False):
        manager = HotkeyManager(config)

        # Set up callbacks
        actions_triggered = []
        manager.on_toggle_recording = lambda: actions_triggered.append("toggle_recording")
        manager.on_quick_note = lambda: actions_triggered.append("quick_note")

        print("  Simulating hotkey presses:")
        manager._handle_toggle_recording()
        print(f"    → Toggle Recording triggered: {actions_triggered}")

        manager._handle_quick_note()
        print(f"    → Quick Note triggered: {actions_triggered}")


def demo_full_integration() -> None:
    """Demonstrate full integration of all components."""
    print_header("Full Integration Demo")

    with patch("recall.app.recording.Recorder") as mock_recorder:
        with patch("recall.app.menubar.RUMPS_AVAILABLE", False):
            with patch("recall.app.hotkeys.PYNPUT_AVAILABLE", False):
                # Configure mock recorder
                mock_instance = MagicMock()
                mock_instance.stop_recording.return_value = Path("/tmp/demo.wav")
                mock_recorder.return_value = mock_instance

                from recall.app.menubar import RecallMenuBar

                app = RecallMenuBar()

                print("RecallMenuBar initialized with:")
                print(f"  ✓ Recording Controller: {type(app.recording_controller).__name__}")
                print(f"  ✓ Notification Manager: {type(app.notification_manager).__name__}")
                print(f"  ✓ Auto-Recording Config: {type(app.auto_recording_config).__name__}")
                print(f"  ✓ Hotkey Manager: {type(app.hotkey_manager).__name__}")
                print(f"  ✓ Hotkey Config: {type(app.hotkey_config).__name__}")

                print("\nSimulating hotkey toggle recording (Cmd+Shift+R):")
                print(f"  Before: {app.state}")
                app.hotkey_manager._handle_toggle_recording()
                print(f"  After: {app.state}")

                print("\nSimulating another toggle (stop recording):")
                app.hotkey_manager._handle_toggle_recording()
                print(f"  After: {app.state}")


def main():
    """Run all demos."""
    print("\n" + "🎙️ " * 20)
    print("\n  RECALL MENU BAR APP DEMO (Sprint 6)")
    print("\n" + "🎙️ " * 20)

    # Enable logging to see notification fallbacks
    import logging

    logging.basicConfig(level=logging.INFO, format="     [%(name)s] %(message)s")

    try:
        demo_recording_workflow()
        demo_notifications()
        demo_auto_recording_config()
        demo_hotkeys()
        demo_full_integration()

        print_header("Demo Complete! 🎉")
        print("All Sprint 6 features demonstrated successfully.")
        print("\nNote: This demo runs in mock mode since rumps and pynput")
        print("are macOS-only dependencies. On macOS with these installed,")
        print("the menu bar app would appear in the system menu bar.\n")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
