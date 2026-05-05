<div align="center">
  <h1>🎙️ TranslateeIQ</h1>
  <p><strong>Turn meeting recordings into searchable transcripts, AI summaries, and actionable minutes — then chat with your meetings.</strong></p>

  <a href="https://github.com/ANUJOMER21/translateeIQ/stargazers">
    <img src="https://img.shields.io/github/stars/ANUJOMER21/translateeIQ?style=for-the-badge&logo=github&color=FFD700" alt="Stars">
  </a>
  <a href="https://github.com/ANUJOMER21/translateeIQ/issues">
    <img src="https://img.shields.io/github/issues/ANUJOMER21/translateeIQ?style=for-the-badge&logo=github" alt="Issues">
  </a>
  <a href="https://github.com/ANUJOMER21/translateeIQ/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/ANUJOMER21/translateeIQ?style=for-the-badge" alt="License">
  </a>

  <br><br>

  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?logo=tailwindcss&logoColor=white" alt="Tailwind">

  <br><br>

  <strong>
    <a href="https://meeting-frontend-pn4443kooa-uc.a.run.app">🌐 Live Demo</a> &nbsp;•&nbsp;
    <a href="https://github.com/ANUJOMER21/translateeIQ/issues">🐛 Report Bug</a> &nbsp;•&nbsp;
    <a href="https://github.com/ANUJOMER21/translateeIQ/issues/new?template=feature_request.md">💡 Request Feature</a>
  </strong>
</div>

---

## ✨ Features

- **🎬 Chunked Upload** — Upload large files with real-time progress (5MB chunks)
- **🎤 Smart Transcription** — Local Whisper ASR with optional mock mode
- **📝 Structured Transcript** — Timestamped + Speaker-labeled using Claude
- **📋 AI Summary** — Automatic concise bullet-point summaries
- **📌 Actionable Minutes** — Extracts decisions, action items (with owner & due date)
- **🔍 Semantic Search** — Powered by ChromaDB vector database
- **💬 Intelligent Chat** — Ask questions about one or all meetings (RAG)
- **🔗 Public Sharing** — Secure tokenized read-only links
- **▶️ Media Player** — Built-in audio/video streaming
- **📄 PDF Export** — Professional Minutes of Meeting PDFs
- **📊 Dashboard Insights** — Trending topics, productivity metrics & stats
- **✅ Action Tracking** — Complete action items from dashboard

**Supported Formats:** `.mp4, .mov, .avi, .mkv, .webm, .mp3, .wav, .m4a, .flac, .aac, .ogg`

---

## 🛠️ Tech Stack

| Layer            | Technology                                      |
|------------------|-------------------------------------------------|
| **Frontend**     | React 18, Vite 5, Tailwind CSS, Zustand        |
| **Backend**      | Django 4.2 + Django REST Framework             |
| **Async**        | Celery 5.3 + Redis                             |
| **AI**           | Whisper (Local) + Anthropic Claude             |
| **Vector Store** | ChromaDB + ONNX MiniLM                         |
| **Storage**      | Google Cloud Storage                           |
| **Deployment**   | Google Cloud Run (API + Worker)                |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ANUJOMER21/translateeIQ.git
cd translateeIQ
2. Frontend
Bashcd frontend
npm install
npm run dev
3. Backend
Bashcd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
python manage.py migrate
python manage.py runserver
4. Additional Services

Redis: redis-server
Celery: celery -A config.celery_app worker -l info

Visit: http://localhost:5173
Tip: Use TRANSCRIPTION_BACKEND=mock in .env for fast development.

📊 Architecture
flowchart LR

    subgraph Client
        A[React Frontend]
    end

    subgraph Backend
        B[Django REST API]
        C[Celery Worker]
        R[Redis / Broker]
    end

    subgraph AI_Services
        D[Whisper ASR]
        E[Claude AI]
        F[ChromaDB]
    end

    subgraph Storage
        G[Google Cloud Storage]
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

☁️ Deployment
Ready for Google Cloud Run.
Deployment scripts are in the deploy/ folder.

📁 Project Structure
texttranslateeIQ/
├── frontend/          # React + Vite SPA
├── backend/           # Django Project
│   ├── apps/
│   │   ├── meetings/
│   │   ├── pipeline/
│   │   ├── agents/
│   │   └── vector_store/
│   └── config/
├── deploy/            # GCP deployment scripts
└── LICENSE

📄 License
Distributed under the MIT License. See LICENSE file for more information.

🙏 Acknowledgments

OpenAI Whisper
Anthropic Claude
ChromaDB

⭐ If you like the project, please give it a star!