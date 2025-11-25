# Installing Recall

## System Requirements

- **macOS 12.0 (Monterey)** or later
- **Apple Silicon (M1/M2/M3)** or Intel Mac
- **4GB RAM** minimum (8GB recommended)
- **5GB disk space** for app and AI models

## Installation Steps

1. **Download the Installer**
   - Download `Recall-Installer.dmg` from the releases page

2. **Open the DMG**
   - Double-click the downloaded DMG file
   - A new Finder window will open

3. **Install the App**
   - Drag `Recall.app` to the Applications folder
   - Wait for the copy to complete

4. **First Launch**
   - Open Recall from Applications or Spotlight
   - Follow the setup wizard to:
     - Download AI models
     - Grant required permissions

5. **Grant Permissions**
   - Microphone access (required)
   - Accessibility access (for global hotkeys)
   - Screen recording (optional, for system audio)

## Uninstalling

1. Quit Recall if running
2. Drag Recall.app from Applications to Trash
3. Remove data (optional): `rm -rf ~/.recall`

## Building from Source

### Prerequisites

- Python 3.11+
- pip and virtualenv
- Xcode Command Line Tools

### Build Steps

```bash
# Clone the repository
git clone https://github.com/your-username/recall.git
cd recall

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install py2app

# Build the app
python setup_app.py py2app

# The app will be in dist/Recall.app
```

### Creating the DMG

```bash
# Requires create-dmg (brew install create-dmg)
./scripts/create_dmg.sh
```

## Troubleshooting

### App won't open
- Right-click and select "Open" to bypass Gatekeeper
- Check System Settings > Privacy & Security

### Models not downloading
- Check internet connection
- Try manual download from releases page
- Place models in `~/.recall/models/`

### Permissions issues
- Open System Settings > Privacy & Security
- Find Recall in the list and enable it
- Restart Recall after granting permissions

### Transcription not working
- Ensure Whisper model is downloaded
- Check microphone permission
- Try restarting the app

### Summarization not working
- Ensure Qwen2.5 model is downloaded
- Check that you have enough RAM (4GB+ recommended)

## Data Location

All Recall data is stored locally in `~/.recall/`:

```
~/.recall/
├── models/           # AI models
│   ├── base.pt       # Whisper model
│   └── qwen2.5-3b-instruct.gguf
├── recordings/       # Your recordings
│   └── 2025/
│       └── 11/
│           └── 25/
│               └── meeting_notes.md
├── knowledge/        # Graph RAG index
└── config.json       # Settings
```

## Support

For issues and feature requests, visit:
https://github.com/your-username/recall/issues
