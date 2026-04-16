# Vitalis — Agentic AI System for Post-Consultation Patient Care

> 🏥 *An AI system purpose-built for healthcare — grounded in medical knowledge, aware of patient context, and designed to accompany patients every step after their visit.*

---

## 🎬 Demo Video

[![Demo Video](https://img.shields.io/badge/YouTube-Watch%20Demo-red?logo=youtube)](https://youtu.be/xKDyuW_a2GA?si=hLmQZTKRfoAHzu9P)

---

## 🌐 Website

[![Website](https://img.shields.io/badge/Website-Visit%20Vitalis-blue?logo=googlechrome)](https://vitalis-one.vercel.app/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
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

**Vitalis** is a full-stack **Agentic AI system** in the medical domain, developed for hospitals and independent healthcare facilities. The product focuses on optimising **post-consultation patient care** — helping patients stay informed, supported, and connected long after they leave the clinic, while simultaneously reducing the burden on hospital staff.

Vitalis is not a replacement for existing hospital systems. Instead, it integrates directly on top of a hospital's current patient-portal infrastructure: the same login credentials patients already use to view their records are used to activate the Vitalis assistant. After a visit, patients are proactively asked for their consent; only upon agreement does the chatbot activate and begin personalised support.

---

## Problem Statement

Despite visible improvements in Vietnamese healthcare quality, the post-consultation patient experience remains severely underserved:

| Statistic | Source |
|---|---|
| ~50% of outpatients are unsatisfied with service quality | *International Journal of Public Health* |
| 20–30% of discharged patients experience post-discharge complications due to lack of follow-up | Global health literature |
| >60% of patients expect digital health tools to be convenient, personalised, and continuously available | *Accenture Digital Health Report* |

**Root causes driving this gap:**

1. **Healthcare systems prioritise treatment over continuous care.** Once a patient leaves, structured follow-up is rare.
2. **Existing chatbots lack medical grounding.** General-purpose LLMs (GPT, Claude, etc.) were not trained on clinical data. As the WHO notes, medically inaccurate AI advice poses significant patient safety risks.
3. **Chatbots are stateless.** They have no awareness of a patient's individual medical history -- reducing trust and clinical relevance. McKinsey identifies personalisation as a key driver of improved treatment outcomes.
4. **Under-resourced consultation staff.** Overloaded hospitals in Vietnam cannot offer adequate one-on-one post-visit support, and many non-clinical advisors lack a medical background.
5. **Reactive, not proactive UX.** Current tools only respond when asked and lack multimodal input support (voice, images).

---

## Solution

Vitalis addresses these gaps with four core pillars:

### 1. 🧠 Medically-Grounded Knowledge
Vitalis uses **MedGemma** — a specialised medical LLM — augmented by two RAG layers:
- **Hierarchical Medical Document RAG**: retrieves context from curated clinical guidelines and medical literature before every text query.
- **Patient Record RAG (FHIR-based)**: retrieves the specific patient's own medical history on demand (with consent).

This combination delivers responses grounded in both general medical knowledge *and* the patient's personal health context.

### 2. 👤 Personalised, Context-Aware Assistance
Unlike stateless chatbots, Vitalis maintains session memory and retrieves individual FHIR medical records per-patient. This enables it to answer questions like *"What were my last blood test results?"* or *"Should I still take the medication from my last visit?"* with real, relevant data.

### 3. 🔐 Privacy-by-Design & Patient Consent
Patient data is protected at every layer. The system only activates for a patient after explicit post-visit consent. Data is isolated per-patient, encrypted in transit, and the architecture is designed to comply with healthcare data regulations. Even system operators cannot read patient data without valid decryption rights.

### 4. 🎙️ Proactive, Multimodal Experience
Vitalis supports text, voice (speech-to-text), and image input (skin condition analysis), making it accessible across patient demographics. The agentic workflow automatically routes each query type to the correct processing module, ensuring consistent and contextually accurate responses throughout the post-care journey.

---

## Key Features

| Feature | Description |
|---|---|
| 🤖 **Medically-Grounded QA** | MedGemma LLM + Hierarchical Medical Doc RAG for accurate, evidence-backed responses |
| 📂 **Personal Medical History** | On-demand RAG retrieval from patient FHIR records (with consent) |
| 🖼️ **Skin Image Analysis** | Classifies 8 clinical dermatological categories using Derm Foundation + XGBoost |
| 🎤 **Voice Input** | Speech-to-text (google/medasr) converts audio to text seamlessly |
| 🚨 **Emergency Detection** | Detects critical symptom keywords and triggers immediate emergency-alert responses |
| 🔐 **Secure, Consent-Based Sessions** | JWT auth + explicit patient consent activation + per-patient data isolation |
| ⚡ **Real-Time Async Responses** | FastAPI + Uvicorn async backend with session-aware conversation memory |
| 🏥 **Hospital-Integration Model** | Deploys on top of existing systems; no changes to core hospital infrastructure |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         USER (Patient)                        │
│           Login with Patient ID · Post-Visit Consent          │
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
│                                                               │
│  input_router ──► process_speech  (google/medasr)             │
│               ──► process_image   (Derm Foundation + XGBoost) │
│               ──► medical_doc_rag (HierarchicalEmbeddingIndex)│
│                       └──► reasoning_node  (MedGemma/Ollama)  │
│                                └──► call_tool (Patient RAG)   │
│               ──► safety_check    (guardrails)                │
│               ──► error_handler                               │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                        DATA LAYER                             │
│  MongoDB        — Conversations & sessions                    │
│  FAISS          — Patient record embeddings (FHIR)           │
│  LlamaIndex     — Medical document embeddings (bge-large)    │
│  FHIR records   — 1,000+ structured patient medical records  │
└──────────────────────────────────────────────────────────────┘
```

### Query Pathways

| # | Type | Flow | Example |
|---|---|---|---|
| 1️⃣ | **General Medical** | `input_router → medical_doc_rag → reasoning → safety_check` | *"What are symptoms of diabetes?"* |
| 2️⃣ | **Personal History (FHIR RAG)** | `input_router → medical_doc_rag → reasoning → call_tool (Patient RAG) → reasoning → safety_check` | *"What were my last blood test results?"* |
| 3️⃣ | **Voice Input** | `input_router → process_speech → medical_doc_rag → reasoning → safety_check` | *[Audio recording of question]* |
| 4️⃣ | **Skin Image** | `input_router → process_image → reasoning → safety_check` | *[Skin photo upload]* |
| 5️⃣ | **Multimodal (Voice + Image)** | `input_router → process_speech → process_image → reasoning → safety_check` | *[Audio] + [Skin photo]* |

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
| **Medical Doc RAG** | LlamaIndex + HierarchicalEmbeddingIndex (bge-large-en-v1.5) |
| **Patient Record RAG** | FAISS + custom FHIR record embeddings |
| **Speech-to-Text** | google/medasr |
| **Image Analysis** | Derm Foundation + XGBoost classifier |
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
│   │   ├── nodes.py            # Workflow nodes (incl. medical_doc_rag_node)
│   │   ├── state.py            # AgentState dataclass
│   │   ├── guardrails.py       # Safety checks & input validation
│   │   ├── medical_doc_rag.py  # MedicalDocRAGService (singleton, lazy-load)
│   │   ├── prompts.py          # LLM system prompts
│   │   └── deployment.md
│   ├── image_process/          # Skin disease classifier
│   │   └── tools/              # LangGraphImageAnalyzerTool (Derm Foundation + XGBoost)
│   ├── patient_database/       # FHIR Patient RAG pipeline
│   │   └── tools/              # PatientRecordRetrieverTool (FAISS)
│   └── speech_to_text_process/ # Audio transcription
│       └── tools/              # langgraph_speech_to_text
│
├── rag_hierarchical_index/     # Hierarchical medical document index
│   ├── embedding.py            # HierarchicalEmbeddingIndex (LlamaIndex)
│   ├── main.py                 # Index build/rebuild script
│   └── large_medical_doc_index/ # Persisted LlamaIndex vector store
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
| Disk | ≥ 20 GB | Model weights + data + doc index |

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

# Medical Document RAG (Hierarchical Index)
MEDICAL_DOC_RAG_ENABLED=True
MEDICAL_DOC_PERSIST_DIR=../rag_hierarchical_index/large_medical_doc_index
MEDICAL_DOC_MIN_SCORE=0.6
MEDICAL_DOC_MAX_CONTEXT_NODES=3

RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100
```

```bash
# 4. Pull MedGemma via Ollama (≈ 2.4 GB download)
ollama pull thiagomoraes/medgemma-4b-it:Q4_K_S
ollama serve                 # Keep running in a separate terminal

# 5. Start MongoDB
net start MongoDB            # Windows service

# 6. (First time only) Build the medical document index
cd ../rag_hierarchical_index
python main.py --rebuild-index
cd ../backend

# 7. Start the backend
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
pip install pillow keras tensorflow joblib xgboost  # Image analysis
pip install faiss-cpu requests             # Patient RAG
pip install llama-index sentence-transformers  # Medical Doc RAG

# Verify all tools load correctly
python -c "from agents.image_process.tools import langgraph_image_analyzer; print('Image tool OK')"
python -c "from agents.speech_to_text_process.tools import langgraph_speech_to_text; print('Speech tool OK')"
python -c "from agents.patient_database.tools.patient_record_tool import PatientRecordRetrieverTool; print('RAG tool OK')"
python -c "from agents.orchestrator.medical_doc_rag import MedicalDocRAGService; print('Medical Doc RAG OK')"

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
    │                    ├── has image? → process_image (Derm Foundation + XGBoost)
    │                    │                    └──► reasoning_node
    │                    └── text only → medical_doc_rag → reasoning_node
    ├── has image?  → process_image (Derm Foundation + XGBoost)
    │                    └──► reasoning_node
    └── text only?  → medical_doc_rag (HierarchicalEmbeddingIndex)
                           └──► reasoning_node (MedGemma)

reasoning_node
    ├── emergency keywords? → immediate emergency response → safety_check
    ├── personal history keywords? → call_tool (FHIR Patient RAG) → reasoning_node
    └── normal query → generate response → safety_check

safety_check → final response
```

### Dual RAG Architecture

Vitalis uses **two complementary RAG systems** that operate at different levels:

| RAG Layer | Data Source | Trigger | Purpose |
|---|---|---|---|
| **Medical Doc RAG** | Curated medical guidelines & literature (LlamaIndex, bge-large-en-v1.5) | Every text/voice query | Grounds the LLM in authoritative clinical knowledge |
| **Patient Record RAG** | Individual FHIR medical records (FAISS) | On-demand, keyword-triggered | Personalises responses with patient-specific history |

The Medical Doc RAG service uses a **singleton + lazy-load** pattern with dual timeouts: 5 minutes for first load (includes HuggingFace model download), 8 seconds for subsequent queries. On timeout or error, it falls back gracefully — the LLM responds without the extra context.

### Skin Disease Categories (Image Analysis)

The image analysis agent uses **Google's Derm Foundation** for feature extraction and a trained **XGBoost classifier** to predict one of **8 clinical dermatological groups**:

`Eczema / Dermatitis` · `Bacterial Infections` · `Fungal Infections` · `Viral Infections` · `Infestations` · `Acneiform` · `Vascular / Benign Lesions` · `Healthy Skin`

### Emergency Detection

The system automatically detects critical keywords (e.g., *chest pain*, *difficulty breathing*, *unconscious*, *severe bleeding*) and immediately generates an emergency-alert response advising the patient to call emergency services — bypassing the normal reasoning pipeline.

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

These records are embedded into a **FAISS vector database** for semantic retrieval during patient-specific RAG queries. Each patient's records are isolated by `patient_id` to prevent cross-patient data leakage.

In addition, the **Hierarchical Medical Document Index** (LlamaIndex + bge-large-en-v1.5) provides a general medical knowledge layer, retrieving relevant clinical guidelines and literature to enrich every text-based response.

---

## Security

| Layer | Mechanism |
|---|---|
| **Authentication** | JWT tokens (HS256), session validation on every request |
| **Patient Consent** | Explicit opt-in activation after consultation; chatbot inactive without consent |
| **Network** | CORS whitelist, rate limiting (20 req/min, 100 req/hour) |
| **Input Validation** | Pydantic schemas, file extension + MIME type verification, size limits |
| **Content Security** | CSP headers, XSS protection, path traversal prevention |
| **Medical Safety** | No definitive diagnoses, mandatory disclaimers, emergency detection |
| **Privacy** | Per-patient data isolation, no cross-patient leakage |
| **Audit** | Request logging with unique IDs and response timing |

---

## Implementation Strategy

Vitalis is designed to **extend, not replace** existing hospital infrastructure:

1. **Plug-in integration**: The chatbot is added as a module on top of the hospital's existing patient-portal, using the same patient credentials already in use.
2. **Hospital data ownership**: All patient data remains under hospital control. Vitalis does not store raw medical records externally.
3. **Consent-first activation**: After each consultation, patients are asked whether they wish to activate the post-care assistant. It activates only on explicit agreement.
4. **Phased deployment**: The system can be rolled out incrementally — starting with one department or clinic, then scaling across the facility.
5. **Maintenance by Vitalis team**: Hospitals handle their own data; Vitalis handles deployment, model updates, and system maintenance.

---

## Roadmap

- [ ] Proactive post-visit follow-up notifications (medication reminders, appointment alerts)
- [ ] Integration of additional specialised AI models (cardiology, pulmonology)
- [ ] Multi-language support (Vietnamese, English)
- [ ] Mobile applications (iOS / Android)
- [ ] Live video consultation handoff to doctors
- [ ] Nutrition and exercise guidance chatbot
- [ ] Prometheus / Grafana monitoring dashboard
- [ ] Expanded admin panel and hospital analytics

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

*Vitalis — Agentic AI for Post-Consultation Patient Care* 🏥💙
