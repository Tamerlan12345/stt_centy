import subprocess
import logging
import json
import os
from pathlib import Path

from app.config import WHISPER_BIN, MODEL_PATH, CPU_THREADS

logger = logging.getLogger(__name__)

def parse_whisper_json(json_path: Path) -> list[dict]:
    """Parses the JSON output from whisper.cpp and returns a list of segments.
    Normalizes the schema since whisper.cpp JSON schema might vary.
    Returns: [{"start": float, "end": float, "text": str}, ...]
    """
    if not json_path.exists():
        return []
    
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []

    segments = []
    # whisper.cpp usually stores transcription in "transcription"
    transcription = data.get("transcription", [])
    
    for item in transcription:
        # Offsets are usually in milliseconds
        start_ms = item.get("offsets", {}).get("from", 0)
        end_ms = item.get("offsets", {}).get("to", 0)
        text = item.get("text", "").strip()
        
        if text:
            segments.append({
                "start": start_ms / 1000.0,
                "end": end_ms / 1000.0,
                "text": text
            })
    return segments

def transcribe_chunk(wav_path: Path, language: str) -> list[dict]:
    """Runs whisper.cpp on a single wav chunk. Returns a list of segments."""
    
    cmd = [
        WHISPER_BIN,
        "-m", MODEL_PATH,
        "-f", str(wav_path),
        "-l", language,
        "-t", str(CPU_THREADS),
        "-oj"  # Output JSON
    ]
    
    logger.info(f"Running whisper.cpp: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            logger.error(f"Whisper CLI failed: {process.stderr}")
            # Sometimes whisper.cpp returns non-zero but still generated output, but usually it's an error.
    except FileNotFoundError:
        logger.error(f"Whisper binary not found at {WHISPER_BIN}")
        # Return a mock segment for testing if binary is missing
        return [{"start": 0.0, "end": 2.0, "text": "[Whisper CLI not found - mocked response]"}]
    except Exception as e:
        logger.error(f"Exception during whisper execution: {e}")
        return []

    # whisper-cli with -oj usually outputs to {wav_path}.json or {wav_path.name}.json
    # Let's check both possibilities.
    expected_json_1 = wav_path.with_suffix(".wav.json")
    expected_json_2 = wav_path.with_name(wav_path.name + ".json")
    expected_json_3 = wav_path.with_suffix(".json")
    
    json_path = None
    for p in [expected_json_1, expected_json_2, expected_json_3]:
        if p.exists():
            json_path = p
            break
            
    if json_path:
        segments = parse_whisper_json(json_path)
        # Cleanup json file
        json_path.unlink(missing_ok=True)
        return segments
    
    # If JSON file wasn't created, we fallback to parsing stdout? 
    # For MVP, just return empty.
    logger.error("Whisper JSON output not found.")
    return []
