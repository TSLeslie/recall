"""
Shared pytest fixtures for Recall test suite.

This file provides reusable fixtures for testing:
- Whisper transcription (mocked)
- LLM analysis (mocked)
- Audio capture (mocked)
- File storage (temporary directories)
- GraphRAG (mocked/temporary)
"""

import struct
import wave
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# =============================================================================
# Temporary Storage Fixtures
# =============================================================================


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary directory for storing recordings/transcripts."""
    storage_dir = tmp_path / "recall_storage"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def temp_graphrag_dir(tmp_path):
    """Temporary directory for GraphRAG working files."""
    graphrag_dir = tmp_path / "graphrag"
    graphrag_dir.mkdir()
    return graphrag_dir


# =============================================================================
# Audio Fixtures
# =============================================================================


@pytest.fixture
def sample_audio_path(tmp_path):
    """Create a minimal valid WAV file for testing.

    Generates 1 second of silence at 16kHz mono, which is sufficient
    for testing transcription pipelines without actual audio content.
    """
    audio_path = tmp_path / "test_audio.wav"
    with wave.open(str(audio_path), "w") as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(16000)  # 16kHz (Whisper's native rate)
        # 1 second of silence (16000 samples of zeros)
        wav.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))
    return audio_path


@pytest.fixture
def sample_audio_bytes():
    """Return raw audio bytes for testing without file I/O."""
    import io

    buffer = io.BytesIO()
    with wave.open(buffer, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))
    buffer.seek(0)
    return buffer.read()


# =============================================================================
# Whisper Mocking Fixtures
# =============================================================================


@pytest.fixture
def mock_whisper(mocker):
    """Mock whisper.load_model to avoid loading actual Whisper model.

    Returns the mock so tests can configure return values:
        mock_whisper.return_value.transcribe.return_value = {"text": "..."}
    """
    mock = mocker.patch("whisper.load_model")
    # Default return value for transcribe
    mock.return_value.transcribe.return_value = {
        "text": "This is a test transcription.",
        "segments": [{"start": 0.0, "end": 2.5, "text": "This is a test transcription."}],
        "language": "en",
    }
    return mock


@pytest.fixture
def mock_whisper_result():
    """Sample Whisper transcription result for testing processors."""
    return {
        "text": "Hello, this is a test meeting. We discussed the quarterly budget and upcoming product launches.",
        "segments": [
            {
                "start": 0.0,
                "end": 3.5,
                "text": "Hello, this is a test meeting.",
                "no_speech_prob": 0.1,
            },
            {
                "start": 3.5,
                "end": 8.0,
                "text": "We discussed the quarterly budget and upcoming product launches.",
                "no_speech_prob": 0.05,
            },
        ],
        "language": "en",
    }


# =============================================================================
# LLM Mocking Fixtures (llama-cpp-python / Qwen)
# =============================================================================


@pytest.fixture
def mock_llama_cpp(mocker):
    """Mock llama_cpp.Llama for low-level LLM tests.

    Returns the mock so tests can configure return values:
        mock_llama_cpp.return_value.return_value = {"choices": [...]}
    """
    mock = mocker.patch("llama_cpp.Llama")
    # Default callable behavior
    mock.return_value.return_value = {"choices": [{"text": "This is a mock LLM response."}]}
    return mock


@pytest.fixture
def mock_llama_analyzer(mocker):
    """Mock LlamaAnalyzer class to avoid loading actual LLM model.

    Returns the instance mock so tests can configure generate():
        mock_llama_analyzer.generate.return_value = "Summary text"
    """
    mock_class = mocker.patch("recall.analyze.LlamaAnalyzer")
    mock_instance = mock_class.return_value
    mock_instance.generate.return_value = "Mock summary of the content."
    return mock_instance


@pytest.fixture
def sample_llm_summary():
    """Sample LLM-generated summary for testing."""
    return """Key Points:
- Meeting covered Q4 budget review
- New product launches planned for December
- Team restructuring into three divisions

