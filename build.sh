#!/bin/bash
set -e

echo "=== STT Centy Build Script ==="
mkdir -p bin models

if [ ! -f bin/whisper-cli ]; then
    echo "Compiling whisper.cpp for Linux..."
    wget -q https://github.com/ggerganov/whisper.cpp/archive/refs/tags/v1.5.4.tar.gz
    tar -xzf v1.5.4.tar.gz
    cd whisper.cpp-1.5.4
    make
    cp main ../bin/whisper-cli
    cd ..
    rm -rf whisper.cpp-1.5.4 v1.5.4.tar.gz
    echo "whisper-cli compiled successfully."
else
    echo "whisper-cli already exists."
fi

if [ ! -f models/ggml-medium-q5_0.bin ]; then
    echo "Downloading ggml-medium-q5_0.bin model..."
    wget -q https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium-q5_0.bin -O models/ggml-medium-q5_0.bin
    echo "Model downloaded."
else
    echo "Model already exists."
fi
