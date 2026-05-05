<div align="center">
  <h1>🎙️ TranslateeIQ</h1>
  <p><strong>Turn meeting recordings into searchable transcripts, AI summaries, and actionable minutes — then chat with your meetings.</strong></p>

  <a href="https://github.com/ANUJOMER21/translateeIQ/stargazers">
    <img src="https://img.shields.io/github/stars/ANUJOMER21/translateeIQ?style=for-the-badge&logo=github&color=FFD700" />
  </a>
  <a href="https://github.com/ANUJOMER21/translateeIQ/issues">
    <img src="https://img.shields.io/github/issues/ANUJOMER21/translateeIQ?style=for-the-badge&logo=github" />
  </a>
  <a href="https://github.com/ANUJOMER21/translateeIQ/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/ANUJOMER21/translateeIQ?style=for-the-badge" />
  </a>

<br><br>

  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?logo=tailwindcss&logoColor=white" />

<br><br>

  <strong>
    <a href="https://meeting-frontend-pn4443kooa-uc.a.run.app">🌐 Live Demo</a> •
    <a href="https://github.com/ANUJOMER21/translateeIQ/issues">🐛 Report Bug</a> •
    <a href="https://github.com/ANUJOMER21/translateeIQ/issues/new?template=feature_request.md">💡 Request Feature</a>
  </strong>
</div>

---

## ✨ Features

* 🎬 Chunked Upload (5MB chunks)
* 🎤 Whisper-based transcription
* 📝 Claude-powered structured transcripts
* 📋 AI summaries & meeting minutes
* 🔍 Semantic search (ChromaDB)
* 💬 Chat with meetings (RAG)
* 🔗 Public sharing links
* 📄 PDF export
* 📊 Dashboard insights
* ✅ Action tracking

---

## 🛠️ Tech Stack

| Layer     | Technology                        |
| --------- | --------------------------------- |
| Frontend  | React 18, Vite, Tailwind, Zustand |
| Backend   | Django + DRF                      |
| Async     | Celery + Redis                    |
| AI        | Whisper + Claude                  |
| Vector DB | ChromaDB                          |
| Storage   | Google Cloud Storage              |

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/ANUJOMER21/translateeIQ.git
cd translateeIQ
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### 4. Services

```bash
redis-server
celery -A config.celery_app worker -l info
```

👉 Open: http://localhost:5173

---

## 📊 Architecture

```mermaid
flowchart LR

    subgraph Client
        A[React Frontend]
    end

    subgraph Backend
        B[Django REST API]
        C[Celery Worker]
        R[Redis]
    end

    subgraph AI
        D[Whisper]
        E[Claude]
        F[ChromaDB]
    end

    subgraph Storage
        G[GCS]
    end

    A --> B
    B --> G
    B --> R
    R --> C
    C --> D
    C --> E
    C --> F
    F --> B
    G --> B
```

---

## ☁️ Deployment

Deployed on Google Cloud Run
Scripts available in `/deploy`

---

## 📁 Project Structure

```bash
translateeIQ/
├── frontend/
├── backend/
│   ├── apps/
│   └── config/
├── deploy/
└── LICENSE
```

---

## 📄 License

MIT License

---

## 🙏 Credits

* OpenAI Whisper
* Anthropic Claude
* ChromaDB

---

⭐ Star this repo if you found it useful!
