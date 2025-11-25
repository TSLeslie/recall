"""Configuration and utilities for the Recall package."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RecallConfig:
    """Configuration settings for Recall."""

    storage_dir: Path
    models_dir: Path
    whisper_model: str
    llm_model_path: Path

    @classmethod
    def default(cls) -> "RecallConfig":
        """Create a default configuration."""
        home = Path.home()
        storage_dir = Path(os.getenv("RECALL_STORAGE_DIR", home / ".recall"))
        models_dir = Path(os.getenv("RECALL_MODELS_DIR", "models"))

        return cls(
            storage_dir=storage_dir,
            models_dir=models_dir,
            whisper_model=DEFAULT_WHISPER_MODEL,
            llm_model_path=models_dir / DEFAULT_LLAMA_MODEL,
        )


def get_default_config() -> RecallConfig:
    """Get the default Recall configuration.

    Returns:
        RecallConfig with default settings
    """
    return RecallConfig.default()


def get_models_dir() -> Path:
    """
    Get the directory for storing model files.

    Returns:
        Path to models directory
    """
    models_dir = Path(os.getenv("RECALL_MODELS_DIR", "models"))
    models_dir.mkdir(exist_ok=True)
    return models_dir


def get_model_path(model_name: str) -> Optional[Path]:
    """
    Get the path to a specific model file.

    Args:
        model_name: Name of the model file

    Returns:
        Path to model file if it exists, None otherwise
    """
    models_dir = get_models_dir()
    model_path = models_dir / model_name

    if model_path.exists():
        return model_path
    return None


# Default configuration
DEFAULT_WHISPER_MODEL = "base"
DEFAULT_LLAMA_MODEL = "qwen2.5-3b-instruct.gguf"  # Faster small model
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
