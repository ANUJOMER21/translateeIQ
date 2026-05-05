# translateeIQ — Backend

## Quick Start

### 1. Install dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum
```

### 3. Start Redis (via Docker)
```bash
docker-compose up -d redis
```

### 4. Run migrations
```bash
python manage.py migrate
python manage.py createsuperuser  # optional
```

### 5. Start Django
```bash
python manage.py runserver 0.0.0.0:8000
```

### 6. Start Celery worker (new terminal)
```bash
celery -A config.celery_app worker --loglevel=info
```

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/meetings/ | List all meetings |
| GET | /api/meetings/{id}/ | Meeting detail |
| PATCH | /api/meetings/{id}/ | Update title |
| DELETE | /api/meetings/{id}/ | Delete meeting |
| GET | /api/meetings/{id}/transcript/ | Get transcript |
| GET | /api/meetings/{id}/summary/ | Get summary |
| GET | /api/meetings/{id}/mom/ | Get MOM |
| POST | /api/upload/init/ | Start chunked upload |
| POST | /api/upload/chunk/ | Send a chunk |
| POST | /api/upload/complete/ | Assemble & process |
| GET | /api/upload/{session_id}/progress/ | Poll progress |
| POST | /api/chat/ | Chat with AI |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OPENAI_API_KEY | — | Required for AI agents |
| TRANSCRIPTION_BACKEND | mock | whisper_local / openai_api / mock |
| WHISPER_MODEL | base | tiny / base / small / medium / large |
| CELERY_BROKER_URL | redis://localhost:6379/0 | Redis URL |

## Transcription Backends

- **mock**: No setup needed. Returns placeholder text (development)
- **whisper_local**: Runs Whisper locally. Needs `openai-whisper` + ffmpeg
- **openai_api**: Uses OpenAI Whisper API. Needs `OPENAI_API_KEY`
