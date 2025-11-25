#!/usr/bin/env python3
"""Demo script for Recall Knowledge System (Sprint 3).

This script demonstrates the complete knowledge pipeline:
1. Creating sample recordings
2. Ingesting them into the knowledge base
3. Syncing with change detection
4. Querying the knowledge base

Run with: python examples/knowledge_demo.py
"""

import tempfile
from datetime import datetime
from pathlib import Path

# Demo banner
print("=" * 60)
print("🧠 Recall Knowledge System Demo")
print("=" * 60)
print()

# Create a temporary directory for the demo
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    recordings_dir = temp_path / "recordings"
    recordings_dir.mkdir()
    state_dir = temp_path / "state"
    state_dir.mkdir()

    # =========================================================================
    # Step 1: Create sample recordings
    # =========================================================================
    print("📝 Step 1: Creating sample recordings...")
    print("-" * 40)

    from recall.storage.markdown import save_recording
    from recall.storage.models import Recording

    recordings = [
        Recording(
            id="meeting-001",
            source="zoom",
            timestamp=datetime(2025, 11, 20, 9, 0, 0),
            title="Q4 Planning Meeting",
            transcript="""
Welcome to the Q4 planning meeting. Today we'll discuss the budget allocation 
for next quarter. The marketing team has requested a 15% increase in their 
budget for the product launch campaign.

Key discussion points:
- Marketing budget increase from $50,000 to $57,500
- Engineering needs additional cloud infrastructure budget
- Customer support team requesting 2 new hires

Action items:
1. Review marketing proposal by Friday
2. Schedule follow-up with finance team
3. Prepare presentation for board meeting on December 5th
            """.strip(),
            summary="Q4 planning meeting covering budget allocation and marketing requests.",
            participants=["Alice", "Bob", "Carol"],
            tags=["meeting", "budget", "Q4"],
        ),
        Recording(
            id="meeting-002",
            source="zoom",
            timestamp=datetime(2025, 11, 22, 10, 0, 0),
            title="Product Launch Sync",
            transcript="""
Product launch update: We're on track for the December 15th launch date.
The marketing team has finalized all campaign assets including the landing page,
email sequences, and social media content.

Engineering status:
- Beta testing completed with 98% satisfaction rate
- Performance optimizations reduced load time by 40%
- Security audit passed with no critical issues

Remaining tasks before launch:
- Final QA review by December 10th
- Press release draft by December 12th
- Customer support training scheduled for next week
- Server scaling prepared for expected traffic spike
            """.strip(),
            summary="Product launch sync - on track for December 15th launch.",
            participants=["Alice", "David", "Eve"],
            tags=["meeting", "product-launch", "Q4"],
        ),
        Recording(
            id="youtube-001",
            source="youtube",
            timestamp=datetime(2025, 11, 21, 14, 30, 0),
            title="Python Best Practices 2025",
            transcript="""
Welcome to Python Best Practices for 2025. In this tutorial, we'll cover 
the most important practices for writing clean, maintainable Python code.

First, always use type hints in your function signatures. Type hints improve
code readability and enable better IDE support and static analysis.

Second, prefer dataclasses for data structures. They reduce boilerplate and
provide automatic __init__, __repr__, and comparison methods.

Third, use async/await for I/O-bound operations. This is especially important
for web applications and network calls.

Fourth, structure your projects with proper packaging. Use pyproject.toml
for modern Python packaging configuration.

Finally, always write tests for your code. Use pytest as your testing framework
and aim for at least 80% code coverage.
            """.strip(),
            summary="Tutorial on Python best practices including type hints and async.",
            tags=["python", "tutorial", "programming"],
        ),
    ]

    for rec in recordings:
        filepath = save_recording(rec, recordings_dir)
        print(f"  ✓ Created: {filepath.name}")

    print(f"\n  Total: {len(recordings)} recordings saved to {recordings_dir}")
    print()

    # =========================================================================
    # Step 2: Demonstrate chunking
    # =========================================================================
    print("✂️  Step 2: Demonstrating transcript chunking...")
    print("-" * 40)

    from recall.knowledge.ingest import chunk_transcript

    sample_text = recordings[0].transcript
    chunks = chunk_transcript(sample_text, chunk_size=500, overlap=100)

    print(f"  Original text: {len(sample_text)} characters")
    print(f"  Chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        preview = chunk[:80].replace("\n", " ") + "..."
        print(f'    Chunk {i + 1}: {len(chunk)} chars - "{preview}"')
    print()

    # =========================================================================
    # Step 3: Knowledge Sync (mocked GraphRAG)
    # =========================================================================
    print("🔄 Step 3: Syncing recordings to knowledge base...")
    print("-" * 40)

    from unittest.mock import AsyncMock, MagicMock, patch

    # Create mock GraphRAG for demo (real one requires LLM model)
    with (
        patch("recall.knowledge.graphrag.SentenceTransformer") as mock_st,
        patch("recall.knowledge.graphrag.GraphRAG") as mock_rag_class,
    ):

        mock_embedding = MagicMock()
        mock_embedding.encode.return_value = [[0.1] * 384]
        mock_st.return_value = mock_embedding

        mock_rag = MagicMock()
        mock_rag.insert = AsyncMock()
        mock_rag.query = AsyncMock(return_value="Mock response for demo")
        mock_rag_class.return_value = mock_rag

        from recall.knowledge.graphrag import RecallGraphRAG
        from recall.knowledge.sync import KnowledgeSync

        graphrag = RecallGraphRAG(working_dir=state_dir / "graphrag")
        sync = KnowledgeSync(graphrag, state_file=state_dir / "sync_state.json")

        # Initial sync
        result = sync.sync(recordings_dir)
        print(f"  Initial sync complete:")
        print(f"    ✓ Added: {result.added} recordings")
        print(f"    ✓ Modified: {result.modified}")
        print(f"    ✓ Deleted: {result.deleted}")
        print(f"    ✓ Errors: {result.errors}")
        print()

        # Show state
        print(f"  Sync state saved to: {sync.state_file}")
        print(f"  Last sync: {sync.last_sync}")
        print(f"  Files tracked: {len(sync.file_hashes)}")
        print()

        # =====================================================================
        # Step 4: Demonstrate change detection
        # =====================================================================
        print("🔍 Step 4: Detecting changes...")
        print("-" * 40)

        # Modify a file
        md_files = list(recordings_dir.rglob("*.md"))
        modified_file = md_files[0]
        original_content = modified_file.read_text()
        modified_file.write_text(original_content + "\n\n## Additional Notes\nThis was updated!")

        # Check for changes
        changes = sync.get_pending_changes(recordings_dir)
        print(f"  Changes detected:")
        print(f"    New files: {len(changes.new)}")
        print(f"    Modified files: {len(changes.modified)}")
        print(f"    Deleted files: {len(changes.deleted)}")
        print(f"    Has changes: {changes.has_changes}")
        print()

        # Incremental sync
        result2 = sync.sync(recordings_dir)
        print(f"  Incremental sync:")
        print(f"    ✓ Added: {result2.added}")
        print(f"    ✓ Modified: {result2.modified}")
        print(f"    ✓ Deleted: {result2.deleted}")
        print()

        # =====================================================================
        # Step 5: Query the knowledge base
        # =====================================================================
        print("❓ Step 5: Querying the knowledge base...")
        print("-" * 40)

        from recall.knowledge.query import ask

        # Configure mock to return realistic responses
        questions = [
            ("When is the product launch?", "The product launch is scheduled for December 15th."),
            (
                "What is the marketing budget?",
                "The marketing budget is being increased by 15% from $50,000 to $57,500.",
            ),
            (
                "What Python practices were covered?",
                "The tutorial covered type hints, dataclasses, async/await, and pytest testing.",
            ),
        ]

        for question, mock_answer in questions:
            mock_rag.query = AsyncMock(return_value=mock_answer)
            answer = ask(question, graphrag)
            print(f"  Q: {question}")
            print(f"  A: {answer.response}")
            if answer.follow_up_questions:
                print(f"  📌 Follow-ups: {answer.follow_up_questions[:2]}")
            print()

    # =========================================================================
    # Step 6: Summary
    # =========================================================================
    print("=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print()
    print("The Recall Knowledge System provides:")
    print("  • Recording storage with Markdown + YAML frontmatter")
    print("  • Intelligent transcript chunking with overlap")
    print("  • Incremental sync with change detection")
    print("  • Natural language Q&A (requires LLM model)")
    print("  • Follow-up question generation")
    print()
    print("To use with real LLM, ensure you have the Qwen model:")
    print("  python scripts/download_qwen_model.py")
    print()