Action Items:
- Review budget proposal by Friday
- Schedule follow-up meeting for next week"""


# =============================================================================
# Audio Capture Mocking Fixtures
# =============================================================================


@pytest.fixture
def mock_sounddevice(mocker):
    """Mock sounddevice module for audio capture tests.

    Mocks both recording and device query functions.
    Patches 'recall.capture.recorder.sd' where sounddevice is used.
    """
    mock = mocker.patch("recall.capture.recorder.sd")

    # Mock device query - return list of devices
    mock.query_devices.return_value = [
        {"name": "Built-in Microphone", "max_input_channels": 2, "max_output_channels": 0},
        {"name": "BlackHole 2ch", "max_input_channels": 2, "max_output_channels": 2},
        {"name": "Built-in Output", "max_input_channels": 0, "max_output_channels": 2},
    ]

    # Mock query_devices with index - return specific device
    def query_device_by_id(device_id=None):
        if device_id is None:
            return mock.query_devices.return_value
        devices = mock.query_devices.return_value
        if device_id >= len(devices):
            raise Exception(f"Invalid device {device_id}")
        return devices[device_id]

    mock.query_devices.side_effect = query_device_by_id

    # Mock recording - returns numpy array
    import numpy as np

    mock.rec.return_value = np.zeros((16000, 1), dtype=np.float32)
    mock.wait.return_value = None

    # Mock InputStream for start/stop workflow
    # The InputStream captures callback and simulates recording
    mock_stream = MagicMock()
    captured_callback = [None]

    def capture_input_stream(**kwargs):
        captured_callback[0] = kwargs.get("callback")
        return mock_stream

    mock.InputStream.side_effect = capture_input_stream

    def start_recording_mock():
        # Simulate callback being called with audio data
        if captured_callback[0]:
            test_audio = np.zeros((1024, 1), dtype=np.float32)
            captured_callback[0](test_audio, 1024, None, None)

    mock_stream.start.side_effect = start_recording_mock
    mock_stream.stop.return_value = None
    mock_stream.close.return_value = None

    return mock


@pytest.fixture
def mock_ytdlp(mocker, tmp_path):
    """Mock yt_dlp for YouTube download tests.

    Creates actual WAV files to simulate yt-dlp download behavior.
    """
    mock = mocker.patch("recall.capture.youtube.yt_dlp.YoutubeDL")

    # Configure context manager behavior
    mock_instance = MagicMock()
    mock.return_value.__enter__.return_value = mock_instance
    mock.return_value.__exit__.return_value = None

    # Default extract_info response
    default_info = {
        "title": "Test Video Title",
        "duration": 300,
        "uploader": "Test Channel",
        "upload_date": "20251125",
        "id": "dQw4w9WgXcQ",
        "description": "Test video description",
        "thumbnail": "https://example.com/thumb.jpg",
    }

    def extract_info_side_effect(url, download=False):
        """Create a mock WAV file when extract_info is called."""
        # Get video ID from the info
        info = dict(default_info)

        # Determine output directory from the configured outtmpl
        # This requires reading the options passed to YoutubeDL
        call_args = mock.call_args
        if call_args and call_args[0]:
            opts = call_args[0][0]
            if "outtmpl" in opts:
                outtmpl = opts["outtmpl"]
                # Replace template variables
                output_path = outtmpl.replace("%(id)s", info["id"]).replace("%(ext)s", "wav")
                output_path = Path(output_path)

                # Create the WAV file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                _create_test_wav(output_path)

        return info

    mock_instance.extract_info.side_effect = extract_info_side_effect

    # Also mock _convert_to_whisper_format to avoid needing ffmpeg
    mocker.patch("recall.capture.youtube._convert_to_whisper_format", return_value=None)

    return mock


def _create_test_wav(path: Path, duration_seconds: float = 1.0):
    """Create a minimal test WAV file at 16kHz mono."""
    sample_rate = 16000
    num_samples = int(duration_seconds * sample_rate)

    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        # Write silence
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))


# =============================================================================
# Storage Fixtures
# =============================================================================


@pytest.fixture
def sample_recording_dict():
    """Sample recording data as a dictionary."""
    return {
        "source": "zoom",
        "timestamp": datetime(2025, 11, 25, 14, 30, 0),
        "duration_seconds": 3600,
        "transcript": "Hello, this is a test meeting about the Q4 roadmap.",
        "summary": "Meeting discussed Q4 roadmap and action items.",
        "participants": ["Alice", "Bob"],
        "tags": ["meeting", "q4", "roadmap"],
    }


@pytest.fixture
def sample_markdown_content():
    """Sample Markdown file content with YAML frontmatter."""
    return """---
source: zoom
timestamp: 2025-11-25T14:30:00
duration_seconds: 3600
summary: Meeting discussed Q4 roadmap and action items.
participants:
  - Alice
  - Bob
tags:
  - meeting
  - q4
  - roadmap
---

Hello, this is a test meeting about the Q4 roadmap.

We discussed the following topics:
1. Budget review
2. Product launches
3. Team restructuring
"""


@pytest.fixture
def test_index(tmp_path):
    """Create an in-memory or temporary SQLite index for testing.

    Note: Implementation depends on RecordingIndex being created.
    This fixture will need updating once storage/index.py exists.
    """
    # Placeholder - returns path for now
    # Will be updated to return actual RecordingIndex instance
    db_path = tmp_path / "test_index.db"
    return db_path


# =============================================================================
# GraphRAG Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_func():
    """Mock async LLM function for GraphRAG.

    Returns a simple echo function for testing graph construction.
    """

    async def _mock_llm(prompt, **kwargs):
        # Simple mock that extracts entities mentioned in prompt
        return f"Mock response based on prompt: {prompt[:100]}..."

    return _mock_llm


@pytest.fixture
def mock_embedding_func():
    """Mock embedding function for GraphRAG.

    Returns fixed-dimension vectors for testing.
    """
    import numpy as np

    async def _mock_embed(texts, **kwargs):
        # Return 384-dim vectors (sentence-transformers default)
        if isinstance(texts, str):
            texts = [texts]
        return np.random.rand(len(texts), 384).astype(np.float32)

    return _mock_embed


# =============================================================================
# Test Markers Registration
# =============================================================================


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "requires_model: marks tests that require actual ML models")
