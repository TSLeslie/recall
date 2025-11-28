"""Configuration and utilities for the Recall package."""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RecallConfig:
    """Configuration settings for Recall."""

    storage_dir: Path
    models_dir: Path
    whisper_model: str
    llm_model_path: Path

    # New configurable fields for RECALL-001
    default_audio_source: str = "microphone"  # microphone/system/both
    retain_audio: bool = False
    enable_graphrag: bool = True
    summary_length: str = "brief"  # brief/detailed

    # Auto-recording settings
    auto_recording_enabled: bool = False
    detect_meeting_apps: bool = True
    detect_system_audio: bool = True
    app_whitelist: List[str] = field(
        default_factory=lambda: [
            "zoom.us",
            "Microsoft Teams",
            "Slack",
            "Discord",
            "Google Meet",
            "Webex",
            "Skype",
            "FaceTime",
        ]
    )

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

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "RecallConfig":
        """Load configuration from a JSON file.

        Args:
            path: Path to config file. Defaults to ~/.recall/config.json

        Returns:
            RecallConfig loaded from file, or defaults if file doesn't exist
        """
        if path is None:
            home = Path.home()
            path = home / ".recall" / "config.json"

        # Start with defaults
        config = cls.default()

        if not path.exists():
            logger.debug(f"Config file not found at {path}, using defaults")
            return config

        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Update config with loaded values
            if "storage_dir" in data:
                config.storage_dir = Path(data["storage_dir"])
            if "models_dir" in data:
                config.models_dir = Path(data["models_dir"])
            if "whisper_model" in data:
                config.whisper_model = data["whisper_model"]
            if "llm_model_path" in data:
                config.llm_model_path = Path(data["llm_model_path"])
            if "default_audio_source" in data:
                config.default_audio_source = data["default_audio_source"]
            if "retain_audio" in data:
                config.retain_audio = data["retain_audio"]
            if "enable_graphrag" in data:
                config.enable_graphrag = data["enable_graphrag"]
            if "summary_length" in data:
                config.summary_length = data["summary_length"]
            if "auto_recording_enabled" in data:
                config.auto_recording_enabled = data["auto_recording_enabled"]
            if "detect_meeting_apps" in data:
                config.detect_meeting_apps = data["detect_meeting_apps"]
            if "detect_system_audio" in data:
                config.detect_system_audio = data["detect_system_audio"]
            if "app_whitelist" in data:
                config.app_whitelist = data["app_whitelist"]

            logger.debug(f"Loaded config from {path}")
            return config

        except json.JSONDecodeError as e:
            logger.warning(f"Malformed config file at {path}: {e}. Using defaults.")
            return cls.default()
        except Exception as e:
            logger.warning(f"Error loading config from {path}: {e}. Using defaults.")
            return cls.default()

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to a JSON file.

        Args:
            path: Path to config file. Defaults to ~/.recall/config.json
        """
        if path is None:
            path = self.storage_dir / "config.json"

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict with Path objects as strings
        data = self.to_dict()

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved config to {path}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary suitable for JSON serialization.

        Returns:
            Dictionary with all config values
        """
        return {
            "storage_dir": str(self.storage_dir),
            "models_dir": str(self.models_dir),
            "whisper_model": self.whisper_model,
            "llm_model_path": str(self.llm_model_path),
            "default_audio_source": self.default_audio_source,
            "retain_audio": self.retain_audio,
            "enable_graphrag": self.enable_graphrag,
            "summary_length": self.summary_length,
            "auto_recording_enabled": self.auto_recording_enabled,
            "detect_meeting_apps": self.detect_meeting_apps,
            "detect_system_audio": self.detect_system_audio,
            "app_whitelist": self.app_whitelist,
        }


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
