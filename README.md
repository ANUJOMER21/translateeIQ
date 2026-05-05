

# 🎙️ TranslateeIQ

**Turn meeting recordings into searchable transcripts, AI summaries, and actionable minutes — then chat with your meetings.**

[Python](https://python.org)
[Django](https://djangoproject.com)
[React](https://react.dev)
[Celery](https://docs.celeryq.dev)
[License](./LICENSE)
[Cloud Run](./deploy/)

  


*Upload a recording → get a transcript, summary, and minutes in minutes → ask AI anything about what was said.*



---

## 🌐 Live Demo

- **App URL:** [https://meeting-frontend-pn4443kooa-uc.a.run.app](https://meeting-frontend-pn4443kooa-uc.a.run.app)

---

## ✨ Features


| Feature                        | Description                                                                         |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| 🎬 **Chunked Upload**          | Upload video/audio files of any size via 5 MB chunks with real-time progress        |
| 🎤 **Transcription**           | Whisper (local) converts speech to text; mock mode for fast development             |
| 📝 **Structured Transcript**   | Claude formats raw text into timestamped, speaker-labeled segments                  |
| 📋 **AI Summary**              | Concise bullet-point summary generated automatically                                |
| 📌 **Minutes of Meeting**      | Decisions, action items (with owner + due date), and notes extracted by AI          |
| 🔍 **Semantic Search**         | Every segment is embedded into ChromaDB for intelligent retrieval                   |
| 💬 **Meeting Chat**            | Ask questions scoped to one meeting or across all meetings with RAG                 |
| 🔗 **Public Meeting Sharing**  | Generate secure tokenized read-only links for external viewers (no login required)  |
| ▶️ **Built-in Media Playback** | Stream uploaded audio/video directly inside private and public meeting detail pages |
| 📄 **Professional PDF Export** | Download polished MOM PDFs for easy sharing and record-keeping                      |
| 📈 **Dashboard Insights**      | See workspace stats, active uploads, recent meetings, and productivity metrics      |
| ✅ **Action Item Tracking**     | Toggle action items done/undone across meetings from one place                      |
| 🔥 **Trending Topics**         | Surface the most discussed topics from your recent meetings                         |
| 👤 **Profile & Preferences**   | Update display name and email notification preferences in-app                       |
| 📊 **Live Pipeline Status**    | Granular step-by-step progress: assembling → transcribing → analyzing → indexing    |


**Supported formats:** Video (`.mp4 .mov .avi .mkv .webm .m4v`) · Audio (`.mp3 .wav .m4a .flac .aac .ogg`)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│           React 18 · Vite · Tailwind · Zustand           │
│    Dashboard · Upload · Meetings · Detail · Chatbot      │
└───────────────────────┬──────────────────────────────────┘
                        │  REST  /api/
          ┌─────────────▼──────────────┐
          │     Django REST Framework   │  ◄── meeting-api (Cloud Run)
          │  /upload/ · /meetings/ · /chat/  │
          └──────┬──────────────┬───────┘
                 │ Celery tasks │ PostgreSQL
    ┌────────────▼───────┐  ┌───▼──────────────────┐
    │   Celery Worker    │  │  Meeting · Transcript │  ◄── meeting-worker (Cloud Run)
    │                    │  │  Summary · MOM        │
    │  1. Assemble GCS   │  │  UploadSession        │
    │  2. Extract audio  │  └───────────────────────┘
    │  3. Whisper ASR    │
    │  4. Claude agents  │──────► ChromaDB
    │  5. Index vectors  │        (embeddings per meeting + global)
    └────────────────────┘
                 │
    ┌────────────▼───────────────────────┐
    │  Google Cloud Storage (GCS)        │
    │  chunks/{session}/ · meetings/{id}/│
    └────────────────────────────────────┘
```

---

## 🧰 Tech Stack


| Layer               | Technology                                                                                           |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **Frontend**        | React 18, Vite 5, Tailwind CSS 3.4, React Router 6, Zustand, Framer Motion, Axios, Lucide Icons      |
| **Backend API**     | Django 4.2, Django REST Framework, SimpleJWT, django-cors-headers, Gunicorn                          |
| **Async Worker**    | Celery 5.3, Redis (broker + result backend), Upstash (cloud Redis)                                   |
| **Transcription**   | OpenAI Whisper (local) · built-in mock for development                                               |
| **AI / LLM**        | Anthropic Claude (`claude-haiku-4-5` by default) for transcript formatting, summaries, MOM, and chat |
| **Vector Store**    | ChromaDB 0.5 with ONNX MiniLM embeddings (CPU, no API key needed)                                    |
| **Media / Storage** | ffmpeg for audio extraction · django-storages + GCS for shared cloud media                           |
| **Infrastructure**  | Google Cloud Run (split API + Worker) · Cloud SQL (PostgreSQL) · Cloud Build                         |


---

## 🚀 Quick Start (Local)

### Prerequisites

- Node.js 18+
- Python 3.11+
- Redis (local or Docker)
- ffmpeg (recommended for video files)

### 1. Clone the repo

```bash
git clone https://github.com/ANUJOMER21/translateeIQ.git
cd translateeIQ
```

### 2. Frontend setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api
```

### 3. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy and configure the env file:

```bash
cp .env.example .env
```

Minimum `.env` for a working local stack:

```env
DJANGO_SECRET_KEY=any-dev-secret-here
DJANGO_DEBUG=True
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Leave blank for mock responses
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5

# Use 'mock' for instant results, 'whisper_local' for real transcription
TRANSCRIPTION_BACKEND=mock
WHISPER_MODEL=base
```

Run migrations:

```bash
python manage.py migrate
```

### 4. Run the stack

Open four terminals:


| Terminal   | Command                                                    |
| ---------- | ---------------------------------------------------------- |
| **Redis**  | `redis-server`                                             |
| **Django** | `cd backend && python manage.py runserver`                 |
| **Celery** | `cd backend && celery -A config.celery_app worker -l info` |
| **Vite**   | `cd frontend && npm run dev`                               |


Open **[http://localhost:5173](http://localhost:5173)** 🎉

---

## ⚡ Pipeline Flow

```
Upload chunks  →  Assemble file  →  Extract audio  →  Whisper ASR
                                                            ↓
        completed  ←  Index vectors  ←  Claude agents  ←  Raw text
```

Frontend polls `GET /api/upload/{session_id}/progress/` and shows granular step labels:

`combining_chunks` → `extracting_audio` → `running_asr` → `formatting_transcript` → `generating_summary` → `generating_mom` → `building_vectors`

---

## 🔧 Configuration Reference

### Frontend (`frontend/.env`)


| Variable       | Default                     | Purpose              |
| -------------- | --------------------------- | -------------------- |
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API base URL |


### Backend (`backend/.env`)


| Variable                | Purpose                                        |
| ----------------------- | ---------------------------------------------- |
| `DJANGO_SECRET_KEY`     | Django secret key (required)                   |
| `DJANGO_DEBUG`          | `True` for dev, `False` for prod               |
| `ALLOWED_HOSTS`         | Comma-separated hostnames                      |
| `DATABASE_URL`          | PostgreSQL URL; omit for SQLite                |
| `CELERY_BROKER_URL`     | Redis broker URL                               |
| `CELERY_RESULT_BACKEND` | Redis result backend URL                       |
| `ANTHROPIC_API_KEY`     | Claude API key                                 |
| `ANTHROPIC_MODEL`       | Claude model ID                                |
| `TRANSCRIPTION_BACKEND` | `mock` or `whisper_local`                      |
| `WHISPER_MODEL`         | `tiny` / `base` / `small` / `medium` / `large` |
| `GS_MEDIA_BUCKET`       | GCS bucket name (Cloud Run split deployment)   |
| `GCP_PROJECT_ID`        | GCP project ID                                 |
| `CORS_ALLOWED_ORIGINS`  | Frontend URL(s), comma-separated               |


---

## ☁️ Deployment (Google Cloud Run)

The app is designed for a **split deployment** — separate Cloud Run services for the API and the Celery worker sharing a GCS media bucket.

### Services deployed


| Service            | Description                             |
| ------------------ | --------------------------------------- |
| `meeting-api`      | Django/Gunicorn — handles HTTP requests |
| `meeting-worker`   | Celery — runs the processing pipeline   |
| `meeting-frontend` | nginx — serves the React SPA            |


### Deploy

```bash
# Copy and fill in your values
cp deploy/env.backend.yaml.example deploy/env.backend.yaml

# Deploy backend (API + Worker)
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export BACKEND_ENV_FILE="deploy/env.backend.yaml"
./deploy/deploy-backend.sh

# Deploy frontend
export VITE_API_URL="https://meeting-api-xxxxx-uc.a.run.app/api"
./deploy/deploy-frontend.sh
```

Required GCP services: Cloud Run · Cloud Build · Artifact Registry · Cloud SQL (PostgreSQL) · Cloud Storage · Upstash Redis

---

## 📁 Project Structure

```
translateeIQ/
├── frontend/                    # React + Vite SPA
│   ├── src/
│   │   ├── pages/               # Dashboard, Upload, Meetings, Detail, Chatbot
│   │   ├── components/          # UI, layout, upload, meeting, chat components
│   │   ├── hooks/               # useUpload (chunked upload + polling)
│   │   ├── services/            # API, auth, meeting, upload, chat services
│   │   ├── store/               # Zustand stores (auth, toast)
│   │   └── utils/               # meetingUtils, notify, tokenStorage
│   ├── Dockerfile               # nginx SPA container (port 8080)
│   └── cloudbuild.yaml          # Cloud Build with VITE_API_URL substitution
│
├── backend/
│   ├── apps/
│   │   ├── meetings/            # Models, REST views, serializers, Celery tasks
│   │   ├── pipeline/            # Audio extraction (ffmpeg), Whisper transcription
│   │   ├── agents/              # Claude agents: transcript, summary, MOM, chat
│   │   └── vector_store/        # ChromaDB index and retrieval
│   ├── config/                  # Django settings, URLs, Celery app, Redis utils
│   ├── docker-entrypoint.sh     # Migrate + collectstatic + gunicorn
│   └── run-celery-cloud-run.sh  # Celery worker startup for Cloud Run
│
└── deploy/
    ├── deploy-backend.sh        # Build + deploy meeting-api and meeting-worker
    ├── deploy-frontend.sh       # Build + deploy meeting-frontend
    ├── env.backend.yaml.example # Backend env template
    └── env.frontend.yaml.example
```

---

## 🛠️ Development Tips

**Run without heavy dependencies:**


| Skip                         | Behavior                                                      |
| ---------------------------- | ------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`          | All agents return mock structured output — great for UI dev   |
| `TRANSCRIPTION_BACKEND=mock` | No Whisper run; placeholder text feeds the pipeline instantly |
| ffmpeg                       | Only needed for video files; audio files work without it      |
| ChromaDB errors              | Non-blocking; chat falls back gracefully if indexing fails    |


**Speed up local dev:**

Add `CELERY_TASK_ALWAYS_EAGER=True` to `backend/.env` to run Celery tasks synchronously in the Django process — no separate worker needed.

---

## 📡 API Reference

All endpoints are under `/api/`. Most endpoints require JWT auth unless marked public.


| Area                 | Endpoints                                                                                                      |
| -------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Auth**             | `POST /auth/register/` · `POST /auth/token/` · `POST /auth/token/refresh/` · `GET/PATCH /auth/me/`             |
| **Meetings**         | `GET /meetings/` · `GET /meetings/{id}/` · `PATCH /meetings/{id}/` · `DELETE /meetings/{id}/`                  |
| **Nested resources** | `GET /meetings/{id}/transcript/` · `/summary/` · `/mom/` · `GET /meetings/{id}/pdf/`                           |
| **Upload**           | `POST /upload/init/` · `POST /upload/chunk/` · `POST /upload/complete/` · `GET /upload/{session_id}/progress/` |
| **Chat**             | `POST /chat/` with `{ meeting_id?, message, scope: "this"                                                      |
| **Public share**     | `GET /public/{token}/` (public read-only meeting view, no auth)                                                |
| **Dashboard**        | `GET /dashboard/` · `GET /action-items/` · `PATCH /action-items/{item_id}/` · `GET /trending-topics/`          |
| **Health**           | `GET /health/` (public)                                                                                        |


---

## 📄 License

Released under the **MIT License** — see [LICENSE](./LICENSE).

Third-party libraries (Django, React, Whisper, ChromaDB, Anthropic SDK, and others) remain under their respective licenses.

---

## 🙏 Acknowledgments

Built on top of amazing open-source work:

- [OpenAI Whisper](https://github.com/openai/whisper) — speech-to-text
- [Anthropic Claude](https://anthropic.com) — language model for AI features
- [ChromaDB](https://www.trychroma.com) — vector embeddings and retrieval
- [Django](https://djangoproject.com) · [Celery](https://docs.celeryq.dev) · [React](https://react.dev) · [Tailwind CSS](https://tailwindcss.com)

---

Built with ❤️ · [github.com/ANUJOMER21/translateeIQ](https://github.com/ANUJOMER21/translateeIQ)