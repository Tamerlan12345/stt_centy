import subprocess
import logging
from pathlib import Path

from app.config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, CHUNK_SECONDS, TEMP_DIR, FFMPEG_BIN

logger = logging.getLogger(__name__)

def convert_to_wav(input_path: Path, output_path: Path) -> bool:
    """Converts media file to 16kHz Mono WAV suitable for whisper.cpp"""
    cmd = [
        FFMPEG_BIN,
        "-y",               # Overwrite
        "-i", str(input_path),
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-ac", str(AUDIO_CHANNELS),
        "-c:a", "pcm_s16le",
        str(output_path)
    ]
    
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            logger.error(f"FFmpeg convert failed: {process.stderr}")
            return False
        return True
    except FileNotFoundError:
        logger.error("FFmpeg not found in system PATH.")
        return False
    except Exception as e:
        logger.error(f"Exception during FFmpeg conversion: {e}")
        return False

def chunk_audio(wav_path: Path, task_id: str) -> list[Path]:
    """Splits the WAV file into smaller chunks, returns list of chunk paths."""
    output_pattern = str(TEMP_DIR / f"{task_id}_chunk_%03d.wav")
    
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i", str(wav_path),
        "-f", "segment",
        "-segment_time", str(CHUNK_SECONDS),
        "-c", "copy",
        output_pattern
    ]
    
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            logger.error(f"FFmpeg chunk failed: {process.stderr}")
            return []
        
        # Find generated chunks
        chunks = sorted(TEMP_DIR.glob(f"{task_id}_chunk_*.wav"))
        return chunks
    except Exception as e:
        logger.error(f"Exception during FFmpeg chunking: {e}")
        return []
