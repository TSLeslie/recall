#!/usr/bin/env python3
"""Demo script for Recall Knowledge System with REAL LLM.

This script demonstrates the complete knowledge pipeline using the
actual Qwen2.5-3B model for embeddings and queries.

Run with: python examples/knowledge_demo_real.py
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path

# Set up logging - only show INFO and above, quiet noisy loggers
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("nano-graphrag").setLevel(logging.WARNING)
logging.getLogger("recall.knowledge.graphrag").setLevel(logging.WARNING)

# Demo banner
print("=" * 60)
print("🧠 Recall Knowledge System Demo (Real LLM)")
print("=" * 60)
print()

# Check for model
MODEL_PATH = Path("models/qwen2.5-3b-instruct.gguf")
if not MODEL_PATH.exists():
    print(f"❌ Model not found at {MODEL_PATH}")
    print("   Run: python scripts/download_qwen_model.py")
    exit(1)

print(f"✓ Found model: {MODEL_PATH}")
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
- Engineering needs additional cloud infrastructure budget of $25,000
- Customer support team requesting 2 new hires at $80,000 each

Action items:
1. Alice will review marketing proposal by Friday November 22nd
2. Bob to schedule follow-up with finance team
3. Carol to prepare presentation for board meeting on December 5th

The total Q4 budget request is $242,500.
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
The product is called "Recall Pro" - our AI-powered note-taking application.

Marketing status:
- Landing page finalized at recall.ai/pro
- Email sequences ready for 50,000 subscribers
- Social media content scheduled for 2 weeks

Engineering status:
- Beta testing completed with 98% satisfaction rate
- Performance optimizations reduced load time by 40%
- Security audit passed with no critical issues

Remaining tasks before launch:
- Final QA review by December 10th (David leading)
- Press release draft by December 12th (Eve writing)
- Customer support training December 8-9
- Server scaling prepared for 100,000 concurrent users
            """.strip(),
            summary="Product launch sync - Recall Pro on track for December 15th.",
            participants=["Alice", "David", "Eve"],
            tags=["meeting", "product-launch", "Q4"],
        ),
        Recording(
            id="standup-001",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 9, 30, 0),
            title="Daily Standup",
            transcript="""
Daily standup for November 25th, 2025.

Alice: Yesterday I finished the API documentation. Today I'm working on
the SDK examples. No blockers.

Bob: I completed the database migration scripts. Today focusing on
performance testing. Blocked on getting access to the staging environment.

Carol: Wrapped up the user onboarding flow. Starting on the settings page
today. No blockers but need design review from David.

David: Design review scheduled for 2pm today. Working on the mobile
responsive layouts. No blockers.
            """.strip(),
            summary="Daily standup - team progress on various tasks.",
            participants=["Alice", "Bob", "Carol", "David"],
            tags=["standup", "daily"],
        ),
    ]

    for rec in recordings:
        filepath = save_recording(rec, recordings_dir)
        print(f"  ✓ Created: {filepath.name}")

    print(f"\n  Total: {len(recordings)} recordings")
    print()

    # =========================================================================
    # Step 2: Initialize Real GraphRAG
    # =========================================================================
    print("🔧 Step 2: Initializing knowledge system...")
    print("-" * 40)
    print("  Loading sentence-transformers model (all-MiniLM-L6-v2)...")

    from recall.knowledge.graphrag import RecallGraphRAG
    from recall.knowledge.sync import KnowledgeSync

    graphrag = RecallGraphRAG(working_dir=state_dir / "graphrag")
    sync = KnowledgeSync(graphrag, state_file=state_dir / "sync_state.json")

    print("  ✓ GraphRAG initialized")
    print()

    # =========================================================================
    # Step 3: Sync recordings to knowledge base
    # =========================================================================
    print("🔄 Step 3: Syncing recordings to knowledge base...")
    print("-" * 40)

    result = sync.sync(recordings_dir)
    print(f"  ✓ Added: {result.added} recordings")
    print(f"  ✓ Modified: {result.modified}")
    print(f"  ✓ Errors: {result.errors}")
    print()

    # =========================================================================
    # Step 4: Query with Real LLM
    # =========================================================================
    print("❓ Step 4: Querying with Qwen2.5-3B...")
    print("-" * 40)
    print()

    from recall.knowledge.query import ask

    questions = [
        "When is the product launch scheduled?",
        "What is the total Q4 budget request?",
        "Who is blocked and why?",
        "What are Alice's tasks?",
    ]

    for question in questions:
        print(f"  Q: {question}")
        print("  🤔 Thinking...")

        try:
            answer = ask(question, graphrag)
            # Truncate long responses
            response = answer.response
            if len(response) > 300:
                response = response[:300] + "..."
            print(f"  A: {response}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")

        print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
