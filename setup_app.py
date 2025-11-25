"""
Setup script for building Recall.app with py2app.

Usage:
    python setup_app.py py2app

This creates a standalone macOS application bundle in dist/Recall.app
"""

from setuptools import setup

# Application entry point
APP = ["src/recall/app/launcher.py"]

# Data files to include
DATA_FILES = [
    ("resources", ["resources/recall.icns"]),
]

# py2app options
OPTIONS = {
    "py2app": {
        "plist": {
            "CFBundleName": "Recall",
            "CFBundleDisplayName": "Recall",
            "CFBundleIdentifier": "com.recall.app",
            "CFBundleVersion": "0.1.0",
            "CFBundleShortVersionString": "0.1.0",
            "LSMinimumSystemVersion": "12.0",
            "CFBundleExecutable": "Recall",
            "CFBundlePackageType": "APPL",
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription": "Recall needs microphone access to record and transcribe audio.",
            "NSAppleEventsUsageDescription": "Recall uses AppleEvents for system integration.",
            "LSUIElement": True,  # Menu bar app (no dock icon)
        },
        "iconfile": "resources/recall.icns",
        "packages": [
            "recall",
            "whisper",
            "llama_cpp",
            "torch",
            "numpy",
            "pydantic",
            "typer",
            "rich",
            "yaml",
            "sentence_transformers",
        ],
        "includes": [
            "rumps",
            "pynput",
        ],
        "excludes": [
            "pytest",
            "pytest_cov",
            "pytest_mock",
            "pytest_asyncio",
            "test",
            "tests",
            "unittest",
            "doctest",
            "setuptools",
            "pip",
            "wheel",
            "distutils",
            "tkinter",
            "matplotlib",
        ],
        "argv_emulation": False,
        "strip": True,
        "optimize": 2,
    }
}

setup(
    name="Recall",
    version="0.1.0",
    description="Local AI-powered note-taking and memory bank",
    author="Your Name",
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=["py2app"],
)
