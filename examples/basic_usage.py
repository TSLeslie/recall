"""
Example script demonstrating basic usage of the Recall package.
"""

import os

from recall import analyze, transcribe
from recall.config import get_model_path


def main():
    # Example 1: Basic transcription
    print("=" * 50)
    print("Example 1: Basic Audio Transcription")
    print("=" * 50)

    audio_file = "examples/harvard.wav"

    # Transcribe with different model sizes
    # Options: 'tiny', 'base', 'small', 'medium', 'large'
    if os.path.exists(audio_file):
        result = transcribe(audio_file, model="base")
        print(f"\nTranscription:\n{result['text']}")
        print(f"\nDetected language: {result.get('language', 'unknown')}")
    else:
        print(f"Audio file not found: {audio_file}")

    # Example 2: Transcription with timestamps
    print("\n" + "=" * 50)
    print("Example 2: Transcription with Timestamps")
    print("=" * 50)

    from recall.transcribe import transcribe_with_timestamps

    if os.path.exists(audio_file):
        result = transcribe_with_timestamps(audio_file, model="base")
        print(f"\nFull text: {result['text']}")
        print("\nSegments:")
        for segment in result["segments"][:3]:  # Show first 3 segments
            print(f"  [{segment['start']:.2f}s - {segment['end']:.2f}s]: {segment['text']}")

    # Example 3: Text analysis with Llama
    print("\n" + "=" * 50)
    print("Example 3: Text Analysis with Llama")
    print("=" * 50)

    # Try Qwen model first (faster), fall back to Llama
    llama_model = get_model_path("qwen2.5-3b-instruct.gguf") or get_model_path(
        "llama-3.1-8b-instruct.gguf"
    )

    if llama_model:
        sample_text = """
        The meeting covered three main topics: the Q4 budget review,
        upcoming product launches, and team restructuring. The budget
        is on track with a slight surplus. Two new products will launch
        in December. The team will be reorganized into three divisions.
        """

        # Summarize
        summary = analyze(
            sample_text,
            prompt="Provide a brief summary of this meeting:",
            model_path=str(llama_model),
            max_tokens=100,
        )
        print(f"\nSummary:\n{summary}")

        # Extract key points
        from recall.analyze import extract_key_points

        key_points = extract_key_points(sample_text, model_path=str(llama_model))
        print(f"\nKey Points:\n{key_points}")
    else:
        print("\nLlama model not found. Please download a model to models/ directory.")
        print("Example: models/llama-3.1-8b-instruct.gguf")

    # Example 4: Combined workflow
    print("\n" + "=" * 50)
    print("Example 4: Complete Workflow")
    print("=" * 50)

    if os.path.exists(audio_file) and llama_model:
        # Step 1: Transcribe
        print("Step 1: Transcribing audio...")
        transcript = transcribe(audio_file, model="base")

        # Step 2: Analyze
        print("Step 2: Analyzing transcript...")
        analysis = analyze(
            transcript["text"],
            prompt="Summarize this transcription and extract action items:",
            model_path=str(llama_model),
            max_tokens=200,
        )

        print(f"\nOriginal transcript length: {len(transcript['text'])} characters")
        print(f"\nAnalysis:\n{analysis}")
    else:
        print("Complete workflow requires both audio file and Llama model.")


if __name__ == "__main__":
    main()
