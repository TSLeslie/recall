"""
Example showing how to download and use Llama models.
"""

import os
from pathlib import Path
from recall.config import get_models_dir


def download_instructions():
    """Print instructions for downloading Llama models."""
    print("=" * 70)
    print("How to Download Llama Models")
    print("=" * 70)

    models_dir = get_models_dir()
    print(f"\nModels directory: {models_dir.absolute()}")

    print("\nOption 1: Download from Hugging Face")
    print("-" * 70)
    print("""
    1. Visit: https://huggingface.co/models?search=llama
    2. Search for GGUF format models (recommended for llama-cpp-python)
    3. Popular choices:
       - TheBloke/Llama-2-7B-Chat-GGUF
       - TheBloke/Llama-2-13B-Chat-GGUF
       - TheBloke/Meta-Llama-3.1-8B-Instruct-GGUF

    4. Download using git-lfs or wget:
       
       # Using huggingface-cli (recommended)
       pip install huggingface-hub
       huggingface-cli download TheBloke/Meta-Llama-3.1-8B-Instruct-GGUF \\
           Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \\
           --local-dir {models_dir} \\
           --local-dir-use-symlinks False
    """)

    print("\nOption 2: Using Python")
    print("-" * 70)
    print("""
    from huggingface_hub import hf_hub_download

    model_path = hf_hub_download(
        repo_id="TheBloke/Meta-Llama-3.1-8B-Instruct-GGUF",
        filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        local_dir="{models_dir}"
    )
    """.format(models_dir=models_dir))

    print("\nOption 3: Manual Download")
    print("-" * 70)
    print(f"""
    1. Download a GGUF model file manually
    2. Place it in: {models_dir.absolute()}
    3. Use it in your code:
    
       from recall import analyze
       
       result = analyze(
           "Your text here",
           model_path="{models_dir}/your-model.gguf"
       )
    """)

    print("\nRecommended Model Sizes:")
    print("-" * 70)
    print("""
    - Q4_K_M: Good balance of quality and size (~4-5 GB for 7B models)
    - Q5_K_M: Better quality, larger size (~5-6 GB)
    - Q8_0: High quality, large size (~7-8 GB)
    
    Choose based on your available RAM and GPU VRAM.
    """)


def check_available_models():
    """Check what models are available in the models directory."""
    models_dir = get_models_dir()
    model_files = list(models_dir.glob("*.gguf"))

    if model_files:
        print("\nAvailable models:")
        for model_file in model_files:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            print(f"  - {model_file.name} ({size_mb:.1f} MB)")
    else:
        print("\nNo models found in the models directory.")


if __name__ == "__main__":
    download_instructions()
    check_available_models()
