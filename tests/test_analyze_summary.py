"""Tests for structured summary generation (Ticket 1.4).

Tests cover:
- SummaryResult model structure
- generate_summary() function with mocked LLM
- Parsing of LLM response into structured fields
- Handling of malformed LLM responses
- Edge cases (empty transcript, very long transcript)
"""

from datetime import datetime

import pytest


class TestSummaryResultModel:
    """Test SummaryResult Pydantic model."""

    def test_summary_result_has_all_fields(self):
        """Test that SummaryResult has all required fields."""
        from recall.analyze import SummaryResult

        result = SummaryResult(
            brief="A one-sentence summary of the meeting.",
            key_points=["Point one", "Point two", "Point three"],
            action_items=["Action item one", "Action item two"],
            participants=["Alice", "Bob"],
            topics=["Budget", "Planning"],
        )

        assert result.brief == "A one-sentence summary of the meeting."
        assert len(result.key_points) == 3
        assert len(result.action_items) == 2
        assert result.participants == ["Alice", "Bob"]
        assert result.topics == ["Budget", "Planning"]

    def test_summary_result_optional_fields_default_empty(self):
        """Test that SummaryResult handles empty optional lists."""
        from recall.analyze import SummaryResult

        result = SummaryResult(
            brief="Just a brief summary.",
            key_points=[],
            action_items=[],
            participants=[],
            topics=[],
        )

        assert result.brief == "Just a brief summary."
        assert result.key_points == []
        assert result.action_items == []

    def test_summary_result_serializes_to_dict(self):
        """Test that SummaryResult can serialize to dict."""
        from recall.analyze import SummaryResult

        result = SummaryResult(
            brief="Brief summary.",
            key_points=["Point 1"],
            action_items=["Action 1"],
            participants=["Alice"],
            topics=["Topic 1"],
        )

        as_dict = result.model_dump()

        assert as_dict["brief"] == "Brief summary."
        assert as_dict["key_points"] == ["Point 1"]
        assert as_dict["action_items"] == ["Action 1"]


class TestGenerateSummary:
    """Test generate_summary() function."""

    def test_generate_summary_returns_summary_result(self, mock_llama_analyzer):
        """Test that generate_summary returns a SummaryResult."""
        from recall.analyze import SummaryResult, generate_summary

        # Configure mock to return structured response
        mock_llama_analyzer.generate.return_value = """
BRIEF: The team discussed Q4 budget and planning.

KEY POINTS:
- Reviewed quarterly budget allocation
- Discussed upcoming product launches
- Agreed on timeline for deliverables

ACTION ITEMS:
- Review budget proposal by Friday
- Schedule follow-up meeting next week

PARTICIPANTS:
- Alice
- Bob
- Charlie

TOPICS:
- Budget
- Product launches
- Timeline
"""

        result = generate_summary(
            transcript="Meeting transcript about Q4 budget...",
            model_path="/models/test.gguf",
        )

        assert isinstance(result, SummaryResult)
        assert "Q4 budget" in result.brief
        assert len(result.key_points) >= 2
        assert len(result.action_items) >= 1

    def test_generate_summary_extracts_brief(self, mock_llama_analyzer):
        """Test that generate_summary extracts brief summary."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: This was a productive meeting about project planning.

KEY POINTS:
- First key point

ACTION ITEMS:
- No action items

PARTICIPANTS:
- None

TOPICS:
- Planning
"""

        result = generate_summary(
            transcript="Some transcript text...",
            model_path="/models/test.gguf",
        )

        assert "productive meeting" in result.brief.lower()

    def test_generate_summary_extracts_key_points(self, mock_llama_analyzer):
        """Test that generate_summary extracts key points as list."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: Meeting summary.

KEY POINTS:
- First important point
- Second important point
- Third important point

ACTION ITEMS:
- None

PARTICIPANTS:
- None

TOPICS:
- General
"""

        result = generate_summary(
            transcript="Transcript...",
            model_path="/models/test.gguf",
        )

        assert len(result.key_points) == 3
        assert "First important point" in result.key_points

    def test_generate_summary_extracts_action_items(self, mock_llama_analyzer):
        """Test that generate_summary extracts action items."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: Meeting with action items.

KEY POINTS:
- Discussion

ACTION ITEMS:
- Send report by EOD
- Schedule follow-up for next week
- Review documentation

PARTICIPANTS:
- None

TOPICS:
- Tasks
"""

        result = generate_summary(
            transcript="Transcript...",
            model_path="/models/test.gguf",
        )

        assert len(result.action_items) == 3
        assert any("report" in item.lower() for item in result.action_items)

    def test_generate_summary_extracts_participants(self, mock_llama_analyzer):
        """Test that generate_summary extracts participant names."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: Team meeting.

KEY POINTS:
- Discussion

ACTION ITEMS:
- None

PARTICIPANTS:
- Alice Johnson
- Bob Smith
- Charlie Brown

TOPICS:
- Team
"""

        result = generate_summary(
            transcript="Transcript...",
            model_path="/models/test.gguf",
        )

        assert len(result.participants) == 3
        assert "Alice Johnson" in result.participants

    def test_generate_summary_extracts_topics(self, mock_llama_analyzer):
        """Test that generate_summary extracts topics."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: Discussion about various topics.

KEY POINTS:
- Point

ACTION ITEMS:
- None

PARTICIPANTS:
- None

TOPICS:
- Budget Planning
- Product Development
- Marketing Strategy
"""

        result = generate_summary(
            transcript="Transcript...",
            model_path="/models/test.gguf",
        )

        assert len(result.topics) == 3
        assert "Budget Planning" in result.topics


