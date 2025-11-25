"""System Audio Monitor for detecting audio via BlackHole loopback.

This module provides monitoring of system audio to detect when audio
is playing (e.g., from Zoom, YouTube, etc.) via the BlackHole virtual
audio device.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


@dataclass
class AudioEvent:
    """Represents an audio detection event.

    Attributes:
        event_type: Type of event - 'started' or 'stopped'
        timestamp: When the event occurred
        source_hint: Optional hint about the audio source (e.g., "Zoom Meeting")
    """

    event_type: str
    timestamp: datetime
    source_hint: Optional[str] = None


class AudioMonitor:
    """Monitors system audio via BlackHole loopback device.

    This class detects when system audio starts and stops playing by
    monitoring audio levels through BlackHole virtual audio device.

    Attributes:
        silence_threshold: RMS amplitude below which audio is considered silence
        silence_duration: Seconds of silence before triggering 'stopped' event
        device_name: Name of the audio device to monitor (default: "BlackHole 2ch")
        is_monitoring: Whether the monitor is currently active
    """

    def __init__(
        self,
        silence_threshold: float = 0.01,
        silence_duration: float = 2.0,
        device_name: str = "BlackHole 2ch",
    ) -> None:
        """Initialize the AudioMonitor.

        Args:
            silence_threshold: RMS amplitude below which audio is silence (0.0-1.0)
            silence_duration: Seconds of silence before 'stopped' event
            device_name: Name of the audio input device (BlackHole)
        """
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.device_name = device_name

        self._is_monitoring = False
        self._callback: Optional[Callable[[AudioEvent], None]] = None
        self._was_audio_present = False
        self._silence_start: Optional[datetime] = None
        self._current_amplitude: float = 0.0
        self._stream: Optional[sd.InputStream] = None

    @property
    def is_monitoring(self) -> bool:
        """Return whether monitoring is active."""
        return self._is_monitoring

    @property
    def current_amplitude(self) -> float:
        """Return the current audio amplitude."""
        return self._current_amplitude

    def start_monitoring(self, callback: Callable[[AudioEvent], None]) -> None:
        """Start monitoring system audio.

        Args:
            callback: Function to call when audio events occur.
                      Receives AudioEvent objects.

        Raises:
            RuntimeError: If BlackHole device is not available.
        """
        self._callback = callback
        device_id = self._find_device()

        if device_id is None:
            raise RuntimeError(f"Audio device '{self.device_name}' not found")

        self._is_monitoring = True
        self._was_audio_present = False
        self._silence_start = None

        # Create and start the audio stream
        self._stream = sd.InputStream(
            device=device_id,
            channels=2,
            samplerate=44100,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop_monitoring(self) -> None:
        """Stop monitoring system audio."""
        self._is_monitoring = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._callback = None

    def _find_device(self) -> Optional[int]:
        """Find the audio device by name.

        Returns:
            Device index if found, None otherwise.
        """
        try:
            devices = sd.query_devices()
            for device in devices:
                if isinstance(device, dict) and device.get("name") == self.device_name:
                    if device.get("max_input_channels", 0) > 0:
                        return device.get("index")
            return None
        except Exception:
            return None

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback for audio stream data.

        Args:
            indata: Audio data as numpy array
            frames: Number of frames
            time_info: Timing information
            status: Status flags
        """
        is_audio = self._is_audio_present(indata)
        self._process_audio_state(is_audio)

    def _is_audio_present(self, audio_data: np.ndarray) -> bool:
        """Determine if audio is present in the data.

        Uses RMS (Root Mean Square) amplitude to determine
        if audio is above the silence threshold.

        Args:
            audio_data: Audio samples as numpy array

        Returns:
            True if audio is above threshold, False otherwise.
        """
        # Calculate RMS amplitude
        rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
        self._current_amplitude = float(rms)

        return rms > self.silence_threshold

    def _process_audio_state(self, is_audio: bool) -> None:
        """Process the current audio state and emit events.

        Args:
            is_audio: Whether audio is currently present
        """
        now = datetime.now()

        if is_audio and not self._was_audio_present:
            # Transition: silence -> audio
            self._was_audio_present = True
            self._silence_start = None
            self._emit_event(AudioEvent(event_type="started", timestamp=now))

        elif not is_audio and self._was_audio_present:
            # Audio stopped, start tracking silence duration
            if self._silence_start is None:
                self._silence_start = now
            else:
                silence_elapsed = (now - self._silence_start).total_seconds()
                if silence_elapsed >= self.silence_duration:
                    # Enough silence has passed, emit stopped event
                    self._was_audio_present = False
                    self._emit_event(AudioEvent(event_type="stopped", timestamp=now))
                    self._silence_start = None

        elif is_audio and self._was_audio_present:
            # Still audio, reset silence tracking
            self._silence_start = None

    def _emit_event(self, event: AudioEvent) -> None:
        """Emit an audio event to the callback.

        Args:
            event: The AudioEvent to emit
        """
        if self._callback is not None:
            self._callback(event)


def is_blackhole_available() -> bool:
    """Check if BlackHole virtual audio device is available.

    Returns:
        True if BlackHole is installed and available, False otherwise.
    """
    try:
        devices = sd.query_devices()
        for device in devices:
            if isinstance(device, dict):
                name = device.get("name", "")
                if "blackhole" in name.lower():
                    return True
        return False
    except Exception:
        return False
