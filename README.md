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

- `POST /upload` (multipart/form-data: `file`, `language`, `prompt`, `callback_url`) -> возвращает `task_id`
- `GET /status/{task_id}` -> статус обработки
- `GET /result/{task_id}` -> JSON с полным результатом и таймкодами
- `GET /download/{task_id}/txt` -> чистый текст
- `GET /download/{task_id}/srt` -> субтитры SRT
- `GET /download/{task_id}/vtt` -> веб-субтитры VTT
- `DELETE /task/{task_id}` -> очистка файлов задачи

## Возврат результата: polling vs webhook (callback_url)

Распознавание — фоновая задача (очередь на 1 воркер), поэтому `/upload` отвечает мгновенно
и не блокирует HTTP-запрос до конца транскрибации. Есть два способа получить результат:

### 1. Polling (без каких-либо изменений на вашей стороне)
Опрашивайте `GET /status/{task_id}` до `status == "completed"` (или `"failed"`), затем читайте
`GET /result/{task_id}`.

### 2. Webhook / callback (push, без n8n)
Передайте `callback_url` в `/upload` — сервис сам отправит `POST` с результатом на этот URL,
как только задача завершится. Опрашивать `/status` не нужно.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@audio.mp3" \
  -F "language=ru" \
  -F "callback_url=https://example.com/my-webhook"
```

Сервис выполнит `POST {callback_url}` с телом, идентичным ответу `GET /result/{task_id}`
(при ошибке — со `status: "failed"` и полем `message`):

```json
{
  "task_id": "20260707_120530_1a2b",
  "status": "completed",
  "language": "ru",
  "model": "whisper-base",
  "duration_seconds": 42.5,
  "text": "...",
  "segments": [{"start": 0.0, "end": 3.2, "text": "..."}],
  "files": {
    "txt": "/download/20260707_120530_1a2b/txt",
    "srt": "/download/20260707_120530_1a2b/srt",
    "vtt": "/download/20260707_120530_1a2b/vtt",
    "json": "/result/20260707_120530_1a2b"
  }
}
```

Особенности:
- `callback_url` должен начинаться с `http://` или `https://`, иначе `/upload` вернёт `400`.
- Доставка колбэка — до 3 попыток с задержкой (2с, 4с) между ними, таймаут 15с на попытку.
- Успех/неуспех доставки сохраняется в `GET /status/{task_id}` как `callback_delivered: true|false` —
  так что если получатель был недоступен, результат всё равно можно забрать через `/result/{task_id}`.
- `callback_url` может указывать на что угодно, принимающее POST JSON — включая n8n Webhook node,
  если результат нужно потом маршрутизировать в другие системы. n8n для самого получения
  транскрипции не требуется.
