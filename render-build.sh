#!/usr/bin/env bash
set -e

# Version marker — bump this to force re-download of FFmpeg binary
FFMPEG_VERSION_MARKER="btbn-gpl-v2"

echo "==> Installing full static FFmpeg with libass, drawtext, freetype..."
mkdir -p bin

# Force re-download if version marker has changed (e.g. switching from eugeneware to BtbN)
if [ -f "bin/.ffmpeg_version" ]; then
    CURRENT_VERSION=$(cat bin/.ffmpeg_version)
else
    CURRENT_VERSION="none"
fi

if [ ! -s "bin/ffmpeg" ] || [ "$CURRENT_VERSION" != "$FFMPEG_VERSION_MARKER" ]; then
    echo "Downloading BtbN FFmpeg GPL static build (includes libass + drawtext + freetype)..."
    rm -f bin/ffmpeg
    
    FFMPEG_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    curl -sL "$FFMPEG_URL" -o /tmp/ffmpeg-build.tar.xz
    
    echo "Extracting ffmpeg binary..."
    # Extract only the ffmpeg binary from the tar archive
    tar -xJf /tmp/ffmpeg-build.tar.xz --wildcards '*/bin/ffmpeg' --strip-components=2 -C bin/
    chmod +x bin/ffmpeg
    rm -f /tmp/ffmpeg-build.tar.xz
    
    # Write version marker
    echo "$FFMPEG_VERSION_MARKER" > bin/.ffmpeg_version
    
    echo "FFmpeg binary size: $(du -sh bin/ffmpeg | cut -f1)"
fi

export PATH="$PWD/bin:$PATH"
pip install -r requirements.txt

echo "==> Build complete. FFmpeg version:"
bin/ffmpeg -version | head -n 5 || true

echo "==> Checking libass and drawtext support:"
bin/ffmpeg -filters 2>/dev/null | grep -E "subtitles|drawtext|ass" || echo "WARNING: filters not found"
