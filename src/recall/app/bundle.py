"""macOS App Bundle configuration and model management.

This module provides:
- App bundle configuration for py2app
- Model download and management
- First-run setup experience
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

# Default models directory
DEFAULT_MODELS_DIR = Path.home() / ".recall" / "models"


@dataclass
class AppConfig:
    """Application bundle configuration."""

    app_name: str = "Recall"
    bundle_identifier: str = "com.recall.app"
    version: str = "0.1.0"
    min_macos_version: str = "12.0"
    icon_name: str = "recall.icns"

    def to_py2app_options(self) -> dict:
        """Convert to py2app options dictionary.

        Returns:
            Dictionary suitable for py2app setup.
        """
        return {
            "options": {
                "py2app": {
                    "plist": {
                        "CFBundleName": self.app_name,
                        "CFBundleIdentifier": self.bundle_identifier,
                        "CFBundleVersion": self.version,
                        "CFBundleShortVersionString": self.version,
                        "LSMinimumSystemVersion": self.min_macos_version,
                        "NSMicrophoneUsageDescription": "Recall needs microphone access to record audio.",
                        "NSAppleEventsUsageDescription": "Recall uses AppleEvents for system integration.",
                    },
                    "iconfile": self.icon_name,
                }
            }
        }


@dataclass
class ModelInfo:
    """Information about a required model."""

    name: str
    filename: str
    url: str
    size_mb: float
    sha256: str = ""


@dataclass
class DownloadProgressEvent:
    """Event for download progress tracking."""

    model_name: str
    downloaded_mb: float
    total_mb: float
    percent: float
    speed_mbps: float = 0.0


class ModelManager:
    """Manages model downloads and verification."""

    # Default required models
    REQUIRED_MODELS = [
        ModelInfo(
            name="Whisper Base",
            filename="base.pt",
            url="https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt",
            size_mb=145,
            sha256="ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e",
        ),
        ModelInfo(
            name="Qwen2.5-3B LLM",
            filename="qwen2.5-3b-instruct.gguf",
            url="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
            size_mb=2048,
        ),
    ]

    def __init__(self, models_dir: Optional[Path] = None):
        """Initialize model manager.

        Args:
            models_dir: Directory for storing models. Defaults to ~/.recall/models
        """
        self.models_dir = models_dir or DEFAULT_MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def get_required_models(self) -> list[ModelInfo]:
        """Get list of required models.

        Returns:
            List of ModelInfo for required models.
        """
        return self.REQUIRED_MODELS.copy()

    def check_model_exists(self, model: ModelInfo) -> bool:
        """Check if a model file exists.

        Args:
            model: Model info to check.

        Returns:
            True if model file exists.
        """
        model_path = self.models_dir / model.filename
        return model_path.exists()

    def get_missing_models(self) -> list[ModelInfo]:
        """Get list of models that need to be downloaded.

        Returns:
            List of ModelInfo for missing models.
        """
        return [m for m in self.get_required_models() if not self.check_model_exists(m)]

    def download_model(
        self,
        model: ModelInfo,
        on_progress: Optional[Callable[[DownloadProgressEvent], None]] = None,
    ) -> Path:
        """Download a model file.

        Args:
            model: Model to download.
            on_progress: Optional callback for progress updates.

        Returns:
            Path to downloaded model file.
        """
        output_path = self.models_dir / model.filename

        # Call the actual download
        result = self._download_file(model.url, output_path, model.size_mb, on_progress)

        # Notify completion if callback provided
        if on_progress:
            on_progress(
                DownloadProgressEvent(
                    model_name=model.name,
                    downloaded_mb=model.size_mb,
                    total_mb=model.size_mb,
                    percent=100.0,
                )
            )

        return result

    def _download_file(
        self,
        url: str,
        output_path: Path,
        total_mb: float,
        on_progress: Optional[Callable[[DownloadProgressEvent], None]] = None,
    ) -> Path:
        """Internal method to download a file with progress.

        Args:
            url: URL to download from.
            output_path: Path to save file to.
            total_mb: Expected file size in MB.
            on_progress: Optional progress callback.

        Returns:
            Path to downloaded file.
        """
        import urllib.request

        # Simple download - can be enhanced with chunked download and progress
        urllib.request.urlretrieve(url, output_path)
        return output_path


@dataclass
class SetupStep:
    """A step in the first-run setup process."""

    name: str
    title: str
    description: str
    required: bool = True
    completed: bool = False


class FirstRunSetup:
    """Manages first-run setup experience."""

    SETUP_COMPLETE_FILE = ".setup_complete"

    DEFAULT_STEPS = [
        SetupStep(
            name="welcome",
            title="Welcome to Recall",
            description="Recall is a local-first AI-powered note-taking system that captures, transcribes, and summarizes audio.",
            required=False,
        ),
        SetupStep(
            name="model_download",
            title="Download AI Models",
            description="Download the Whisper transcription model and Qwen2.5 summarization model.",
            required=True,
        ),
        SetupStep(
            name="permissions",
            title="Grant Permissions",
            description="Grant microphone and accessibility permissions for full functionality.",
            required=True,
        ),
        SetupStep(
            name="complete",
            title="Setup Complete",
            description="You're all set! Recall is ready to use.",
            required=False,
        ),
    ]

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize first-run setup.

        Args:
            config_dir: Directory for storing config. Defaults to ~/.recall
        """
        self.config_dir = config_dir or (Path.home() / ".recall")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_file = self.config_dir / self.SETUP_COMPLETE_FILE

    def is_first_run(self) -> bool:
        """Check if this is the first run.

        Returns:
            True if setup has not been completed.
        """
        return not self._setup_file.exists()

    def mark_setup_complete(self) -> None:
        """Mark the setup as complete."""
        self._setup_file.write_text(json.dumps({"version": "0.1.0"}))

    def get_setup_steps(self) -> list[SetupStep]:
        """Get the setup steps.

        Returns:
            List of SetupStep objects.
        """
        return [SetupStep(**step.__dict__) for step in self.DEFAULT_STEPS]


