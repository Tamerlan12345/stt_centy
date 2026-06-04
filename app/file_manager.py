import json
import uuid
from datetime import datetime
import shutil
from pathlib import Path

from app.config import UPLOAD_DIR, RESULT_DIR, TEMP_DIR

def generate_task_id() -> str:
    """Generates a task_id like 20260604_120530_1a2b"""
    now = datetime.now()
    date_part = now.strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:4]
    return f"{date_part}_{short_uuid}"

def get_status_file(task_id: str) -> Path:
    return RESULT_DIR / f"{task_id}_status.json"

def init_task_status(task_id: str, filename: str):
    """Initializes the task status file."""
    status_data = {
        "task_id": task_id,
        "status": "queued",
        "filename": filename,
        "message": "Файл принят в обработку",
        "created_at": datetime.now().isoformat()
    }
    update_task_status(task_id, status_data)
    return status_data

def update_task_status(task_id: str, updates: dict):
    """Updates the task status file with new data."""
    status_file = get_status_file(task_id)
    data = {}
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
    
    data.update(updates)
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_task_status(task_id: str) -> dict:
    """Reads the current status of a task."""
    status_file = get_status_file(task_id)
    if not status_file.exists():
        return None
    with open(status_file, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_task_files(task_id: str):
    """Deletes all files associated with a task_id."""
    # Delete from uploads
    for f in UPLOAD_DIR.glob(f"{task_id}_*"):
        f.unlink(missing_ok=True)
    
    # Delete from temp
    for f in TEMP_DIR.glob(f"{task_id}*"):
        f.unlink(missing_ok=True)
        
    # Delete from results
    for f in RESULT_DIR.glob(f"{task_id}*"):
        f.unlink(missing_ok=True)
