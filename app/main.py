import os
import shutil
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import UPLOAD_DIR, RESULT_DIR, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from app.file_manager import generate_task_id, init_task_status, get_task_status, delete_task_files
from app.task_worker import worker_loop, add_task

app = FastAPI(title="STT Centy API", description="Local whisper.cpp STT API")

# Add CORS so webhooks/clients can call it easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to start the background queue worker
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(worker_loop())

@app.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    prompt: str = Form(""),
    callback_url: str = Form(None)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if callback_url and not callback_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="callback_url must start with http:// or https://")

    task_id = generate_task_id()
    
    # Check extension to ensure it is media
    ext = Path(file.filename).suffix.lower()
    
    # Save the file with task_id prefix
    safe_filename = f"{task_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
        
    # Check size
    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        file_path.unlink()
        raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB")

    # Initialize status
    status_data = init_task_status(task_id, file.filename)
    
    # Add to background queue
    await add_task(task_id, file.filename, language, prompt, callback_url)
    
    return JSONResponse(content=status_data)

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    status_data = get_task_status(task_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(content=status_data)

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    json_path = RESULT_DIR / f"{task_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Result not ready or task not found")
    
    # We can just return it as FileResponse for efficiency
    return FileResponse(path=json_path, media_type="application/json")

@app.get("/download/{task_id}/{fmt}")
async def download_result(task_id: str, fmt: str):
    if fmt not in ["txt", "srt", "vtt"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use txt, srt, or vtt")
        
    file_path = RESULT_DIR / f"{task_id}.{fmt}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found or not ready")
        
    return FileResponse(
        path=file_path, 
        media_type="text/plain", 
        filename=f"{task_id}.{fmt}"
    )

@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    delete_task_files(task_id)
    return {"message": "Task and files deleted successfully"}

# Mount static files for the frontend UI
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_path = static_dir / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>UI Building...</h1>")
