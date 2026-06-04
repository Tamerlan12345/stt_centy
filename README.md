# STT Centy

Production-ready Speech-to-Text backend powered by `whisper.cpp` and `FastAPI`.

## Требования
- Python 3.11+
- FFmpeg (установлен в системе и доступен в PATH)
- `whisper.cpp` бинарники (`whisper-cli.exe`)

## Установка

1. Создайте виртуальное окружение:
   ```cmd
   python -m venv venv
   call venv\Scripts\activate
   ```

2. Установите зависимости:
   ```cmd
   pip install -r requirements.txt
   ```

3. Подготовьте модели и бинарники:
   - Скачайте `whisper-cli.exe` и поместите в папку `bin/`.
   - Скачайте модель `ggml-base.bin` и поместите в папку `models/`.

## Запуск
```cmd
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Откройте в браузере: `http://localhost:8000`

## API Endpoints

- `POST /upload` (multipart/form-data: `file`, `language`) -> возвращает `task_id`
- `GET /status/{task_id}` -> статус обработки
- `GET /result/{task_id}` -> JSON с полным результатом и таймкодами
- `GET /download/{task_id}/txt` -> чистый текст
- `GET /download/{task_id}/srt` -> субтитры SRT
- `GET /download/{task_id}/vtt` -> веб-субтитры VTT
- `DELETE /task/{task_id}` -> очистка файлов задачи
