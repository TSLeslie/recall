# Recall Permissions Guide

Recall requires certain macOS permissions to function properly.

## Required Permissions

### Microphone Access

**Why needed:** Record audio from your microphone for transcription.

**How to grant:**
1. Open System Settings > Privacy & Security > Microphone
2. Find "Recall" in the list
3. Toggle the switch to enable

**If Recall doesn't appear in the list:**
- Launch Recall and try to record
- The permission dialog should appear
- If not, you may need to add it manually using Terminal:
  ```bash
  tccutil reset Microphone
  ```
  Then relaunch Recall.

### Accessibility Access

**Why needed:** Register global keyboard shortcuts that work system-wide.

**How to grant:**
1. Open System Settings > Privacy & Security > Accessibility
2. Click the lock icon to make changes (enter your password)
3. Click the "+" button
4. Navigate to Applications and select Recall.app
5. Ensure the checkbox next to Recall is enabled
6. **Restart Recall** for changes to take effect

**Troubleshooting:**
- If hotkeys still don't work, try removing and re-adding Recall
- On some systems, you may need to restart your Mac

## Optional Permissions

### Screen Recording

**Why needed:** Capture system audio (from Zoom, YouTube, other apps)

**Note:** This permission is only needed if you want to record audio playing from other applications. Microphone recording works without this permission.

**How to grant:**
1. Open System Settings > Privacy & Security > Screen Recording
2. Find "Recall" in the list
3. Toggle the switch to enable
4. **Restart Recall** for changes to take effect

**Why "Screen Recording" for audio?**
macOS groups system audio capture under Screen Recording permissions for security reasons. Recall doesn't actually record your screen—it only captures audio.

## Checking Permission Status

### From the App

1. Click the Recall menu bar icon
2. Select "Preferences" (or press ⌘,)
3. Go to the "Permissions" tab
4. View status of each permission

### From Terminal

```bash
# Check microphone permission
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT * FROM access WHERE service='kTCCServiceMicrophone' AND client='com.recall.app'"

# Check accessibility permission  
sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT * FROM access WHERE service='kTCCServiceAccessibility' AND client='com.recall.app'"
```

## Revoking Permissions

If you want to revoke permissions:

1. Open System Settings > Privacy & Security
2. Select the relevant category
3. Find Recall in the list
4. Toggle the switch to disable

Or use Terminal:
```bash
# Reset microphone permission
tccutil reset Microphone com.recall.app

# Reset accessibility permission (requires admin)
sudo tccutil reset Accessibility com.recall.app
```

## Privacy Information

### What Recall Does

- Records audio from your microphone or system
- Processes audio **locally** using AI models
- Saves transcripts and summaries as local Markdown files
- Indexes your notes locally for search

### What Recall Does NOT Do

- Send any data to external servers
- Access files outside `~/.recall/` directory
- Record without your explicit action
- Share your data with third parties

### Data Location

All your data stays on your Mac:
```
~/.recall/
├── recordings/    # Your audio recordings and transcripts
├── knowledge/     # Local search index
├── models/        # AI models
└── config.json    # Your settings
```

## Troubleshooting

### "Recall is not permitted to record"

**Cause:** Microphone permission not granted.

**Fix:**
1. Open System Settings > Privacy & Security > Microphone
2. Enable Recall
3. Restart Recall

### Global hotkeys not working

**Cause:** Accessibility permission not granted.

**Fix:**
1. Open System Settings > Privacy & Security > Accessibility
2. Add and enable Recall
3. Restart Recall

### Can't capture Zoom/YouTube audio

**Cause:** Screen Recording permission not granted.

**Fix:**
1. Open System Settings > Privacy & Security > Screen Recording
2. Enable Recall
3. Restart Recall

### Permission changes not taking effect

**Fix:** Restart Recall after changing permissions. Some changes require a full app restart to take effect.

### "Allow" button doesn't appear

**Cause:** macOS may suppress repeated permission requests.

**Fix:**
1. Open System Settings > Privacy & Security
2. Manually add Recall to the relevant permission list
3. Or reset the permission using `tccutil reset` command

## Contact

For permission-related issues not covered here, please open an issue at:
https://github.com/your-username/recall/issues
