# 🛡️ CampusSafe

AI-powered campus safety web application built for DAVV Indore.

CampusSafe helps students report safety incidents, send SOS alerts to guardians, and ask an AI chatbot for real-time safety guidance — all running locally with a self-built AI layer, no external API dependency.

---

## Features

- **Live Safety Map** — DAVV campus zones color-coded green, orange, or red, updated automatically as new reports come in
- **SOS Alerts** — one-tap emergency alert using real GPS location, emailed instantly to a guardian
- **Incident Reporting** — students describe what happened; AI reads the description and adjusts the severity if it sounds more serious than the rating given
- **AI Safety Chat** — ask questions like "is it safe to walk near SCSIT right now?" and get answers grounded in real, current campus data
- **Admin Dashboard** — live charts, SOS history, and an AI-generated safety briefing
- **Student Profile** — manage guardian contact and view personal alert/report history

## How the AI Works

CampusSafe implements three AI concepts, all running fully offline through a local language model:

**1. Sentiment Analysis**
TextBlob reads every incident description and scores how serious the language sounds. The higher of this AI score and the student's own severity rating is always used, so a report is never under-rated just because a student minimized it while describing it.

**2. Retrieval-based Search (RAG)**
Incident reports are converted into 768-number vector embeddings using Ollama's `nomic-embed-text` model, stored in a plain JSON file, and compared using cosine similarity computed with NumPy. This finds relevant past incidents by *meaning*, not just matching keywords.

This was originally built with ChromaDB, a dedicated vector database. Isolated testing traced a hard, unrecoverable process crash to ChromaDB's native `hnswlib` indexing library on Windows — reproducible even with a minimal test vector, unrelated to any of our own application code. Rather than depend on an unstable library, the same retrieval concept was rebuilt from scratch using a JSON file and a hand-written cosine similarity function, giving full control and a fully understood, stable implementation.

**3. Agent-style Tool Routing**
Before answering, the AI decides whether a question is about a specific zone's current status or about past incidents, and pulls the relevant live data accordingly before generating its response.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Database | SQLite |
| AI Model | Ollama (qwen2.5:3b + nomic-embed-text) |
| Maps | Folium + OpenStreetMap |
| Sentiment | TextBlob |
| Vector Search | NumPy (cosine similarity) |
| Email Alerts | smtplib (Gmail) |
| Charts | Plotly |
| Location | streamlit-geolocation (browser GPS) |


## Screenshots

### Login & Registration
<img width="1920" height="856" alt="Image" src="https://github.com/user-attachments/assets/0b39569a-2458-455a-b987-b31b5b5de088" />
<img width="1920" height="731" alt="Image" src="https://github.com/user-attachments/assets/dce87883-e38b-45ac-a5b5-4eb0f83a966f" />
<img width="1920" height="725" alt="Image" src="https://github.com/user-attachments/assets/028fb1e8-392f-4080-a750-7f9e8bca0a45" />
<img width="1920" height="862" alt="Image" src="https://github.com/user-attachments/assets/2bb1b67b-265a-493a-9231-3aa4d4736432" />
<img width="1904" height="881" alt="Image" src="https://github.com/user-attachments/assets/9d6d6646-73e2-4e69-9bb6-f4fad1f01e94" />
<img width="1920" height="859" alt="Image" src="https://github.com/user-attachments/assets/7a8ccdec-4b8b-4539-8980-2d689cef7b07" />
<img width="1920" height="850" alt="Image" src="https://github.com/user-attachments/assets/57cceba2-3001-483c-8cde-daf3c64f0882" />
<img width="1920" height="857" alt="Image" src="https://github.com/user-attachments/assets/c03cb5f7-45bf-43f4-ac20-9e944bd22017" />
<img width="1920" height="867" alt="Image" src="https://github.com/user-attachments/assets/32d9da05-1b04-465d-a59b-fa6044cf41b4" />
<img width="1920" height="864" alt="Image" src="https://github.com/user-attachments/assets/09bf0a88-82f5-4255-83ea-d0e8f51703af" />

