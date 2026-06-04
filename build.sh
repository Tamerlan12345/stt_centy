#!/bin/bash
set -e

echo "=== STT Centy Build Script ==="
mkdir -p models

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Downloading Vosk Russian model..."
if [ ! -d models/vosk-model-ru ]; then
    python -c "import urllib.request, zipfile, io; print('Downloading vosk model...'); r = urllib.request.urlopen('https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip'); print('Extracting...'); z = zipfile.ZipFile(io.BytesIO(r.read())); z.extractall('models')"
    mv models/vosk-model-small-ru-0.22 models/vosk-model-ru
    echo "Vosk model downloaded."
else
    echo "Vosk model already exists."
fi

echo "Build complete."
