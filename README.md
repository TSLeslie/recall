# Recall - Local AI Note-Taking & Memory Bank

A local-first, privacy-focused AI-powered system for capturing, transcribing, summarizing, and searching audio from meetings, videos, and voice notes. All processing happens on your Mac using local AI models.

## ✨ Features

### 🎙️ Audio Capture
- **System Audio** - Record from Zoom, YouTube, or any app (via BlackHole)
- **Microphone** - Direct voice recording
- **YouTube** - Download and transcribe YouTube videos
- **Auto-Detection** - Automatically start recording when audio sources are detected

### 🤖 Local AI Processing
- **Whisper** - OpenAI's speech recognition model for accurate transcription
- **Qwen2.5-3B** - Local LLM for summarization via llama-cpp-python
- **Graph RAG** - Semantic search across all your notes using nano-graphrag

### 📝 Note Management
- **Quick Notes** - Create text notes that integrate with your knowledge base
- **Voice Notes** - Record and transcribe voice memos
- **Markdown Storage** - Human-readable files with YAML frontmatter
- **SQLite Index** - Fast full-text search

### 🖥️ macOS Menu Bar App
- **One-Click Recording** - Start/stop from the menu bar
- **Global Hotkeys** - ⌘⇧R to toggle recording
- **Notifications** - Recording status and completion alerts
- **Auto-Recording** - Trigger recording when Zoom/Meet detected

## 🚀 Getting Started

### Prerequisites

- **macOS 12.0+** (Monterey or later)
- **Python 3.11+**
- **BlackHole** (for system audio capture): `brew install blackhole-2ch`

### Installation

```bash
# Clone the repository
git clone https://github.com/TSLeslie/recall.git
cd recall

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-macos.txt  # rumps, pynput for menu bar

# Install in development mode
pip install -e .
```

### Download AI Models

```bash
# Download Whisper model (automatic on first use)
# Download Qwen2.5-3B for summarization
python scripts/download_qwen_model.py
```

### Run the Menu Bar App

```bash
python src/recall/app/launcher.py
```

Or use the CLI:

```bash
recall --help
recall transcribe audio.mp3
recall record --duration 60
recall search "meeting notes"
```

## 📁 Project Structure

```
recall/
├── src/recall/
│   ├── app/              # macOS menu bar app
│   │   ├── menubar.py    # Menu bar UI (rumps)
│   │   ├── hotkeys.py    # Global keyboard shortcuts
│   │   ├── recording.py  # Recording controller
│   │   └── notifications.py
│   ├── capture/          # Audio capture
│   │   ├── recorder.py   # Microphone/system audio
│   │   ├── youtube.py    # YouTube download
│   │   ├── detector.py   # Audio source detection
│   │   └── monitor.py    # Auto-detection monitoring
│   ├── knowledge/        # Graph RAG
│   │   ├── graphrag.py   # nano-graphrag wrapper
│   │   ├── ingest.py     # Document ingestion
│   │   └── query.py      # Semantic search
│   ├── notes/            # Note management
│   │   ├── quick_note.py # Text notes
│   │   └── voice_note.py # Voice memos
│   ├── storage/          # Persistence
│   │   ├── models.py     # Pydantic data models
│   │   ├── markdown.py   # Markdown file I/O
│   │   └── index.py      # SQLite search index
│   ├── pipeline/         # Processing pipeline
│   ├── analyze.py        # LLM summarization
│   ├── transcribe.py     # Whisper transcription
│   └── cli.py            # Command-line interface
├── tests/                # 570 tests, 80%+ coverage
├── examples/             # Demo scripts
├── docs/                 # Documentation
└── models/               # Local AI models (gitignored)
```

## 🧪 Development

### Dev Container

This project includes a VS Code Dev Container for consistent development:

```bash
# Open in VS Code and click "Reopen in Container"
# Or use the command palette: Dev Containers: Reopen in Container
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/recall --cov-report=term-missing

# Run specific test file
pytest tests/test_knowledge_query.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## 📊 Data Storage

All data is stored locally in `~/.recall/`:

```
~/.recall/
├── models/           # AI models (~2GB)
├── recordings/       # Markdown files organized by date
│   └── 2025-11/
│       └── 25/
│           └── zoom_meeting.md
├── knowledge/        # Graph RAG index
└── config.json       # Settings
```

### Recording Format

Recordings are stored as Markdown with YAML frontmatter:

```markdown
---
id: abc123-def456
source: zoom
timestamp: 2025-11-25T14:30:00
duration_seconds: 3600
summary: Weekly team standup discussing Q4 roadmap
tags: [meeting, team, roadmap]
---

[Full transcript here...]
```

## 🔒 Privacy

- **100% Local** - All processing happens on your Mac
- **No Cloud** - Audio and transcripts never leave your device
- **Your Data** - Stored as readable Markdown files you control

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Transcription | OpenAI Whisper |
| Summarization | Qwen2.5-3B via llama-cpp-python |
| Knowledge Graph | nano-graphrag |
| Embeddings | sentence-transformers |
| Menu Bar | rumps |
| Hotkeys | pynput |
| Storage | Markdown + SQLite |
| CLI | Typer + Rich |
| Testing | pytest (570 tests) |

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

1. Fork the repository
2. Create a feature branch
3. Write tests (TDD encouraged)
4. Submit a pull request

