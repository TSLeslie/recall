# Recall - AI Audio Transcription & Analysis

A Python project for audio transcription and analysis using Whisper AI and Llama-3.1 models.

## Features

- 🎤 **Audio Transcription**: Leverage OpenAI's Whisper model for accurate speech-to-text conversion
- 🤖 **AI Analysis**: Use Llama-3.1 for post-processing, summarization, and analysis of transcriptions
- 🐳 **Dev Container**: Fully containerized development environment with GPU support
- 🛠️ **Modern Python**: Built with Python 3.11+ and best practices

## Getting Started

### Prerequisites

- Docker with GPU support (for CUDA acceleration)
- VS Code with Dev Containers extension
- NVIDIA GPU (recommended for optimal performance)

### Setup

1. Open this project in VS Code
2. When prompted, click "Reopen in Container" or run the command "Dev Containers: Reopen in Container"
3. Wait for the container to build and dependencies to install
4. You're ready to go!

## Project Structure

```
recall/
├── .devcontainer/          # Dev container configuration
├── src/                    # Source code
│   └── recall/            # Main package
├── tests/                  # Test files
├── models/                 # Local model storage (gitignored)
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── setup.py               # Package setup
└── pyproject.toml         # Project configuration
```

## Usage

### Basic Transcription

```python
from recall import transcribe

# Transcribe an audio file
result = transcribe("audio.mp3", model="base")
print(result["text"])
```

### With Llama Analysis

```python
from recall import transcribe, analyze

# Transcribe and analyze
transcript = transcribe("audio.mp3")
analysis = analyze(transcript["text"], prompt="Summarize this conversation")
print(analysis)
```

## Models

### Whisper Models
- `tiny`: Fastest, least accurate (~1GB)
- `base`: Good balance (~1GB)
- `small`: Better accuracy (~2GB)
- `medium`: High accuracy (~5GB)
- `large`: Best accuracy (~10GB)

### Llama-3.1
Download the model from Hugging Face or use llama-cpp-python for GGUF format models.

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