def get_app_version() -> str:
    """Get the application version.

    Returns:
        Version string.
    """
    return "0.1.0"


def get_bundle_info() -> dict:
    """Get bundle info dictionary for Info.plist.

    Returns:
        Dictionary with bundle info keys.
    """
    config = AppConfig()
    return {
        "CFBundleName": config.app_name,
        "CFBundleIdentifier": config.bundle_identifier,
        "CFBundleVersion": config.version,
        "CFBundleShortVersionString": config.version,
        "LSMinimumSystemVersion": config.min_macos_version,
        "CFBundleExecutable": config.app_name,
        "CFBundlePackageType": "APPL",
        "NSHighResolutionCapable": True,
        "NSMicrophoneUsageDescription": "Recall needs microphone access to record audio.",
        "NSAppleEventsUsageDescription": "Recall uses AppleEvents for system integration.",
    }


def get_py2app_options() -> dict:
    """Get py2app options dictionary.

    Returns:
        Dictionary with py2app configuration.
    """
    return {
        "py2app": {
            "plist": get_bundle_info(),
            "packages": [
                "recall",
                "whisper",
                "llama_cpp",
                "torch",
                "numpy",
                "pydantic",
            ],
            "includes": [
                "rumps",
                "pynput",
            ],
            "excludes": [
                "pytest",
                "pytest_cov",
                "pytest_mock",
                "test",
                "tests",
                "unittest",
                "doctest",
                "setuptools",
                "pip",
                "wheel",
            ],
            "iconfile": "resources/recall.icns",
        }
    }


def generate_setup_py() -> str:
    """Generate setup.py content for py2app.

    Returns:
        String content for setup.py.
    """
    options = get_py2app_options()

    return f'''"""
Setup script for building Recall.app with py2app.

Usage:
    python setup_app.py py2app
"""

from setuptools import setup

APP = ["src/recall/app/launcher.py"]
DATA_FILES = [
    ("resources", ["resources/recall.icns"]),
]
OPTIONS = {options}

setup(
    name="Recall",
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=["py2app"],
)
'''


# Exports
__all__ = [
    "AppConfig",
    "ModelInfo",
    "DownloadProgressEvent",
    "ModelManager",
    "SetupStep",
    "FirstRunSetup",
    "get_app_version",
    "get_bundle_info",
    "get_py2app_options",
    "generate_setup_py",
]
