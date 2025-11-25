"""
Demo: Recording and Ingestion Pipeline

This script demonstrates the full Recall pipeline:
1. Recording from microphone (or using existing audio)
2. Transcribing with Whisper
3. Summarizing with local LLM
4. Saving as Markdown with metadata
5. Searching recordings

Run with: python examples/demo_recording_pipeline.py
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_progress_callback(event):
    """Print progress events during ingestion."""
    bar_length = 30
    filled = int(bar_length * event.progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"  [{bar}] {event.progress*100:5.1f}% - {event.message}")


def demo_with_existing_audio():
    """Demo using existing Harvard audio file."""
    from recall.config import get_model_path
    from recall.pipeline import ingest_audio
    from recall.storage.index import RecordingIndex
    from recall.storage.markdown import list_recordings

    print("=" * 60)
    print("DEMO: Recording Pipeline with Existing Audio")
    print("=" * 60)

    # Check for audio file
    audio_file = Path("examples/harvard.wav")
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False

    print(f"\n✓ Found audio file: {audio_file}")

    # Check for LLM model
    model_path = get_model_path("qwen2.5-3b-instruct.gguf")
    if model_path:
        print(f"✓ Found LLM model: {model_path.name}")
        skip_summary = False
    else:
        print("⚠ No LLM model found - will skip summarization")
        skip_summary = True

    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_dir = Path(temp_dir) / "recordings"
        storage_dir.mkdir()
        print(f"\n📁 Storage directory: {storage_dir}")

        # Run ingestion pipeline
        print("\n" + "-" * 40)
        print("Starting Ingestion Pipeline...")
        print("-" * 40)

        try:
            recording = ingest_audio(
                audio_path=audio_file,
                source="microphone",
                storage_dir=storage_dir,
                title="Harvard Sentences Demo",
                tags=["demo", "test", "harvard"],
                participants=["Speaker 1"],
                skip_summary=skip_summary,
                progress_callback=demo_progress_callback,
            )

            print("\n" + "-" * 40)
            print("✓ Ingestion Complete!")
            print("-" * 40)

            # Display recording details
            print("\n📝 Recording Details:")
            print(f"   ID: {recording.id}")
            print(f"   Title: {recording.title}")
            print(f"   Source: {recording.source}")
            print(f"   Timestamp: {recording.timestamp}")
            print(f"   Duration: {recording.duration_seconds}s")
            print(f"   Tags: {recording.tags}")

            print("\n📜 Transcript (first 200 chars):")
            print(f"   {recording.transcript[:200]}...")

            print("\n📋 Summary:")
            print(
                f"   {recording.summary[:300]}..."
                if len(recording.summary) > 300
                else f"   {recording.summary}"
            )

            # List saved files
            print("\n" + "-" * 40)
            print("Saved Markdown Files:")
            print("-" * 40)
            for md_file in list_recordings(storage_dir):
                print(f"   📄 {md_file.name}")

            # Demo search functionality
            print("\n" + "-" * 40)
            print("Search Demo:")
            print("-" * 40)

            index = RecordingIndex(":memory:")
            # Get the actual saved file path
            saved_files = list(list_recordings(storage_dir))
            if saved_files:
                index.add_recording(saved_files[0], recording)

            # Search for "harvard"
            results = index.search("harvard")
            print(f"   Search 'harvard': {len(results)} result(s)")

            # Filter by source
            results = index.filter(source="microphone")
            print(f"   Filter source='microphone': {len(results)} result(s)")

            # Filter by tags
            results = index.filter(tags=["demo"])
            print(f"   Filter tags=['demo']: {len(results)} result(s)")

            return True

        except Exception as e:
            print(f"\n❌ Error during ingestion: {e}")
            import traceback

            traceback.print_exc()
            return False


def demo_recorder_preview():
    """Show how to use the Recorder (without actually recording)."""
    print("\n" + "=" * 60)
    print("DEMO: Recorder Usage Preview")
    print("=" * 60)

    print(
        """
The Recorder class provides microphone recording:

```python
from recall.capture import Recorder
from recall.pipeline import ingest_audio

# Initialize recorder
recorder = Recorder(output_dir=Path("./recordings"))

# Option 1: Fixed duration recording
audio_path = recorder.record(duration_seconds=30)

# Option 2: Start/Stop recording
recorder.start_recording()
# ... wait for user to stop ...
audio_path = recorder.stop_recording()

# Ingest the recording
recording = ingest_audio(
    audio_path=audio_path,
    source="microphone",
    storage_dir=Path("./transcripts"),
    title="My Meeting",
    progress_callback=lambda e: print(f"{e.progress*100:.0f}% - {e.message}")
)

print(f"Saved: {recording.title}")
print(f"Summary: {recording.summary}")
```

Note: Actual microphone recording requires:
- sounddevice package
- Working audio input device
- Not running in a container/CI environment
"""
    )


def demo_youtube_preview():
    """Show how to use YouTube audio extraction."""
    print("\n" + "=" * 60)
    print("DEMO: YouTube Audio Extraction Preview")
    print("=" * 60)

    print(
        """
The YouTube module provides audio extraction from videos:

```python
from recall.capture import download_audio
from recall.pipeline import ingest_audio

# Download audio from YouTube
result = download_audio(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir=Path("./downloads"),
    progress_callback=lambda p: print(f"Downloading: {p}%")
)

print(f"Downloaded: {result.title}")
print(f"Duration: {result.duration}s")

# Ingest the audio
recording = ingest_audio(
    audio_path=result.audio_path,
    source="youtube",
    storage_dir=Path("./transcripts"),
    title=result.title,
)
```

Note: YouTube download requires:
- yt-dlp package
- ffmpeg installed
- Network access
"""
    )


def main():
    print("\n🎙️  RECALL - Recording Pipeline Demo")
    print("━" * 60)

    # Run the main demo with existing audio
    success = demo_with_existing_audio()

    # Show usage examples
    demo_recorder_preview()
    demo_youtube_preview()

    print("\n" + "=" * 60)
    if success:
        print("✅ Demo completed successfully!")
    else:
        print("⚠️  Demo completed with errors")
    print("=" * 60)


if __name__ == "__main__":
    main()
