"""Tests for model discovery and path configuration.

This module tests:
- Finding models in custom directories
- Auto-discovering models in common locations
- Interactive download prompts
- Model path configuration
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Test: ModelManager path configuration
# ============================================================================


class TestModelManagerPathConfiguration:
    """Tests for configuring custom model paths."""

    def test_model_manager_accepts_multiple_search_paths(self, tmp_path):
        """Test ModelManager can search multiple directories for models."""
        from recall.app.bundle import ModelManager

        path1 = tmp_path / "models1"
        path2 = tmp_path / "models2"
        path1.mkdir()
        path2.mkdir()

        manager = ModelManager(search_paths=[path1, path2])

        assert path1 in manager.search_paths
        assert path2 in manager.search_paths

    def test_model_manager_finds_model_in_custom_path(self, tmp_path):
        """Test that ModelManager finds models in custom search paths."""
        from recall.app.bundle import ModelInfo, ModelManager

        # Create model in custom location
        custom_models_dir = tmp_path / "my_models"
        custom_models_dir.mkdir()
        model_file = custom_models_dir / "qwen2.5-3b-instruct.gguf"
        model_file.write_bytes(b"fake model data")

        manager = ModelManager(search_paths=[custom_models_dir])

        model_info = ModelInfo(
            name="Qwen2.5-3B LLM",
            filename="qwen2.5-3b-instruct.gguf",
            url="http://example.com/model.gguf",
            size_mb=2048,
        )

        assert manager.check_model_exists(model_info) is True
        assert manager.find_model_path(model_info) == model_file

    def test_model_manager_searches_default_paths(self):
        """Test ModelManager searches default locations."""
        from recall.app.bundle import ModelManager

        manager = ModelManager()

        # Should include default paths
        default_paths = manager.get_default_search_paths()
        assert len(default_paths) > 0
        assert any(".recall" in str(p) for p in default_paths)

    def test_model_manager_includes_project_models_dir(self, tmp_path):
        """Test ModelManager includes ./models relative to project."""
        from recall.app.bundle import ModelManager

        # Simulate project structure
        project_dir = tmp_path / "recall_project"
        project_dir.mkdir()
        models_dir = project_dir / "models"
        models_dir.mkdir()

        manager = ModelManager(project_dir=project_dir)

        assert models_dir in manager.search_paths

    def test_find_model_path_returns_none_when_not_found(self, tmp_path):
        """Test find_model_path returns None when model not found."""
        from recall.app.bundle import ModelInfo, ModelManager

        manager = ModelManager(search_paths=[tmp_path])

        model_info = ModelInfo(
            name="Missing Model",
            filename="nonexistent.gguf",
            url="http://example.com/missing.gguf",
            size_mb=100,
        )

        assert manager.find_model_path(model_info) is None

    def test_model_manager_prefers_first_found(self, tmp_path):
        """Test ModelManager returns first found model when in multiple paths."""
        from recall.app.bundle import ModelInfo, ModelManager

        path1 = tmp_path / "models1"
        path2 = tmp_path / "models2"
        path1.mkdir()
        path2.mkdir()

        # Create model in both locations
        model1 = path1 / "model.gguf"
        model2 = path2 / "model.gguf"
        model1.write_bytes(b"model from path1")
        model2.write_bytes(b"model from path2")

        manager = ModelManager(search_paths=[path1, path2])

        model_info = ModelInfo(
            name="Test Model",
            filename="model.gguf",
            url="http://example.com/model.gguf",
            size_mb=100,
        )

        # Should find in first path
        found_path = manager.find_model_path(model_info)
        assert found_path == model1


# ============================================================================
# Test: Model Discovery
# ============================================================================


class TestModelDiscovery:
    """Tests for auto-discovering existing models."""

    def test_discover_all_models(self, tmp_path):
        """Test discovering all models across search paths."""
        from recall.app.bundle import ModelManager

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create some model files
        (models_dir / "qwen2.5-3b-instruct.gguf").write_bytes(b"qwen model")
        (models_dir / "base.pt").write_bytes(b"whisper model")

        manager = ModelManager(search_paths=[models_dir])
        discovered = manager.discover_existing_models()

        assert len(discovered) == 2
        assert any("qwen" in m.name.lower() for m in discovered)
        assert any("whisper" in m.name.lower() for m in discovered)

    def test_discover_models_reports_location(self, tmp_path):
        """Test that discovered models include their location."""
        from recall.app.bundle import ModelManager

        models_dir = tmp_path / "models"
        models_dir.mkdir()
        model_file = models_dir / "qwen2.5-3b-instruct.gguf"
        model_file.write_bytes(b"qwen model")

        manager = ModelManager(search_paths=[models_dir])
        discovered = manager.discover_existing_models()

        assert len(discovered) >= 1
        found_model = next(m for m in discovered if "qwen" in m.name.lower())
        assert found_model.found_path == model_file

    def test_get_model_status_summary(self, tmp_path):
        """Test getting a summary of which models are found vs missing."""
        from recall.app.bundle import ModelManager

        models_dir = tmp_path / "models"
        models_dir.mkdir()
        # Only create Qwen, not Whisper
        (models_dir / "qwen2.5-3b-instruct.gguf").write_bytes(b"qwen model")

        manager = ModelManager(search_paths=[models_dir])
        status = manager.get_model_status()

        assert "found" in status
        assert "missing" in status
        assert len(status["found"]) >= 1
        assert len(status["missing"]) >= 1
        assert any("qwen" in m.name.lower() for m in status["found"])
        assert any("whisper" in m.name.lower() for m in status["missing"])


# ============================================================================
# Test: Whisper Model Location
# ============================================================================


class TestWhisperModelDiscovery:
    """Tests for finding Whisper models in their default cache location."""

    def test_whisper_cache_in_default_search_paths(self):
        """Test that ~/.cache/whisper is included in default search paths."""
        from recall.app.bundle import ModelManager

        manager = ModelManager()
        paths = manager.get_default_search_paths()

        # Whisper stores models in ~/.cache/whisper
        assert any(".cache/whisper" in str(p) for p in paths)

    def test_find_whisper_model_in_cache(self, tmp_path):
        """Test finding Whisper model in cache directory."""
        from recall.app.bundle import ModelInfo, ModelManager

        # Simulate Whisper cache structure
        cache_dir = tmp_path / ".cache" / "whisper"
        cache_dir.mkdir(parents=True)
        whisper_model = cache_dir / "base.pt"
        whisper_model.write_bytes(b"whisper model data")

        manager = ModelManager(search_paths=[cache_dir])

        model_info = ModelInfo(
            name="Whisper Base",
            filename="base.pt",
            url="http://example.com/base.pt",
            size_mb=145,
        )

        assert manager.find_model_path(model_info) == whisper_model


# ============================================================================
# Test: Interactive Model Setup
# ============================================================================


class TestInteractiveModelSetup:
    """Tests for interactive model setup prompts."""

    def test_prompt_for_model_path(self, tmp_path, monkeypatch):
        """Test prompting user for custom model path."""
        from recall.app.bundle import ModelManager

        models_dir = tmp_path / "my_models"
        models_dir.mkdir()
        (models_dir / "qwen2.5-3b-instruct.gguf").write_bytes(b"model")

        # Simulate user input
        monkeypatch.setattr("builtins.input", lambda _: str(models_dir))

        manager = ModelManager()
        custom_path = manager.prompt_for_model_path()

        assert custom_path == models_dir

    def test_validate_model_path_exists(self, tmp_path):
        """Test validation of model path."""
        from recall.app.bundle import ModelManager

        manager = ModelManager()

        valid_path = tmp_path / "models"
        valid_path.mkdir()

        assert manager.validate_model_path(valid_path) is True
        assert manager.validate_model_path(tmp_path / "nonexistent") is False

    def test_prompt_download_or_locate(self, monkeypatch):
        """Test prompting user to download or locate existing models."""
        from recall.app.bundle import ModelManager, ModelSetupChoice

        # User chooses to locate existing models
        monkeypatch.setattr("builtins.input", lambda _: "2")

        manager = ModelManager()
        choice = manager.prompt_download_or_locate()

        assert choice == ModelSetupChoice.LOCATE_EXISTING

    def test_model_setup_choice_enum(self):
        """Test ModelSetupChoice enum values."""
        from recall.app.bundle import ModelSetupChoice

        assert hasattr(ModelSetupChoice, "DOWNLOAD")
        assert hasattr(ModelSetupChoice, "LOCATE_EXISTING")
        assert hasattr(ModelSetupChoice, "SKIP")


# ============================================================================
# Test: Launcher Integration
# ============================================================================


class TestLauncherModelIntegration:
    """Tests for launcher integration with model discovery."""

    def test_launcher_checks_for_existing_models(self, tmp_path):
        """Test that launcher checks for existing models before prompting download."""
        from recall.app.installer import AppLauncher

        # Create models in project directory
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "qwen2.5-3b-instruct.gguf").write_bytes(b"qwen")

        launcher = AppLauncher(config_dir=tmp_path, project_dir=tmp_path)

        # Should detect existing models
        existing = launcher.find_existing_models()
        assert len(existing) >= 1

    def test_launcher_offers_download_for_missing_models(self, tmp_path):
        """Test launcher offers to download missing models."""
        from recall.app.installer import AppLauncher

        launcher = AppLauncher(config_dir=tmp_path)

        missing = launcher.get_missing_models()

        # Should have both Whisper and Qwen missing
        assert len(missing) >= 2

    def test_launcher_uses_custom_model_path(self, tmp_path):
        """Test launcher can use user-specified model path."""
        from recall.app.installer import AppLauncher

        custom_models = tmp_path / "custom_models"
        custom_models.mkdir()
        (custom_models / "qwen2.5-3b-instruct.gguf").write_bytes(b"qwen")
        (custom_models / "base.pt").write_bytes(b"whisper")

        launcher = AppLauncher(config_dir=tmp_path)
        launcher.set_models_path(custom_models)

        # Now all models should be found
        missing = launcher.get_missing_models()
        assert len(missing) == 0

    def test_launcher_saves_model_path_to_config(self, tmp_path):
        """Test launcher saves custom model path to config file."""
        from recall.app.installer import AppLauncher

        custom_models = tmp_path / "custom_models"
        custom_models.mkdir()

        launcher = AppLauncher(config_dir=tmp_path)
        launcher.set_models_path(custom_models)

        # Verify saved in config
        config_file = tmp_path / "config.json"
        assert config_file.exists()

        import json

        config = json.loads(config_file.read_text())
        assert config.get("models_path") == str(custom_models)

    def test_launcher_loads_model_path_from_config(self, tmp_path):
        """Test launcher loads custom model path from config on init."""
        import json

        from recall.app.installer import AppLauncher

        custom_models = tmp_path / "custom_models"
        custom_models.mkdir()

        # Pre-create config with model path
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"models_path": str(custom_models)}))

        launcher = AppLauncher(config_dir=tmp_path)

        assert custom_models in launcher.model_manager.search_paths


# ============================================================================
# Test: Download with Progress
# ============================================================================


class TestModelDownloadWithProgress:
    """Tests for downloading models with progress indication."""

    def test_download_model_shows_progress(self, tmp_path):
        """Test that download shows progress updates."""
        from recall.app.bundle import ModelInfo, ModelManager

        manager = ModelManager(models_dir=tmp_path)
        progress_updates = []

        def on_progress(event):
            progress_updates.append(event)

        model_info = ModelInfo(
            name="Test Model",
            filename="test.bin",
            url="http://example.com/test.bin",
            size_mb=100,
        )

        with patch.object(manager, "_download_file") as mock_download:
            mock_download.return_value = tmp_path / "test.bin"
            (tmp_path / "test.bin").write_bytes(b"data")

            manager.download_model(model_info, on_progress=on_progress)

        # Should have at least completion event
        assert len(progress_updates) >= 1
        assert progress_updates[-1].percent == 100.0

    def test_download_model_to_specified_directory(self, tmp_path):
        """Test downloading model to specified directory."""
        from recall.app.bundle import ModelInfo, ModelManager

        download_dir = tmp_path / "downloads"
        download_dir.mkdir()

        manager = ModelManager(models_dir=download_dir)

        model_info = ModelInfo(
            name="Test Model",
            filename="test.bin",
            url="http://example.com/test.bin",
            size_mb=1,
        )

        with patch.object(manager, "_download_file") as mock_download:
            expected_path = download_dir / "test.bin"
            mock_download.return_value = expected_path
            expected_path.write_bytes(b"data")

            result = manager.download_model(model_info)

            assert result == expected_path
            assert result.parent == download_dir
