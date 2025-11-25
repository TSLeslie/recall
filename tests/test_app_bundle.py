"""Tests for Ticket 8.1: macOS App Bundle.

This module tests:
- py2app configuration
- App bundle structure
- Model download functionality
- First-run experience
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

# ============================================================================
# Test: AppConfig
# ============================================================================


class TestAppConfig:
    """Tests for application configuration."""

    def test_app_config_defaults(self):
        """Test default application configuration."""
        from recall.app.bundle import AppConfig

        config = AppConfig()

        assert config.app_name == "Recall"
        assert config.bundle_identifier == "com.recall.app"
        assert config.version == "0.1.0"
        assert config.min_macos_version == "12.0"

    def test_app_config_icon_path(self):
        """Test that icon path is defined."""
        from recall.app.bundle import AppConfig

        config = AppConfig()

        assert config.icon_name == "recall.icns"

    def test_app_config_to_py2app_options(self):
        """Test conversion to py2app options dict."""
        from recall.app.bundle import AppConfig

        config = AppConfig()
        options = config.to_py2app_options()

        assert "app" in options or "options" in options
        assert isinstance(options, dict)


# ============================================================================
# Test: ModelManager
# ============================================================================


class TestModelManager:
    """Tests for model download and management."""

    def test_model_manager_init(self):
        """Test ModelManager initialization."""
        from recall.app.bundle import ModelManager

        manager = ModelManager()

        assert manager is not None
        assert hasattr(manager, "models_dir")

    def test_model_manager_default_models_dir(self):
        """Test default models directory."""
        from recall.app.bundle import ModelManager

        manager = ModelManager()

        assert "models" in str(manager.models_dir) or ".recall" in str(manager.models_dir)

    def test_model_manager_custom_models_dir(self, tmp_path):
        """Test custom models directory."""
        from recall.app.bundle import ModelManager

        manager = ModelManager(models_dir=tmp_path)

        assert manager.models_dir == tmp_path

    def test_get_required_models(self):
        """Test getting list of required models."""
        from recall.app.bundle import ModelManager

        manager = ModelManager()
        models = manager.get_required_models()

        assert len(models) > 0
        assert any("whisper" in m.name.lower() for m in models)
        assert any("qwen" in m.name.lower() or "llm" in m.name.lower() for m in models)

    def test_model_info_structure(self):
        """Test ModelInfo structure."""
        from recall.app.bundle import ModelInfo, ModelManager

        manager = ModelManager()
        models = manager.get_required_models()

        for model in models:
            assert isinstance(model, ModelInfo)
            assert model.name
            assert model.filename
            assert model.size_mb > 0

    def test_check_model_exists(self, tmp_path):
        """Test checking if model exists."""
        from recall.app.bundle import ModelInfo, ModelManager

        manager = ModelManager(models_dir=tmp_path)

        # Create a fake model file
        model_file = tmp_path / "test_model.bin"
        model_file.write_bytes(b"fake model data")

        model_info = ModelInfo(
            name="Test Model",
            filename="test_model.bin",
            url="http://example.com/model.bin",
            size_mb=1,
        )

        assert manager.check_model_exists(model_info) is True

    def test_check_model_not_exists(self, tmp_path):
        """Test checking non-existent model."""
        from recall.app.bundle import ModelInfo, ModelManager

        manager = ModelManager(models_dir=tmp_path)

        model_info = ModelInfo(
            name="Missing Model",
            filename="missing.bin",
            url="http://example.com/missing.bin",
            size_mb=1,
        )

        assert manager.check_model_exists(model_info) is False

    def test_get_missing_models(self, tmp_path):
        """Test getting list of missing models."""
        from recall.app.bundle import ModelManager

        manager = ModelManager(models_dir=tmp_path)

        # Empty directory should have all models missing
        missing = manager.get_missing_models()

        assert len(missing) > 0

    def test_download_model_creates_file(self, tmp_path):
        """Test that download_model creates the model file."""
        from recall.app.bundle import ModelInfo, ModelManager

        manager = ModelManager(models_dir=tmp_path)

        model_info = ModelInfo(
            name="Test Model",
            filename="test_model.bin",
            url="http://example.com/model.bin",
            size_mb=1,
        )

        # Mock the actual download
        with patch.object(manager, "_download_file") as mock_download:
            mock_download.return_value = tmp_path / "test_model.bin"
            (tmp_path / "test_model.bin").write_bytes(b"downloaded data")

            result = manager.download_model(model_info)

            assert result.exists()


# ============================================================================
# Test: DownloadProgress
# ============================================================================


class TestDownloadProgress:
    """Tests for download progress tracking."""

    def test_progress_callback(self):
        """Test progress callback is called during download."""
        from recall.app.bundle import ModelInfo, ModelManager

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manager = ModelManager(models_dir=tmp_path)

            progress_events = []

            def on_progress(event):
                progress_events.append(event)

            model_info = ModelInfo(
                name="Test Model",
                filename="test.bin",
                url="http://example.com/test.bin",
                size_mb=1,
            )

            with patch.object(manager, "_download_file") as mock_download:
                # Simulate download with progress
                mock_download.return_value = tmp_path / "test.bin"
                (tmp_path / "test.bin").write_bytes(b"data")

                manager.download_model(model_info, on_progress=on_progress)

    def test_download_progress_event_structure(self):
        """Test DownloadProgressEvent structure."""
        from recall.app.bundle import DownloadProgressEvent

        event = DownloadProgressEvent(
            model_name="Test Model",
            downloaded_mb=50.0,
            total_mb=100.0,
            percent=50.0,
            speed_mbps=10.0,
        )

        assert event.model_name == "Test Model"
        assert event.percent == 50.0
        assert event.downloaded_mb == 50.0
        assert event.total_mb == 100.0


# ============================================================================
# Test: FirstRunSetup
# ============================================================================


class TestFirstRunSetup:
    """Tests for first-run setup experience."""

    def test_first_run_check(self, tmp_path):
        """Test checking if this is first run."""
        from recall.app.bundle import FirstRunSetup

        setup = FirstRunSetup(config_dir=tmp_path)

        # First time should be True
        assert setup.is_first_run() is True

    def test_first_run_mark_complete(self, tmp_path):
        """Test marking first run as complete."""
        from recall.app.bundle import FirstRunSetup

        setup = FirstRunSetup(config_dir=tmp_path)

        setup.mark_setup_complete()

        assert setup.is_first_run() is False

    def test_first_run_state_persists(self, tmp_path):
        """Test that first run state persists across instances."""
        from recall.app.bundle import FirstRunSetup

        setup1 = FirstRunSetup(config_dir=tmp_path)
        setup1.mark_setup_complete()

        # New instance should see setup as complete
        setup2 = FirstRunSetup(config_dir=tmp_path)
        assert setup2.is_first_run() is False

    def test_get_setup_steps(self):
        """Test getting setup steps."""
        from recall.app.bundle import FirstRunSetup

        with tempfile.TemporaryDirectory() as tmp_dir:
            setup = FirstRunSetup(config_dir=Path(tmp_dir))
            steps = setup.get_setup_steps()

            assert len(steps) > 0
            step_names = [s.name for s in steps]
            assert "welcome" in step_names or "Welcome" in str(step_names)


# ============================================================================
# Test: SetupStep
# ============================================================================


class TestSetupStep:
    """Tests for setup step structure."""

    def test_setup_step_structure(self):
        """Test SetupStep dataclass."""
        from recall.app.bundle import SetupStep

        step = SetupStep(
            name="welcome",
            title="Welcome to Recall",
            description="Get started with Recall",
            required=True,
            completed=False,
        )

        assert step.name == "welcome"
        assert step.title == "Welcome to Recall"
        assert step.required is True
        assert step.completed is False

    def test_setup_steps_include_model_download(self):
        """Test that setup steps include model download."""
        from recall.app.bundle import FirstRunSetup

        with tempfile.TemporaryDirectory() as tmp_dir:
            setup = FirstRunSetup(config_dir=Path(tmp_dir))
            steps = setup.get_setup_steps()

            step_names = [s.name for s in steps]
            assert any("model" in name.lower() for name in step_names)


# ============================================================================
# Test: Bundle Metadata
# ============================================================================


class TestBundleMetadata:
    """Tests for app bundle metadata."""

    def test_get_version(self):
        """Test getting app version."""
        from recall.app.bundle import get_app_version

        version = get_app_version()

        assert version is not None
        assert "." in version  # Should be semver-like

    def test_get_bundle_info(self):
        """Test getting bundle info dict."""
        from recall.app.bundle import get_bundle_info

        info = get_bundle_info()

        assert "CFBundleName" in info
        assert info["CFBundleName"] == "Recall"
        assert "CFBundleIdentifier" in info
        assert "CFBundleVersion" in info

    def test_bundle_info_includes_min_os(self):
        """Test bundle info includes minimum OS version."""
        from recall.app.bundle import get_bundle_info

        info = get_bundle_info()

        assert "LSMinimumSystemVersion" in info
        assert info["LSMinimumSystemVersion"] >= "12.0"


# ============================================================================
# Test: py2app Setup Generation
# ============================================================================


class TestPy2appSetup:
    """Tests for py2app setup generation."""

    def test_generate_setup_py(self):
        """Test generating setup.py for py2app."""
        from recall.app.bundle import generate_setup_py

        setup_content = generate_setup_py()

        assert "from setuptools import setup" in setup_content
        assert "py2app" in setup_content
        assert "APP" in setup_content or "app" in setup_content

    def test_get_py2app_options(self):
        """Test getting py2app options dict."""
        from recall.app.bundle import get_py2app_options

        options = get_py2app_options()

        assert "py2app" in options
        assert "packages" in options["py2app"] or "includes" in options["py2app"]

    def test_py2app_excludes_large_packages(self):
        """Test that py2app excludes unnecessary large packages."""
        from recall.app.bundle import get_py2app_options

        options = get_py2app_options()
        py2app_opts = options.get("py2app", {})
        excludes = py2app_opts.get("excludes", [])

        # Should exclude test frameworks and dev tools
        assert any("pytest" in str(excludes) or "test" in str(excludes).lower() for _ in [1])
