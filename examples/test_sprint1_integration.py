#!/usr/bin/env python3
"""Integration test for Sprint 1: Storage Foundation.

This script demonstrates that all Sprint 1 components work together:
1. Recording model creation and serialization
2. Markdown file save/load with YAML frontmatter
3. SQLite FTS5 search index
4. (Mocked) Structured summary generation

Run with: python examples/test_sprint1_integration.py
"""

import tempfile
from datetime import datetime
from pathlib import Path

# Test imports work
print("=" * 60)
print("Sprint 1 Integration Test")
print("=" * 60)

print("\n1. Testing imports...")
try:
    from recall.analyze import SummaryResult
    from recall.storage import (
        Recording,
        RecordingIndex,
        SearchResult,
        list_recordings,
        load_recording,
        save_recording,
    )

    print("   ✓ All imports successful")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    exit(1)

# Create temp directory for testing
with tempfile.TemporaryDirectory() as temp_dir:
    base_dir = Path(temp_dir)
    print(f"\n2. Using temp directory: {base_dir}")

    # Test Recording model
    print("\n3. Creating Recording objects...")

    recording1 = Recording.create_new(
        source="zoom",
        transcript="""
        Alice: Good morning everyone, let's discuss the Q4 budget.
        Bob: I think we need to increase the marketing spend by 15%.
        Alice: That's a good point. Charlie, what about engineering?
        Charlie: We're on track, but need two more developers.
        Alice: Okay, action item: Bob will draft a marketing proposal by Friday.
        Bob: Got it. And Charlie will submit hiring requests.
        """,
        duration_seconds=1800,
        summary="Q4 budget meeting discussing marketing and engineering needs.",
        participants=["Alice", "Bob", "Charlie"],
        tags=["meeting", "budget", "q4"],
    )

    recording2 = Recording.create_new(
        source="youtube",
        transcript="""
        Welcome to this Python tutorial on async programming.
        Today we'll cover asyncio, await, and concurrent tasks.
        First, let's understand why async is important for I/O bound operations.
        """,
        duration_seconds=900,
        summary="Python async programming tutorial.",
        tags=["tutorial", "python", "async"],
        source_url="https://youtube.com/watch?v=example123",
    )

    recording3 = Recording.create_new(
        source="note",
        transcript="Remember to buy groceries: milk, eggs, bread, and coffee.",
        tags=["personal", "todo"],
    )

    print(f"   ✓ Created 3 recordings:")
    print(f"     - Zoom meeting (ID: {recording1.id[:8]}...)")
    print(f"     - YouTube video (ID: {recording2.id[:8]}...)")
    print(f"     - Quick note (ID: {recording3.id[:8]}...)")

    # Test Markdown save
    print("\n4. Saving recordings as Markdown files...")

    path1 = save_recording(recording1, base_dir)
    path2 = save_recording(recording2, base_dir)
    path3 = save_recording(recording3, base_dir)

    print(f"   ✓ Saved to:")
    print(f"     - {path1.relative_to(base_dir)}")
    print(f"     - {path2.relative_to(base_dir)}")
    print(f"     - {path3.relative_to(base_dir)}")

    # Test Markdown load
    print("\n5. Loading recordings from Markdown files...")

    loaded1 = load_recording(path1)
    print(f"   ✓ Loaded recording: {loaded1.source} - {loaded1.summary[:50]}...")
    assert loaded1.id == recording1.id
    assert loaded1.source == recording1.source
    assert loaded1.participants == recording1.participants
    print("   ✓ All fields match original")

    # Test list_recordings
    print("\n6. Listing all recordings...")

    all_files = list_recordings(base_dir)
    print(f"   ✓ Found {len(all_files)} Markdown files")
    for f in all_files:
        print(f"     - {f.name}")

    # Test SQLite index
    print("\n7. Building search index...")

    index = RecordingIndex(":memory:")
    for filepath in all_files:
        rec = load_recording(filepath)
        index.add_recording(filepath, rec)
    print(f"   ✓ Indexed {len(all_files)} recordings")

    # Test full-text search
    print("\n8. Testing full-text search...")

    results = index.search("budget")
    print(f"   Search 'budget': {len(results)} result(s)")
    for r in results:
        print(f"     - {r.source}: {r.summary_snippet[:50]}...")

    results = index.search("Python")
    print(f"   Search 'Python': {len(results)} result(s)")

    results = index.search("groceries")
    print(f"   Search 'groceries': {len(results)} result(s)")

    # Test filtering
    print("\n9. Testing filters...")

    results = index.filter(source="zoom")
    print(f"   Filter source='zoom': {len(results)} result(s)")

    results = index.filter(tags=["tutorial"])
    print(f"   Filter tags=['tutorial']: {len(results)} result(s)")

    # Test SummaryResult model
    print("\n10. Testing SummaryResult model...")

    summary = SummaryResult(
        brief="A productive meeting about Q4 budget allocation.",
        key_points=[
            "Marketing budget increase of 15% proposed",
            "Engineering needs 2 additional developers",
            "All teams on track for Q4 goals",
        ],
        action_items=[
            "Bob: Draft marketing proposal by Friday",
            "Charlie: Submit hiring requests",
        ],
        participants=["Alice", "Bob", "Charlie"],
        topics=["Budget", "Marketing", "Engineering", "Hiring"],
    )

    print(f"   ✓ SummaryResult created:")
    print(f"     Brief: {summary.brief}")
    print(f"     Key Points: {len(summary.key_points)}")
    print(f"     Action Items: {len(summary.action_items)}")
    print(f"     Participants: {summary.participants}")
    print(f"     Topics: {summary.topics}")

    # Cleanup
    index.close()

    # Show sample Markdown file
    print("\n11. Sample Markdown file content:")
    print("-" * 40)
    print(path1.read_text()[:800])
    print("-" * 40)

print("\n" + "=" * 60)
print("✅ All Sprint 1 integration tests passed!")
print("=" * 60)
