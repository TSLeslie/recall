#!/usr/bin/env python3
"""End-to-End Demo: Real Audio Processing Pipeline

This demo runs the FULL Recall pipeline with real components:
1. Real Whisper transcription (uses actual model)
2. Real LLM summarization (uses Qwen2.5-3B)
3. Real storage (Markdown files)
4. Real knowledge base (Graph RAG)

Run: python examples/full_pipeline_demo.py

Note: First run will download Whisper model (~140MB for 'base')
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent.parent)


def check_prerequisites():
    """Check that required models and files exist."""
    print("\n📋 Checking prerequisites...")

    # Check audio file
    audio_file = Path("examples/harvard.wav")
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    print(f"✅ Audio file: {audio_file} ({audio_file.stat().st_size / 1024:.1f} KB)")

    # Check LLM model
    model_path = Path("models/qwen2.5-3b-instruct.gguf")
    if not model_path.exists():
        print(f"⚠️  LLM model not found: {model_path}")
        print("   Will skip summarization (transcription still works)")
    else:
        print(f"✅ LLM model: {model_path.name} ({model_path.stat().st_size / 1e9:.1f} GB)")

    return True


def demo_transcription(audio_path: Path) -> dict:
    """Run real Whisper transcription."""
    print("\n" + "=" * 60)
    print("🎤 STEP 1: Whisper Transcription")
    print("=" * 60)

    print(f"\nTranscribing: {audio_path.name}")
    print("Model: whisper 'base' (will download on first run ~140MB)")
    print("\nThis may take 30-60 seconds...\n")

    start_time = time.time()

    import whisper

    # Load model (downloads if needed)
    print("Loading Whisper model...")
    model = whisper.load_model("base")

    # Transcribe
    print("Transcribing audio...")
    result = model.transcribe(str(audio_path))

    elapsed = time.time() - start_time

    print(f"\n✅ Transcription complete in {elapsed:.1f}s")
    print(f"   Language detected: {result.get('language', 'unknown')}")
    print(f"   Text length: {len(result['text'])} characters")
    print(f"   Segments: {len(result.get('segments', []))}")

    print("\n📝 Transcript Preview:")
    print("-" * 40)
    preview = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
    print(preview)
    print("-" * 40)

    return result


def demo_summarization(transcript: str) -> str:
    """Run real LLM summarization."""
    print("\n" + "=" * 60)
    print("🤖 STEP 2: LLM Summarization")
    print("=" * 60)

    model_path = Path("models/qwen2.5-3b-instruct.gguf")
    if not model_path.exists():
        print("\n⚠️  Skipping summarization (model not found)")
        return "Summary not available - LLM model not installed."

    print(f"\nModel: {model_path.name}")
    print("This may take 30-60 seconds...\n")

    start_time = time.time()

    from recall.analyze import summarize

    # Generate summary
    print("Generating summary...")
    summary = summarize(transcript, str(model_path))

    elapsed = time.time() - start_time

    print(f"\n✅ Summarization complete in {elapsed:.1f}s")

    print("\n📋 Summary:")
    print("-" * 40)
    print(summary)
    print("-" * 40)

    return summary


def demo_storage(transcript: str, summary: str, audio_path: Path) -> Path:
    """Store as Markdown with frontmatter."""
    print("\n" + "=" * 60)
    print("💾 STEP 3: Storage (Markdown)")
    print("=" * 60)

    from recall.storage.markdown import save_recording
    from recall.storage.models import Recording

    # Create storage directory
    storage_dir = Path("demo_output/recordings")
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Create recording object
    recording = Recording.create_new(
        source="system",  # Use 'system' for demo audio
        transcript=transcript,
        summary=summary,
        title=f"Demo Recording - {audio_path.stem}",
        duration_seconds=int(audio_path.stat().st_size / 32000),  # Rough estimate
        tags=["demo", "harvard-sentences", "test"],
    )

    # Save to Markdown
    filepath = save_recording(recording, storage_dir)

    print(f"\n✅ Saved to: {filepath}")
    print(f"   Size: {filepath.stat().st_size} bytes")

    print("\n📄 File Preview:")
    print("-" * 40)
    content = filepath.read_text()
    preview = content[:800] + "\n..." if len(content) > 800 else content
    print(preview)
    print("-" * 40)

    return filepath


def demo_knowledge_base(filepath: Path, transcript: str):
    """Add to knowledge base (Graph RAG)."""
    print("\n" + "=" * 60)
    print("🧠 STEP 4: Knowledge Base (Graph RAG)")
    print("=" * 60)

    from recall.knowledge.graphrag import RecallGraphRAG
    from recall.knowledge.ingest import ingest_recording

    # Create knowledge base directory
    kb_dir = Path("demo_output/knowledge_base")
    kb_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nKnowledge base: {kb_dir}")
    print("Indexing content...")

    start_time = time.time()

    try:
        # Initialize GraphRAG
        graphrag = RecallGraphRAG(
            working_dir=str(kb_dir),
        )

        # Ingest the recording
        ingest_recording(
            graphrag=graphrag,
            transcript=transcript,
            source=str(filepath),
            metadata={
                "type": "recording",
                "source": "system",
                "demo": True,
            },
        )

        elapsed = time.time() - start_time
        print(f"\n✅ Indexed in {elapsed:.1f}s")

        # Try a query
        print("\n🔍 Testing Knowledge Query:")
        print("-" * 40)

        from recall.knowledge.query import ask

        result = ask("What was discussed?", graphrag)

        print("Query: 'What was discussed?'")
        answer = result.answer if hasattr(result, "answer") else str(result)
        print(f"Answer: {answer[:300]}..." if len(answer) > 300 else f"Answer: {answer}")

    except Exception as e:
        print(f"\n⚠️  Knowledge base indexing failed: {e}")
        print("   (This is optional - main pipeline still works)")


def demo_search_and_ask():
    """Demo searching and asking questions."""
    print("\n" + "=" * 60)
    print("❓ STEP 5: Search & Ask")
    print("=" * 60)

    kb_dir = Path("demo_output/knowledge_base")

    if not kb_dir.exists():
        print("\n⚠️  Knowledge base not found, skipping")
        return

    from recall.knowledge.graphrag import RecallGraphRAG
    from recall.knowledge.query import ask

    print("\nQuerying your knowledge base...\n")

    try:
        graphrag = RecallGraphRAG(
            working_dir=str(kb_dir),
        )

        questions = [
            "What topics were covered?",
            "Summarize the main points",
        ]

        for q in questions:
            print(f"Q: {q}")
            result = ask(q, graphrag)
            answer = result.answer if hasattr(result, "answer") else str(result)
            print(f"A: {answer[:200]}..." if len(answer) > 200 else f"A: {answer}")
            print()

    except Exception as e:
        print(f"⚠️  Query failed: {e}")


def main():
    """Run the full pipeline demo."""
    print("\n" + "🎙️ " + "=" * 54 + " 🎙️")
    print("      RECALL: Full Pipeline Demo (Real Models)")
    print("🎙️ " + "=" * 54 + " 🎙️")

    # Check prerequisites
    if not check_prerequisites():
        return 1

    audio_path = Path("examples/harvard.wav")

    try:
        # Step 1: Transcription
        result = demo_transcription(audio_path)
        transcript = result["text"]

        # Step 2: Summarization
        summary = demo_summarization(transcript)

        # Step 3: Storage
        filepath = demo_storage(transcript, summary, audio_path)

        # Step 4: Knowledge Base
        demo_knowledge_base(filepath, transcript)

        # Step 5: Search
        demo_search_and_ask()

        # Summary
        print("\n" + "=" * 60)
        print("✅ DEMO COMPLETE!")
        print("=" * 60)
        print(
            f"""
What happened:
  1. 🎤 Transcribed real audio with Whisper
  2. 🤖 Summarized with local LLM (Qwen2.5-3B)
  3. 💾 Saved as Markdown: demo_output/recordings/
  4. 🧠 Indexed in knowledge base: demo_output/knowledge_base/
  5. ❓ Queried the knowledge base

Output files:
  - {filepath}
  - demo_output/knowledge_base/

Next steps:
  - View your recording: cat {filepath}
  - Ask questions: recall ask "What was discussed?"
  - Try the CLI: python -m recall.cli --help
"""
        )

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
