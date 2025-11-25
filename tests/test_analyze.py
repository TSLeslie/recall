"""Tests for analysis functionality."""

import pytest
from recall.analyze import analyze


def test_analyze_requires_model_path():
    """Test that analyze raises ValueError without model_path."""
    with pytest.raises(ValueError):
        analyze("Some text to analyze")


# Add more tests as needed with actual model files
