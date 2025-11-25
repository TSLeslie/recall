"""Microphone recording module for Recall.

Provides the Recorder class for capturing audio from microphone input devices.
Records in 16kHz mono WAV format optimized for Whisper transcription.
"""

import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import sounddevice as sd


class RecordingError(Exception):
    """Error raised when recording operations fail."""

    pass


class DeviceNotFoundError(Exception):
    """Error raised when an audio device is not found."""

    pass


@dataclass
class AudioDevice:
    """Represents an audio input device.

    Attributes:
        id: Device index in sounddevice.
        name: Human-readable device name.
        max_input_channels: Maximum number of input channels.
    """

    id: int
    name: str
    max_input_channels: int


class Recorder:
    """Records audio from microphone to WAV files.

    Records at 16kHz mono, optimized for Whisper transcription.
    Supports both fixed-duration recording and start/stop workflow.

    Attributes:
        output_dir: Directory where recordings are saved.
        sample_rate: Audio sample rate (default: 16000 Hz).
        channels: Number of audio channels (default: 1 for mono).
        device_id: Selected input device ID (None for default).

    Example:
        >>> recorder = Recorder(output_dir=Path("./recordings"))
        >>> # Fixed duration recording
        >>> audio_path = recorder.record(duration_seconds=30)
        >>> # Or start/stop workflow
        >>> recorder.start_recording()
        >>> # ... do stuff ...
        >>> audio_path = recorder.stop_recording()
    """

    def __init__(
        self,
        output_dir: Path,
        sample_rate: int = 16000,
        channels: int = 1,
    ):
        """Initialize the Recorder.

        Args:
            output_dir: Directory where recordings will be saved.
            sample_rate: Sample rate in Hz (default: 16000 for Whisper).
            channels: Number of channels (default: 1 for mono).
        """
        self.output_dir = output_dir
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_id: Optional[int] = None

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Recording state
        self._is_recording = False
        self._recording_data: list = []
        self._stream: Optional[sd.InputStream] = None
        self._start_time: Optional[datetime] = None

    @property
    def is_recording(self) -> bool:
        """Return whether recording is in progress."""
        return self._is_recording

    def _generate_filename(self, timestamp: Optional[datetime] = None) -> Path:
        """Generate filename for recording.

        Args:
            timestamp: Timestamp to use (default: current time).

        Returns:
            Path to the WAV file.
        """
        if timestamp is None:
            timestamp = datetime.now()
        filename = f"mic_{timestamp.strftime('%Y%m%d_%H%M%S')}.wav"
        return self.output_dir / filename

    def _write_wav(self, audio_data, filepath: Path) -> None:
        """Write audio data to WAV file.

        Args:
            audio_data: Numpy array of audio samples.
            filepath: Path to write the WAV file.
        """
        import numpy as np

        # Convert float32 to int16
        if audio_data.dtype == np.float32:
            # Scale to int16 range
            audio_int16 = (audio_data * 32767).astype(np.int16)
        else:
            audio_int16 = audio_data.astype(np.int16)

        # Flatten if needed (remove channel dimension for mono)
        if audio_int16.ndim > 1 and audio_int16.shape[1] == 1:
            audio_int16 = audio_int16.flatten()

        with wave.open(str(filepath), "w") as wav:
            wav.setnchannels(self.channels)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.sample_rate)
            wav.writeframes(audio_int16.tobytes())

    def start_recording(self) -> None:
        """Start recording audio.

        Begins recording from the selected input device.
        Use stop_recording() to end recording and save the file.

        Raises:
            RecordingError: If already recording.
        """
        if self._is_recording:
            raise RecordingError("Already recording")

        self._recording_data = []
        self._start_time = datetime.now()

        def callback(indata, frames, time, status):
            """Callback for audio stream."""
            self._recording_data.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device_id,
            callback=callback,
        )
        self._stream.start()
        self._is_recording = True

    def stop_recording(self) -> Path:
        """Stop recording and save to WAV file.

        Returns:
            Path to the saved WAV file.

        Raises:
            RecordingError: If not currently recording.
        """
        if not self._is_recording:
            raise RecordingError("Not recording")

        # Stop the stream
        self._stream.stop()
        self._stream.close()
        self._stream = None
        self._is_recording = False

        # Concatenate recorded chunks
        import numpy as np

        audio_data = np.concatenate(self._recording_data, axis=0)

        # Generate filename and save
        filepath = self._generate_filename(self._start_time)
        self._write_wav(audio_data, filepath)

        return filepath

    def record(self, duration_seconds: float) -> Path:
        """Record audio for a fixed duration.

        Args:
            duration_seconds: Duration to record in seconds.

        Returns:
            Path to the saved WAV file.
        """
        # Calculate number of frames
        num_frames = int(duration_seconds * self.sample_rate)

        # Record audio
        audio_data = sd.rec(
            num_frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device_id,
            dtype="float32",
        )
        sd.wait()

        # Generate filename and save
        filepath = self._generate_filename()
        self._write_wav(audio_data, filepath)

        return filepath

    def get_input_devices(self) -> list[AudioDevice]:
        """Get list of available audio input devices.

        Returns:
            List of AudioDevice objects for input devices.
        """
        devices = sd.query_devices()
        input_devices = []

        for idx, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                input_devices.append(
                    AudioDevice(
                        id=idx,
                        name=device["name"],
                        max_input_channels=device["max_input_channels"],
                    )
                )

        return input_devices

    def set_input_device(self, device_id: int) -> None:
        """Set the input device for recording.

        Args:
            device_id: Device index to use for recording.

        Raises:
            DeviceNotFoundError: If device ID is invalid.
        """
        try:
            device_info = sd.query_devices(device_id)
            if device_info["max_input_channels"] == 0:
                raise DeviceNotFoundError(f"Device {device_id} is not an input device")
            self.device_id = device_id
        except Exception as e:
            raise DeviceNotFoundError(f"Device {device_id} not found: {e}") from e
