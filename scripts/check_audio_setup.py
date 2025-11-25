#!/usr/bin/env python3
"""Audio Setup Verification Script for Recall.

This script checks if the system is properly configured for
audio capture with BlackHole virtual audio device.

Usage:
    python scripts/check_audio_setup.py
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import sounddevice as sd


@dataclass
class AudioSetupStatus:
    """Status of the audio setup.

    Attributes:
        blackhole_found: Whether BlackHole device was detected
        blackhole_device_id: Device ID if found
        blackhole_channels: Number of channels available
        is_ready: Whether the setup is ready for capture
        message: Human-readable status message
    """

    blackhole_found: bool
    blackhole_device_id: Optional[int]
    blackhole_channels: int
    is_ready: bool
    message: str


def check_blackhole_device() -> Tuple[Optional[int], int]:
    """Check if BlackHole virtual audio device is available.

    Returns:
        Tuple of (device_id, channels) if found, (None, 0) otherwise.
    """
    try:
        devices = sd.query_devices()
        for device in devices:
            if isinstance(device, dict):
                name = device.get("name", "")
                if "blackhole" in name.lower():
                    device_id = device.get("index")
                    channels = device.get("max_input_channels", 0)
                    return (device_id, channels)
        return (None, 0)
    except Exception:
        return (None, 0)


def check_audio_setup() -> AudioSetupStatus:
    """Check the complete audio setup status.

    Returns:
        AudioSetupStatus with the current configuration state.
    """
    device_id, channels = check_blackhole_device()

    if device_id is not None:
        return AudioSetupStatus(
            blackhole_found=True,
            blackhole_device_id=device_id,
            blackhole_channels=channels,
            is_ready=True,
            message="System audio capture is ready!",
        )
    else:
        return AudioSetupStatus(
            blackhole_found=False,
            blackhole_device_id=None,
            blackhole_channels=0,
            is_ready=False,
            message="BlackHole not found. Please install it to enable system audio capture.",
        )


def get_setup_recommendations(status: AudioSetupStatus) -> List[str]:
    """Get setup recommendations based on current status.

    Args:
        status: Current AudioSetupStatus

    Returns:
        List of recommendation strings.
    """
    recommendations = []

    if not status.blackhole_found:
        recommendations.extend(
            [
                "Install BlackHole virtual audio driver:",
                "  brew install blackhole-2ch",
                "Or download from: https://github.com/ExistentialAudio/BlackHole/releases",
                "",
                "After installation:",
                "1. Open Audio MIDI Setup (Applications > Utilities)",
                "2. Create a Multi-Output Device",
                "3. Add both your speakers and BlackHole 2ch",
                "4. Set the Multi-Output Device as your default output",
            ]
        )
    else:
        recommendations.extend(
            [
                "Play some audio (e.g., YouTube video)",
                "Run: recall status",
                "Start recording: recall record --source system",
            ]
        )

    return recommendations


def print_status_report(status: AudioSetupStatus) -> None:
    """Print a formatted status report.

    Args:
        status: Current AudioSetupStatus
    """
    print("\n🔊 Recall Audio Setup Checker")
    print("=" * 32)
    print("\nChecking audio devices...\n")

    if status.blackhole_found:
        print("✅ BlackHole found!")
        print(f"   - Device ID: {status.blackhole_device_id}")
        print(f"   - Input channels: {status.blackhole_channels}")
        print()
        print("✅", status.message)
    else:
        print("❌ BlackHole not found!")
        print()
        print(status.message)

    print()
    print("Recommended next steps:")
    for i, rec in enumerate(get_setup_recommendations(status), 1):
        if rec:  # Skip empty strings for spacing
            print(f"  {rec}")
        else:
            print()


def list_all_devices() -> None:
    """List all available audio devices."""
    print("\n📋 Available Audio Devices:")
    print("-" * 40)
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if isinstance(device, dict):
                name = device.get("name", "Unknown")
                inputs = device.get("max_input_channels", 0)
                outputs = device.get("max_output_channels", 0)
                print(f"  [{i}] {name}")
                print(f"      Inputs: {inputs}, Outputs: {outputs}")
    except Exception as e:
        print(f"  Error listing devices: {e}")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for not ready).
    """
    status = check_audio_setup()
    print_status_report(status)

    # Optionally show all devices
    print()
    list_all_devices()

    return 0 if status.is_ready else 1


if __name__ == "__main__":
    exit(main())
