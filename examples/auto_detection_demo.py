#!/usr/bin/env python3
"""Demo: Auto-Detection Features (Sprint 5)

This demo showcases the new auto-detection capabilities:
1. System Audio Monitor - detects when audio starts/stops
2. Application Detector - identifies running audio apps
3. Audio Setup Checker - verifies BlackHole configuration

Run: python examples/auto_detection_demo.py
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

# ============================================================================
# Demo 1: Application Detector (Real)
# ============================================================================


def demo_application_detector():
    """Demo the application detector with real system processes."""
    print("\n" + "=" * 60)
    print("🔍 DEMO 1: Application Detector")
    print("=" * 60)
    print("\nScanning for running audio applications...\n")

    from recall.capture.detector import (
        AudioAppCategory,
        get_active_audio_app,
        get_running_audio_apps,
        is_meeting_app_running,
    )

    # Get all running audio apps
    apps = get_running_audio_apps()

    if apps:
        print(f"Found {len(apps)} audio application(s):\n")
        for app in apps:
            icon = {
                AudioAppCategory.MEETING: "📹",
                AudioAppCategory.MEDIA: "🎵",
                AudioAppCategory.BROWSER: "🌐",
                AudioAppCategory.OTHER: "📱",
            }.get(app.category, "📱")

            print(f"  {icon} {app.name}")
            print(f"     Category: {app.category.value}")
            print(f"     Process: {app.process_name}")
            if app.pid:
                print(f"     PID: {app.pid}")
            print()
    else:
        print("  No audio applications detected.")
        print("  (Try opening Chrome, Spotify, or a meeting app)\n")

    # Check meeting status
    print("-" * 40)
    if is_meeting_app_running():
        print("📹 Meeting app detected! Recording would be auto-tagged.")
    else:
        print("📹 No meeting app running.")

    # Get primary app
    active = get_active_audio_app()
    if active:
        print(f"🎯 Primary audio source: {active.name} ({active.category.value})")

    print()


# ============================================================================
# Demo 2: Audio Monitor (Simulated)
# ============================================================================


def demo_audio_monitor_simulated():
    """Demo the audio monitor with simulated events."""
    print("\n" + "=" * 60)
    print("🔊 DEMO 2: System Audio Monitor (Simulated)")
    print("=" * 60)
    print("\nSimulating audio detection events...\n")

    from recall.capture.monitor import AudioEvent, AudioMonitor

    # Create monitor with custom settings
    monitor = AudioMonitor(
        silence_threshold=0.01, silence_duration=2.0, device_name="BlackHole 2ch"
    )

    print(f"Monitor Configuration:")
    print(f"  - Silence threshold: {monitor.silence_threshold}")
    print(f"  - Silence duration: {monitor.silence_duration}s")
    print(f"  - Device: {monitor.device_name}")
    print(f"  - Is monitoring: {monitor.is_monitoring}")
    print()

    # Simulate events
    events = []

    def on_audio_event(event: AudioEvent):
        events.append(event)
        icon = "▶️" if event.event_type == "started" else "⏹️"
        print(f"  {icon} Audio {event.event_type} at {event.timestamp.strftime('%H:%M:%S')}")
        if event.source_hint:
            print(f"     Source: {event.source_hint}")

    print("Simulating audio events:")
    print("-" * 40)

    # Simulate: silence -> audio -> silence
    on_audio_event(
        AudioEvent(event_type="started", timestamp=datetime.now(), source_hint="Zoom Meeting")
    )

    time.sleep(0.5)

    on_audio_event(
        AudioEvent(
            event_type="stopped",
            timestamp=datetime.now(),
        )
    )

    print()
    print(f"Total events captured: {len(events)}")
    print()


# ============================================================================
# Demo 3: Audio Setup Checker
# ============================================================================


def demo_audio_setup_checker():
    """Demo the audio setup verification."""
    print("\n" + "=" * 60)
    print("🔧 DEMO 3: Audio Setup Checker")
    print("=" * 60)

    import sys
    from pathlib import Path

    # Add scripts to path for import
    scripts_path = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_path.parent))

    from scripts.check_audio_setup import (
        check_audio_setup,
        get_setup_recommendations,
    )

    status = check_audio_setup()

    print(f"\nSetup Status:")
    print(f"  - BlackHole found: {'✅ Yes' if status.blackhole_found else '❌ No'}")
    if status.blackhole_device_id is not None:
        print(f"  - Device ID: {status.blackhole_device_id}")
        print(f"  - Channels: {status.blackhole_channels}")
    print(f"  - Ready for capture: {'✅ Yes' if status.is_ready else '❌ No'}")
    print()

    print("Recommendations:")
    for rec in get_setup_recommendations(status)[:5]:  # Show first 5
        if rec:
            print(f"  → {rec}")
    print()


# ============================================================================
# Demo 4: Integration Example
# ============================================================================


def demo_integration_example():
    """Show how the components work together."""
    print("\n" + "=" * 60)
    print("🎯 DEMO 4: Integration Example")
    print("=" * 60)
    print("\nHow auto-detection enhances Recall:\n")

    from recall.capture.detector import get_active_audio_app, is_meeting_app_running

    # Scenario simulation
    print("Scenario: User starts a Zoom meeting")
    print("-" * 40)

    code_example = """
from recall.capture import (
    AudioMonitor,
    get_active_audio_app,
    is_meeting_app_running,
)
from recall.pipeline import ingest_audio

# 1. Check what app is playing audio
app = get_active_audio_app()
if app:
    print(f"Detected: {app.name} ({app.category.value})")

# 2. Auto-tag based on source
if is_meeting_app_running():
    source = "zoom"  # or detect specific app
else:
    source = "system"

# 3. Start monitoring for audio
def on_audio_event(event):
    if event.event_type == "started":
        # Begin recording automatically
        recorder.start()
    elif event.event_type == "stopped":
        # Stop and process the recording
        audio_path = recorder.stop()
        ingest_audio(audio_path, source=source)

monitor = AudioMonitor()
monitor.start_monitoring(on_audio_event)
"""

    print("```python")
    print(code_example)
    print("```")
    print()

    # Show what would happen
    print("What happens automatically:")
    print("  1. Recall detects Zoom is running → tags as 'meeting'")
    print("  2. Audio monitor detects when meeting audio starts")
    print("  3. Recording begins automatically")
    print("  4. When audio stops for 2+ seconds, recording ends")
    print("  5. Audio is transcribed, summarized, and indexed")
    print()


# ============================================================================
# Main
# ============================================================================


def main():
    """Run all demos."""
    print("\n" + "🎙️ " + "=" * 56 + " 🎙️")
    print("       RECALL AUTO-DETECTION DEMO (Sprint 5)")
    print("🎙️ " + "=" * 56 + " 🎙️")

    try:
        demo_application_detector()
        demo_audio_monitor_simulated()
        demo_audio_setup_checker()
        demo_integration_example()

        print("=" * 60)
        print("✅ Demo complete!")
        print("=" * 60)
        print("\nTo use these features in your code:")
        print("  from recall.capture import AudioMonitor, get_running_audio_apps")
        print("\nTo check your audio setup:")
        print("  python scripts/check_audio_setup.py")
        print("\nSee docs/AUDIO_SETUP.md for BlackHole installation guide.")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
