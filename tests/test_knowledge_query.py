"""Tests for Query Interface (Ticket 4.3).

Tests the natural language query interface that combines GraphRAG
with SQLite FTS for hybrid search.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_graphrag(mocker):
    """Mock RecallGraphRAG for query testing."""
    from recall.knowledge.graphrag import QueryResult, SourceReference

    mock = MagicMock()
    mock.query.return_value = QueryResult(
        answer="The Q4 budget meeting discussed financial projections and resource allocation.",
        sources=[
            SourceReference(
                filepath=Path("/recordings/meeting1.md"),
                excerpt="We reviewed the Q4 budget projections...",
                relevance=0.92,
            )
        ],
        confidence=0.85,
    )
    return mock


@pytest.fixture
def mock_index(mocker):
    """Mock RecordingIndex for hybrid search."""
    from recall.storage.index import SearchResult

    mock = MagicMock()
    mock.search.return_value = [
        SearchResult(
            filepath=Path("/recordings/meeting1.md"),
            source="zoom",
            timestamp=datetime(2025, 11, 25, 14, 0, 0),
            summary_snippet="...Q4 budget projections were reviewed...",
            relevance_score=0.85,
        )
    ]
    return mock


# ============================================================================
# Answer Model Tests
# ============================================================================


class TestAnswerModel:
    """Tests for the Answer model."""

    def test_answer_has_response(self):
        """Test that Answer has a response field."""
        from recall.knowledge.query import Answer

        answer = Answer(
            response="The meeting discussed Q4 budget.",
            sources=[],
            follow_up_questions=[],
        )

        assert answer.response == "The meeting discussed Q4 budget."

    def test_answer_has_sources(self):
        """Test that Answer has sources list."""
        from recall.knowledge.query import Answer, Source

        sources = [
            Source(
                recording_path=Path("/test/recording.md"),
                excerpt="Budget discussion excerpt",
                timestamp=datetime(2025, 11, 25, 14, 0, 0),
            )
        ]

        answer = Answer(
            response="The budget was discussed.",
            sources=sources,
            follow_up_questions=[],
        )

        assert len(answer.sources) == 1
        assert answer.sources[0].recording_path == Path("/test/recording.md")

    def test_answer_has_follow_up_questions(self):
        """Test that Answer has follow-up questions."""
        from recall.knowledge.query import Answer

        answer = Answer(
            response="The budget was discussed.",
            sources=[],
            follow_up_questions=[
                "What was the total budget?",
                "Who attended the meeting?",
            ],
        )

        assert len(answer.follow_up_questions) == 2


# ============================================================================
# Source Model Tests
# ============================================================================


class TestSourceModel:
    """Tests for the Source model."""

    def test_source_has_required_fields(self):
        """Test that Source has all required fields."""
        from recall.knowledge.query import Source

        source = Source(
            recording_path=Path("/recordings/meeting.md"),
            excerpt="This is a relevant excerpt from the meeting.",
            timestamp=datetime(2025, 11, 25, 14, 30, 0),
        )

        assert source.recording_path == Path("/recordings/meeting.md")
        assert "excerpt" in source.excerpt
        assert source.timestamp == datetime(2025, 11, 25, 14, 30, 0)


# ============================================================================
# ask() Function Tests
# ============================================================================


class TestAskFunction:
    """Tests for the ask() function."""

    def test_ask_returns_answer(self, mock_graphrag):
        """Test that ask() returns an Answer object."""
        from recall.knowledge.query import Answer, ask

        result = ask("What was discussed in the Q4 meeting?", mock_graphrag)

        assert isinstance(result, Answer)

    def test_ask_includes_response(self, mock_graphrag):
        """Test that ask() includes a response."""
        from recall.knowledge.query import ask

        result = ask("What was discussed in the Q4 meeting?", mock_graphrag)

        assert len(result.response) > 0
        assert "Q4" in result.response or "budget" in result.response.lower()

    def test_ask_includes_sources(self, mock_graphrag):
        """Test that ask() includes source references."""
        from recall.knowledge.query import ask

        result = ask("What was discussed in the Q4 meeting?", mock_graphrag)

        assert isinstance(result.sources, list)

    def test_ask_calls_graphrag_query(self, mock_graphrag):
        """Test that ask() calls GraphRAG query."""
        from recall.knowledge.query import ask

        ask("Test question?", mock_graphrag)

        mock_graphrag.query.assert_called_once()

    def test_ask_generates_follow_up_questions(self, mock_graphrag):
        """Test that ask() generates follow-up questions."""
        from recall.knowledge.query import ask

        result = ask("What was discussed in the Q4 meeting?", mock_graphrag)

        assert isinstance(result.follow_up_questions, list)


# ============================================================================
# search() Function Tests
# ============================================================================


class TestSearchFunction:
    """Tests for the search() function."""

    def test_search_returns_list(self, mock_graphrag, mock_index):
        """Test that search() returns a list of SearchHit."""
        from recall.knowledge.query import SearchHit, search

        results = search("budget", mock_graphrag, mock_index)

        assert isinstance(results, list)

    def test_search_hit_has_required_fields(self, mock_graphrag, mock_index):
        """Test that SearchHit has all required fields."""
        from recall.knowledge.query import search

        results = search("budget", mock_graphrag, mock_index)

        if results:
            hit = results[0]
            assert hasattr(hit, "recording_path")
            assert hasattr(hit, "title")
            assert hasattr(hit, "snippet")
            assert hasattr(hit, "score")

    def test_search_uses_index(self, mock_graphrag, mock_index):
        """Test that search() uses the SQLite index."""
        from recall.knowledge.query import search

        search("budget", mock_graphrag, mock_index)

        mock_index.search.assert_called()

    def test_search_empty_query_returns_empty(self, mock_graphrag, mock_index):
        """Test that empty query returns empty results."""
        from recall.knowledge.query import search

        results = search("", mock_graphrag, mock_index)

        assert results == []


# ============================================================================
# Hybrid Search Tests
# ============================================================================


class TestHybridSearch:
    """Tests for hybrid search combining GraphRAG and FTS."""

    def test_hybrid_search_combines_results(self, mock_graphrag, mock_index):
        """Test that hybrid search combines GraphRAG and FTS results."""
        from recall.knowledge.query import hybrid_search

        results = hybrid_search("Q4 budget meeting", mock_graphrag, mock_index)

        assert isinstance(results, list)

    def test_hybrid_search_ranks_by_relevance(self, mock_graphrag, mock_index):
        """Test that results are ranked by relevance."""
        from recall.knowledge.query import hybrid_search

        results = hybrid_search("Q4 budget", mock_graphrag, mock_index)

        if len(results) > 1:
            # Results should be sorted by score (descending)
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_hybrid_search_deduplicates(self, mock_graphrag, mock_index):
        """Test that duplicate results are deduplicated."""
        from recall.knowledge.query import hybrid_search

        results = hybrid_search("budget", mock_graphrag, mock_index)

        # No duplicate paths
        paths = [r.recording_path for r in results]
        assert len(paths) == len(set(paths))


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestQueryErrorHandling:
    """Tests for error handling in query functions."""

    def test_ask_handles_graphrag_error(self, mock_graphrag):
        """Test that ask() handles GraphRAG errors gracefully."""
        from recall.knowledge.query import Answer, ask

        mock_graphrag.query.side_effect = Exception("GraphRAG error")

        result = ask("Test question?", mock_graphrag)

        assert isinstance(result, Answer)
        assert "error" in result.response.lower() or len(result.response) > 0

    def test_search_handles_index_error(self, mock_graphrag, mock_index):
        """Test that search() handles index errors gracefully."""
        from recall.knowledge.query import search

        mock_index.search.side_effect = Exception("Index error")

        results = search("test query", mock_graphrag, mock_index)

        assert results == []
