import logging
from pathlib import Path
from faster_whisper import WhisperModel

from app.config import CPU_THREADS

logger = logging.getLogger(__name__)

# Lazy loading of Faster-Whisper model
_fw_model = None

def load_model():
    global _fw_model
    if _fw_model is None:
        logger.info("Loading Faster-Whisper model into memory...")
        # 'large-v3-turbo' is optimized for speed/accuracy balance on CPU/Edge
        # compute_type "int8" is crucial for CPU speed and RAM footprint.
        _fw_model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=CPU_THREADS)
        logger.info("Faster-Whisper model loaded successfully.")
    return True

def transcribe_chunk(wav_path: Path, language: str) -> list[dict]:
    """Runs Faster-Whisper on a single wav chunk. Returns a list of segments."""
    try:
        load_model()
        
        # faster-whisper accepts standard language codes
        lang_code = language if language in ['ru', 'kk', 'en'] else None
        
        segments_generator, info = _fw_model.transcribe(
            str(wav_path),
            language=lang_code,
            beam_size=5,
            word_timestamps=True
        )
        
        segments = []
        for segment in segments_generator:
            segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            
        return segments

    except Exception as e:
        logger.error(f"Exception during Faster-Whisper execution: {e}")
        return []


