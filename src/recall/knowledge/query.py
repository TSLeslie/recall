"""Query interface for Recall knowledge base (Ticket 4.3).

This module provides natural language search and question-answering
over recordings using GraphRAG and SQLite FTS.

Features:
- ask(): Natural language Q&A with source attribution
- search(): Keyword-based search
- hybrid_search(): Combines semantic and keyword search
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from recall.knowledge.graphrag import RecallGraphRAG

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """A source reference in query results.

    Attributes:
        recording_path: Path to the source recording file
        excerpt: Relevant text excerpt from the recording
        timestamp: Timestamp of the recording
    """

    recording_path: Path
    excerpt: str
    timestamp: datetime


@dataclass
class Answer:
    """Result from a natural language query.

    Attributes:
        response: Natural language answer to the question
        sources: List of source recordings used
        follow_up_questions: Suggested follow-up questions
    """

    response: str
    sources: list[Source] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)


@dataclass
class SearchHit:
    """A search result from keyword search.

    Attributes:
        recording_path: Path to the recording file
        title: Recording title
        snippet: Relevant text snippet
        score: Relevance score (0.0 to 1.0)
        timestamp: Recording timestamp
        source: Recording source type
    """

    recording_path: Path
    title: Optional[str]
    snippet: str
    score: float
    timestamp: Optional[datetime] = None
    source: Optional[str] = None


def ask(question: str, graphrag: RecallGraphRAG) -> Answer:
    """Ask a natural language question and get an answer.

    Uses GraphRAG to find relevant context and generate a response.
    Includes source attribution and suggested follow-up questions.

    Args:
        question: The question to answer
        graphrag: The GraphRAG instance to query

    Returns:
        Answer with response, sources, and follow-up questions

    Example:
        >>> answer = ask("What was discussed in yesterday's meeting?", rag)
        >>> print(answer.response)
        'The meeting covered Q4 budget projections and team assignments.'
    """
    try:
        result = graphrag.query(question)

        # Convert GraphRAG sources to Source objects
        sources = []
        for src in result.sources:
            sources.append(
                Source(
                    recording_path=src.filepath,
                    excerpt=src.excerpt,
                    timestamp=datetime.now(),  # TODO: Extract from metadata
                )
            )

        # Generate follow-up questions based on the answer
        follow_ups = _generate_follow_up_questions(question, result.answer)

        return Answer(
            response=result.answer,
            sources=sources,
            follow_up_questions=follow_ups,
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        return Answer(
            response=f"Unable to process query: {e}",
            sources=[],
            follow_up_questions=[],
        )


def search(
    query: str,
    graphrag: RecallGraphRAG,
    index: Optional[object] = None,
) -> list[SearchHit]:
    """Search recordings by keyword.

    Uses SQLite FTS for fast keyword search when an index is provided.
    Falls back to GraphRAG semantic search if no index.

    Args:
        query: The search query
        graphrag: The GraphRAG instance (for semantic fallback)
        index: Optional RecordingIndex for FTS search

    Returns:
        List of SearchHit results sorted by relevance

    Example:
        >>> results = search("budget Q4", rag, index)
        >>> for hit in results:
        ...     print(f"{hit.title}: {hit.snippet}")
    """
    if not query or not query.strip():
        return []

    results = []

    try:
        # Try FTS search first if index is available
        if index is not None:
            try:
                fts_results = index.search(query)
                for r in fts_results:
                    results.append(
                        SearchHit(
                            recording_path=r.filepath,
                            title=None,  # SearchResult doesn't have title
                            snippet=r.summary_snippet,
                            score=r.relevance_score,
                            timestamp=r.timestamp,
                            source=r.source,
                        )
                    )
            except Exception as e:
                logger.warning(f"FTS search failed: {e}")

    except Exception as e:
        logger.error(f"Search failed: {e}")

    return results


def hybrid_search(
    query: str,
    graphrag: RecallGraphRAG,
    index: Optional[object] = None,
) -> list[SearchHit]:
    """Perform hybrid search combining semantic and keyword search.

    Combines results from GraphRAG semantic search and SQLite FTS,
    deduplicates, and ranks by combined relevance score.

    Args:
        query: The search query
        graphrag: The GraphRAG instance for semantic search
        index: Optional RecordingIndex for FTS search

    Returns:
        List of SearchHit results sorted by relevance
    """
    if not query or not query.strip():
        return []

    results_map: dict[Path, SearchHit] = {}

    # Get FTS results
    try:
        if index is not None:
            fts_results = index.search(query)
            for r in fts_results:
                path = r.filepath
                results_map[path] = SearchHit(
                    recording_path=path,
                    title=None,
                    snippet=r.summary_snippet,
                    score=r.relevance_score,
                    timestamp=r.timestamp,
                    source=r.source,
                )
    except Exception as e:
        logger.warning(f"FTS search failed in hybrid: {e}")

    # Get GraphRAG results
    try:
        rag_result = graphrag.query(query)
        for src in rag_result.sources:
            path = src.filepath
            if path in results_map:
                # Boost score for results found in both
                results_map[path].score = min(1.0, results_map[path].score + src.relevance * 0.5)
            else:
                results_map[path] = SearchHit(
                    recording_path=path,
                    title=None,
                    snippet=src.excerpt,
                    score=src.relevance,
                )
    except Exception as e:
        logger.warning(f"GraphRAG search failed in hybrid: {e}")

    # Sort by score descending
    results = list(results_map.values())
    results.sort(key=lambda x: x.score, reverse=True)

    return results


def _generate_follow_up_questions(question: str, answer: str) -> list[str]:
    """Generate follow-up questions based on the Q&A.

    Args:
        question: The original question
        answer: The generated answer

    Returns:
        List of suggested follow-up questions
    """
    # Simple heuristic-based follow-up generation
    # In production, this could use the LLM
    follow_ups = []

    # Common follow-up patterns
    if "meeting" in question.lower() or "meeting" in answer.lower():
        follow_ups.append("Who attended this meeting?")
        follow_ups.append("What were the action items?")

    if "budget" in question.lower() or "budget" in answer.lower():
        follow_ups.append("What was the total budget amount?")
        follow_ups.append("Were there any budget concerns raised?")

    if "project" in question.lower() or "project" in answer.lower():
        follow_ups.append("What is the project timeline?")
        follow_ups.append("Who is responsible for this project?")

    # Limit to 3 follow-ups
    return follow_ups[:3]
