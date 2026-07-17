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

<table>
  <!-- SECTION 1: MAIN DASHBOARD & ANALYTICS -->
  <tr>
    <td colspan="2" align="center"><h3>📊 Section 1: Main Dashboard Overview & Analytics</h3></td>
  </tr>
  <tr>
    <td align="center">
      <p><b>01. Main Dashboard View</b></p>
      <img width="100%" alt="Main Dashboard View" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>02. Analytics & Reporting</b></p>
      <img width="100%" alt="Analytics & Reporting" src="https://github.com" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <p><b>03. Performance Metrics</b></p>
      <img width="100%" alt="Performance Metrics" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>04. User Activity Logs</b></p>
      <img width="100%" alt="User Activity Logs" src="https://github.com" />
    </td>
  </tr>

  <!-- SECTION 2: DATA MANAGEMENT & TABLES -->
  <tr>
    <td colspan="2" align="center"><h3>⚙️ Section 2: Core Components & Data Management</h3></td>
  </tr>
  <tr>
    <td align="center">
      <p><b>05. Navigation & Status Summary</b></p>
      <img width="100%" alt="Navigation & Status Summary" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>06. Data Tables & Records</b></p>
      <img width="100%" alt="Data Tables & Records" src="https://github.com" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <p><b>07. Content Filters & Queries</b></p>
      <img width="100%" alt="Content Filters & Queries" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>08. Document Management Panel</b></p>
      <img width="100%" alt="Document Management Panel" src="https://github.com" />
    </td>
  </tr>

  <!-- SECTION 3: SYSTEM CONFIGURATIONS & OPERATIONS -->
  <tr>
    <td colspan="2" align="center"><h3>🛠️ Section 3: Operations & System Settings</h3></td>
  </tr>
  <tr>
    <td align="center">
      <p><b>09. System Configuration</b></p>
      <img width="100%" alt="System Configuration" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>10. Operational Metrics</b></p>
      <img width="100%" alt="Operational Metrics" src="https://github.com" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <p><b>11. User Profiles & Access</b></p>
      <img width="100%" alt="User Profiles & Access" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>12. Task Management Tracker</b></p>
      <img width="100%" alt="Task Management Tracker" src="https://github.com" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <p><b>13. Advanced Settings Layout</b></p>
      <img width="100%" alt="Advanced Settings Layout" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>14. Security & Permissions</b></p>
      <img width="100%" alt="Security & Permissions" src="https://github.com" />
    </td>
  </tr>

  <!-- SECTION 4: ADDITIONAL INTERFACES -->
  <tr>
    <td colspan="2" align="center"><h3>💡 Section 4: Secondary Interfaces & Utilities</h3></td>
  </tr>
  <tr>
    <td align="center">
      <p><b>15. Notification Centre</b></p>
      <img width="100%" alt="Notification Centre" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>16. Full Screen Overview</b></p>
      <img width="100%" alt="Full Screen Overview" src="https://github.com" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <p><b>17. Audit Logs & History</b></p>
      <img width="100%" alt="Audit Logs & History" src="https://github.com" />
    </td>
    <td align="center">
      <p><b>18. Help & Support Portal</b></p>
      <img width="100%" alt="Help & Support Portal" src="https://github.com" />
    </td>
  </tr>
</table>


All AI runs locally through [Ollama](https://ollama.com) — no external API calls, no internet dependency, no cost.

---

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

---
