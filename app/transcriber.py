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
        _fw_model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=CPU_THREADS)
        logger.info("Faster-Whisper model loaded successfully.")
    return True

def transcribe_chunk(wav_path: Path, language: str, prompt: str = "") -> list[dict]:
    """Runs Faster-Whisper on a single wav chunk. Returns a list of segments."""
    try:
        load_model()
        
        # faster-whisper accepts standard language codes
        lang_code = language if language in ['ru', 'kk', 'en'] else None
        
        segments_generator, info = _fw_model.transcribe(
            str(wav_path),
            language=lang_code,
            beam_size=5,
            word_timestamps=True,
            initial_prompt=prompt if prompt.strip() else None,
            vad_filter=False,             # Не вырезать тишину — пусть модель читает всё
            no_speech_threshold=0.1,      # Дефолт 0.6 — слишком агрессивный: пропускал "Алматы"
            log_prob_threshold=-2.0,      # Дефолт -1.0 — разрешаем неуверенные токены
            condition_on_previous_text=True  # Используем контекст предыдущих слов
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


