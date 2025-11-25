# Recall - Implementation Tickets with Acceptance Criteria

## Overview

This document contains detailed tickets with acceptance criteria for building Recall, a local AI-powered note-taking and memory bank system.

---

## Epic 1: Storage & Data Models

**Goal:** Define data structures and Markdown-based persistence as the foundation for all other features.

### Ticket 1.1: Recording Data Model

**Create `src/recall/storage/models.py` with Pydantic models**

**Acceptance Criteria:**
- [ ] `Recording` model with fields:
  - `id: str` - UUID, auto-generated
  - `source: Literal["zoom", "youtube", "microphone", "system", "note"]`
  - `timestamp: datetime` - when recording started
  - `duration_seconds: Optional[int]`
  - `transcript: str`
  - `summary: Optional[str]`
  - `participants: Optional[List[str]]`
  - `tags: List[str]` - default empty list
  - `source_url: Optional[str]` - for YouTube
  - `audio_path: Optional[Path]` - path to audio file if retained
- [ ] `Recording.create_new()` class method that auto-generates ID and sets timestamp to now
- [ ] Model validates that `source` is one of allowed values
- [ ] Model serializes to/from dict for YAML frontmatter
- [ ] All fields have appropriate type hints
- [ ] Unit tests for model creation, validation, serialization

---

### Ticket 1.2: Markdown Storage

**Create `src/recall/storage/markdown.py` for Markdown file I/O**

**Acceptance Criteria:**
- [ ] `save_recording(recording: Recording, base_dir: Path) -> Path`
  - Saves to `{base_dir}/YYYY-MM/{timestamp}_{source}.md`
  - Creates directory structure if not exists
  - Writes YAML frontmatter with all metadata fields
  - Writes transcript as Markdown body
  - Returns path to created file
- [ ] `load_recording(filepath: Path) -> Recording`
  - Parses YAML frontmatter using `pyyaml`
  - Extracts transcript from body
  - Returns populated Recording model
  - Raises `ValueError` for malformed files
- [ ] `list_recordings(base_dir: Path) -> List[Path]`
  - Returns all `.md` files in base_dir recursively
  - Sorted by filename (chronological)
- [ ] Default base_dir is `~/.recall/recordings/`
- [ ] Frontmatter uses `---` delimiters
- [ ] Unit tests for save, load, round-trip, error handling

---

### Ticket 1.3: SQLite Search Index

**Create `src/recall/storage/index.py` for fast search and filtering**

**Acceptance Criteria:**
- [ ] `RecordingIndex` class with constructor taking db path (or `:memory:`)
- [ ] `add_recording(filepath: Path, recording: Recording)` - indexes a recording
- [ ] `remove_recording(filepath: Path)` - removes from index
- [ ] `search(query: str) -> List[SearchResult]` - full-text search on transcript/summary
- [ ] `filter(source: str = None, start_date: date = None, end_date: date = None, tags: List[str] = None) -> List[SearchResult]`
- [ ] `SearchResult` includes: filepath, source, timestamp, summary snippet, relevance score
- [ ] SQLite FTS5 for full-text search
- [ ] `rebuild_index(base_dir: Path)` - scans all Markdown files and rebuilds index
- [ ] Index stored at `~/.recall/index.db` by default
- [ ] Unit tests with in-memory database

---

### Ticket 1.4: Structured Summary Generation

**Extend `src/recall/analyze.py` for structured summaries**

**Acceptance Criteria:**
- [ ] `generate_summary(transcript: str, model_path: str) -> SummaryResult`
- [ ] `SummaryResult` model with fields:
  - `brief: str` - 1-2 sentence summary
  - `key_points: List[str]` - bullet points
  - `action_items: List[str]` - extracted action items
  - `participants: List[str]` - detected participant names
  - `topics: List[str]` - main topics discussed
