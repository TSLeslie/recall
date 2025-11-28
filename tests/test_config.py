"""Tests for RecallConfig (RECALL-001: Config Persistence).

TDD tests for configuration load/save functionality:
- Load from JSON file
- Save to JSON file
- Handle missing file gracefully
- Handle malformed JSON gracefully
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from recall.config import RecallConfig


class TestRecallConfigDefaults:
    """Tests for RecallConfig default values."""

    def test_default_creates_config(self):
        """Test that default() creates a valid config."""
        config = RecallConfig.default()
        assert config is not None
        assert isinstance(config.storage_dir, Path)

    def test_default_has_new_fields(self):
        """Test that default config has new configurable fields."""
        config = RecallConfig.default()

        assert hasattr(config, "default_audio_source")
        assert hasattr(config, "retain_audio")
        assert hasattr(config, "enable_graphrag")
        assert hasattr(config, "summary_length")

    def test_default_audio_source_value(self):
        """Test default audio source is 'microphone'."""
        config = RecallConfig.default()
        assert config.default_audio_source == "microphone"

    def test_default_retain_audio_value(self):
        """Test default retain_audio is False."""
        config = RecallConfig.default()
        assert config.retain_audio is False

    def test_default_enable_graphrag_value(self):
        """Test default enable_graphrag is True."""
        config = RecallConfig.default()
        assert config.enable_graphrag is True

    def test_default_summary_length_value(self):
        """Test default summary_length is 'brief'."""
        config = RecallConfig.default()
        assert config.summary_length == "brief"

    def test_default_auto_recording_fields(self):
        """Test default auto-recording settings."""
        config = RecallConfig.default()
        assert config.auto_recording_enabled is False
        assert config.detect_meeting_apps is True
        assert config.detect_system_audio is True
        assert isinstance(config.app_whitelist, list)
        assert "zoom.us" in config.app_whitelist


class TestRecallConfigLoad:
    """Tests for RecallConfig.load() method."""

    def test_load_missing_file_returns_defaults(self, tmp_path):
        """Test that loading from missing file returns defaults."""
        config_path = tmp_path / "nonexistent" / "config.json"
        config = RecallConfig.load(config_path)

        assert config is not None
        assert config.default_audio_source == "microphone"

    def test_load_valid_json(self, tmp_path):
        """Test loading from a valid JSON file."""
        config_path = tmp_path / "config.json"
        data = {
            "storage_dir": str(tmp_path),
            "default_audio_source": "system",
            "retain_audio": True,
            "whisper_model": "small",
        }
        config_path.write_text(json.dumps(data))

        config = RecallConfig.load(config_path)

        assert config.storage_dir == tmp_path
        assert config.default_audio_source == "system"
        assert config.retain_audio is True
        assert config.whisper_model == "small"

    def test_load_partial_config_uses_defaults(self, tmp_path):
        """Test that partial config fills in defaults."""
        config_path = tmp_path / "config.json"
        data = {"retain_audio": True}
        config_path.write_text(json.dumps(data))

        config = RecallConfig.load(config_path)

        assert config.retain_audio is True
        # Other fields should be defaults
        assert config.default_audio_source == "microphone"
        assert config.enable_graphrag is True

    def test_load_malformed_json_returns_defaults(self, tmp_path):
        """Test that malformed JSON returns defaults."""
        config_path = tmp_path / "config.json"
        config_path.write_text("{ invalid json")

        config = RecallConfig.load(config_path)

        assert config is not None
        assert config.default_audio_source == "microphone"

    def test_load_default_path_when_none(self, tmp_path):
        """Test that load() uses default path when None provided."""
        with patch.object(Path, "home", return_value=tmp_path):
            config_path = tmp_path / ".recall" / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"retain_audio": True}
            config_path.write_text(json.dumps(data))

            config = RecallConfig.load()

            assert config.retain_audio is True

    def test_load_auto_recording_settings(self, tmp_path):
        """Test loading auto-recording settings."""
        config_path = tmp_path / "config.json"
        data = {
            "auto_recording_enabled": True,
            "detect_meeting_apps": False,
            "app_whitelist": ["zoom.us", "Teams"],
        }
        config_path.write_text(json.dumps(data))

        config = RecallConfig.load(config_path)

        assert config.auto_recording_enabled is True
        assert config.detect_meeting_apps is False
        assert config.app_whitelist == ["zoom.us", "Teams"]


class TestRecallConfigSave:
    """Tests for RecallConfig.save() method."""

    def test_save_creates_file(self, tmp_path):
        """Test that save() creates a config file."""
        config = RecallConfig.default()
        config.storage_dir = tmp_path
        config_path = tmp_path / "config.json"

        config.save(config_path)

        assert config_path.exists()

    def test_save_creates_parent_directories(self, tmp_path):
        """Test that save() creates parent directories."""
        config = RecallConfig.default()
        config.storage_dir = tmp_path
        config_path = tmp_path / "nested" / "dir" / "config.json"

        config.save(config_path)

        assert config_path.exists()

    def test_save_writes_valid_json(self, tmp_path):
        """Test that save() writes valid JSON."""
        config = RecallConfig.default()
        config.storage_dir = tmp_path
        config_path = tmp_path / "config.json"

        config.save(config_path)

        # Should be parseable JSON
        data = json.loads(config_path.read_text())
        assert isinstance(data, dict)

    def test_save_includes_all_fields(self, tmp_path):
        """Test that save() includes all configuration fields."""
        config = RecallConfig.default()
        config.storage_dir = tmp_path
        config.default_audio_source = "both"
        config.retain_audio = True
        config_path = tmp_path / "config.json"

        config.save(config_path)

        data = json.loads(config_path.read_text())
        assert data["default_audio_source"] == "both"
        assert data["retain_audio"] is True
        assert "storage_dir" in data
        assert "whisper_model" in data
        assert "enable_graphrag" in data

    def test_save_default_path_when_none(self, tmp_path):
        """Test that save() uses default path when None provided."""
        config = RecallConfig.default()
        config.storage_dir = tmp_path

        config.save()

        config_path = tmp_path / "config.json"
        assert config_path.exists()


class TestRecallConfigRoundTrip:
    """Tests for load/save round-trip."""

    def test_round_trip_preserves_values(self, tmp_path):
        """Test that save then load preserves all values."""
        original = RecallConfig.default()
        original.storage_dir = tmp_path
        original.default_audio_source = "system"
        original.retain_audio = True
        original.whisper_model = "medium"
        original.enable_graphrag = False
        original.summary_length = "detailed"
        original.auto_recording_enabled = True
        original.app_whitelist = ["Custom App"]

        config_path = tmp_path / "config.json"
        original.save(config_path)

        loaded = RecallConfig.load(config_path)

        assert loaded.storage_dir == original.storage_dir
        assert loaded.default_audio_source == original.default_audio_source
        assert loaded.retain_audio == original.retain_audio
        assert loaded.whisper_model == original.whisper_model
        assert loaded.enable_graphrag == original.enable_graphrag
        assert loaded.summary_length == original.summary_length
        assert loaded.auto_recording_enabled == original.auto_recording_enabled
        assert loaded.app_whitelist == original.app_whitelist


class TestRecallConfigToDict:
    """Tests for RecallConfig.to_dict() method."""

    def test_to_dict_returns_dict(self):
        """Test that to_dict returns a dictionary."""
        config = RecallConfig.default()
        data = config.to_dict()
        assert isinstance(data, dict)

    def test_to_dict_has_all_fields(self):
        """Test that to_dict includes all fields."""
        config = RecallConfig.default()
        data = config.to_dict()

        expected_fields = [
            "storage_dir",
            "models_dir",
            "whisper_model",
            "llm_model_path",
            "default_audio_source",
            "retain_audio",
            "enable_graphrag",
            "summary_length",
            "auto_recording_enabled",
            "detect_meeting_apps",
            "detect_system_audio",
            "app_whitelist",
        ]

        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_to_dict_paths_as_strings(self):
        """Test that Path objects are converted to strings."""
        config = RecallConfig.default()
        data = config.to_dict()

        assert isinstance(data["storage_dir"], str)
        assert isinstance(data["models_dir"], str)
        assert isinstance(data["llm_model_path"], str)
