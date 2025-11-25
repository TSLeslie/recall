#!/usr/bin/env python3
"""Simple demo for Recall with real Qwen LLM.

This demo shows:
1. Recording storage and retrieval
2. Direct LLM Q&A over transcripts
3. No complex GraphRAG pipeline - just simple RAG

Run with: python examples/simple_llm_demo.py
"""

import tempfile
from datetime import datetime
from pathlib import Path

print("=" * 60)
print("🧠 Recall Simple LLM Demo")
print("=" * 60)
print()

# Check for model
MODEL_PATH = Path("models/qwen2.5-3b-instruct.gguf")
if not MODEL_PATH.exists():
    print(f"❌ Model not found at {MODEL_PATH}")
    exit(1)

print(f"✓ Found model: {MODEL_PATH}")
print()

# =========================================================================
# Step 1: Create sample recordings
# =========================================================================
print("📝 Step 1: Creating sample recordings...")
print("-" * 40)

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    recordings_dir = temp_path / "recordings"
    recordings_dir.mkdir()

    from recall.storage.markdown import save_recording
    from recall.storage.models import Recording

    recordings = [
        Recording(
            id="meeting-001",
            source="zoom",
            timestamp=datetime(2025, 11, 20, 9, 0, 0),
            title="Q4 Planning Meeting",
            transcript="""Q4 Planning Meeting - November 20, 2025

Attendees: Alice (PM), Bob (Engineering), Carol (Marketing)

Alice: Welcome everyone. Let's discuss our Q4 budget allocation.

Carol: Marketing is requesting a 15% budget increase from $50,000 to $57,500 
for our product launch campaign. We need this for paid ads and influencer 
partnerships.

Bob: Engineering needs $25,000 for additional cloud infrastructure to handle 
the expected traffic spike at launch.

Alice: That brings our total Q4 budget request to $242,500. I'll prepare the 
board presentation for December 5th.

Action Items:
1. Alice: Review marketing proposal by Friday
2. Bob: Schedule meeting with finance team
3. Carol: Finalize campaign assets by November 28th

Meeting adjourned at 10:15 AM.""",
            summary="Q4 planning - total budget request $242,500",
            participants=["Alice", "Bob", "Carol"],
        ),
        Recording(
            id="meeting-002",
            source="zoom",
            timestamp=datetime(2025, 11, 22, 10, 0, 0),
            title="Product Launch Sync",
            transcript="""Product Launch Sync - November 22, 2025

Attendees: Alice, David (QA), Eve (Marketing)

Alice: Launch date is confirmed for December 15th. Status updates?

David: Beta testing completed with 98% satisfaction. Performance is up 40%.
Security audit passed. Final QA review scheduled for December 10th.

Eve: All marketing assets ready. Landing page at recall.ai/pro is live.
Email sequences queued for 50,000 subscribers. Press release draft due 
December 12th.

Alice: Perfect. Customer support training is December 8-9. We're on track!

The product name is "Recall Pro" - our AI-powered note-taking application.""",
            summary="Recall Pro launch on track for December 15th",
            participants=["Alice", "David", "Eve"],
        ),
        Recording(
            id="standup-001",
            source="zoom",
            timestamp=datetime(2025, 11, 25, 9, 30, 0),
            title="Daily Standup",
            transcript="""Daily Standup - November 25, 2025

Alice: Yesterday I finished API documentation. Today working on SDK examples.

Bob: Completed database migration scripts. Today doing performance testing.
I'm BLOCKED - waiting for staging environment access from IT.

Carol: Wrapped up user onboarding flow. Starting settings page today.
Need design review from David at 2pm.

David: Will do Carol's design review at 2pm. Working on mobile layouts.""",
            summary="Daily standup - Bob blocked on staging access",
            participants=["Alice", "Bob", "Carol", "David"],
        ),
    ]

    for rec in recordings:
        filepath = save_recording(rec, recordings_dir)
        print(f"  ✓ {rec.title}")

    print()

    # =========================================================================
    # Step 2: Load LLM
    # =========================================================================
    print("🔧 Step 2: Loading Qwen2.5-3B model...")
    print("-" * 40)

    from llama_cpp import Llama

    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=4096,
        n_threads=4,
        verbose=False,
    )
    print("  ✓ Model loaded successfully")
    print()

    # =========================================================================
    # Step 3: Build context from recordings
    # =========================================================================
    print("📚 Step 3: Building knowledge context...")
    print("-" * 40)

    from recall.storage.markdown import list_recordings, load_recording

    context_parts = []
    for filepath in list_recordings(recordings_dir):
        rec = load_recording(filepath)
        context_parts.append(
            f"=== {rec.title} ({rec.timestamp.strftime('%Y-%m-%d')}) ===\n{rec.transcript}"
        )

    full_context = "\n\n".join(context_parts)
    print(f"  ✓ Loaded {len(context_parts)} recordings")
    print(f"  ✓ Total context: {len(full_context)} characters")
    print()

    # =========================================================================
    # Step 4: Ask questions with real LLM
    # =========================================================================
    print("❓ Step 4: Asking questions (Real LLM)...")
    print("-" * 40)
    print()

    def ask_question(question: str) -> str:
        """Ask a question using RAG with the LLM."""
        prompt = f"""Based on the following meeting transcripts, answer the question concisely.

TRANSCRIPTS:
{full_context}

QUESTION: {question}

ANSWER:"""

        response = llm(
            prompt,
            max_tokens=200,
            temperature=0.3,
            stop=["\n\n", "QUESTION:", "TRANSCRIPTS:"],
        )
        return response["choices"][0]["text"].strip()

    questions = [
        "When is the product launch date?",
        "What is the total Q4 budget request?",
        "Who is blocked and why?",
        "What is Alice working on today?",
        "What is the name of the product being launched?",
    ]

    for q in questions:
        print(f"  Q: {q}")
        print("  🤔 Thinking...", end=" ", flush=True)
        answer = ask_question(q)
        print(f"\r  A: {answer}")
        print()

    print("=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
