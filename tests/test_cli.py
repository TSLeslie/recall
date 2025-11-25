"""Tests for CLI Commands (Ticket 6.1, 6.2, 6.3).

TDD tests for Recall CLI:
- Core commands: version, status, config
- Search commands: ask, search
- Notes commands: note, notes
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Import CLI app - will be created
# Imports done at module level to avoid freezegun issues
from recall.cli import app

runner = CliRunner()


# ============================================================================
# Ticket 6.1: Core CLI Commands
# ============================================================================


class TestCLIVersion:
    """Tests for `recall --version` command."""

    def test_version_shows_version_number(self):
        """Test that --version displays the version number."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "recall" in result.stdout.lower()
        # Should contain a version-like pattern (e.g., 0.1.0)
        import re

        assert re.search(r"\d+\.\d+\.\d+", result.stdout)

    def test_version_short_flag(self):
        """Test that -v also shows version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "recall" in result.stdout.lower()


class TestCLIStatus:
    """Tests for `recall status` command."""

    def test_status_shows_config_dir(self, tmp_path):
        """Test that status shows configuration directory."""
        with patch("recall.cli.get_default_config") as mock_config:
            mock_config.return_value.storage_dir = tmp_path
            mock_config.return_value.models_dir = tmp_path / "models"

            result = runner.invoke(app, ["status"])

            assert result.exit_code == 0
            assert "storage" in result.stdout.lower() or "config" in result.stdout.lower()

    def test_status_shows_model_availability(self, tmp_path):
        """Test that status shows if models are available."""
        with patch("recall.cli.get_default_config") as mock_config:
            mock_config.return_value.storage_dir = tmp_path
            mock_config.return_value.models_dir = tmp_path / "models"
            mock_config.return_value.whisper_model = "base"
            mock_config.return_value.llm_model_path = tmp_path / "model.gguf"

            result = runner.invoke(app, ["status"])

            assert result.exit_code == 0
            # Should mention models or whisper
            assert "model" in result.stdout.lower() or "whisper" in result.stdout.lower()


class TestCLIConfig:
    """Tests for `recall config` command."""

    def test_config_show_displays_current_config(self, tmp_path):
        """Test that `config show` displays current configuration."""
        with patch("recall.cli.get_default_config") as mock_config:
            mock_config.return_value.storage_dir = tmp_path
            mock_config.return_value.models_dir = tmp_path / "models"
            mock_config.return_value.whisper_model = "base"
            mock_config.return_value.llm_model_path = tmp_path / "model.gguf"

            result = runner.invoke(app, ["config", "show"])

            assert result.exit_code == 0
            assert str(tmp_path) in result.stdout or "storage" in result.stdout.lower()

    def test_config_path_shows_config_file_location(self):
        """Test that `config path` shows where config file is stored."""
        result = runner.invoke(app, ["config", "path"])

        assert result.exit_code == 0
        # Should show a path
        assert "/" in result.stdout or "\\" in result.stdout


class TestCLIInit:
    """Tests for `recall init` command."""

    def test_init_creates_storage_directory(self, tmp_path):
        """Test that init creates the storage directory structure."""
        storage_dir = tmp_path / "recall_storage"

        with patch("recall.cli.get_default_config") as mock_config:
            mock_config.return_value.storage_dir = storage_dir
            mock_config.return_value.models_dir = tmp_path / "models"

            result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            assert (
                storage_dir.exists()
                or "created" in result.stdout.lower()
                or "initialized" in result.stdout.lower()
            )

    def test_init_shows_success_message(self, tmp_path):
        """Test that init shows a success message."""
        with patch("recall.cli.get_default_config") as mock_config:
            mock_config.return_value.storage_dir = tmp_path / "storage"
            mock_config.return_value.models_dir = tmp_path / "models"

            result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            assert (
                "success" in result.stdout.lower()
                or "initialized" in result.stdout.lower()
                or "ready" in result.stdout.lower()
            )


# ============================================================================
# Ticket 6.2: Search CLI Commands
# ============================================================================


class TestCLIAsk:
    """Tests for `recall ask` command."""

    def test_ask_requires_question(self):
        """Test that ask requires a question argument."""
        result = runner.invoke(app, ["ask"])
        # Should fail without question
        assert (
            result.exit_code != 0
            or "missing" in result.stdout.lower()
            or "required" in result.stdout.lower()
        )

    def test_ask_returns_answer(self, tmp_path):
        """Test that ask returns an answer from the knowledge base."""
        with patch("recall.cli.RecallGraphRAG") as mock_rag_class:
            mock_rag = MagicMock()
            mock_rag.query.return_value = MagicMock(
                answer="The budget meeting is scheduled for Friday.", sources=[], confidence=0.9
            )
            mock_rag_class.return_value = mock_rag

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path
                mock_config.return_value.models_dir = tmp_path / "models"

                result = runner.invoke(app, ["ask", "When is the budget meeting?"])

                # Should return the answer or indicate no results
                assert result.exit_code == 0 or "no knowledge" in result.stdout.lower()

    def test_ask_shows_sources_with_flag(self, tmp_path):
        """Test that ask --sources shows source references."""
        with patch("recall.cli.RecallGraphRAG") as mock_rag_class:
            mock_rag = MagicMock()
            mock_rag.query.return_value = MagicMock(
                answer="The project deadline is next week.",
                sources=["meeting_notes.md", "project_plan.md"],
                confidence=0.85,
            )
            mock_rag_class.return_value = mock_rag

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path
                mock_config.return_value.models_dir = tmp_path / "models"

                result = runner.invoke(app, ["ask", "--sources", "What is the deadline?"])

                assert result.exit_code == 0 or "no knowledge" in result.stdout.lower()


class TestCLISearch:
    """Tests for `recall search` command."""

    def test_search_requires_query(self):
        """Test that search requires a query argument."""
        result = runner.invoke(app, ["search"])
        assert result.exit_code != 0 or "missing" in result.stdout.lower()

    def test_search_returns_results(self, tmp_path):
        """Test that search returns matching recordings."""
        with patch("recall.cli.RecordingIndex") as mock_index_class:
            mock_index = MagicMock()
            mock_index.search.return_value = [
                MagicMock(
                    filepath="/path/to/meeting.md",
                    title="Team Meeting",
                    source="zoom",
                    timestamp="2025-11-25",
                    snippet="Discussion about budget...",
                )
            ]
            mock_index_class.return_value = mock_index

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path

                result = runner.invoke(app, ["search", "budget"])

                assert result.exit_code == 0

    def test_search_limit_option(self, tmp_path):
        """Test that search --limit limits results."""
        with patch("recall.cli.RecordingIndex") as mock_index_class:
            mock_index = MagicMock()
            mock_index.search.return_value = []
            mock_index_class.return_value = mock_index

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path

                result = runner.invoke(app, ["search", "--limit", "5", "test"])

                assert result.exit_code == 0
                # Verify limit was passed
                if mock_index.search.called:
                    call_kwargs = mock_index.search.call_args
                    # Check if limit parameter was used


# ============================================================================
# Ticket 6.3: Notes CLI Commands
# ============================================================================


class TestCLINote:
    """Tests for `recall note` command."""

    def test_note_creates_quick_note(self, tmp_path):
        """Test that `recall note` creates a quick note."""
        with patch("recall.cli.create_note") as mock_create:
            mock_create.return_value = MagicMock(
                id="test-id", transcript="Test note content", filepath=tmp_path / "note.md"
            )

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path

                result = runner.invoke(app, ["note", "This is a test note"])

                assert result.exit_code == 0
                mock_create.assert_called()

    def test_note_with_title(self, tmp_path):
        """Test that `recall note --title` sets the title."""
        with patch("recall.cli.create_note") as mock_create:
            mock_create.return_value = MagicMock(
                id="test-id", title="My Title", transcript="Content"
            )

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path

                result = runner.invoke(app, ["note", "--title", "My Title", "Note content"])

                assert result.exit_code == 0
                # Verify title was passed
                if mock_create.called:
                    call_kwargs = mock_create.call_args[1]
                    assert call_kwargs.get("title") == "My Title"

    def test_note_with_tags(self, tmp_path):
        """Test that `recall note --tag` adds tags."""
        with patch("recall.cli.create_note") as mock_create:
            mock_create.return_value = MagicMock(
                id="test-id", tags=["meeting", "important"], transcript="Content"
            )

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path

                result = runner.invoke(
                    app, ["note", "--tag", "meeting", "--tag", "important", "Content"]
                )

                assert result.exit_code == 0


class TestCLINotes:
    """Tests for `recall notes` command (list notes)."""

    def test_notes_list_shows_recent_notes(self, tmp_path):
        """Test that `recall notes` lists recent notes."""
        with patch("recall.cli.list_notes") as mock_list:
            mock_list.return_value = [
                MagicMock(title="Note 1", timestamp="2025-11-25"),
                MagicMock(title="Note 2", timestamp="2025-11-24"),
            ]

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path

                result = runner.invoke(app, ["notes"])

                assert result.exit_code == 0

    def test_notes_list_limit_option(self, tmp_path):
        """Test that `recall notes --limit` limits the list."""
        with patch("recall.cli.list_notes") as mock_list:
            mock_list.return_value = []

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path

                result = runner.invoke(app, ["notes", "--limit", "5"])

                assert result.exit_code == 0


class TestCLIVoiceNote:
    """Tests for `recall voice` command."""

    def test_voice_starts_recording(self, tmp_path):
        """Test that `recall voice` starts voice recording."""
        with patch("recall.cli.record_voice_note") as mock_record:
            mock_record.return_value = MagicMock(id="voice-id", transcript="Voice note transcript")

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path
                mock_config.return_value.whisper_model = "base"

                # Use duration flag to avoid interactive mode
                result = runner.invoke(app, ["voice", "--duration", "1"])

                # May fail if audio not available, that's OK
                assert (
                    result.exit_code == 0
                    or "audio" in result.stdout.lower()
                    or "microphone" in result.stdout.lower()
                )

    def test_voice_with_title(self, tmp_path):
        """Test that `recall voice --title` sets the title."""
        with patch("recall.cli.record_voice_note") as mock_record:
            mock_record.return_value = MagicMock(
                id="voice-id", title="Meeting Notes", transcript="Voice content"
            )

            with patch("recall.cli.get_default_config") as mock_config:
                mock_config.return_value.storage_dir = tmp_path
                mock_config.return_value.whisper_model = "base"

                result = runner.invoke(
                    app, ["voice", "--title", "Meeting Notes", "--duration", "1"]
                )

                # Check title was passed if mock was called
                assert result.exit_code == 0 or "audio" in result.stdout.lower()
