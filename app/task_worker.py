import asyncio
import logging
from pathlib import Path

from app.file_manager import update_task_status, get_status_file, delete_task_files
from app.audio_converter import convert_to_wav, chunk_audio
from app.transcriber import transcribe_chunk
from app.subtitle_builder import save_results
from app.config import UPLOAD_DIR, TEMP_DIR, CHUNK_SECONDS

logger = logging.getLogger(__name__)

# Single queue to enforce 1 concurrent task
task_queue = asyncio.Queue()

async def add_task(task_id: str, original_filename: str, language: str):
    await task_queue.put({
        "task_id": task_id,
        "filename": original_filename,
        "language": language
    })
    logger.info(f"Task {task_id} added to queue. Queue size: {task_queue.qsize()}")

async def process_task(task_info: dict):
    task_id = task_info["task_id"]
    language = task_info["language"]
    
    logger.info(f"Starting processing for task {task_id}")
    
    # Locate original uploaded file
    input_files = list(UPLOAD_DIR.glob(f"{task_id}_*"))
    if not input_files:
        update_task_status(task_id, {"status": "failed", "message": "Original file not found"})
        return
        
    input_path = input_files[0]
    wav_path = TEMP_DIR / f"{task_id}.wav"
    
    try:
        # CONVERTING
        update_task_status(task_id, {"status": "converting", "message": "Конвертация в WAV"})
        success = await asyncio.to_thread(convert_to_wav, input_path, wav_path)
        if not success:
            raise Exception("FFmpeg conversion failed.")
            
        # CHUNKING
        update_task_status(task_id, {"status": "chunking", "message": "Разделение аудио"})
        chunks = await asyncio.to_thread(chunk_audio, wav_path, task_id)
        if not chunks:
            # If the file was very short, it might not chunk depending on ffmpeg version.
            # But our chunk_audio relies on segment, so it should always return at least 1 chunk.
            raise Exception("No chunks generated.")
            
        # TRANSCRIBING
        update_task_status(task_id, {"status": "transcribing", "message": "Распознавание речи"})
        all_segments = []
        
        for i, chunk_path in enumerate(chunks):
            logger.info(f"Transcribing chunk {i+1}/{len(chunks)}")
            segments = await asyncio.to_thread(transcribe_chunk, chunk_path, language)
            
            # Adjust timestamps by adding chunk offset
            offset = i * CHUNK_SECONDS
            for seg in segments:
                seg["start"] += offset
                seg["end"] += offset
                
            all_segments.extend(segments)
            
        # FINALIZING
        update_task_status(task_id, {"status": "finalizing", "message": "Формирование результата"})
        metadata = {"language": language}
        final_result = await asyncio.to_thread(save_results, task_id, all_segments, metadata)
        
        update_task_status(task_id, {
            "status": "completed",
            "message": "Успешно",
            **final_result
        })
        
        # Cleanup
        logger.info(f"Task {task_id} completed successfully. Cleaning up temp files.")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        update_task_status(task_id, {"status": "failed", "message": str(e)})
        
    finally:
        # Always delete the input and temp files, but keep results
        try:
            # Delete from uploads
            for f in UPLOAD_DIR.glob(f"{task_id}_*"):
                f.unlink(missing_ok=True)
            # Delete from temp
            for f in TEMP_DIR.glob(f"{task_id}*"):
                f.unlink(missing_ok=True)
        except Exception as cleanup_err:
            logger.error(f"Cleanup failed for {task_id}: {cleanup_err}")

async def worker_loop():
    logger.info("Task worker loop started.")
    while True:
        task_info = await task_queue.get()
        try:
            await process_task(task_info)
        except Exception as e:
            logger.error(f"Worker loop caught exception: {e}")
        finally:
            task_queue.task_done()
