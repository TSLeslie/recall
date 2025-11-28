# Product Requirements Document: Recall Menu Bar UI

## Overview

The Recall menu bar app (`menubar.py`) has five unimplemented menu item callbacks. This PRD defines the features, user flows, and technical requirements for each.

---

## 1. Quick Note (⌘N)

### Purpose
Allow users to quickly capture text notes without leaving their current context.

### User Flow
1. User clicks "Quick Note..." or presses ⌘N
2. A text input dialog appears with a multi-line text field
3. User enters note content and optionally a title
4. User clicks "Save" or presses Enter
5. Note is saved, indexed, and optionally ingested to GraphRAG
6. Notification confirms save

### UI Requirements
- **Dialog**: `rumps.Window` with title "Quick Note"
- **Fields**: Text area (main content), optional title field
- **Buttons**: Save, Cancel
- **Keyboard**: Enter to save, Escape to cancel

### Backend Integration
- Call `create_note()` from `src/recall/notes/quick_note.py` with content
- Index via `RecordingIndex` from `src/recall/storage/index.py` for search
- Optionally ingest to GraphRAG if enabled in settings

### Success Criteria
- Note saved to `~/.recall/notes/` as Markdown
- Note appears in search results
- Notification shown on save

---

## 2. Voice Note (⌘V)

### Purpose
Record short voice memos, automatically transcribe, and save as searchable notes.

### User Flow
1. User clicks "Voice Note" or presses ⌘V
2. Recording starts immediately; menu icon changes to 🔴
3. Menu item changes to "Stop Voice Note"
4. User clicks again to stop
5. Audio is transcribed via Whisper, summarized, and saved
6. Notification confirms save with duration

### UI Requirements
- **No dialog needed** - uses menu state toggle
- **Visual feedback**: Menu bar icon shows recording state
- **Menu item**: Toggles between "Voice Note" and "Stop Voice Note (0:15)"

### Backend Integration
- Call `start_voice_note()` from `src/recall/notes/voice_note.py` on start
- Call `stop_voice_note()` from `src/recall/notes/voice_note.py` on stop
- Use `NotificationManager` from `src/recall/app/notifications.py` for feedback

### Success Criteria
- Voice note transcribed and saved to `~/.recall/notes/`
- Summary auto-generated for notes > 100 chars
- Audio optionally retained based on settings

---

## 3. Search (⌘S)

### Purpose
Search across all recordings and notes using keywords or natural language.

### User Flow
1. User clicks "Search..." or presses ⌘S
2. Search input dialog appears
3. User enters query and presses Enter
4. Results displayed (top 5-10 matches)
5. User can click a result to open the file

### UI Requirements
- **Input Dialog**: `rumps.Window` with search field
- **Results Display**: Options:
  - A) `rumps.alert` showing formatted results
  - B) Open results in default Markdown viewer
  - C) Copy results to clipboard with file paths
- **Result format**: Title, snippet, date, relevance score

### Backend Integration
- Use `RecordingIndex.search()` from `src/recall/storage/index.py` for keyword search
- Optionally use `hybrid_search()` from `src/recall/knowledge/query.py` for semantic search
- Results are `SearchResult` or `SearchHit` objects

### Success Criteria
- Returns relevant results within 1 second
- Shows meaningful snippets with query context
- Provides path to open source files

---

## 4. Open Library

### Purpose
Quick access to the recordings folder in Finder.

### User Flow
1. User clicks "Open Library"
2. Finder opens at `~/.recall/recordings/`

### UI Requirements
- **No dialog** - direct action
- **Fallback**: If folder doesn't exist, create it first

### Technical Implementation
```python
import subprocess
subprocess.run(["open", str(recordings_path)])
```

### Backend Integration
- Get path from `RecallConfig` in `src/recall/config.py`: `config.storage_dir / "recordings"`

### Success Criteria
- Finder opens to correct folder
- Works even if folder is empty/new

---

## 5. Settings (⌘,)

