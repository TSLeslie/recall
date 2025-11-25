#!/usr/bin/env python3
"""
Script to download Qwen2.5-3B model - much faster than 8B models.
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
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    model_name = "qwen2.5-3b-instruct.gguf"
    model_path = models_dir / model_name

    if model_path.exists():
        print(f"Qwen model already exists at: {model_path}")
        return

    print("Downloading Qwen2.5-3B-Instruct model...")
    print("This model is ~2GB and significantly faster than 8B models!")
    print("Perfect for meeting summarization with good quality.\n")

    url = "https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf"

    try:
        urlretrieve(url, model_path, download_progress)
        print(f"\n\nModel downloaded successfully to: {model_path}")
        print(f"Size: {model_path.stat().st_size / (1024**3):.2f} GB")
        print("\n✓ This model will be 2-3x faster than the 8B model!")
    except Exception as e:
        print(f"\n\nError downloading model: {e}")
        if model_path.exists():
            model_path.unlink()
        sys.exit(1)


if __name__ == "__main__":
    main()
