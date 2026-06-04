import logging
import os
import json
from pathlib import Path
from vosk import Model, KaldiRecognizer
import wave

from app.config import MODEL_PATH

logger = logging.getLogger(__name__)

# Lazy loading of Vosk model to prevent loading on every chunk
_vosk_model = None

def load_model():
    global _vosk_model
    if _vosk_model is None:
        if not os.path.exists(MODEL_PATH):
            logger.error(f"Vosk model not found at {MODEL_PATH}")
            return False
            
        logger.info("Loading Vosk STT model into memory...")
        # Vosk requires the extracted folder path
        _vosk_model = Model(MODEL_PATH)
        logger.info("Vosk model loaded successfully.")
    return True

def transcribe_chunk(wav_path: Path, language: str) -> list[dict]:
    """Runs Vosk STT on a single wav chunk. Returns a list of segments."""
    if language == 'kk':
        logger.warning("Current Vosk model is optimized for Russian only.")
        
    try:
        if not load_model():
            return []
            
        wf = wave.open(str(wav_path), "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            logger.error("Audio file must be WAV format mono PCM.")
            return []
            
        rec = KaldiRecognizer(_vosk_model, wf.getframerate())
        rec.SetWords(True)
        
        segments = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if 'text' in res and res['text'].strip():
                    # Find start/end from words if available
                    start = res.get('result', [{}])[0].get('start', 0.0)
                    end = res.get('result', [{}])[-1].get('end', 0.0)
                    segments.append({
                        "start": float(start),
                        "end": float(end),
                        "text": res['text']
                    })
                    
        res = json.loads(rec.FinalResult())
        if 'text' in res and res['text'].strip():
            start = res.get('result', [{}])[0].get('start', 0.0) if res.get('result') else 0.0
            end = res.get('result', [{}])[-1].get('end', 0.0) if res.get('result') else 0.0
            segments.append({
                "start": float(start),
                "end": float(end),
                "text": res['text']
            })
            
        return segments

    except Exception as e:
        logger.error(f"Exception during Vosk STT execution: {e}")
        return []