### Purpose
Configure Recall preferences including recording source, auto-recording, storage location, and model settings.

### User Flow
1. User clicks "Settings..." or presses ⌘,
2. Settings dialog/panel appears
3. User modifies settings
4. Changes saved on close or "Apply"

### Settings Categories

#### Recording Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| Default Source | Dropdown | microphone | microphone / system / both |
| Retain Audio | Toggle | false | Keep original audio files |
| Whisper Model | Dropdown | base | tiny / base / small / medium |

#### Auto-Recording Settings (from `AutoRecordingConfig` in `src/recall/app/notifications.py`)
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| Enable Auto-Recording | Toggle | false | Master switch |
| Detect Meeting Apps | Toggle | true | Trigger for Zoom, Teams, etc. |
| Detect System Audio | Toggle | true | Trigger for BlackHole |
| App Whitelist | List | [zoom.us, Teams, ...] | Apps that trigger recording |

#### Storage Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| Storage Directory | Path | ~/.recall | Base storage location |
| Enable GraphRAG | Toggle | true | Ingest to knowledge base |

#### Model Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| LLM Model | Dropdown | qwen2.5-3b | Model for summarization |
| Summary Length | Dropdown | brief | brief / detailed |

### UI Options (in order of complexity)
1. **Simple**: Multiple `rumps.alert` dialogs for each category
2. **Medium**: Single `rumps.Window` with formatted text display of current settings
3. **Advanced**: Native macOS preferences panel via PyObjC

### Backend Integration
- Read/write to `RecallConfig` in `src/recall/config.py`
- Persist to `~/.recall/config.json`
- Update `AutoRecordingConfig` settings

### Success Criteria
- Settings persist across app restarts
- Changes take effect immediately where applicable
- Invalid paths/values show error feedback

---

## Technical Considerations

### UI Framework Choice
| Approach | Pros | Cons |
|----------|------|------|
| rumps dialogs | Native look, no dependencies | Limited customization |
| tkinter | Cross-platform, built-in | Non-native appearance |
| PyObjC/AppKit | Fully native, powerful | macOS only, complex |

**Recommendation**: Start with `rumps.Window` for Quick Note and Search, use subprocess for Open Library. Settings may require PyObjC for proper preferences panel.

### Error Handling
- All dialogs should handle cancellation gracefully
- File operations should catch and report errors via notifications
- Model loading failures should show user-friendly messages

### Persistence
- Extend `config.py` to load/save from JSON
- Add `RecallConfig.load()` and `RecallConfig.save()` methods

---

## Implementation Priority

1. **Open Library** - Simplest, high utility (1 hour)
2. **Quick Note** - High user value, straightforward (2-4 hours)
3. **Voice Note** - Leverages existing recording infra (4-6 hours)
4. **Search** - Important for knowledge retrieval (4-6 hours)
5. **Settings** - Most complex, can be iterative (8-16 hours)

---

## Open Questions

1. **Settings persistence format** - Should settings use JSON, YAML, or plist (macOS native)? JSON aligns with existing patterns but plist integrates better with macOS preferences.

2. **Search results presentation** - Should results open in a separate window, show as a submenu, or open files directly in the default Markdown editor?

3. **Voice note duration limit** - Should there be a maximum recording duration for voice notes to prevent accidental long recordings?

---

## Implementation Tickets

### RECALL-001: Extend RecallConfig for JSON Persistence

**Priority**: High  
**Estimate**: 2 hours  
**Labels**: backend, config, foundation

#### Description
Extend `RecallConfig` in `src/recall/config.py` to support loading and saving configuration from a JSON file at `~/.recall/config.json`. This is a prerequisite for the Settings UI and enables persistence of user preferences.

