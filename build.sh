#!/bin/bash
set -e

echo "=== STT Centy Build Script ==="
mkdir -p models

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Downloading Vosk Russian model..."
if [ ! -d models/vosk-model-ru ]; then
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip -O models/vosk.zip
    unzip -q models/vosk.zip -d models/
    mv models/vosk-model-small-ru-0.22 models/vosk-model-ru
    rm models/vosk.zip
    echo "Vosk model downloaded."
else
    echo "Vosk model already exists."
fi

echo "Build complete."
