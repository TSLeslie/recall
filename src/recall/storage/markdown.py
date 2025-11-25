"""Markdown file I/O for Recall recordings.

This module handles reading and writing Recording objects as Markdown files
with YAML frontmatter. The format is human-readable and version control friendly.

File Format:
    ---
    id: uuid-here
    source: zoom
    timestamp: '2025-11-25T14:30:00'
    ...
    ---

    Transcript content here...

Directory Structure:
    base_dir/
        2025-01/
            20250115_143000_zoom.md
            20250120_090000_youtube.md
        2025-02/
            20250205_160000_note.md
"""

from pathlib import Path
from typing import List

import yaml

from .models import Recording


def save_recording(recording: Recording, base_dir: Path) -> Path:
    """Save a Recording as a Markdown file with YAML frontmatter.

    The file is saved to: {base_dir}/{YYYY-MM}/{timestamp}_{source}.md

    Args:
        recording: The Recording to save
        base_dir: Base directory for recordings storage

    Returns:
        Path to the created Markdown file
    """
    # Create YYYY-MM subdirectory
    year_month = recording.timestamp.strftime("%Y-%m")
    target_dir = base_dir / year_month
    target_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename: timestamp_source.md
    timestamp_str = recording.timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp_str}_{recording.source}.md"
    filepath = target_dir / filename

    # Build file content
    frontmatter = recording.to_frontmatter_dict()
    frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    content = f"---\n{frontmatter_yaml}---\n\n{recording.transcript}\n"

    # Write file
    filepath.write_text(content)

    return filepath


def load_recording(filepath: Path) -> Recording:
    """Load a Recording from a Markdown file with YAML frontmatter.

    Args:
        filepath: Path to the Markdown file

    Returns:
        Recording instance populated from the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is malformed (missing frontmatter, invalid YAML)
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Recording file not found: {filepath}")

    content = filepath.read_text()

    # Parse frontmatter
    if not content.startswith("---"):
        raise ValueError(f"Missing frontmatter in file: {filepath}")

    # Split on frontmatter delimiter
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed frontmatter in file: {filepath}")

    frontmatter_str = parts[1].strip()
    transcript = parts[2].strip()

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

    if frontmatter is None:
        raise ValueError(f"Empty frontmatter in file: {filepath}")

    return Recording.from_frontmatter_dict(frontmatter, transcript)


def list_recordings(base_dir: Path) -> List[Path]:
    """List all recording Markdown files in the base directory.

    Recursively finds all .md files and returns them sorted by filename
    (which provides chronological ordering due to timestamp-based names).

    Args:
        base_dir: Base directory to search

    Returns:
        List of Paths to .md files, sorted by filename
    """
    if not base_dir.exists():
        return []

    # Find all .md files recursively
    md_files = list(base_dir.rglob("*.md"))

    # Sort by filename (timestamp-based names provide chronological order)
    md_files.sort(key=lambda p: p.name)

    return md_files