- [ ] Uses structured prompt to extract all fields
- [ ] Handles transcripts up to 32k tokens (Qwen context window)
- [ ] Falls back gracefully if LLM response is malformed
- [ ] Unit tests with mocked LLM responses

---

## Epic 2: Audio Capture Layer

**Goal:** Enable audio capture from multiple sources.

### Ticket 2.1: Microphone Recording

**Create `src/recall/capture/recorder.py` for microphone capture**

**Acceptance Criteria:**
- [ ] `Recorder` class with constructor taking `output_dir: Path`
- [ ] `start_recording() -> None` - begins recording from default input device
- [ ] `stop_recording() -> Path` - stops and returns path to WAV file
- [ ] `record(duration_seconds: int) -> Path` - record for fixed duration
- [ ] Records at 16kHz mono (Whisper's preferred format)
- [ ] Saves as WAV with timestamp filename: `{output_dir}/mic_{timestamp}.wav`
- [ ] `is_recording: bool` property
- [ ] `get_input_devices() -> List[AudioDevice]` - list available inputs
- [ ] `set_input_device(device_id: int)` - select specific device
- [ ] Handles device not found errors gracefully
- [ ] Unit tests with mocked sounddevice

---

### Ticket 2.2: YouTube Audio Extraction

**Create `src/recall/capture/youtube.py` for YouTube download**

**Acceptance Criteria:**
- [ ] `download_audio(url: str, output_dir: Path) -> YouTubeResult`
- [ ] `YouTubeResult` model with fields:
  - `audio_path: Path`
  - `title: str`
  - `duration_seconds: int`
  - `channel: str`
  - `upload_date: date`
  - `url: str`
- [ ] Downloads audio only (not video) in best quality
- [ ] Converts to WAV 16kHz mono for Whisper compatibility
- [ ] Filename: `{output_dir}/youtube_{video_id}_{timestamp}.wav`
- [ ] Validates URL is a valid YouTube link
- [ ] Raises `YouTubeDownloadError` on failure with descriptive message
- [ ] Supports playlists: `download_playlist(url) -> List[YouTubeResult]`
- [ ] Unit tests with mocked yt-dlp

---

### Ticket 2.3: System Audio Monitor

**Create `src/recall/capture/monitor.py` for background audio detection**

**Acceptance Criteria:**
- [ ] `AudioMonitor` class for detecting system audio
- [ ] `start_monitoring(callback: Callable[[AudioEvent], None])` - begins monitoring
- [ ] `stop_monitoring()` - stops monitoring
- [ ] `AudioEvent` model: `type: Literal["started", "stopped"]`, `timestamp: datetime`, `source_hint: Optional[str]`
- [ ] Detects audio via amplitude threshold on BlackHole loopback device
- [ ] Configurable silence threshold and duration before "stopped" event
- [ ] `is_monitoring: bool` property
- [ ] `is_blackhole_available() -> bool` - checks if BlackHole is installed
- [ ] Unit tests with mocked sounddevice

---

### Ticket 2.4: Application Detector

**Create `src/recall/capture/detector.py` for detecting audio-related apps**

**Acceptance Criteria:**
- [ ] `get_running_audio_apps() -> List[AudioApp]`
- [ ] `AudioApp` model: `name: str`, `pid: int`, `category: Literal["meeting", "media", "browser", "other"]`
- [ ] Detects: Zoom, Microsoft Teams, Google Meet (via browser), Slack Huddle
- [ ] Detects: YouTube, Spotify, Apple Music, VLC
- [ ] `is_meeting_active() -> bool` - returns True if any meeting app running
- [ ] `is_media_playing() -> bool` - returns True if media app in foreground
- [ ] macOS-specific implementation using `psutil` + `NSWorkspace` via pyobjc
- [ ] Unit tests with mocked process list

---

### Ticket 2.5: BlackHole Setup Documentation

**Create setup documentation for macOS audio capture**

**Acceptance Criteria:**
- [ ] `docs/AUDIO_SETUP.md` with:
  - BlackHole installation instructions (Homebrew)
  - Multi-Output Device configuration steps with screenshots
  - Troubleshooting common issues
  - Permissions required (microphone access)
- [ ] `scripts/check_audio_setup.py` that verifies:
  - BlackHole is installed
  - Multi-Output Device is configured
  - Permissions are granted
  - Prints actionable error messages if not

---

## Epic 3: Ingestion Pipeline

**Goal:** Orchestrate the full flow from audio to searchable knowledge.

### Ticket 3.1: Core Ingestion Pipeline

**Create `src/recall/pipeline/ingest.py` for audio processing**

**Acceptance Criteria:**
- [ ] `ingest_audio(audio_path: Path, source: str, **metadata) -> Recording`
- [ ] Pipeline steps:
  1. Transcribe audio using Whisper
  2. Generate structured summary using LLM
  3. Create Recording model with all metadata
  4. Save as Markdown file
  5. Update SQLite index
- [ ] Returns the created Recording
- [ ] `IngestConfig` dataclass for configuring:
  - `whisper_model: str` (default "base")
  - `llm_model_path: Path`
  - `storage_dir: Path`
- [ ] Handles errors at each step gracefully
- [ ] Unit tests with mocked Whisper and LLM

---

### Ticket 3.2: Progress Callbacks and Error Handling

**Add progress reporting to ingestion pipeline**

**Acceptance Criteria:**
- [ ] `ingest_audio(..., on_progress: Callable[[ProgressEvent], None])`
- [ ] `ProgressEvent` model:
  - `step: Literal["transcribing", "summarizing", "saving", "indexing", "complete", "error"]`
  - `progress: float` (0.0 to 1.0)
  - `message: str`
  - `error: Optional[str]`
- [ ] Progress callback invoked at each pipeline step
- [ ] On error: callback with error details, partial results saved if possible
- [ ] `IngestResult` includes: `success: bool`, `recording: Optional[Recording]`, `errors: List[str]`
- [ ] Unit tests for progress callbacks and error scenarios

---

### Ticket 3.3: Directory Watcher

**Create `src/recall/pipeline/watch.py` for auto-ingestion**

**Acceptance Criteria:**
- [ ] `DirectoryWatcher` class monitoring a directory for new audio files
- [ ] `start_watching(input_dir: Path, on_new_file: Callable[[Path], None])`
- [ ] `stop_watching()`
- [ ] Detects new `.wav`, `.mp3`, `.m4a`, `.webm` files
- [ ] Debounces rapid file changes (wait for file to be fully written)
- [ ] `auto_ingest_watcher(input_dir: Path, config: IngestConfig)` - convenience function that auto-ingests new files
- [ ] Uses `watchdog` library or polling fallback
- [ ] Unit tests with temporary directory

---

## Epic 4: Graph RAG & Knowledge Search

**Goal:** Enable semantic search and question-answering over all recordings.

### Ticket 4.1: GraphRAG Wrapper

**Create `src/recall/knowledge/graphrag.py` wrapping nano-graphrag**

**Acceptance Criteria:**
- [ ] `RecallGraphRAG` class wrapping `nano_graphrag.GraphRAG`
- [ ] Constructor takes `working_dir: Path`, auto-configures for local models
- [ ] Uses Qwen2.5-3B via llama-cpp-python for LLM operations
- [ ] Uses sentence-transformers for embeddings (all-MiniLM-L6-v2)
- [ ] `insert(text: str, metadata: dict)` - add document to graph
- [ ] `query(question: str) -> QueryResult` - semantic search
- [ ] `QueryResult` model: `answer: str`, `sources: List[SourceReference]`, `confidence: float`
- [ ] `SourceReference`: `filepath: Path`, `excerpt: str`, `relevance: float`
- [ ] Working directory defaults to `~/.recall/graphrag/`
- [ ] Unit tests with mocked LLM and embeddings

---

### Ticket 4.2: Recording Ingestion to GraphRAG

**Create `src/recall/knowledge/ingest.py` for adding recordings to knowledge base**

**Acceptance Criteria:**
- [ ] `ingest_recording(recording: Recording, graphrag: RecallGraphRAG)`
- [ ] Chunks transcript into ~500 token segments with overlap
- [ ] Each chunk includes metadata: source, timestamp, summary
- [ ] `ingest_all(base_dir: Path, graphrag: RecallGraphRAG)` - bulk ingest all recordings
- [ ] Tracks which recordings already ingested (avoids duplicates)
- [ ] `sync_knowledge_base(base_dir: Path, graphrag: RecallGraphRAG)` - adds new, removes deleted
- [ ] Unit tests with mock GraphRAG

---

### Ticket 4.3: Query Interface

**Create `src/recall/knowledge/query.py` for natural language search**

**Acceptance Criteria:**
- [ ] `ask(question: str, graphrag: RecallGraphRAG) -> Answer`
- [ ] `Answer` model:
  - `response: str` - natural language answer
  - `sources: List[Source]` - referenced recordings
  - `follow_up_questions: List[str]` - suggested related questions
- [ ] `Source`: `recording_path: Path`, `excerpt: str`, `timestamp: datetime`
- [ ] `search(keywords: str, graphrag: RecallGraphRAG) -> List[SearchHit]` - keyword search
- [ ] Combines GraphRAG results with SQLite FTS for hybrid search
- [ ] Unit tests with mock GraphRAG

---

### Ticket 4.4: Incremental Knowledge Updates

**Implement efficient incremental updates to knowledge base**

**Acceptance Criteria:**
- [ ] `KnowledgeSync` class tracking sync state
- [ ] Stores last sync timestamp and file hashes
- [ ] `get_pending_changes(base_dir: Path) -> ChangeSet`
- [ ] `ChangeSet`: `new: List[Path]`, `modified: List[Path]`, `deleted: List[Path]`
- [ ] Only processes changed files on sync
- [ ] State persisted to `~/.recall/sync_state.json`
- [ ] `force_rebuild()` - full re-index ignoring state
- [ ] Unit tests for change detection

---

## Epic 5: Quick Notes

**Goal:** Enable rapid capture of personal notes via voice or text.

### Ticket 5.1: Text Quick Notes

**Create `src/recall/notes/quick_note.py` for text notes**

**Acceptance Criteria:**
- [ ] `create_note(content: str, tags: List[str] = None) -> Recording`
- [ ] Creates Recording with `source="note"`
- [ ] Saves to `~/.recall/notes/YYYY-MM/{timestamp}_note.md`
- [ ] Auto-generates brief summary using LLM (or first 100 chars if short)
- [ ] `append_to_note(filepath: Path, content: str)` - add to existing note
- [ ] `list_notes(base_dir: Path) -> List[Recording]`
- [ ] Notes are indexed and searchable like recordings
- [ ] Unit tests for note creation and retrieval

---

### Ticket 5.2: Voice Quick Notes

**Create `src/recall/notes/voice_note.py` for voice notes**

**Acceptance Criteria:**
- [ ] `record_voice_note(duration_seconds: int = 60) -> Recording`
- [ ] Records from microphone, transcribes, saves as note
- [ ] `start_voice_note() -> None` and `stop_voice_note() -> Recording` for variable length
- [ ] Auto-generates summary from transcription
- [ ] Audio file optionally retained (configurable)
- [ ] Saves to `~/.recall/notes/YYYY-MM/{timestamp}_voice.md`
- [ ] Unit tests with mocked recorder and Whisper

---

### Ticket 5.3: Notes Integration with Knowledge Base

**Integrate notes into GraphRAG**

**Acceptance Criteria:**
- [ ] Notes automatically ingested to GraphRAG on creation
- [ ] Notes searchable alongside recordings in `ask()` and `search()`
- [ ] Notes appear in query source references
- [ ] `sync_knowledge_base()` includes notes directory
- [ ] Unit tests verifying notes in search results

---

## Epic 6: CLI Interface

**Goal:** Provide command-line access to all Recall features.

### Ticket 6.1: Core CLI Commands

**Create `src/recall/cli.py` using Typer**

**Acceptance Criteria:**
- [ ] `recall record` - start/stop microphone recording
  - `--duration` - record for fixed time
  - `--device` - select input device
- [ ] `recall import <path>` - import audio file or YouTube URL
  - Auto-detects YouTube URLs vs local files
- [ ] `recall ingest <path>` - process audio through pipeline
- [ ] `recall list` - list all recordings
  - `--source` - filter by source
  - `--since` - filter by date
  - `--limit` - max results
- [ ] `recall search <query>` - full-text search
- [ ] `recall ask <question>` - natural language query
- [ ] All commands have `--help` with examples
- [ ] Unit tests for CLI argument parsing

---

### Ticket 6.2: CLI Entry Point

**Configure CLI as installable command**

**Acceptance Criteria:**
- [ ] Add to `pyproject.toml`:
  ```toml
  [project.scripts]
  recall = "recall.cli:app"
  ```
- [ ] `pip install -e .` makes `recall` command available
- [ ] `recall --version` shows version
- [ ] `recall --help` shows all commands
- [ ] Works in dev container after install

---

### Ticket 6.3: Rich Output Formatting

**Add formatted output using Rich**

**Acceptance Criteria:**
- [ ] `--format` option: `table` (default), `json`, `markdown`
- [ ] Table output with colors and borders for `list`, `search`
- [ ] Syntax-highlighted JSON for `--format json`
- [ ] Progress bars for long operations (ingest, sync)
- [ ] Spinners for operations with unknown duration
- [ ] Error messages in red with suggestions
- [ ] Unit tests for output formatting

---

## Epic 7: macOS Menu Bar App

**Goal:** Native desktop experience for effortless capture.

### Ticket 7.1: Basic Menu Bar App

**Create `src/recall/app/menubar.py` using rumps**

**Acceptance Criteria:**
- [ ] App appears in macOS menu bar with icon
- [ ] Status indicator: 🎤 idle, 🔴 recording, ⚙️ processing
- [ ] Menu items:
  - "Start Recording" / "Stop Recording" (toggles)
  - "Quick Note..." (opens text input)
  - "Voice Note" (records until clicked again)
  - Separator
  - "Search..." (opens search dialog)
  - "Open Library" (opens Finder to recordings folder)
  - Separator
  - "Settings..."
  - "Quit"
- [ ] App runs as background process
- [ ] Unit tests for menu state changes

---

### Ticket 7.2: Recording Controls

**Implement recording functionality in menu bar**

**Acceptance Criteria:**
- [ ] "Start Recording" begins microphone capture
- [ ] Menu icon changes to 🔴 while recording
- [ ] "Stop Recording" stops and triggers ingestion pipeline
- [ ] Menu icon changes to ⚙️ during processing
- [ ] Notification shown when recording saved: "Recording saved: {title}"
- [ ] Recording duration shown in menu while active
- [ ] Keyboard shortcut shown next to menu item
- [ ] Unit tests with mocked recorder

---

### Ticket 7.3: Notifications and Auto-Recording

**Add notification system and auto-recording triggers**

**Acceptance Criteria:**
- [ ] macOS notifications via `rumps.notification()`
- [ ] Notification when auto-recording starts: "Recording detected audio from {source}"
- [ ] Notification includes "Stop" action button
- [ ] Auto-recording triggers when:
  - Meeting app detected (Zoom, Teams)
  - System audio starts (via BlackHole monitor)
- [ ] Auto-recording configurable in Settings (on/off, app whitelist)
- [ ] Unit tests with mocked notifications

---

### Ticket 7.4: Global Hotkeys

**Add keyboard shortcuts using pynput**

**Acceptance Criteria:**
- [ ] `Cmd+Shift+R` - toggle recording
- [ ] `Cmd+Shift+N` - quick text note
- [ ] `Cmd+Shift+V` - voice note
- [ ] `Cmd+Shift+S` - open search
- [ ] Hotkeys work when app is in background
- [ ] Hotkeys configurable in Settings
- [ ] Conflicts detected and reported
- [ ] Requires Accessibility permission (prompt user)
- [ ] Unit tests for hotkey registration

---

## Epic 8: Packaging & Distribution

**Goal:** Make Recall installable by end users.

### Ticket 8.1: macOS App Bundle

**Create standalone .app using py2app**

**Acceptance Criteria:**
- [ ] `setup_app.py` or `pyproject.toml` config for py2app
- [ ] Builds `Recall.app` bundle
- [ ] App icon (custom .icns file)
- [ ] App launches menu bar interface
- [ ] First launch downloads models if not present
- [ ] Progress shown during model download
- [ ] App size < 100MB (models downloaded separately)
- [ ] Build tested on macOS 12+

---

### Ticket 8.2: Permissions Handling

**Handle macOS security permissions**

**Acceptance Criteria:**
- [ ] Microphone permission requested on first recording
- [ ] Accessibility permission requested for global hotkeys
- [ ] Screen Recording permission requested for system audio (if needed)
- [ ] Graceful degradation if permissions denied
- [ ] Settings shows permission status with "Grant" buttons
- [ ] `docs/PERMISSIONS.md` explaining each permission

---

### Ticket 8.3: Installer and Setup

**Create user-friendly installation experience**

**Acceptance Criteria:**
- [ ] DMG installer with drag-to-Applications
- [ ] First-run wizard:
  1. Welcome screen
  2. Permissions requests
  3. BlackHole installation prompt (optional)
  4. Model download
  5. Ready to use
- [ ] Uninstaller removes app data (with confirmation)
- [ ] `docs/INSTALL.md` with manual installation steps

---

## Implementation Notes

### Testing Strategy

All tickets should be implemented using TDD per `.github/agents/tdd.agent.md`:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor with tests green
4. Maintain ≥80% coverage

### Dependencies Between Tickets

```
1.1 ─┬─► 1.2 ─┬─► 1.3 ─► 3.1 ─► 3.2
     │        │           │
     │        ▼           ▼
     │       1.4 ◄────── 4.1 ─► 4.2 ─► 4.3 ─► 4.4
     │
     ▼
    2.1 ─► 2.3 ─► 2.4
     │
    2.2
     
5.1 ─► 5.2 ─► 5.3 (depends on 4.x)

6.1 ─► 6.2 ─► 6.3 (depends on 3.x, 4.x, 5.x)

7.1 ─► 7.2 ─► 7.3 ─► 7.4 (depends on 2.x, 3.x, 5.x)

8.1 ─► 8.2 ─► 8.3 (depends on 7.x)
```

### Recommended Implementation Order

1. **Sprint 1:** 1.1, 1.2, 1.3, 1.4 (Storage foundation)
2. **Sprint 2:** 2.1, 2.2, 3.1, 3.2 (Basic capture and pipeline)
3. **Sprint 3:** 4.1, 4.2, 4.3, 4.4 (Knowledge search)
4. **Sprint 4:** 5.1, 5.2, 5.3, 6.1, 6.2, 6.3 (Notes and CLI)
5. **Sprint 5:** 2.3, 2.4, 2.5 (Auto-detection)
6. **Sprint 6:** 7.1, 7.2, 7.3, 7.4 (Menu bar app)
7. **Sprint 7:** 8.1, 8.2, 8.3 (Packaging)
