## Architecture
- **Language**: Python 3.11
- **Framework**: FastAPI
- **Backend Service**: STT Centy
- **Core STT**: whisper.cpp (via subprocess)
- **Audio Processing**: FFmpeg (via subprocess)
- **Concurrency**: `asyncio.Queue` with a single background worker to enforce the 1-task limit (3GB RAM constraint).
- **State Storage**: File-system based (`results/{task_id}_status.json`) to avoid DB dependency while maintaining state across restarts.
- **Frontend**: Vanilla HTML/JS/CSS with a modern UI, served statically by FastAPI.

## Module Registry
| Module | Path | Responsibility | Depends on | Depended on by |
|--------|------|----------------|------------|----------------|
| main | `app/main.py` | FastAPI entrypoint, API routes | `task_worker`, `file_manager` | - |
| config | `app/config.py` | Configuration constants | - | all |
| task_worker | `app/task_worker.py` | Background queue processor | `audio_converter`, `transcriber`, `subtitle_builder` | `main` |
| audio_converter | `app/audio_converter.py` | FFmpeg wrapper (convert/chunk) | `config` | `task_worker` |
| transcriber | `app/transcriber.py` | whisper.cpp wrapper | `config` | `task_worker` |
| subtitle_builder | `app/subtitle_builder.py` | SRT/VTT/JSON generation | `config` | `task_worker` |
| file_manager | `app/file_manager.py` | Disk operations, path traversal safety | `config` | all |

## Decisions Log
| # | Date | Decision | Context | Alternatives rejected | Reversal cost |
|---|------|----------|---------|-----------------------|---------------|
| 1 | 2026-06-04 | File-based status storage | Need persistent task tracking without a database. | SQLite (too heavy for MVP), In-memory dict (lost on restart). | Low |
| 2 | 2026-06-04 | `asyncio.Queue` worker | Need to limit concurrent STT processing to 1 due to 3GB RAM limit. | Celery/Redis (too heavy). ThreadPoolExecutor (less control). | Low |
| 3 | 2026-06-04 | Windows Executable Name | The OS is Windows. `whisper-cli` defaults to `whisper-cli.exe` in config. | `.sh` or linux binaries. | Low |

## Task Log
| # | Task | Mode | Status | Files | Goals satisfied (G1–G4) | Notes |
|---|------|------|--------|-------|-------------------------|-------|
| 1 | Setup Base Project & API | Feature | In Progress | `PROJECT.md`, `app/*` | G1, G2, G3, G4 | - |

## Known Issues & Technical Debt
| Issue | Severity | Location | Impact on G1 / G3 / G4 | Owner | Plan |
|-------|----------|----------|------------------------|-------|------|
| Whisper binary missing | High | `bin/` | Will crash if user doesn't place binary | AI | Document setup steps clearly |
| FFmpeg missing | High | System | Will crash if not installed | AI | Document setup steps clearly |

## Build & Test Commands
- Run Server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
