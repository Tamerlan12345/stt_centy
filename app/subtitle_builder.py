import json
from pathlib import Path
from app.config import RESULT_DIR

def format_timestamp(seconds: float, separator: str = ",") -> str:
    """Formats float seconds into HH:MM:SS,mmm or HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    # Handle ms rounding to 1000
    if ms == 1000:
        ms = 0
        secs += 1
        if secs == 60:
            secs = 0
            minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"

def build_txt(segments: list[dict]) -> str:
    """Builds a plain text string from segments."""
    return " ".join([seg["text"] for seg in segments])

def build_srt(segments: list[dict]) -> str:
    """Builds an SRT formatted string."""
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_str = format_timestamp(seg["start"], ",")
        end_str = format_timestamp(seg["end"], ",")
        lines.append(str(i))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines)

def build_vtt(segments: list[dict]) -> str:
    """Builds a WebVTT formatted string."""
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, start=1):
        start_str = format_timestamp(seg["start"], ".")
        end_str = format_timestamp(seg["end"], ".")
        lines.append(str(i))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines)

def save_results(task_id: str, segments: list[dict], metadata: dict) -> dict:
    """Saves TXT, SRT, VTT, and JSON results to the results folder.
    Returns the final JSON data.
    """
    full_text = build_txt(segments)
    srt_content = build_srt(segments)
    vtt_content = build_vtt(segments)
    
    txt_path = RESULT_DIR / f"{task_id}.txt"
    srt_path = RESULT_DIR / f"{task_id}.srt"
    vtt_path = RESULT_DIR / f"{task_id}.vtt"
    json_path = RESULT_DIR / f"{task_id}.json"
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)
        
    final_json = {
        "task_id": task_id,
        "status": "completed",
        "language": metadata.get("language", "auto"),
        "model": "whisper-base",
        "duration_seconds": segments[-1]["end"] if segments else 0.0,
        "text": full_text,
        "segments": segments,
        "files": {
            "txt": f"/download/{task_id}/txt",
            "srt": f"/download/{task_id}/srt",
            "vtt": f"/download/{task_id}/vtt",
            "json": f"/result/{task_id}"
        }
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
        
    return final_json
