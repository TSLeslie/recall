"""Text analysis using Llama models."""

import re
from typing import Any, Dict, List, Optional

from llama_cpp import Llama
from pydantic import BaseModel, Field


class SummaryResult(BaseModel):
    """Structured summary result from LLM analysis.

    Contains extracted information from a transcript including
    brief summary, key points, action items, participants, and topics.
    """

    brief: str = Field(..., description="1-2 sentence summary")
    key_points: List[str] = Field(default_factory=list, description="Key points as bullet list")
    action_items: List[str] = Field(default_factory=list, description="Extracted action items")
    participants: List[str] = Field(default_factory=list, description="Detected participant names")
    topics: List[str] = Field(default_factory=list, description="Main topics discussed")


class LlamaAnalyzer:
    """Wrapper for Llama model inference."""

    def __init__(self, model_path: str, n_ctx: int = 32768, n_gpu_layers: int = -1):
        """
        Initialize the Llama model.

        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size (default 32768 for long meetings, max 131072)
            n_gpu_layers: Number of layers to offload to GPU (-1 for all, 0 for CPU only)
        """
        self.model = Llama(
            model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, verbose=False
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs,
    ) -> str:
        """
        Generate text using the Llama model.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            echo=False,
            **kwargs,
        )
        return output["choices"][0]["text"]


def analyze(
    text: str,
    prompt: str = "Summarize the following text:",
    model_path: Optional[str] = None,
    n_ctx: int = 32768,
    **kwargs,
) -> str:
    """
    Analyze text using a Llama model.

    Args:
        text: Input text to analyze
        prompt: Analysis instruction/prompt
        model_path: Path to Llama GGUF model file
        n_ctx: Context window size (default 32768 for long meetings)
        **kwargs: Additional arguments for generation

    Returns:
        Analysis result as string
    """
    if model_path is None:
        raise ValueError(
            "model_path must be provided. "
            "Download a Llama model in GGUF format and specify its path."
        )

    analyzer = LlamaAnalyzer(model_path, n_ctx=n_ctx)

    full_prompt = f"{prompt}\n\nText:\n{text}\n\nAnalysis:"

    result = analyzer.generate(full_prompt, **kwargs)
    return result.strip()


def summarize(text: str, model_path: str, max_length: int = 200) -> str:
    """
    Summarize text using Llama.

    Args:
        text: Text to summarize
        model_path: Path to Llama model
        max_length: Maximum summary length in tokens

    Returns:
        Summary text
    """
    prompt = (
        "Please provide a concise summary of the following text. "
        "Focus on the key points and main ideas."
    )
    return analyze(text, prompt=prompt, model_path=model_path, max_tokens=max_length)


def extract_key_points(text: str, model_path: str) -> str:
    """
    Extract key points from text.

    Args:
        text: Input text
        model_path: Path to Llama model

    Returns:
        Key points as formatted text
    """
    prompt = "Extract the key points from the following text. " "List them as bullet points."
    return analyze(text, prompt=prompt, model_path=model_path)


# Structured summary generation prompt
_SUMMARY_PROMPT = """Analyze the following transcript and extract structured information.

Format your response EXACTLY as follows (use these exact section headers):

BRIEF: [1-2 sentence summary of the overall content]

KEY POINTS:
- [First key point]
- [Second key point]
- [Add more as needed]

ACTION ITEMS:
- [First action item, if any]
- [Add more as needed, or "None" if no action items]

PARTICIPANTS:
- [Name of first participant mentioned]
- [Add more as needed, or "None" if no participants detected]

TOPICS:
- [First main topic discussed]
- [Add more as needed]

TRANSCRIPT:
{transcript}

Now provide the structured analysis:"""


def _parse_section(response: str, section_name: str) -> List[str]:
    """Parse a bullet-point section from the LLM response.

    Args:
        response: Full LLM response text
        section_name: Name of section to extract (e.g., "KEY POINTS")

    Returns:
        List of items found in the section
    """
    items = []

    # Find section start
    section_pattern = rf"{section_name}:\s*\n"
    match = re.search(section_pattern, response, re.IGNORECASE)

    if not match:
        return items

    # Extract content after section header until next section or end
    start_pos = match.end()
    # Look for next section header (word in caps followed by colon)
    next_section = re.search(r"\n[A-Z][A-Z ]+:", response[start_pos:])
    end_pos = start_pos + next_section.start() if next_section else len(response)

    section_content = response[start_pos:end_pos]

    # Extract bullet points (lines starting with - or *)
    for line in section_content.split("\n"):
        line = line.strip()
        if line.startswith(("-", "*", "•")):
            item = line.lstrip("-*• ").strip()
            if item and item.lower() != "none":
                items.append(item)

    return items


def _parse_brief(response: str) -> str:
    """Parse the brief summary from the LLM response.

    Args:
        response: Full LLM response text

    Returns:
        Brief summary string
    """
    # Look for BRIEF: section
    match = re.search(r"BRIEF:\s*(.+?)(?:\n\n|\n[A-Z])", response, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: use first sentence or paragraph
    lines = response.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line and not line.endswith(":"):
            return line[:500]  # Limit length

    return "Summary not available."


def generate_summary(transcript: str, model_path: str, n_ctx: int = 32768) -> SummaryResult:
    """Generate a structured summary from a transcript.

    Uses the LLM to extract key information including a brief summary,
    key points, action items, participants, and topics.

    Args:
        transcript: The transcript text to summarize
        model_path: Path to the Llama model file
        n_ctx: Context window size (default 32768 for long transcripts)

    Returns:
        SummaryResult with structured summary information
    """
    # Handle empty/whitespace transcript
    if not transcript or not transcript.strip():
        return SummaryResult(
            brief="No content to summarize.",
            key_points=[],
            action_items=[],
            participants=[],
            topics=[],
        )

    # Create analyzer and generate response
    analyzer = LlamaAnalyzer(model_path, n_ctx=n_ctx)
    prompt = _SUMMARY_PROMPT.format(transcript=transcript)

    response = analyzer.generate(prompt, max_tokens=1024, temperature=0.3)

    # Parse response into structured format
    brief = _parse_brief(response)
    key_points = _parse_section(response, "KEY POINTS")
    action_items = _parse_section(response, "ACTION ITEMS")
    participants = _parse_section(response, "PARTICIPANTS")
    topics = _parse_section(response, "TOPICS")

    # Handle malformed response - use response as brief if parsing failed
    if not brief or brief == "Summary not available.":
        # Try to extract something meaningful
        clean_response = response.strip()
        if clean_response:
            brief = clean_response[:500]

    return SummaryResult(
        brief=brief,
        key_points=key_points,
        action_items=action_items,
        participants=participants,
        topics=topics,
    )