#### Acceptance Criteria
- [ ] Add `RecallConfig.load(path: Path) -> RecallConfig` class method that reads from JSON
- [ ] Add `RecallConfig.save(path: Path) -> None` instance method that writes to JSON
- [ ] Handle missing config file gracefully (return defaults)
- [ ] Handle malformed JSON gracefully (log warning, return defaults)
- [ ] Add new configurable fields:
  - `default_audio_source: str` (microphone/system/both)
  - `retain_audio: bool`
  - `whisper_model: str`
  - `enable_graphrag: bool`
  - `summary_length: str` (brief/detailed)
- [ ] Merge `AutoRecordingConfig` fields into unified config
- [ ] Unit tests for load/save round-trip
- [ ] Unit tests for missing file handling
- [ ] Unit tests for malformed JSON handling

#### Technical Notes
- Use `dataclasses.asdict()` for serialization
- Use `json.dumps(..., indent=2)` for human-readable output
- Config path should be configurable for testing

---

### RECALL-002: Implement Open Library Menu Action

**Priority**: High  
**Estimate**: 1 hour  
**Labels**: ui, menubar, quick-win

#### Description
Implement the `on_open_library()` callback in `menubar.py` to open Finder at the recordings directory.

#### Acceptance Criteria
- [ ] Clicking "Open Library" opens Finder at `~/.recall/recordings/`
- [ ] If directory doesn't exist, create it before opening
- [ ] Works with custom storage directory from config
- [ ] Handle subprocess errors gracefully (show notification on failure)
- [ ] Unit test for directory creation
- [ ] Unit test for subprocess call (mocked)

#### Technical Notes
```python
import subprocess
from recall.config import get_default_config

def on_open_library(self, sender) -> None:
    config = get_default_config()
    recordings_path = config.storage_dir / "recordings"
    recordings_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["open", str(recordings_path)])
```

---

### RECALL-003: Implement Quick Note Dialog

**Priority**: High  
**Estimate**: 3 hours  
**Labels**: ui, menubar, notes

#### Description
Implement the `on_quick_note()` callback to show a text input dialog and save the note using the existing `create_note()` function.

#### Acceptance Criteria
- [ ] Clicking "Quick Note..." or ⌘N shows a `rumps.Window` dialog
- [ ] Dialog has title "Quick Note" and placeholder text
- [ ] User can enter multi-line text content
- [ ] Clicking "Save" (or pressing Enter) saves the note
- [ ] Clicking "Cancel" (or pressing Escape) dismisses without saving
- [ ] Note saved to `~/.recall/notes/` as Markdown with frontmatter
- [ ] Note indexed in SQLite for search (if index exists)
- [ ] Success notification shown: "Note saved"
- [ ] Empty content shows warning and doesn't save
- [ ] Handle `create_note()` exceptions with error notification
- [ ] Unit tests for dialog response handling
- [ ] Integration test for note creation flow

#### Technical Notes
```python
def on_quick_note(self, sender) -> None:
    window = rumps.Window(
        message="Enter your note:",
        title="Quick Note",
        default_text="",
        ok="Save",
        cancel="Cancel",
        dimensions=(320, 160),
    )
    response = window.run()
    if response.clicked and response.text.strip():
        # Save note
```

---

### RECALL-004: Implement Voice Note Recording Toggle

**Priority**: Medium  
**Estimate**: 4 hours  
**Labels**: ui, menubar, notes, recording

#### Description
Implement the `on_voice_note()` callback to toggle voice note recording, integrating with the existing `start_voice_note()` and `stop_voice_note()` functions.

#### Acceptance Criteria
- [ ] First click starts voice recording via `start_voice_note()`
- [ ] Menu bar icon changes to 🎙️ (distinct from main recording 🔴)
- [ ] Menu item text changes to "Stop Voice Note"
- [ ] Notification shown: "Voice note recording..."
- [ ] Second click stops recording via `stop_voice_note()`
- [ ] Audio transcribed via Whisper automatically
- [ ] Note saved to `~/.recall/notes/` with transcript
- [ ] Success notification: "Voice note saved (0:15)"
- [ ] Menu item reverts to "Voice Note"
- [ ] Handle microphone permission errors with user-friendly message
- [ ] Handle transcription failures gracefully
- [ ] Add `_voice_note_active: bool` state to `RecallMenuBar`
- [ ] Unit tests for state transitions
- [ ] Integration test for full record-transcribe-save flow

