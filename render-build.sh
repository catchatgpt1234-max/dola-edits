#!/usr/bin/env bash
set -e

echo "==> Installing static FFmpeg..."
python install_ffmpeg.py

export PATH="$PWD/bin:$PATH"

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Build complete. FFmpeg version:"
bin/ffmpeg -version | head -n 3 || true
