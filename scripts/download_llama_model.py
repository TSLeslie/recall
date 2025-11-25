#!/usr/bin/env python3
"""
Script to download a Llama model for use with the Recall package.
"""

import sys
from pathlib import Path
from urllib.request import urlretrieve


def download_progress(block_num, block_size, total_size):
    """Show download progress."""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(downloaded * 100 / total_size, 100)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(
            f"\rDownloading: {percent:.1f}% ({mb_downloaded:.1f}MB / {mb_total:.1f}MB)"
        )
        sys.stdout.flush()


def main():
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Model information - Using smaller, faster Qwen2.5-3B instead of 8B
    model_name = "llama-3.1-8b-instruct.gguf"
    model_path = models_dir / model_name

    if model_path.exists():
        print(f"Model already exists at: {model_path}")
        print("\nFor faster performance, consider using a smaller model:")
        print("  - Qwen2.5-3B-Instruct (~2GB, much faster)")
        print("  - Phi-3.5-mini (~2.4GB, good balance)")
        return

    print("Downloading Qwen2.5-3B-Instruct model (smaller and faster)...")
    print("Note: This is ~2GB and much faster than the 8B model.\n")

    # Using Qwen2.5-3B-Instruct Q4_K_M quantization for speed
    url = "https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf"

    # Download to qwen model name first
    qwen_model_path = models_dir / "qwen2.5-3b-instruct.gguf"

    try:
        urlretrieve(url, qwen_model_path, download_progress)
        print(f"\n\nModel downloaded successfully to: {qwen_model_path}")
        print(f"Size: {qwen_model_path.stat().st_size / (1024**3):.2f} GB")
        print("\nThis model is significantly faster than 8B models while maintaining good quality.")
        print("Perfect for meeting transcription summarization!")
    except Exception as e:
        print(f"\n\nError downloading model: {e}")
        if qwen_model_path.exists():
            qwen_model_path.unlink()
        sys.exit(1)


if __name__ == "__main__":
    main()