#### Technical Notes
- Need new state `AppState.VOICE_RECORDING` or separate flag
- Consider showing elapsed time in menu item: "Stop Voice Note (0:15)"
- Reuse `NotificationManager.notify_recording_started()` pattern

---

### RECALL-005: Implement Search Dialog

**Priority**: Medium  
**Estimate**: 4 hours  
**Labels**: ui, menubar, search

#### Description
Implement the `on_search()` callback to show a search input dialog and display results from the SQLite index.

#### Acceptance Criteria
- [ ] Clicking "Search..." or ⌘S shows a `rumps.Window` input dialog
- [ ] Dialog has title "Search Recall" and search icon/placeholder
- [ ] User enters query and clicks "Search"
- [ ] Results fetched from `RecordingIndex.search()`
- [ ] Top 5 results displayed in a `rumps.alert` dialog
- [ ] Each result shows: title/filename, snippet (50 chars), date
- [ ] Results are clickable paths that open in default Markdown viewer
- [ ] Empty query shows warning
- [ ] No results shows "No matches found" message
- [ ] Handle index not initialized (show helpful error)
- [ ] Search completes within 1 second for typical queries
- [ ] Unit tests for search flow
- [ ] Unit tests for result formatting

#### Technical Notes
```python
def on_search(self, sender) -> None:
    window = rumps.Window(
        message="Search your notes and recordings:",
        title="Search Recall",
        ok="Search",
        cancel="Cancel",
    )
    response = window.run()
    if response.clicked and response.text.strip():
        results = self._perform_search(response.text)
        self._display_results(results)
```

#### Future Enhancements (out of scope)
- Hybrid search with GraphRAG semantic search
- Search history / recent queries
- Advanced filters (date range, source type)

---

### RECALL-006: Implement Settings Dialog - Basic

**Priority**: Medium  
**Estimate**: 6 hours  
**Labels**: ui, menubar, settings

#### Description
Implement a basic Settings dialog using `rumps.Window` that allows users to view and modify key settings. This is the first iteration; a more polished native UI can follow.

#### Acceptance Criteria
- [ ] Clicking "Settings..." or ⌘, shows settings dialog
- [ ] Display current settings in a readable format
- [ ] Allow modification of these settings:
  - [ ] Default audio source (microphone/system/both)
  - [ ] Whisper model (tiny/base/small/medium)
  - [ ] Retain audio files (yes/no)
  - [ ] Enable auto-recording (yes/no)
- [ ] "Save" persists changes to `~/.recall/config.json`
- [ ] "Cancel" discards changes
- [ ] Changes take effect immediately (no restart required)
- [ ] Invalid values show validation error
- [ ] Unit tests for settings load/save
- [ ] Unit tests for validation

#### Technical Notes
Due to `rumps.Window` limitations (single text field), implement as:
1. Show current settings as formatted text
2. User edits inline (key: value format)
3. Parse and validate on save

Alternative: Multiple sequential dialogs for each setting category.

#### Dependencies
- RECALL-001 (Config Persistence)

---

### RECALL-007: Add Voice Note State to Menu Bar

**Priority**: Medium  
**Estimate**: 2 hours  
**Labels**: ui, menubar, refactor

#### Description
Extend `AppState` enum and menu bar to support voice note recording as a distinct state from main recording.

#### Acceptance Criteria
- [ ] Add `AppState.VOICE_RECORDING` with icon 🎙️
- [ ] Voice note recording doesn't conflict with main recording state
- [ ] Menu correctly shows both states if both are active
- [ ] State persists correctly across menu rebuilds
- [ ] Unit tests for state transitions

#### Dependencies
- RECALL-004 (Voice Note)

---

### RECALL-008: Add Search Results Action Menu

**Priority**: Low  
**Estimate**: 3 hours  
**Labels**: ui, menubar, search, enhancement

