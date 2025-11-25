# Audio Setup Guide for Recall

This guide explains how to set up audio capture for Recall on macOS. Recall uses **BlackHole** - a free, open-source virtual audio driver - to capture system audio from applications like Zoom, YouTube, Spotify, and more.

## Table of Contents

1. [Overview](#overview)
2. [Install BlackHole](#install-blackhole)
3. [Configure Multi-Output Device](#configure-multi-output-device)
4. [Verify Setup](#verify-setup)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

---

## Overview

### How It Works

Recall captures audio using a "loopback" setup:

```
Audio Source (Zoom, YouTube, etc.)
         │
         ▼
┌─────────────────────────┐
│  Multi-Output Device    │
│  ┌─────────────────────┐│
│  │ Built-in Output     ││ ──► Speakers/Headphones (you hear audio)
│  └─────────────────────┘│
│  ┌─────────────────────┐│
│  │ BlackHole 2ch       ││ ──► Recall (captures audio)
│  └─────────────────────┘│
└─────────────────────────┘
```

This setup allows Recall to capture system audio while you continue to hear it normally through your speakers or headphones.

### Requirements

- macOS 10.14 (Mojave) or later
- Administrator access (for installation)
- ~10 MB disk space

---

## Install BlackHole

### Option 1: Homebrew (Recommended)

If you have Homebrew installed:

```bash
brew install blackhole-2ch
```

### Option 2: Direct Download

1. Go to [BlackHole GitHub Releases](https://github.com/ExistentialAudio/BlackHole/releases)
2. Download `BlackHole2ch-0.6.0.pkg` (or latest version)
3. Open the downloaded package
4. Follow the installation wizard
5. **Restart your Mac** after installation

### Option 3: Build from Source

For advanced users who want to customize the channel count:

```bash
git clone https://github.com/ExistentialAudio/BlackHole.git
cd BlackHole
./installer.sh 2  # 2 channels is sufficient for stereo
```

---

## Configure Multi-Output Device

After installing BlackHole, you need to create a Multi-Output Device to route audio to both your speakers and BlackHole simultaneously.

### Step 1: Open Audio MIDI Setup

1. Open **Finder**
2. Go to **Applications** → **Utilities** → **Audio MIDI Setup**
   - Or press `Cmd + Space` and type "Audio MIDI Setup"

### Step 2: Create Multi-Output Device

1. Click the **+** button in the bottom-left corner
2. Select **Create Multi-Output Device**

### Step 3: Configure Outputs

1. In the right panel, check the boxes for:
   - ✅ **Built-in Output** (or your preferred speakers/headphones)
   - ✅ **BlackHole 2ch**

2. Make sure **Built-in Output** is listed FIRST (drag to reorder if needed)
   - This ensures you hear audio through your speakers

3. (Optional) Rename the device:
   - Right-click the device in the left panel
   - Select **Rename**
   - Enter a name like "Recall Audio"

### Step 4: Set as Default Output

1. Right-click your new Multi-Output Device
2. Select **Use This Device For Sound Output**

Or via System Preferences:
1. Open **System Preferences** → **Sound**
2. Click the **Output** tab
3. Select your Multi-Output Device

---

## Verify Setup

### Using the Verification Script

Recall includes a verification script to check your audio setup:

```bash
python scripts/check_audio_setup.py
```

Expected output when everything is configured correctly:

```
🔊 Recall Audio Setup Checker
================================

Checking audio devices...

✅ BlackHole 2ch found!
   - Device ID: 3
   - Input channels: 2
   - Output channels: 2

✅ System audio capture is ready!

Recommended next steps:
1. Play some audio (e.g., YouTube video)
2. Run: recall status
3. Start recording: recall record --source system
```

### Manual Verification

1. **Check BlackHole is installed:**
   ```bash
   # Should show "BlackHole 2ch" in the list
   python -c "import sounddevice; print([d['name'] for d in sounddevice.query_devices()])"
   ```

2. **Test audio capture:**
   ```bash
   # Record 5 seconds of system audio
   recall record --source system --duration 5 --output test.wav
   ```

3. **Play back the recording:**
   ```bash
   afplay test.wav
   ```

---

## Troubleshooting

### BlackHole not appearing in Audio MIDI Setup

1. **Restart your Mac** after installation
2. Check Security & Privacy settings:
   - Go to **System Preferences** → **Security & Privacy** → **Privacy** tab
   - Ensure the installer was allowed to run
3. Try reinstalling BlackHole

### No audio captured (silent recording)

1. **Check Multi-Output Device is default:**
   - System Preferences → Sound → Output
   - Select your Multi-Output Device

2. **Check BlackHole is in the Multi-Output:**
   - Open Audio MIDI Setup
   - Click your Multi-Output Device
   - Ensure BlackHole 2ch is checked

3. **Check audio is actually playing:**
   - Play a YouTube video or music
   - Verify you can hear it through speakers

### Can't hear audio anymore

1. **Check speaker order in Multi-Output:**
   - Your speakers/headphones should be FIRST in the list
   - BlackHole should be SECOND

2. **Check volume:**
   - Multi-Output devices don't show in the menu bar volume
   - Use the volume keys on your keyboard
   - Or: System Preferences → Sound → Output → Volume slider

### "Permission denied" errors

On macOS Catalina and later, you may need to grant microphone access:

1. Go to **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Microphone** in the left panel
3. Ensure **Terminal** (or your IDE) is checked

### BlackHole shows 0 channels

This can happen with older macOS versions. Try:

```bash
# Uninstall existing version
brew uninstall blackhole-2ch

# Install latest version
brew update
brew install blackhole-2ch

# Restart
sudo reboot
```

---

## FAQ

### Q: Is BlackHole safe?

**A:** Yes. BlackHole is:
- Open source (MIT license)
- No analytics or data collection
- Signed by Apple (when installed via Homebrew)
- Used by professional audio applications

### Q: Does BlackHole affect audio quality?

**A:** No. BlackHole passes audio through without modification. It supports:
- 2 to 256 channels
- Sample rates from 44.1kHz to 192kHz
- Bit depths from 16 to 32-bit float

### Q: Can I use BlackHole 16ch or 64ch instead?

**A:** Yes! Any BlackHole variant works. Recall uses 2 channels by default, but you can configure it:

```python
from recall.capture import AudioMonitor

monitor = AudioMonitor(device_name="BlackHole 16ch")
```

### Q: Will this capture all system audio?

**A:** Yes, when properly configured. This includes:
- Browser audio (YouTube, Netflix, etc.)
- Meeting apps (Zoom, Teams, Google Meet)
- Media players (Spotify, Apple Music, VLC)
- Any application audio routed to the default output

### Q: Can I capture just specific applications?

**A:** Not directly with BlackHole, but Recall's application detector can identify which app is playing audio and tag recordings appropriately.

### Q: How do I uninstall BlackHole?

**Homebrew:**
```bash
brew uninstall blackhole-2ch
```

**Manual:**
1. Delete `/Library/Audio/Plug-Ins/HAL/BlackHole2ch.driver`
2. Restart your Mac

---

## Additional Resources

- [BlackHole GitHub](https://github.com/ExistentialAudio/BlackHole) - Official repository
- [BlackHole Wiki](https://github.com/ExistentialAudio/BlackHole/wiki) - Detailed documentation
- [Apple Audio MIDI Setup Guide](https://support.apple.com/guide/audio-midi-setup/welcome/mac)

---

*Last updated: 2025*
