"""GraphRAG wrapper for Recall.

This module provides the RecallGraphRAG class that wraps nano-graphrag
for semantic search and question-answering over recordings.

The wrapper:
- Auto-configures nano-graphrag to use local LLM (Qwen2.5-3B)
- Uses sentence-transformers for embeddings
- Provides synchronous interface over async nano-graphrag
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from nano_graphrag import GraphRAG
from nano_graphrag._utils import EmbeddingFunc
from sentence_transformers import SentenceTransformer

from recall.config import DEFAULT_LLAMA_MODEL, get_model_path

logger = logging.getLogger(__name__)

# Default working directory for GraphRAG
DEFAULT_GRAPHRAG_DIR = Path.home() / ".recall" / "graphrag"

# Embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIM = 384


@dataclass
class SourceReference:
    """A reference to a source document in query results.

    Attributes:
        filepath: Path to the source Markdown file
        excerpt: Relevant text excerpt from the source
        relevance: Relevance score between 0.0 and 1.0
    """

    filepath: Path
    excerpt: str
    relevance: float


@dataclass
class QueryResult:
    """Result from a GraphRAG query.

    Attributes:
        answer: The generated answer to the query
        sources: List of source references used to generate the answer
        confidence: Confidence score between 0.0 and 1.0
    """

    answer: str
    sources: list[SourceReference] = field(default_factory=list)
    confidence: float = 0.0


class RecallGraphRAG:
    """GraphRAG wrapper configured for local LLM and embeddings.

    This class wraps nano-graphrag and configures it to use:
    - Qwen2.5-3B via llama-cpp-python for LLM operations
    - sentence-transformers (all-MiniLM-L6-v2) for embeddings

    Example:
        >>> rag = RecallGraphRAG(working_dir=Path("~/.recall/graphrag"))
        >>> rag.insert("Meeting discussed the Q4 budget review.")
        >>> result = rag.query("What was discussed in the meeting?")
        >>> print(result.answer)
        'The meeting discussed the Q4 budget review.'
    """

    def __init__(
        self,
        working_dir: Optional[Path] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """Initialize RecallGraphRAG.

        Args:
            working_dir: Directory for GraphRAG storage. Defaults to ~/.recall/graphrag/
            embedding_model: Name of sentence-transformers model for embeddings
        """
        self.working_dir = Path(working_dir) if working_dir else DEFAULT_GRAPHRAG_DIR
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        self._embedding_model = SentenceTransformer(embedding_model)

        # Create embedding function wrapper for nano-graphrag
        async def embedding_func(texts: list[str]) -> np.ndarray:
            embeddings = self._embedding_model.encode(texts, convert_to_numpy=True)
            return embeddings

        # Create LLM completion function for nano-graphrag
        # nano-graphrag passes: prompt, system_prompt=None, history_messages=[], **kwargs
        async def llm_complete(
            prompt: str, system_prompt: str = None, history_messages: list = None, **kwargs
        ) -> str:
            return await self._llm_complete(
                prompt, system_prompt=system_prompt, history_messages=history_messages, **kwargs
            )

        # Initialize GraphRAG with custom functions
        self._graphrag = GraphRAG(
            working_dir=str(self.working_dir),
            embedding_func=EmbeddingFunc(
                embedding_dim=EMBEDDING_DIM,
                max_token_size=8192,
                func=embedding_func,
            ),
            best_model_func=llm_complete,
            cheap_model_func=llm_complete,
            enable_llm_cache=False,  # Disable cache to ensure our JSON handling is used
        )

        # Store LLM instance for reuse
        self._llm = None

    def _get_llm(self):
        """Get or create the LLM instance."""
        if self._llm is None:
            from llama_cpp import Llama

            model_path = get_model_path(DEFAULT_LLAMA_MODEL)
            if model_path is None:
                raise RuntimeError(f"LLM model not found: {DEFAULT_LLAMA_MODEL}")

            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=4096,
                n_threads=4,
                verbose=False,
            )
        return self._llm

    def _detect_json_request(self, text: str) -> bool:
        """Detect if the text explicitly asks for JSON output format.

        This checks for explicit instructions to output JSON, not just
        the presence of JSON data in the context.
        """
        if not text:
            return False

        text_lower = text.lower()

        # These indicate the prompt ASKS FOR JSON output
        json_output_indicators = [
            "response should be json",
            "json formatted as follows",
            "return output as a well-formed json",
            "the response should be json formatted",
            '"points": [',  # The JSON format example showing expected output
            '{"description":',  # The JSON format example
            "score_value",  # Variable in JSON template, not actual data
        ]

        # Check if asking FOR JSON output (not just containing JSON data)
        for indicator in json_output_indicators:
            if indicator in text_lower:
                return True

        # Also check for the specific nano-graphrag pattern
        if "importance score" in text_lower and "json formatted" in text_lower:
            return True

        return False

    def _detect_entity_extraction(self, text: str) -> bool:
        """Detect if this is an entity extraction prompt."""
        if not text:
            return False
        return '("entity"' in text and "<|>" in text

    async def _llm_complete(
        self, prompt: str, system_prompt: str = None, history_messages: list = None, **kwargs
    ) -> str:
        """Complete a prompt using local LLM.

        nano-graphrag calls this with:
        - prompt: The user query or content to process
        - system_prompt: Instructions for the LLM (contains JSON format specs)
        - history_messages: Conversation history for multi-turn
        - **kwargs: Other args like response_format, hashing_kv, etc.

        Args:
            prompt: The prompt/query to complete
            system_prompt: System instructions (may contain JSON format requirements)
            history_messages: Previous conversation messages
            **kwargs: Additional arguments (response_format, hashing_kv, etc.)

        Returns:
            Generated completion text
        """
        try:
            llm = self._get_llm()

            # Check what type of output is expected - check BOTH prompt and system_prompt
            combined_text = f"{prompt or ''} {system_prompt or ''}"
            expects_json = self._detect_json_request(combined_text)
            is_entity_extraction = self._detect_entity_extraction(combined_text)

            logger.info(
                f"LLM completing (expects_json={expects_json}, entity_extraction={is_entity_extraction})"
            )

            # Build messages list
            messages = []

            # Use provided system_prompt if available, otherwise create our own
            if system_prompt:
                # nano-graphrag provides its own system prompt with instructions
                messages.append({"role": "system", "content": system_prompt})
            elif is_entity_extraction:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "You are an expert entity extractor. Extract entities and relationships "
                            "EXACTLY in the format shown in the examples. Use the EXACT delimiters: "
                            "<|> between fields, ## between records, and <|COMPLETE|> at the end."
                        ),
                    }
                )
            elif expects_json:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that ALWAYS responds with valid JSON. "
                            'Respond with: {"points": [{"description": "answer", "score": 85}]}'
                        ),
                    }
                )
            else:
                messages.append(
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer concisely based on context.",
                    }
                )

            # Add history messages if provided
            if history_messages:
                messages.extend(history_messages)

            # Add the user prompt
            messages.append({"role": "user", "content": prompt})

            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=2048 if is_entity_extraction else 1024,
                temperature=0.1 if (expects_json or is_entity_extraction) else 0.7,
                stop=["</s>"],
            )

            result = response["choices"][0]["message"]["content"].strip()

            # Post-process based on expected format
            if expects_json and result:
                result = self._ensure_valid_json(result)
                logger.debug(f"JSON response: {result[:200]}...")

            return result
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            # Return appropriate fallback based on expected format
            combined_text = f"{prompt or ''} {system_prompt or ''}"
            if self._detect_json_request(combined_text):
                return '{"points": [{"description": "Unable to process request", "score": 0}]}'
            return f"Error generating response: {e}"

    def _ensure_valid_json(self, text: str) -> str:
        """Ensure the response is valid JSON, converting if needed."""
        import json
        import re

        logger.debug(f"_ensure_valid_json input (first 100): {text[:100] if text else 'empty'}")

        # Try to parse as-is first
        try:
            json.loads(text)
            logger.debug("Input is already valid JSON")
            return text
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                json.loads(match.group())
                logger.debug(f"Found valid JSON in text: {match.group()[:100]}")
                return match.group()
            except json.JSONDecodeError:
                pass

        # Convert plain text response to valid JSON format
        logger.debug("Converting plain text to JSON format")
        # Escape the text properly for JSON
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()
        # Truncate if too long
        if len(escaped_text) > 500:
            escaped_text = escaped_text[:500] + "..."

        result = f'{{"points": [{{"description": "{escaped_text}", "score": 70}}]}}'
        logger.debug(f"Converted result: {result[:100]}")
        return result

    def insert(self, text: str, metadata: Optional[dict] = None) -> None:
        """Insert a document into the knowledge graph.

        Args:
            text: The text content to insert
            metadata: Optional metadata dictionary (source, timestamp, etc.)
        """
        if not text or not text.strip():
            return

        # Format text with metadata if provided
        formatted_text = text
        if metadata:
            meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
            formatted_text = f"[{meta_str}]\n\n{text}"

        try:
            # nano-graphrag's insert() is synchronous and handles its own event loop
            self._graphrag.insert(formatted_text)
        except Exception as e:
            logger.error(f"Failed to insert document: {e}")

    def query(self, question: str) -> QueryResult:
        """Query the knowledge graph with a natural language question.

        Args:
            question: The question to answer

        Returns:
            QueryResult with answer, sources, and confidence
        """
        try:
            # nano-graphrag's query() is synchronous and handles its own event loop
            answer = self._graphrag.query(question)

            # nano-graphrag returns the final synthesized answer as a string
            # (after processing through global_reduce_rag_response)
            return QueryResult(
                answer=answer if answer else "No answer found.",
                sources=[],
                confidence=0.8 if answer else 0.0,
            )

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QueryResult(
                answer=f"Error processing query: {e}",
                sources=[],
                confidence=0.0,
            )
