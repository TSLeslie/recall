"""Tests for GraphRAG wrapper (Ticket 4.1).

Tests the RecallGraphRAG class that wraps nano-graphrag for
semantic search and question-answering over recordings.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def temp_graphrag_dir(tmp_path):
    """Temporary directory for GraphRAG working files."""
    graphrag_dir = tmp_path / "graphrag"
    graphrag_dir.mkdir()
    return graphrag_dir


@pytest.fixture
def mock_nano_graphrag(mocker):
    """Mock nano_graphrag.GraphRAG to avoid actual model loading.

    Note: nano-graphrag's sync methods (.insert(), .query()) handle their own
    event loops internally and return regular values, not coroutines.
    """
    mock = mocker.patch("recall.knowledge.graphrag.GraphRAG")
    mock_instance = MagicMock()
    mock.return_value = mock_instance

    # Mock insert (sync - nano-graphrag handles event loop internally)
    mock_instance.insert = MagicMock()

    # Mock query (sync - nano-graphrag handles event loop internally)
    mock_instance.query = MagicMock(return_value="This is the answer based on the context.")

    return mock_instance


@pytest.fixture
def mock_sentence_transformer(mocker):
    """Mock SentenceTransformer for embeddings."""
    mock = mocker.patch("recall.knowledge.graphrag.SentenceTransformer")
    mock_instance = MagicMock()
    mock.return_value = mock_instance

    # Return fake embeddings
    import numpy as np

    mock_instance.encode.return_value = np.random.rand(384).astype(np.float32)

    return mock_instance


@pytest.fixture
def mock_llama(mocker):
    """Mock Llama for LLM operations."""
    mock = mocker.patch("recall.knowledge.graphrag.Llama")
    mock_instance = MagicMock()
    mock.return_value = mock_instance

    # Mock completion
    mock_instance.return_value = {"choices": [{"text": "Generated response from LLM"}]}

    return mock_instance


# ============================================================================
# RecallGraphRAG Initialization Tests
# ============================================================================


class TestRecallGraphRAGInit:
    """Tests for RecallGraphRAG initialization."""

    def test_graphrag_constructor_accepts_working_dir(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that RecallGraphRAG accepts a working directory."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        assert rag.working_dir == temp_graphrag_dir

    def test_graphrag_creates_working_dir_if_missing(
        self, tmp_path, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that working directory is created if it doesn't exist."""
        from recall.knowledge.graphrag import RecallGraphRAG

        working_dir = tmp_path / "new_graphrag_dir"
        assert not working_dir.exists()

        rag = RecallGraphRAG(working_dir=working_dir)

        assert working_dir.exists()

    def test_graphrag_default_working_dir(
        self, mock_nano_graphrag, mock_sentence_transformer, mocker
    ):
        """Test that default working directory is ~/.recall/graphrag/."""
        from recall.knowledge.graphrag import DEFAULT_GRAPHRAG_DIR, RecallGraphRAG

        # Mock Path.home() to use temp dir
        mock_home = mocker.patch("pathlib.Path.home")
        mock_home.return_value = Path("/mock/home")

        # Just verify the default constant
        assert "graphrag" in str(DEFAULT_GRAPHRAG_DIR)

    def test_graphrag_uses_local_llm(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that GraphRAG is configured to use local LLM."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        # Verify the RAG was initialized with LLM completion function
        assert rag._graphrag is not None
        # The LLM function is configured in the constructor
        assert hasattr(rag, "_llm_complete")

    def test_graphrag_uses_sentence_transformer_embeddings(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that GraphRAG uses sentence-transformers for embeddings."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        # Verify embedding model was initialized
        assert rag._embedding_model is not None


# ============================================================================
# Insert Tests
# ============================================================================


class TestRecallGraphRAGInsert:
    """Tests for inserting documents into GraphRAG."""

    def test_insert_adds_text_to_graph(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that insert adds text to the knowledge graph."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        rag.insert("This is a test document about machine learning.")

        mock_nano_graphrag.insert.assert_called_once()

    def test_insert_accepts_metadata(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that insert accepts metadata dictionary."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        metadata = {"source": "zoom", "timestamp": "2025-11-25T14:00:00"}
        rag.insert("Meeting transcript content", metadata=metadata)

        # Insert should be called
        mock_nano_graphrag.insert.assert_called_once()

    def test_insert_handles_empty_text(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that insert handles empty text gracefully."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        # Should not raise, but also should not insert
        rag.insert("")
        rag.insert("   ")

        # No inserts should happen for empty text
        mock_nano_graphrag.insert.assert_not_called()


# ============================================================================
# Query Tests
# ============================================================================


class TestRecallGraphRAGQuery:
    """Tests for querying the GraphRAG."""

    def test_query_returns_query_result(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that query returns a QueryResult object."""
        from recall.knowledge.graphrag import QueryResult, RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        result = rag.query("What is machine learning?")

        assert isinstance(result, QueryResult)

    def test_query_result_has_answer(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that QueryResult has an answer field."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        result = rag.query("What is machine learning?")

        assert hasattr(result, "answer")
        assert isinstance(result.answer, str)
        assert len(result.answer) > 0

    def test_query_result_has_sources(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that QueryResult has sources list."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        result = rag.query("What is machine learning?")

        assert hasattr(result, "sources")
        assert isinstance(result.sources, list)

    def test_query_result_has_confidence(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that QueryResult has confidence score."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        result = rag.query("What is machine learning?")

        assert hasattr(result, "confidence")
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_query_calls_graphrag_query(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that query calls the underlying GraphRAG query."""
        from recall.knowledge.graphrag import RecallGraphRAG

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        rag.query("What topics were discussed?")

        mock_nano_graphrag.query.assert_called_once()


# ============================================================================
# SourceReference Tests
# ============================================================================


class TestSourceReference:
    """Tests for SourceReference model."""

    def test_source_reference_has_required_fields(self):
        """Test that SourceReference has all required fields."""
        from recall.knowledge.graphrag import SourceReference

        ref = SourceReference(
            filepath=Path("/test/recording.md"),
            excerpt="This is a relevant excerpt",
            relevance=0.85,
        )

        assert ref.filepath == Path("/test/recording.md")
        assert ref.excerpt == "This is a relevant excerpt"
        assert ref.relevance == 0.85

    def test_source_reference_relevance_between_0_and_1(self):
        """Test that relevance score is between 0 and 1."""
        from recall.knowledge.graphrag import SourceReference

        ref = SourceReference(filepath=Path("/test/recording.md"), excerpt="Excerpt", relevance=0.5)

        assert 0.0 <= ref.relevance <= 1.0


# ============================================================================
# QueryResult Tests
# ============================================================================


class TestQueryResult:
    """Tests for QueryResult model."""

    def test_query_result_has_all_fields(self):
        """Test that QueryResult has all required fields."""
        from recall.knowledge.graphrag import QueryResult, SourceReference

        sources = [SourceReference(filepath=Path("/test/r1.md"), excerpt="Ex1", relevance=0.9)]

        result = QueryResult(
            answer="The meeting discussed the Q4 budget.", sources=sources, confidence=0.85
        )

        assert result.answer == "The meeting discussed the Q4 budget."
        assert len(result.sources) == 1
        assert result.confidence == 0.85

    def test_query_result_empty_sources(self):
        """Test QueryResult with no sources."""
        from recall.knowledge.graphrag import QueryResult

        result = QueryResult(answer="No relevant information found.", sources=[], confidence=0.0)

        assert result.sources == []
        assert result.confidence == 0.0


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestRecallGraphRAGErrors:
    """Tests for error handling in GraphRAG."""

    def test_query_handles_graphrag_error(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that query handles GraphRAG errors gracefully."""
        from recall.knowledge.graphrag import QueryResult, RecallGraphRAG

        mock_nano_graphrag.query.side_effect = Exception("GraphRAG error")

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        # Should not raise, but return empty result
        result = rag.query("Test query")

        assert isinstance(result, QueryResult)
        assert "error" in result.answer.lower() or result.confidence == 0.0

    def test_insert_handles_graphrag_error(
        self, temp_graphrag_dir, mock_nano_graphrag, mock_sentence_transformer
    ):
        """Test that insert handles GraphRAG errors gracefully."""
        from recall.knowledge.graphrag import RecallGraphRAG

        mock_nano_graphrag.insert.side_effect = Exception("Insert error")

        rag = RecallGraphRAG(working_dir=temp_graphrag_dir)

        # Should not raise
        rag.insert("Test content")  # Should handle gracefully
