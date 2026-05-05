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
#mermaid-diagram-mermaid-vby9m8j{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-diagram-mermaid-vby9m8j .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-diagram-mermaid-vby9m8j .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-diagram-mermaid-vby9m8j .error-icon{fill:#552222;}#mermaid-diagram-mermaid-vby9m8j .error-text{fill:#552222;stroke:#552222;}#mermaid-diagram-mermaid-vby9m8j .edge-thickness-normal{stroke-width:1px;}#mermaid-diagram-mermaid-vby9m8j .edge-thickness-thick{stroke-width:3.5px;}#mermaid-diagram-mermaid-vby9m8j .edge-pattern-solid{stroke-dasharray:0;}#mermaid-diagram-mermaid-vby9m8j .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-diagram-mermaid-vby9m8j .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-diagram-mermaid-vby9m8j .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-diagram-mermaid-vby9m8j .marker{fill:#666;stroke:#666;}#mermaid-diagram-mermaid-vby9m8j .marker.cross{stroke:#666;}#mermaid-diagram-mermaid-vby9m8j svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-diagram-mermaid-vby9m8j p{margin:0;}#mermaid-diagram-mermaid-vby9m8j .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-diagram-mermaid-vby9m8j .cluster-label text{fill:#333;}#mermaid-diagram-mermaid-vby9m8j .cluster-label span{color:#333;}#mermaid-diagram-mermaid-vby9m8j .cluster-label span p{background-color:transparent;}#mermaid-diagram-mermaid-vby9m8j .label text,#mermaid-diagram-mermaid-vby9m8j span{fill:#000000;color:#000000;}#mermaid-diagram-mermaid-vby9m8j .node rect,#mermaid-diagram-mermaid-vby9m8j .node circle,#mermaid-diagram-mermaid-vby9m8j .node ellipse,#mermaid-diagram-mermaid-vby9m8j .node polygon,#mermaid-diagram-mermaid-vby9m8j .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-diagram-mermaid-vby9m8j .rough-node .label text,#mermaid-diagram-mermaid-vby9m8j .node .label text,#mermaid-diagram-mermaid-vby9m8j .image-shape .label,#mermaid-diagram-mermaid-vby9m8j .icon-shape .label{text-anchor:middle;}#mermaid-diagram-mermaid-vby9m8j .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-diagram-mermaid-vby9m8j .rough-node .label,#mermaid-diagram-mermaid-vby9m8j .node .label,#mermaid-diagram-mermaid-vby9m8j .image-shape .label,#mermaid-diagram-mermaid-vby9m8j .icon-shape .label{text-align:center;}#mermaid-diagram-mermaid-vby9m8j .node.clickable{cursor:pointer;}#mermaid-diagram-mermaid-vby9m8j .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-diagram-mermaid-vby9m8j .arrowheadPath{fill:#333333;}#mermaid-diagram-mermaid-vby9m8j .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-diagram-mermaid-vby9m8j .flowchart-link{stroke:#666;fill:none;}#mermaid-diagram-mermaid-vby9m8j .edgeLabel{background-color:white;text-align:center;}#mermaid-diagram-mermaid-vby9m8j .edgeLabel p{background-color:white;}#mermaid-diagram-mermaid-vby9m8j .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-diagram-mermaid-vby9m8j .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-diagram-mermaid-vby9m8j .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-diagram-mermaid-vby9m8j .cluster text{fill:#333;}#mermaid-diagram-mermaid-vby9m8j .cluster span{color:#333;}#mermaid-diagram-mermaid-vby9m8j div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-diagram-mermaid-vby9m8j .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-diagram-mermaid-vby9m8j rect.text{fill:none;stroke-width:0;}#mermaid-diagram-mermaid-vby9m8j .icon-shape,#mermaid-diagram-mermaid-vby9m8j .image-shape{background-color:white;text-align:center;}#mermaid-diagram-mermaid-vby9m8j .icon-shape p,#mermaid-diagram-mermaid-vby9m8j .image-shape p{background-color:white;padding:2px;}#mermaid-diagram-mermaid-vby9m8j .icon-shape rect,#mermaid-diagram-mermaid-vby9m8j .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-diagram-mermaid-vby9m8j :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}React FrontendDjango REST APICelery WorkerWhisper ASRClaude AIChromaDBGoogle Cloud Storage

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



  Made with ❤️ for teams who want meetings to be actually useful.


  ⭐ If you like the project, please give it a star!