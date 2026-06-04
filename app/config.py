import os
from pathlib import Path
import platform
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent

# Support both Windows (.exe) and Linux binary names
DEFAULT_BIN_NAME = "whisper-cli.exe" if platform.system() == "Windows" else "whisper-cli"

MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "ggml-base.bin"))
WHISPER_BIN = os.getenv("WHISPER_BIN", str(BASE_DIR / "bin" / DEFAULT_BIN_NAME))

UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
RESULT_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"

# Use standalone FFmpeg binary installed via pip
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

CHUNK_SECONDS = 60
MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

DEFAULT_LANGUAGE = "auto"
DEFAULT_OUTPUT_FORMATS = ["txt", "json", "srt", "vtt"]

CPU_THREADS = 3

# Ensure directories exist
for d in [UPLOAD_DIR, TEMP_DIR, RESULT_DIR, LOGS_DIR, BASE_DIR / "models", BASE_DIR / "bin"]:
    d.mkdir(parents=True, exist_ok=True)
