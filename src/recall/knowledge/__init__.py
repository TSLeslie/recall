"""Knowledge module for Recall.

This module provides Graph RAG (Retrieval-Augmented Generation) capabilities
for semantic search and question-answering over recordings.
"""

from recall.knowledge.graphrag import (
    DEFAULT_GRAPHRAG_DIR,
    QueryResult,
    RecallGraphRAG,
    SourceReference,
)
from recall.knowledge.ingest import (
    KnowledgeIngestor,
    chunk_transcript,
    ingest_all,
    ingest_recording,
)
from recall.knowledge.query import (
    Answer,
    SearchHit,
    Source,
    ask,
    hybrid_search,
    search,
)
from recall.knowledge.sync import (
    ChangeSet,
    KnowledgeSync,
    SyncResult,
    compute_file_hash,
)

__all__ = [
    "RecallGraphRAG",
    "QueryResult",
    "SourceReference",
    "DEFAULT_GRAPHRAG_DIR",
    "ingest_recording",
    "ingest_all",
    "chunk_transcript",
    "KnowledgeIngestor",
    "ask",
    "search",
    "hybrid_search",
    "Answer",
    "Source",
    "SearchHit",
    "KnowledgeSync",
    "ChangeSet",
    "SyncResult",
    "compute_file_hash",
]
