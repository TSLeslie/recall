"""Tests for microphone recording (Ticket 2.1).

Tests cover:
- Recorder initialization with output directory
- start_recording() / stop_recording() workflow
- record() for fixed duration
- 16kHz mono WAV output (Whisper format)
- Filename format: mic_{timestamp}.wav
- is_recording property
- get_input_devices() returns available devices
- set_input_device() selects specific device
- Error handling for device not found
"""

from pathlib import Path

import pytest


class TestRecorderInit:
    """Test Recorder initialization."""

    def test_recorder_accepts_output_dir(self, temp_storage_dir):
        """Test that Recorder accepts output directory."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)

        assert recorder.output_dir == temp_storage_dir

    def test_recorder_creates_output_dir_if_missing(self, tmp_path):
        """Test that Recorder creates output directory if it doesn't exist."""
        from recall.capture.recorder import Recorder

        new_dir = tmp_path / "recordings" / "audio"
        Recorder(output_dir=new_dir)

        assert new_dir.exists()

    def test_recorder_default_sample_rate_is_16khz(self, temp_storage_dir):
        """Test that Recorder uses 16kHz sample rate (Whisper preferred)."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)

        assert recorder.sample_rate == 16000

    def test_recorder_default_channels_is_mono(self, temp_storage_dir):
        """Test that Recorder uses mono channel (Whisper preferred)."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)

        assert recorder.channels == 1


class TestRecordingWorkflow:
    """Test start/stop recording workflow."""

    def test_is_recording_initially_false(self, temp_storage_dir):
        """Test that is_recording is False initially."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)

        assert recorder.is_recording is False

    def test_start_recording_sets_is_recording_true(self, temp_storage_dir, mock_sounddevice):
        """Test that start_recording sets is_recording to True."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.start_recording()

        assert recorder.is_recording is True

    def test_stop_recording_sets_is_recording_false(self, temp_storage_dir, mock_sounddevice):
        """Test that stop_recording sets is_recording to False."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.start_recording()
        recorder.stop_recording()

        assert recorder.is_recording is False

    def test_stop_recording_returns_path(self, temp_storage_dir, mock_sounddevice):
        """Test that stop_recording returns path to WAV file."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.start_recording()
        audio_path = recorder.stop_recording()

        assert isinstance(audio_path, Path)
        assert audio_path.suffix == ".wav"
        assert audio_path.parent == temp_storage_dir

    def test_stop_recording_creates_wav_file(self, temp_storage_dir, mock_sounddevice):
        """Test that stop_recording creates a WAV file."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.start_recording()
        audio_path = recorder.stop_recording()

        assert audio_path.exists()

    def test_recording_filename_format(self, temp_storage_dir, mock_sounddevice):
        """Test that recording filename follows mic_{timestamp}.wav format."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.start_recording()
        audio_path = recorder.stop_recording()

        # Should be mic_YYYYMMDD_HHMMSS.wav
        assert audio_path.name.startswith("mic_")
        assert audio_path.name.endswith(".wav")
        # Check timestamp format in filename
        timestamp_part = audio_path.stem.replace("mic_", "")
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS

    def test_stop_without_start_raises_error(self, temp_storage_dir):
        """Test that stop_recording without start raises error."""
        from recall.capture.recorder import Recorder, RecordingError

        recorder = Recorder(output_dir=temp_storage_dir)

        with pytest.raises(RecordingError):
            recorder.stop_recording()


class TestFixedDurationRecording:
    """Test record() for fixed duration."""

    def test_record_returns_path(self, temp_storage_dir, mock_sounddevice):
        """Test that record() returns path to WAV file."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        audio_path = recorder.record(duration_seconds=1)

        assert isinstance(audio_path, Path)
        assert audio_path.exists()
        assert audio_path.suffix == ".wav"

    def test_record_calls_sounddevice_with_correct_params(self, temp_storage_dir, mock_sounddevice):
        """Test that record() uses correct sample rate and channels."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.record(duration_seconds=2)

        # Check sounddevice.rec was called with correct parameters
        mock_sounddevice.rec.assert_called_once()
        call_kwargs = mock_sounddevice.rec.call_args
        assert call_kwargs[1]["samplerate"] == 16000
        assert call_kwargs[1]["channels"] == 1

    def test_record_waits_for_completion(self, temp_storage_dir, mock_sounddevice):
        """Test that record() waits for recording to complete."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.record(duration_seconds=1)

        mock_sounddevice.wait.assert_called_once()


class TestAudioDevices:
    """Test audio device management."""

    def test_get_input_devices_returns_list(self, temp_storage_dir, mock_sounddevice):
        """Test that get_input_devices returns list of AudioDevice."""
        from recall.capture.recorder import AudioDevice, Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        devices = recorder.get_input_devices()

        assert isinstance(devices, list)
        assert len(devices) > 0
        assert all(isinstance(d, AudioDevice) for d in devices)

    def test_audio_device_has_required_fields(self, temp_storage_dir, mock_sounddevice):
        """Test that AudioDevice has id, name, and max_channels."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        devices = recorder.get_input_devices()

        device = devices[0]
        assert hasattr(device, "id")
        assert hasattr(device, "name")
        assert hasattr(device, "max_input_channels")

    def test_set_input_device_changes_device(self, temp_storage_dir, mock_sounddevice):
        """Test that set_input_device changes the recording device."""
        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        recorder.set_input_device(1)

        assert recorder.device_id == 1

    def test_set_input_device_invalid_raises_error(self, temp_storage_dir, mock_sounddevice):
        """Test that set_input_device with invalid ID raises error."""
        from recall.capture.recorder import DeviceNotFoundError, Recorder

        # Configure mock to raise error for invalid device
        mock_sounddevice.query_devices.side_effect = lambda x: (_ for _ in ()).throw(
            Exception("Invalid device")
        )

        recorder = Recorder(output_dir=temp_storage_dir)

        with pytest.raises(DeviceNotFoundError):
            recorder.set_input_device(999)


class TestWAVFileFormat:
    """Test WAV file output format."""

    def test_wav_file_is_16khz(self, temp_storage_dir, mock_sounddevice):
        """Test that WAV file has 16kHz sample rate."""
        import wave

        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        audio_path = recorder.record(duration_seconds=1)

        with wave.open(str(audio_path), "rb") as wav:
            assert wav.getframerate() == 16000

    def test_wav_file_is_mono(self, temp_storage_dir, mock_sounddevice):
        """Test that WAV file has 1 channel (mono)."""
        import wave

        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        audio_path = recorder.record(duration_seconds=1)

        with wave.open(str(audio_path), "rb") as wav:
            assert wav.getnchannels() == 1

    def test_wav_file_is_16bit(self, temp_storage_dir, mock_sounddevice):
        """Test that WAV file has 16-bit sample width."""
        import wave

        from recall.capture.recorder import Recorder

        recorder = Recorder(output_dir=temp_storage_dir)
        audio_path = recorder.record(duration_seconds=1)

        with wave.open(str(audio_path), "rb") as wav:
            assert wav.getsampwidth() == 2  # 2 bytes = 16 bits