#### Description
Enhance search results to allow opening files directly from the results dialog.

#### Acceptance Criteria
- [ ] Each search result can be clicked to open in default app
- [ ] Option to copy file path to clipboard
- [ ] Option to reveal in Finder
- [ ] Results show relative paths for readability
- [ ] Unit tests for file open action

#### Dependencies
- RECALL-005 (Search Dialog)

---

### RECALL-009: Settings Dialog - Native macOS Preferences

**Priority**: Low  
**Estimate**: 8 hours  
**Labels**: ui, settings, enhancement, pyobjc

#### Description
Replace the basic settings dialog with a native macOS preferences panel using PyObjC for a polished user experience.

#### Acceptance Criteria
- [ ] Native macOS preferences window with tabs
- [ ] Recording tab with audio source, model selection
- [ ] Auto-Recording tab with app whitelist management
- [ ] Storage tab with directory picker
- [ ] About tab with version info and links
- [ ] Standard macOS keyboard shortcuts work
- [ ] Window remembers position
- [ ] Integration tests for preferences flow

#### Dependencies
- RECALL-006 (Basic Settings)
- PyObjC dependency addition

#### Technical Notes
This is a significant enhancement. Consider as a future sprint item.

---

### RECALL-010: Error Handling and Notifications Polish

**Priority**: Low  
**Estimate**: 2 hours  
**Labels**: ui, error-handling, polish

#### Description
Ensure all menu actions have consistent error handling and user feedback.

#### Acceptance Criteria
- [ ] All file operations wrapped in try/except
- [ ] Errors shown via `NotificationManager.notify_error()`
- [ ] Specific error messages (not generic "An error occurred")
- [ ] Microphone permission errors have actionable message
- [ ] Model loading failures suggest solutions
- [ ] Network errors (if any) handled gracefully

#### Dependencies
- All other tickets (RECALL-002 through RECALL-008)

---

## Dependency Graph

```
RECALL-001 (Config Persistence)
    │
    ├──► RECALL-006 (Settings - Basic)
    │        │
    │        └──► RECALL-009 (Settings - Native) [Low Priority]
    │
    └──► RECALL-002 (Open Library) [No config dependency, can start immediately]

RECALL-002 (Open Library)
    └──► [Independent - Quick Win]

RECALL-003 (Quick Note)
    └──► [Independent - Can start immediately]

RECALL-004 (Voice Note)
    │
    └──► RECALL-007 (Voice Note State)

RECALL-005 (Search)
    │
    └──► RECALL-008 (Search Results Actions) [Low Priority]

RECALL-010 (Error Handling)
    └──► [Depends on all: RECALL-002 through RECALL-008]
```

### Recommended Execution Order

```
Phase 1 - Foundation (Week 1)
├── RECALL-001: Config Persistence [2h]
└── RECALL-002: Open Library [1h] ← Quick win, ship immediately

Phase 2 - Core Features (Week 1-2)
├── RECALL-003: Quick Note [3h]
├── RECALL-004: Voice Note [4h]
└── RECALL-007: Voice Note State [2h]

Phase 3 - Search & Settings (Week 2)
├── RECALL-005: Search Dialog [4h]
└── RECALL-006: Settings Basic [6h]

Phase 4 - Polish (Week 3+)
├── RECALL-008: Search Results Actions [3h]
├── RECALL-009: Settings Native [8h]
└── RECALL-010: Error Handling [2h]
```

### Critical Path

```
RECALL-001 ──► RECALL-006 ──► RECALL-009
```

The config persistence work unblocks settings, which is a significant user-facing feature.

### Parallelization Opportunities

These tickets can be worked on in parallel by different developers:

- **Developer A**: RECALL-001, RECALL-006, RECALL-009 (config/settings track)
- **Developer B**: RECALL-002, RECALL-003, RECALL-004, RECALL-007 (actions track)
- **Developer C**: RECALL-005, RECALL-008 (search track)
