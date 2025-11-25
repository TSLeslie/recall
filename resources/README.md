# Recall Resources

This directory contains resources for the Recall macOS app.

## Files

- `recall.icns` - Application icon (macOS format)

## Creating the Icon

To create a proper macOS icon:

1. Create a 1024x1024 PNG image
2. Use `iconutil` to convert to .icns:

```bash
# Create iconset directory
mkdir recall.iconset

# Create required sizes (assuming you have icon.png at 1024x1024)
sips -z 16 16 icon.png --out recall.iconset/icon_16x16.png
sips -z 32 32 icon.png --out recall.iconset/icon_16x16@2x.png
sips -z 32 32 icon.png --out recall.iconset/icon_32x32.png
sips -z 64 64 icon.png --out recall.iconset/icon_32x32@2x.png
sips -z 128 128 icon.png --out recall.iconset/icon_128x128.png
sips -z 256 256 icon.png --out recall.iconset/icon_128x128@2x.png
sips -z 256 256 icon.png --out recall.iconset/icon_256x256.png
sips -z 512 512 icon.png --out recall.iconset/icon_256x256@2x.png
sips -z 512 512 icon.png --out recall.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out recall.iconset/icon_512x512@2x.png

# Convert to .icns
iconutil -c icns recall.iconset -o recall.icns

# Clean up
rm -rf recall.iconset
```

## Placeholder

For development, create a placeholder .icns file:

```bash
# On macOS, create empty placeholder
touch recall.icns
```

The icon should represent:
- 🎙️ Audio recording
- 📝 Note taking
- 🧠 AI/Memory theme
