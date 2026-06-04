#!/bin/bash
set -e

echo "=== STT Centy Build Script ==="
mkdir -p models

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Pre-downloading Faster-Whisper model..."
python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')"

echo "Build complete."
