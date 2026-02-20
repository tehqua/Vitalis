# Vitalis — AI-Powered Medical Consultation System

> 🏥 *A common, but not commonplace, solution. In this project, it may not be groundbreaking, but it is broadly implementable and reliably effective*

---

## 🎬 Demo Video

<!-- 📌 Paste your YouTube demo link here -->
[![Demo Video](https://img.shields.io/badge/YouTube-Watch%20Demo-red?logo=youtube)](https://youtu.be/xKDyuW_a2GA?si=hLmQZTKRfoAHzu9P)

---

## 🌐 Website

<!-- 📌 Paste your product introduction website link here -->
[![Website](https://img.shields.io/badge/Website-Visit%20Vitalis-blue?logo=googlechrome)](https://vitalis-one.vercel.app/)

---

## 📋 Table of Contents

- [Demo Video](#demo-video)
- [Website](#website)
- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Agents / Orchestrator Setup](#agents--orchestrator-setup)
- [How It Works](#how-it-works)
- [API Reference](#api-reference)
- [Data](#data)
- [Security](#security)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Disclaimer](#disclaimer)

---

## Overview

**Vitalis** is a full-stack AI agent system designed to provide intelligent medical consultation services for hospital patients. It combines a specialized medical LLM (**MedGemma**), a multi-agent orchestration framework (**LangGraph**), RAG-based patient record retrieval, dermatology image classification, and speech-to-text processing — all packaged behind a clean chatbot web interface.

### Problems It Solves

| Problem | Vitalis's Solution |
|---|---|
| Patients can't access medical info outside office hours | 24/7 AI-powered chatbot |
| Doctors spend time answering repetitive basic questions | AI handles first-level consultation |
| Patients struggle to describe symptoms accurately | Supports voice input and image upload |
| No context-aware health advice | Integrates personal FHIR medical records via RAG |
| Skin conditions hard to self-assess | Deep Learning skin disease classifier (8 categories) |

---

## Key Features

| Feature | Description |
|---|---|
| 🤖 **Intelligent Medical QA** | MedGemma LLM answers general health questions |
| 📂 **Personal Medical History** | RAG retrieval from FHIR medical records |
| 🖼️ **Skin Image Analysis** | Classifies 8 dermatological conditions with confidence scores |
| 🎤 **Voice Input** | Speech-to-text (google/medasr) converts audio to text |
| 🚨 **Emergency Detection** | Detects critical symptoms and triggers immediate alert |
| 🔐 **Secure Sessions** | JWT-based authentication with patient data isolation |
| ⚡ **Real-Time Responses** | Async FastAPI backend with session-aware conversation memory |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         USER (Patient)                        │
│              Login with Patient ID via Web UI                 │
└────────────────────────┬─────────────────────────────────────┘
                         │  Text | Voice | Image
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  FRONTEND  (React 18 + Vite)                  │
│   Chatbot UI · Image Upload · Voice Recording · History       │
└────────────────────────┬─────────────────────────────────────┘
                         │  REST API
                         ▼
┌──────────────────────────────────────────────────────────────┐
│               BACKEND API  (FastAPI + Uvicorn)                │
│  JWT Auth · File Upload · Rate Limiting · MongoDB Storage     │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│         AI ORCHESTRATOR  (LangGraph)                          │
│                                                              │
│  input_router ──► process_speech  (google/medasr)            │
│               ──► process_image   (Derm Foundation + LR)     │
│               ──► reasoning_node  (MedGemma via Ollama)      │
│                       └──► call_tool  (RAG / Patient DB)     │
│               ──► safety_check    (guardrails)               │
│               ──► error_handler                              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                        DATA LAYER                             │
│  MongoDB        — Conversations & sessions                   │
│  Vector DB      — Medical record embeddings (FAISS)          │
│  FHIR records   — 1,000+ structured patient medical records  │
└──────────────────────────────────────────────────────────────┘
```

### 3 Query Pathways

| # | Type | Flow | Example |
|---|---|---|---|
| 1️⃣ | **General Medical** | `input_router → reasoning → safety_check` | *"What are symptoms of diabetes?"* |
| 2️⃣ | **Personal History (RAG)** | `input_router → reasoning → call_tool (RAG) → reasoning → safety_check` | *"What were my last blood test results?"* |
| 3️⃣ | **Multimodal (Image / Audio)** | `input_router → process_speech/image → reasoning → safety_check` | *[Skin photo]* *"Is this a fungal infection?"* |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Vanilla CSS |
| **Backend** | FastAPI 0.109, Uvicorn, Pydantic 2.5 |
| **Database** | MongoDB 7.0 (Motor async driver) |
| **Authentication** | JWT (python-jose, HS256) |
| **AI Orchestration** | LangGraph, LangChain-core |
| **Medical LLM** | MedGemma 4B IT (via Ollama) |
| **Speech-to-Text** | google/medasr |
| **Image Analysis** | Derm Foundation + Logistic Regression |
| **RAG / Vector Search** | FAISS + custom FHIR record embeddings |
| **File Handling** | aiofiles, python-magic |

---

## Project Structure

```
vitalis/
├── frontend/                   # React 18 + Vite web application
│   ├── src/
│   │   ├── pages/              # LoginPage, ChatPage
│   │   ├── components/         # Sidebar, TopBar, MessageBubble, ChatInput
│   │   ├── hooks/              # useAuth, useChat
│   │   └── services/           # api.js (all backend calls)
│   └── readme.md
│
├── backend/                    # FastAPI REST API
│   ├── main.py                 # Application entry point
│   ├── routers/                # auth, chat, upload, health
│   ├── services/               # OrchestratorService, FileService
│   ├── middleware.py            # CORS, RateLimiter, Security headers
│   ├── scheduler.py            # Background cleanup tasks
│   └── readme.md
│
├── agents/                     # AI agent modules
│   ├── orchestrator/           # LangGraph orchestration graph
│   │   ├── agent.py            # MedicalChatbotAgent
│   │   ├── nodes.py            # Workflow nodes
│   │   ├── state.py            # AgentState dataclass
│   │   ├── guardrails.py       # Safety checks
│   │   ├── prompts.py          # LLM system prompts
│   │   └── deployment.md
│   ├── image_process/          # Skin disease classifier
│   │   └── tools/              # langgraph_image_analyzer
│   ├── patient_database/       # RAG pipeline
│   │   └── tools/              # PatientRecordRetrieverTool
│   └── speech_to_text_process/ # Audio transcription
│       └── tools/              # langgraph_speech_to_text
│
├── medgemma/                   # Local MedGemma model files
│   └── google_medgemma_4b_it/
│
├── docs/                       # Project documentation
│   ├── project_overview.md
│   ├── backend_architecture.md
│   └── workflow.md
│
├── assets/                     # Static assets
├── scripts/                    # Utility scripts
└── uploads/                    # Temporary uploaded files
```

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.9+ | Add to PATH on Windows |
| Node.js | 18+ | For frontend |
| MongoDB | 7.0 | Run as a service |
| Ollama | Latest | For local LLM inference |
| RAM | ≥ 8 GB | Required for MedGemma model |
| Disk | ≥ 20 GB | Model weights + data |

---

### Backend Setup

```bash
# 1. Create and activate virtual environment
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
notepad .env                 # Edit settings below
```

**Key `.env` settings:**

```env
DEBUG=True
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-generated-secret-key   # python -c "import secrets; print(secrets.token_urlsafe(32))"
DATABASE_URL=mongodb://localhost:27017
DATABASE_NAME=medical_chatbot
CORS_ORIGINS=http://localhost:3000
ORCHESTRATOR_MODEL=thiagomoraes/medgemma-4b-it:Q4_K_S
OLLAMA_BASE_URL=http://localhost:11434
PATIENT_DB_VECTOR_DIR=../agents/patient_database/data/vectordb
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100
```

```bash
# 4. Pull MedGemma via Ollama (≈ 2.4 GB download)
ollama pull thiagomoraes/medgemma-4b-it:Q4_K_S
ollama serve                 # Keep running in a separate terminal

# 5. Start MongoDB
net start MongoDB            # Windows service

# 6. Start the backend
python main.py
# → API available at http://localhost:8000
# → Swagger docs at http://localhost:8000/api/docs
```

---

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# → App available at http://localhost:3000
```

For production:
```bash
npm run build          # Output in dist/
npm run preview        # Preview production build
```

---

### Agents / Orchestrator Setup

```bash
# From project root, install agent dependencies
pip install langgraph langchain-core ollama pydantic
pip install librosa torch transformers    # Speech-to-text
pip install pillow keras tensorflow joblib # Image analysis
pip install faiss-cpu requests             # RAG

# Verify all tools load correctly
python -c "from agents.image_process.tools import langgraph_image_analyzer; print('Image tool OK')"
python -c "from agents.speech_to_text_process.tools import langgraph_speech_to_text; print('Speech tool OK')"
python -c "from agents.patient_database.tools.patient_record_tool import PatientRecordRetrieverTool; print('RAG tool OK')"

# Run orchestrator unit tests
cd agents/orchestrator
python -m pytest tests/test_agent.py -v
```

---

## How It Works

### Agent Workflow (LangGraph)

```
input_router
    ├── has audio?  → process_speech (google/medasr)
    │                    └──► process_image (if image also present)
    ├── has image?  → process_image (Derm Foundation)
    └── text only?  → reasoning_node (MedGemma)

reasoning_node
    ├── emergency keywords? → immediate emergency response
    ├── history keywords?   → call_tool (RAG retrieval) → reasoning_node
    └── normal query        → generate response

safety_check → final response
```

### Skin Disease Categories (Image Analysis)

The image analysis agent classifies photos into **8 dermatological groups**:

`Acne` · `Actinic Keratosis` · `Basal Cell Carcinoma` · `Dermatitis` · `Eczema` · `Melanoma` · `Psoriasis` · `Rosacea`

### Emergency Detection

The system automatically detects critical keywords (e.g., *chest pain*, *difficulty breathing*, *unconscious*, *severe bleeding*) and immediately generates an emergency-alert response advising the patient to call emergency services.

---

## API Reference

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/login` | POST | ❌ | Login with Patient ID → JWT token |
| `/api/auth/logout` | POST | ✅ | Invalidate session |
| `/api/chat/message` | POST | ✅ | Send text message |
| `/api/chat/message-with-image` | POST | ✅ | Send message + image |
| `/api/chat/message-with-audio` | POST | ✅ | Send audio message |
| `/api/chat/history` | GET | ✅ | Get conversation history |
| `/api/chat/history` | DELETE | ✅ | Clear conversation history |
| `/api/upload/image` | POST | ✅ | Upload image file |
| `/api/upload/audio` | POST | ✅ | Upload audio file |
| `/api/upload/limits` | GET | ❌ | Get file size/format limits |
| `/api/health` | GET | ❌ | System health check |

**Interactive Docs:** `http://localhost:8000/api/docs` (Swagger UI)

**Patient ID format:**
```
FirstName###_LastName###_<uuid>
Example: Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58
```

**File upload limits:**
- Images: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp` — max **10 MB**
- Audio: `.wav`, `.mp3`, `.m4a`, `.ogg`, `.webm` — max **50 MB**

---

## Data

The system is powered by **1,000+ FHIR-formatted medical records** covering:

- Patient demographics
- Clinical encounters
- Laboratory observations
- Medication prescriptions
- Condition diagnoses
- Medical procedures

These records are embedded into a **FAISS vector database** for semantic retrieval during RAG queries. Each patient's records are isolated by `patient_id` to prevent cross-patient data leakage.

---

## Security

| Layer | Mechanism |
|---|---|
| **Authentication** | JWT tokens (HS256), session validation on every request |
| **Network** | CORS whitelist, rate limiting (20 req/min, 100 req/hour) |
| **Input Validation** | Pydantic schemas, file extension + MIME type verification, size limits |
| **Content Security** | CSP headers, XSS protection, path traversal prevention |
| **Medical Safety** | No definitive diagnoses, mandatory disclaimers, emergency detection |
| **Privacy** | Per-patient data isolation, no cross-patient leakage |
| **Audit** | Request logging with unique IDs and response timing |

---

## Roadmap

- [ ] Integration of additional specialized AI models (cardiology, pulmonology)
- [ ] Multi-language support
- [ ] Mobile applications (iOS / Android)
- [ ] Live video consultation with doctors
- [ ] Medication and follow-up appointment reminders
- [ ] Nutrition and exercise chatbot
- [ ] Prometheus / Grafana monitoring dashboard

---

## Documentation

| File | Description |
|---|---|
| [`docs/project_overview.md`](docs/project_overview.md) | Full project overview and problem statement |
| [`docs/workflow.md`](docs/workflow.md) | Detailed LangGraph agent workflow with IO examples |
| [`docs/backend_architecture.md`](docs/backend_architecture.md) | Deep-dive into backend layers, middleware, and request flows |
| [`backend/readme.md`](backend/readme.md) | Step-by-step backend deployment guide (Windows) |
| [`frontend/readme.md`](frontend/readme.md) | Frontend setup and deployment guide |
| [`agents/readme.md`](agents/readme.md) | Orchestrator usage, configuration, and API reference |
| [`agents/orchestrator/deployment.md`](agents/orchestrator/deployment.md) | Orchestrator deployment and integration guide |

---

## Disclaimer

> **Vitalis is a medical consultation *support* tool — it is NOT a replacement for a licensed physician.**
>
> The system provides reference information, preliminary assessments, and educational content only. It does not issue definitive diagnoses. Always consult a qualified healthcare professional for medical decisions.

---

*Vitalis — AI-Powered Healthcare for You* 🏥💙
