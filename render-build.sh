#!/usr/bin/env bash
set -e

echo "==> Installing full static FFmpeg with drawtext and freetype..."
mkdir -p bin

if [ ! -s "bin/ffmpeg" ]; then
    echo "Downloading Linux static FFmpeg binary..."
    curl -sL https://github.com/eugeneware/ffmpeg-static/releases/download/b6.0/ffmpeg-linux-x64 -o bin/ffmpeg
    chmod +x bin/ffmpeg
fi

export PATH="$PWD/bin:$PATH"
pip install -r requirements.txt
echo "==> Build complete. FFmpeg version:"
bin/ffmpeg -version | head -n 2 || true