class TestGenerateSummaryErrorHandling:
    """Test error handling in generate_summary."""

    def test_generate_summary_handles_malformed_response(self, mock_llama_analyzer):
        """Test that generate_summary handles malformed LLM responses."""
        from recall.analyze import generate_summary

        # LLM returns something that doesn't match expected format
        mock_llama_analyzer.generate.return_value = """
This is just a plain text response without any structure.
It doesn't have the expected sections at all.
The LLM sometimes does this.
"""

        result = generate_summary(
            transcript="Transcript...",
            model_path="/models/test.gguf",
        )

        # Should still return a valid SummaryResult with fallback values
        assert result.brief != ""  # Should have some content
        assert isinstance(result.key_points, list)
        assert isinstance(result.action_items, list)

    def test_generate_summary_handles_partial_response(self, mock_llama_analyzer):
        """Test that generate_summary handles partially structured responses."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: This meeting had a brief.

KEY POINTS:
- Only one point

But then it rambles on without proper structure...
"""

        result = generate_summary(
            transcript="Transcript...",
            model_path="/models/test.gguf",
        )

        # Should extract what it can
        assert "meeting" in result.brief.lower()
        assert len(result.key_points) >= 1

    def test_generate_summary_empty_transcript_returns_default(self, mock_llama_analyzer):
        """Test that generate_summary handles empty transcript gracefully."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: No content to summarize.

KEY POINTS:
- None

ACTION ITEMS:
- None

PARTICIPANTS:
- None

TOPICS:
- None
"""

        result = generate_summary(
            transcript="   ",  # Whitespace only
            model_path="/models/test.gguf",
        )

        assert isinstance(result.brief, str)


class TestGenerateSummaryIntegration:
    """Integration-style tests for generate_summary."""

    def test_generate_summary_uses_correct_prompt(self, mock_llama_analyzer):
        """Test that generate_summary sends structured prompt to LLM."""
        from recall.analyze import generate_summary

        mock_llama_analyzer.generate.return_value = """
BRIEF: Summary.

KEY POINTS:
- Point

ACTION ITEMS:
- None

PARTICIPANTS:
- None

TOPICS:
- Topic
"""

        generate_summary(
            transcript="This is the actual transcript content to analyze.",
            model_path="/models/test.gguf",
        )

        # Check that generate was called
        mock_llama_analyzer.generate.assert_called_once()

        # Check that the transcript was included in the prompt
        call_args = mock_llama_analyzer.generate.call_args
        prompt = call_args[0][0] if call_args[0] else call_args[1].get("prompt", "")
        assert "actual transcript content" in prompt.lower()
