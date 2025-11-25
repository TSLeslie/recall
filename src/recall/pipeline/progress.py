"""Progress reporting for Recall pipeline operations.

Provides the ProgressEvent model for reporting pipeline progress
to callers via callbacks.
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

# Valid stages in the ingestion pipeline
ProgressStage = Literal["starting", "transcribing", "summarizing", "saving", "completed"]


@dataclass
class ProgressEvent:
    """Event representing progress in a pipeline operation.

    Attributes:
        stage: Current stage of the pipeline.
        progress: Progress as float between 0.0 and 1.0.
        message: Human-readable progress message.
        details: Optional dictionary with additional details.

    Example:
        >>> event = ProgressEvent(
        ...     stage="transcribing",
        ...     progress=0.5,
        ...     message="Processing audio (50%)",
        ...     details={"elapsed_seconds": 30}
        ... )
    """

    stage: ProgressStage
    progress: float
    message: str
    details: Optional[dict[str, Any]] = field(default=None)

    def __post_init__(self):
        """Validate progress is in valid range."""
        if not 0.0 <= self.progress <= 1.0:
            raise ValueError(f"progress must be between 0.0 and 1.0, got {self.progress}")
