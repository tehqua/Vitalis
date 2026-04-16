# 📋 COMPREHENSIVE SYSTEM ANALYSIS REPORT — VITALIS

> **Project:** Vitalis — Agentic AI for Post-Consultation Patient Care  
> **Backend language:** Python (FastAPI, LangGraph)  
> **Frontend language:** JavaScript (React 18 + Vite)  
> **Analysis date:** 13/04/2026  
> **Version:** 1.1.0  

---

## TABLE OF CONTENTS

1. [Part 1 – Backend (FastAPI)](#part-1--backend-fastapi)
2. [Part 2 – Orchestrator Agent (LangGraph)](#part-2--orchestrator-agent-langgraph)
3. [Part 3 – Image Processing Agent](#part-3--image-processing-agent)
4. [Part 4 – Speech-to-Text Agent](#part-4--speech-to-text-agent)
5. [Part 5 – Patient Database Agent (RAG)](#part-5--patient-database-agent-rag)
6. [Part 6 – Hierarchical Medical Document RAG](#part-6--hierarchical-medical-document-rag)
7. [Part 7 – Frontend (React/Vite)](#part-7--frontend-reactvite)
8. [System-Wide Analysis](#system-wide-analysis)

---

## PART 1 – BACKEND (FastAPI)

### 1.1. Overview

The backend is the API middleware layer — the sole communication gateway between the Frontend and the entire AI system. Built with **FastAPI** using an **async/await** model, it efficiently handles concurrent requests. The database is **MongoDB** (via `motor` async driver). Settings are loaded via `pydantic-settings` with `@lru_cache`.

**Directory structure:**
```
backend/
├── main.py          # Application entry point, lifespan management
├── config.py        # Settings (pydantic-settings, lru_cache)
├── auth.py          # JWT auth utilities
├── database.py      # MongoDB async CRUD operations
├── middleware.py    # 5 middleware layers (CORS, Logging, ErrorHandler, SecurityHeaders, RateLimit)
├── schemas.py       # Pydantic request/response models
├── validators.py    # InputValidator, FileValidator
├── scheduler.py     # Background task scheduler
└── routers/
    ├── auth.py      # /api/auth/login, /logout
    ├── chat.py      # /api/chat/message, /message-with-image, /message-with-audio, /history
    ├── upload.py    # /api/upload/image, /audio, /limits
    └── health.py    # /api/health
```

---

### 1.2. Execution Flows

#### A. Application Startup (Lifespan)

```
uvicorn main:app
    └── lifespan() [asynccontextmanager]
        ├── init_db()          → Connect MongoDB, create indexes
        ├── start_scheduler()  → Start 3 background tasks
        │     ├── cleanup_sessions (every 30 min)
        │     ├── cleanup_files    (every 60 min)
        │     └── cleanup_database (every 120 min)
        └── [yield] → App ready to receive requests
```

#### B. Standard Request Flow

```
Client → [CORSMiddleware]
       → [LoggingMiddleware]
       → [ErrorHandlerMiddleware]
       → [SecurityHeadersMiddleware]
       → [RateLimitMiddleware] (20 req/min, 100 req/hour per IP)
       → Router
       → get_current_user() [Bearer JWT Dependency]
            ├── verify_token()      → Decode JWT, verify signature + expiry
            └── db.get_session()    → Check session still active in MongoDB
       → Handler logic
       → Response
```

#### C. Authentication Flow (Login)

```
POST /api/auth/login { patient_id }
    ├── validate_patient_id() → Regex: ^[A-Z][a-z]+\d+_[A-Z][a-z]+\d+_[uuid36]$
    ├── db.create_session()   → Create MongoDB session (TTL: 30 min)
    └── create_access_token() → JWT HS256 (TTL: 60 min)
         payload: { patient_id, session_id, exp }
    → LoginResponse { access_token, token_type, session_id, expires_in }
```

#### D. Text Chat Flow (POST /api/chat/message)

```
POST /api/chat/message { message, session_id }
    ├── [Middleware stack]
    ├── get_current_user() → TokenData { patient_id, session_id }
    ├── orchestrator.process_message(patient_id, text_input, session_id)
    │       └── [Full Orchestrator Agent — Part 2]
    ├── db.save_conversation() → Save Q&A to MongoDB
    └── ChatResponse { response, session_id, timestamp, metadata }
```

#### E. Image Chat Flow (POST /api/chat/message-with-image)

```
POST /api/chat/message-with-image [multipart: message?, image]
    ├── FileService.save_uploaded_file() → Validate + save image to disk
    ├── orchestrator.process_message(..., image_file_path=...)
    └── db.save_conversation() + ChatResponse (with image_path in metadata)
```

#### F. Audio Chat Flow (POST /api/chat/message-with-audio)

```
POST /api/chat/message-with-audio [multipart: audio]
    ├── FileService.save_uploaded_file() → Validate + save audio to disk
    ├── orchestrator.process_message(..., audio_file_path=...)
    └── db.save_conversation() + ChatResponse
```

---

### 1.3. Configuration

| Parameter | Default | Source |
|-----------|---------|--------|
| `HOST` | `0.0.0.0` | `.env` |
| `PORT` | `8000` | `.env` |
| `DEBUG` | `False` | `.env` |
| `SECRET_KEY` | ⚠️ no-safe-default | `.env` — must be overridden |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | `.env` |
| `SESSION_EXPIRE_MINUTES` | `30` | `.env` |
| `DATABASE_URL` | `mongodb://localhost:27017` | `.env` |
| `DATABASE_NAME` | `medical_chatbot` | `.env` |
| `UPLOAD_DIR` | `uploads` | `.env` |
| `MAX_FILE_SIZE_MB` | `10` | `.env` |
| `RATE_LIMIT_PER_MINUTE` | `20` | `.env` |
| `RATE_LIMIT_PER_HOUR` | `100` | `.env` |
| `CORS_ORIGINS` | `localhost:3000, localhost:5173` | `.env` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | `.env` |
| `ORCHESTRATOR_MODEL` | `thiagomoraes/medgemma-4b-it:Q4_K_S` | `.env` |
| `PATIENT_DB_VECTOR_DIR` | `../agents/patient_database/data/vectordb` | `.env` |
| `MEDICAL_DOC_RAG_ENABLED` | `True` | `.env` |
| `MEDICAL_DOC_PERSIST_DIR` | `../rag_hierarchical_index/large_medical_doc_index` | `.env` |
| `MEDICAL_DOC_MIN_SCORE` | `0.6` | `.env` |
| `MEDICAL_DOC_MAX_CONTEXT_NODES` | `3` | `.env` |

**Middleware stack (outer → inner application):**
1. `CORSMiddleware` — Cross-origin control
2. `LoggingMiddleware` — Log every request/response with unique ID
3. `ErrorHandlerMiddleware` — Catch ValueError, Exception → structured JSON error
4. `SecurityHeadersMiddleware` — Add CSP, X-Frame-Options, XSS-Protection, HSTS
5. `RateLimitMiddleware` — Rate limiting per IP (sliding window, in-memory)

---

### 1.4. Strengths

✅ **Fully async architecture**: FastAPI + Motor → high throughput, non-blocking  
✅ **Clearly layered middleware**: Each middleware has a single, independent responsibility (SRP)  
✅ **Multi-layer security**: JWT + session validation + rate limiting + security headers  
✅ **Multi-level validation**: Pydantic schemas + InputValidator + FileValidator (magic number detection)  
✅ **Background scheduler**: Automatic sessions/files/DB cleanup without external cron  
✅ **Settings with `lru_cache`**: Config loaded once, I/O-efficient  
✅ **Swagger UI**: `/api/docs` fully available for dev/test  
✅ **Lifespan lifecycle management**: Clean startup/shutdown, no resource leaks  
✅ **Executor for sync code**: `run_in_executor` prevents blocking async event loop during LangGraph `graph.invoke()`

### 1.5. Weaknesses

❌ **Rate limiting in-memory**: Not correct with horizontal scaling (multi-process) → needs Redis  
❌ **Patient existence not verified on login**: Login only checks patient_id format, not actual patient in DB  
❌ **File ID is hash(path)**: Not unique, cannot reverse-lookup from file_id → file_path  
❌ **Upload delete/getInfo not implemented**: `501 Not Implemented` stubs left in upload router  
❌ **No refresh token**: JWT expiry → forced logout, poor UX for long sessions  
❌ **Upload directory has no per-user quota**: Users can upload unlimited number of files  
❌ **Conversation timestamps identical**: User message and AI response saved with the same `created_at`  

---

## PART 2 – ORCHESTRATOR AGENT (LangGraph)

### 2.1. Overview

The Orchestrator is the **intelligent coordination hub** of the entire system. Built with **LangGraph** (StateGraph) — a framework for complex AI workflows with typed state and conditional routing. The LLM is **MedGemma 4B** running locally via **Ollama**.

**File structure:**
```
agents/orchestrator/
├── agent.py           # MedicalChatbotAgent: init + build graph + process_message
├── nodes.py           # WorkflowNodes: 8 processing nodes
├── state.py           # AgentState TypedDict (20 fields)
├── config.py          # OrchestratorConfig dataclass
├── prompts.py         # System prompts + template formatters
├── guardrails.py      # MedicalGuardrails + InputValidator
├── medical_doc_rag.py # MedicalDocRAGService (singleton, lazy-load)
└── utils.py           # ConversationMemory, helper functions
```

---

### 2.2. Execution Flow

#### A. LangGraph Graph Topology

```
                    ┌─────────────────┐
                    │   input_router  │ (Entry Point)
                    └────────┬────────┘
                             │ routing_decision
              ┌──────────────┼──────────────────────┐
              │              │                       │
              ▼              ▼                       ▼
        process_speech  process_image           error_handler
              │              │                       │
              │ (if image)   │                       ▼
              ─────────────►─┘                      END
              │              │
              │              ▼
              └──────► medical_doc_rag_node
                             │
                             ▼
                         reasoning ◄──────────────────┐
                             │                         │
                    ┌────────┴────────┐                │
                    │                 │                │
                    ▼                 ▼                │
                call_tool       safety_check           │
                    │                 │                │
                    └────────────────►│ (reasoning ──► ┘ loop for RAG)
                                      ▼
                                      END
```

#### B. Node Details

**Node 1: `input_router`**
```
INPUT: AgentState { patient_id, user_text_input?, audio_file_path?, image_file_path? }
PROCESS:
  1. determine_input_type() → "text" | "speech" | "image" | "multimodal"
  2. validate_patient_id() → regex check
  3. validate_image_file() / validate_audio_file() if present
  4. Set routing_decision:
     - audio_file → "process_speech"
     - image only → "process_image"
     - text only  → "reasoning" (via medical_doc_rag first)
     - multimodal (audio+image) → "process_speech" first
OUTPUT: state with routing_decision
```

**Node 2: `process_speech`**
```
INPUT: state with audio_file_path
PROCESS:
  1. Call LangGraphSpeechToTextTool._run(audio_path)
     → google/medasr pipeline (20s chunks, 2s stride)
  2. Store result in state["transcribed_text"]
  3. If image also present → routing "process_image"
  4. Otherwise → routing "reasoning" (via medical_doc_rag)
OUTPUT: state with transcribed_text
```

**Node 3: `process_image`**
```
INPUT: state with image_file_path
PROCESS:
  1. Call LangGraphImageAnalyzerTool._run(image_path)
     → Derm Foundation embed → XGBoost classify
  2. Parse JSON result → state["image_analysis_result"]
  3. tool_calls_completed += ["analyze_skin_image"]
  4. Always routing → "reasoning"
OUTPUT: state with image_analysis_result { class_id, class_name, confidence, all_probabilities }
```

**Node 4: `medical_doc_rag_node`** *(New in v1.1)*
```
INPUT: state with user query text
PROCESS:
  1. extract_text_from_state() → get query from user_text_input or transcribed_text or messages
  2. If no query OR service unavailable → medical_doc_context = None, route to reasoning
  3. MedicalDocRAGService.retrieve(query)
     - Singleton + lazy-load pattern
     - First load timeout: 5 min (HuggingFace download)
     - Subsequent query timeout: 8 sec
     - On timeout/error: graceful fallback (context = None, LLM still responds)
  4. Store in state["medical_doc_context"]
  5. routing → "reasoning"
OUTPUT: state with medical_doc_context (string or None)
```

**Node 5: `reasoning_node`** *(Most important node)*
```
INPUT: state with full context
PROCESS:
  1. extract_text_from_state() → combine user_text + transcribed_text
  2. guardrails.sanitize_input() → strip HTML/script injection
  3. guardrails.detect_emergency() →
     - If emergency: generate_emergency_response() → safety_check immediately
  4. Check if Patient RAG needed:
     Keywords: ["my", "history", "record", "medication", "prescription",
                "visit", "test", "result", "doctor", "appointment",
                "vaccine", "allergy", "blood pressure", "lab"]
     - If keyword AND no rag_context yet → routing "call_tool"
  5. Build Ollama messages:
     [system: MASTER_SYSTEM_PROMPT + patient_context (already authenticated)]
     [system: image_analysis_context?]
     [system: rag_context?]
     [system: medical_doc_context?]
     [history: last 5 messages]
     [user: current input]
  6. Call ollama.chat(model, messages, {temperature: 0.3, num_predict: 1024})
  7. Store response → routing "safety_check"
OUTPUT: state with final_response
```

**Node 6: `call_tool`**
```
INPUT: state with next_action = "retrieve_patient_records"
PROCESS:
  1. PatientRecordRetrieverTool._run(patient_id, query, top_k=3)
  2. Store result in state["rag_context"]
  3. routing → "reasoning" (loop back with context loaded)
OUTPUT: state with rag_context
```

**Node 7: `safety_check`**
```
INPUT: state with final_response
PROCESS:
  1. guardrails.validate_response() → Check prohibited phrases + diagnosis patterns
     - Hard violations (prohibited phrases) → replace entire response with safe fallback
     - Soft violations (diagnosis patterns only) → append disclaimer note
  2. guardrails.validate_patient_privacy() → No other patient IDs exposed
  3. clean_response() → Remove excess blank lines, normalise whitespace
OUTPUT: state with validated final_response, safety_check_passed=True
```

**Node 8: `error_handler`**
```
INPUT: state with routing_decision = "error"
OUTPUT: Generic error message + routing "end"
```

#### C. AgentState Management

```python
AgentState = {
    # Identity
    "patient_id": str,
    "session_id": str,
    "timestamp": str,

    # Input sources
    "current_input_type": "text"|"speech"|"image"|"multimodal",
    "user_text_input": Optional[str],
    "audio_file_path": Optional[str],
    "image_file_path": Optional[str],

    # Processed inputs
    "transcribed_text": Optional[str],
    "image_analysis_result": Optional[Dict],

    # RAG layers
    "rag_context": Optional[Dict],       # Patient FHIR RAG (FAISS)
    "rag_needed": bool,
    "medical_doc_context": Optional[str], # Medical document RAG (LlamaIndex)

    # Control flow
    "routing_decision": str,
    "requires_tool_call": bool,
    "tool_calls_completed": List[str],
    "next_action": Optional[str],

    # Output
    "final_response": Optional[str],

    # Safety
    "safety_check_passed": bool,
    "emergency_detected": bool,

    # Memory
    "messages": Annotated[List[Message], add_messages],
    "agent_scratchpad": str,
}
```

#### D. ConversationMemory

```
MedicalChatbotAgent.memory = ConversationMemory(max_messages=50)
- Stored in-memory per agent instance
- Truncate: keep system messages + recent non-system messages
- Only 5 most recent messages passed to LLM context window
```

---

### 2.3. Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `thiagomoraes/medgemma-4b-it:Q4_K_S` | LLM via Ollama |
| `model_temperature` | `0.3` | Low creativity → suitable for medical |
| `model_max_tokens` | `1024` | Max output token limit |
| `ollama_base_url` | `http://localhost:11434` | Ollama server address |
| `rag_top_k` | `3` | Patient records returned per query |
| `enable_emergency_detection` | `True` | Emergency keyword detection |
| `require_medical_disclaimer` | `True` | Add disclaimer (soft violations) |
| `max_conversation_length` | `50` | Max messages in memory |
| `session_timeout_minutes` | `30` | Session timeout |
| `medical_doc_rag_enabled` | `True` | Enable hierarchical doc RAG |

**Emergency Keywords (hardcoded):**
- Chest pain, breathing difficulty, severe bleeding
- Loss of consciousness, stroke symptoms (FAST)
- Severe allergic reaction, head trauma
- Poisoning/overdose, seizures
- Suicidal ideation (want to die, kill myself, end my life)

**Prohibited Phrases (output hard-validation):**
- "you definitely have", "you are diagnosed with"
- "i diagnose you", "this is definitely"
- "you need this medication", "stop taking your medication"

---

### 2.4. Strengths

✅ **LangGraph StateGraph**: Clearly structured, conditional workflow — easy to debug and extend  
✅ **Multi-modal from design**: Text/speech/image/multimodal handled in one pipeline  
✅ **Emergency detection first**: Checked before any LLM call → fast response for life-critical situations  
✅ **Dual guardrails**: Validate both input (XSS sanitisation) and output (prohibited phrases, privacy)  
✅ **Lazy loading for tools**: Models load on first use → fast startup  
✅ **Keyword-based Patient RAG trigger**: Simple, effective, no fine-tuning required  
✅ **Context-aware**: Combines image analysis + Patient RAG + Medical Doc RAG + conversation history in one LLM call  
✅ **Temperature 0.3**: Appropriate for medical use, minimises hallucination  
✅ **Dual RAG layers**: Medical Doc RAG grounds every query in clinical evidence; Patient RAG personalises with FHIR records  

### 2.5. Weaknesses

❌ **ConversationMemory not per-session**: Singleton `MedicalChatbotAgent` → all users share one memory (race condition under concurrency)  
❌ **RAG trigger too coarse (keyword matching)**: Word "my" in normal sentences can trigger unnecessary RAG  
❌ **Medical disclaimer commented out**: `# response = self.guardrails.add_medical_disclaimer(response)` → no automatic disclaimer appended  
❌ **Dead code in nodes.py**: Commented block followed by replacement block (lines 357–364) → code smell  
❌ **No retry logic for LLM**: If Ollama times out or crashes → no retry, immediate error response  
❌ **`process_message()` synchronous**: `self.graph.invoke()` is blocking — must use `run_in_executor` in FastAPI async context  
❌ **`_route_from_reasoning` may miss edge**: If reasoning sets routing="error", graph may not have an edge to error_handler from reasoning  
❌ **`agent_scratchpad` unused**: Field exists in AgentState but has no actual logic value  

---

## PART 3 – IMAGE PROCESSING AGENT

### 3.1. Overview

The image analysis agent uses a **two-stage architecture**:
1. **Derm Foundation** (Google, Keras/TensorFlow `TFSMLayer`): Extract embeddings from dermatological images
2. **XGBoost classifier** (scikit-learn / xgboost): Classify based on embedding

Supports classification into **8 clinical skin disease groups:**

| ID | Group |
|----|-------|
| 0 | Eczema/Dermatitis |
| 1 | Bacterial Infections |
| 2 | Fungal Infections |
| 3 | Viral Infections |
| 4 | Infestations (Parasites) |
| 5 | Acneiform (Acne-like) |
| 6 | Vascular/Benign Lesions |
| 7 | Healthy Skin |

---

### 3.2. Execution Flow

```
image_path received
    │
    ▼
_validate_image_file(image_path)
    ├── os.path.exists() → FileNotFoundError if missing
    └── PIL.Image.open().verify() → ValueError if corrupt
    │
    ▼
_initialize_models()  [Lazy Loading — runs only first time]
    ├── joblib.load(xgb_path) → Load XGBoost model (.pkl or .json)
    └── keras.layers.TFSMLayer(derm_model_path)
        └── keras.Sequential([derm_layer]) → Keras model
    │
    ▼
_encode_image(image_path)
    ├── tf.io.read_file(image_path) → Read raw bytes
    ├── Pack into tf.train.Example { image/encoded: bytes }
    ├── Serialize → tf.constant([serialized_string])
    ├── derm_layer(inputs=...) → output["embedding"]
    └── .numpy().squeeze() → numpy array (1D embedding vector)
    │
    ▼
embedding.reshape(1, -1)
    │
    ▼
xgb_model.predict(embedding) → pred_class (int 0-7)
xgb_model.predict_proba(embedding) → pred_proba (array[8])
    │
    ▼
Format Result:
{
    "class_id": int,
    "class_name": CLASS_NAMES[pred_class],
    "confidence": float,
    "all_probabilities": { class_name: float, ... }
}
    │
    ▼
json.dumps(result) → JSON string returned to Orchestrator
```

**LangGraph Wrapper:**
```python
class LangGraphImageAnalyzerTool(LangChainBaseTool):
    name: str = "analyze_skin_image"
    args_schema: ImageAnalysisInput { image_path: str }
    _run(image_path) → ImageAnalyzerTool.execute(image_path)
```

---

### 3.3. Configuration

| Parameter | Description |
|-----------|-------------|
| `xgb_path` | Path to XGBoost model file (.pkl or .json) |
| `derm_model_path` | Path to Derm Foundation SavedModel directory |
| Lazy initialization | Models load only when `_run()` is first called |

**Training pipeline (from notebooks):**
- `1.data_fetching.ipynb` → Data collection
- `2.eda.ipynb` → Exploratory data analysis
- `3.data_processing.ipynb` → Preprocessing
- `4.modeling.ipynb` → Train XGBoost on Derm Foundation embeddings
- `5.inference.ipynb` → Test inference pipeline

---

### 3.4. Strengths

✅ **Effective transfer learning**: Derm Foundation is a medical-specialist model → high-quality embeddings  
✅ **Lightweight classifier**: XGBoost → very fast inference after embedding extraction  
✅ **Lazy loading**: No RAM consumption when not in use  
✅ **Full probability output**: Returns probabilities for all 8 classes, not just top-1  
✅ **Image validation**: Checks file existence + content integrity before processing  
✅ **LangChain compatible**: Standard `BaseTool` wrapper → easy integration  

### 3.5. Weaknesses

❌ **Heavy TensorFlow dependency**: TF + Keras → slow load, high RAM, potential version conflicts  
❌ **No image preprocessing**: Derm Foundation receives raw bytes → no resize/normalise → low-quality images may produce incorrect results  
❌ **8 classes too broad**: "Bacterial/Fungal/Viral Infections" — too generic for clinical dermatology  
❌ **No confidence threshold**: No warning when confidence is low (e.g., < 50%) → could mislead users  
❌ **Not thread-safe**: `_initialize_models()` may race condition if 2 concurrent requests hit the first call simultaneously  

---

## PART 4 – SPEECH-TO-TEXT AGENT

### 4.1. Overview

The speech-to-text agent uses **Google MedASR** (`google/medasr`) — an Automatic Speech Recognition (ASR) model specifically fine-tuned for the medical domain. Architecture is **CTC (Connectionist Temporal Classification)** with optional beam search via `pyctcdecode` and KenLM.

---

### 4.2. Execution Flow

```
audio_path received
    │
    ▼
_validate_audio_file(audio_path)
    ├── os.path.exists() → FileNotFoundError
    └── librosa.load(sr=16000, mono=True) → Verify loadable
    │
    ▼
_initialize_pipeline()  [Lazy Loading]
    ├── LasrFeatureExtractor.from_pretrained("google/medasr")
    │     └── _processor_class = "LasrProcessorWithLM"
    ├── [Optional] KenLM Language Model:
    │     ├── AutoTokenizer.from_pretrained("google/medasr")
    │     └── LasrCtcBeamSearchDecoder(tokenizer, lm_path)
    │           ├── Build vocab array from tokenizer
    │           ├── Token normalisation: '▁' → '#', prefix '▁'
    │           └── pyctcdecode.build_ctcdecoder(vocab, kenlm)
    └── transformers.pipeline("automatic-speech-recognition", model, feature_extractor, decoder)
    │
    ▼
pipeline(audio_path, chunk_length_s=20, stride_length_s=2, decoder_kwargs?)
    │ Chunked processing: splits audio into 20s chunks, 2s overlap
    │
    ▼
result["text"] → transcribed_text
    │
    ▼
[LasrCtcBeamSearchDecoder._restore_text()]
    └── text.replace(" ","").replace("#"," ").strip()
    │
    ▼
Return transcribed_text (string)
```

---

### 4.3. Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_id` | `google/medasr` | HuggingFace model ID |
| `lm_path` | `None` | Path to KenLM binary (.binary) |
| `chunk_length_s` | `20` | Processing chunk duration (seconds) |
| `stride_length_s` | `2` | Overlap between chunks (seconds) |
| `beam_width` | `8` | Beam search width (when LM enabled) |
| Input audio | WAV, 16kHz, mono (recommended) | Librosa auto-resamples |

---

### 4.4. Strengths

✅ **Domain-specific model**: MedASR fine-tuned for medicine → recognises medical terminology better than general Whisper  
✅ **Chunked processing**: Handles long files without OOM  
✅ **KenLM integration**: Language model assists medical vocabulary correction  
✅ **Librosa preprocessing**: Automatic resample and mono conversion  
✅ **Lazy loading**: Pipeline initialised only when needed  

### 4.5. Weaknesses

❌ **HuggingFace download on first use**: `from_pretrained()` downloads ~GB on first call → high initial latency, requires internet  
❌ **English only**: `google/medasr` is English-only ASR → not suitable for Vietnamese patients  
❌ **No VAD (Voice Activity Detection)**: Cannot distinguish speech from silence → processes long silent segments  
❌ **Synchronous (blocking)**: Pipeline blocks calling thread during transcription  
❌ **`chunk_length_s=20` hardcoded**: Not configurable via API or .env → inflexible  
❌ **No noise reduction**: No preprocessing step to handle noisy audio  

---

## PART 5 – PATIENT DATABASE AGENT (RAG)

### 5.1. Overview

The patient record retrieval agent uses **RAG (Retrieval-Augmented Generation)** with **FAISS** as the vector store. Each patient has their own FAISS index pre-built and stored on disk. Embeddings are generated with **Ollama `nomic-embed-text`**.

**RAG Pipeline Structure:**
```
agents/patient_database/
├── rag_pipeline/
│   ├── parser.py                # Parse medical records → structured data
│   ├── narrative_transformer.py # Convert structured data → text narratives
│   ├── episode_builder.py       # Group medical events into episodes
│   ├── batch_embed.py           # Batch embedding via Ollama
│   ├── faiss_index.py           # Build/save/load FAISS index
│   ├── patient_rag.py           # Core retrieval function
│   └── pipeline.py              # Orchestrate full build pipeline
├── data/vectordb/               # {patient_id}.index + {patient_id}.pkl
└── tools/patient_record_tool.py # LangChain wrapper
```

---

### 5.2. Execution Flow

#### A. Build Phase (Offline — runs once)

```
Medical Records (FHIR JSON/CSV)
    │
    ▼
parser.py → Parse structured medical data
    │
    ▼
narrative_transformer.py → Transform into text narratives
    │ Example: "Patient visited on 2023-01-15 for hypertension..."
    │
    ▼
episode_builder.py → Group into episodes (visits, medications, labs)
    │
    ▼
batch_embed.py → POST http://localhost:11434/api/embeddings
    │     body: { model: "nomic-embed-text", prompt: text }
    │     → embedding vector per document
    │
    ▼
faiss_index.py →
    ├── faiss.IndexFlatIP (Inner Product = cosine after L2 normalize)
    ├── faiss.normalize_L2(vectors)
    ├── index.add(vectors)
    ├── faiss.write_index(index, "{patient_id}.index")
    └── pickle.dump({"documents": [...], "vectors": np.array(...)}, "{patient_id}.pkl")
    → Pre-computed vectors stored alongside documents ✅ (fixed v1.1)
```

#### B. Retrieval Phase (Runtime)

```
patient_record_tool._run(patient_id, query, top_k=3)
    │
    ▼
retrieve_patient_context(patient_id, query, top_k)
    │
    ├── load_patient_index(patient_id)
    │     ├── faiss.read_index("{patient_id}.index")
    │     └── pickle.load("{patient_id}.pkl")
    │           → documents list + pre-computed vectors
    │
    ├── extract_year(query)
    │     └── Regex for 4-digit year → filter docs by year metadata
    │
    ├── [Optional] Year Filter:
    │     filtered_docs = [doc for doc in documents if doc.metadata.year == year]
    │     → Use corresponding pre-computed vectors (NO re-embedding) ✅
    │
    ├── embed_query(query) → query_vec (1 Ollama HTTP call)
    │     faiss.normalize_L2(query_vec)
    │
    ├── Build temp FAISS IndexFlatIP from filtered pre-computed vectors
    │     (no re-embedding of documents) ✅
    │     temp_index.search(query_vec, top_k)
    │
    └── Return:
        {
            "context": "\n\n".join([docs[i]["text"] for i in indices]),
            "sources": [docs[i] for i in indices]
        }
```

---

### 5.3. Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `VECTOR_DB_DIR` | `../data/vectordb` | Directory containing FAISS indexes |
| `OLLAMA_EMBED_URL` | `http://localhost:11434/api/embeddings` | Embedding API endpoint |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `top_k` | `3` (default) | Number of documents to return |
| Year filter | Regex `(19\|20)\d{2}` | Temporal filtering by year mention in query |
| Index type | `faiss.IndexFlatIP` | Exact search with inner product |

---

### 5.4. Strengths

✅ **Per-patient isolation**: Each patient has their own FAISS index → absolute security, no data leakage  
✅ **Offline pre-built index**: Fast retrieval, no rebuild required at runtime  
✅ **No re-embedding bug fixed**: Pre-computed vectors stored in `.pkl`; retrieval only embeds the query (O(1) embedding calls) ✅  
✅ **Structured metadata preservation**: Documents have `metadata.year`, supports temporal filtering  
✅ **Narrative transformation**: Medical records converted to natural language → context-rich chunks  
✅ **Hybrid retrieval**: Combines structured year filter + semantic FAISS search  

### 5.5. Weaknesses

✅ ~~**RE-EMBED ALL DOCS ON EVERY RETRIEVAL**~~ → **RESOLVED** *(11/03/2026)*  
❌ **Embedding via HTTP (synchronous)**: `requests.post()` to Ollama is blocking + network overhead  
❌ **No graceful handling if patient index missing**: Raw exception instead of "no records found" message  
❌ **`pickle.load` not secure**: Pickle deserialization can be exploited if `.pkl` file is tampered  
❌ **`_arun` not implemented**: `NotImplementedError` → cannot use in truly async context  

---

## PART 6 – HIERARCHICAL MEDICAL DOCUMENT RAG

### 6.1. Overview

The Medical Document RAG service provides a **general clinical knowledge layer** separate from per-patient records. It uses **LlamaIndex** with a `HierarchicalEmbeddingIndex` pattern to index curated medical literature and clinical guidelines.

**File structure:**
```
rag_hierarchical_index/
├── embedding.py               # HierarchicalEmbeddingIndex (LlamaIndex)
├── main.py                    # Index build/rebuild script
└── large_medical_doc_index/   # Persisted LlamaIndex vector store
```

**Integration in orchestrator:**
```
agents/orchestrator/
└── medical_doc_rag.py         # MedicalDocRAGService (singleton, lazy-load)
```

---

### 6.2. Execution Flow

#### A. Index Build Phase (Offline — `python main.py --rebuild-index`)

```
Medical literature documents (PDF/text)
    │
    ▼
HierarchicalEmbeddingIndex
    ├── Parse documents into hierarchical nodes
    ├── Generate embeddings: bge-large-en-v1.5 (HuggingFace)
    └── Persist to: large_medical_doc_index/
        ├── docstore.json
        ├── index_store.json
        └── vector_store directories
```

#### B. Retrieval Phase (Runtime)

```
MedicalDocRAGService.retrieve(query)
    │
    ├── First call: load index from disk (timeout: 5 min)
    │     └── Load HierarchicalEmbeddingIndex from persisted store
    │
    ├── Query: HierarchicalRetriever.retrieve(query, score_threshold=0.6, top_k=3)
    │     ├── Embed query with bge-large-en-v1.5
    │     └── Semantic search over index
    │
    ├── If timeout / error → return None (graceful fallback)
    │
    └── Return: context string (concatenated relevant chunks) or None
```

---

### 6.3. Singleton + Lazy-Load Pattern

```python
class MedicalDocRAGService:
    _instance: Optional["MedicalDocRAGService"] = None

    @classmethod
    def get_instance(cls, config) -> "MedicalDocRAGService":
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def retrieve(self, query: str) -> Optional[str]:
        # First call: load index (up to 5 min timeout)
        # Subsequent calls: query only (8 sec timeout)
        # On any error/timeout: return None (LLM answers without extra context)
```

---

### 6.4. Strengths

✅ **Hierarchical retrieval**: Captures both document-level and chunk-level context → richer responses  
✅ **Singleton**: Index loaded once, reused across all requests  
✅ **Graceful fallback**: On timeout or error, LLM still responds without the RAG context  
✅ **High-quality embeddings**: `bge-large-en-v1.5` is a strong general-purpose medical embedding model  
✅ **Persisted index**: No rebuild required on restart — fast startup after first build  

### 6.5. Weaknesses

❌ **First-load delay**: 5-minute timeout for first call (HuggingFace model download included) → first user of a new server instance experiences latency  
❌ **Synchronous retrieval**: Not async — runs in the thread executor like LangGraph  
❌ **Index freshness**: No automated index rebuild — medical literature updates require manual rebuild  
❌ **bge-large-en-v1.5 English-only**: Not optimised for multilingual medical text  

---

## PART 7 – FRONTEND (REACT/VITE)

### 7.1. Overview

The frontend is built with **React 18 + Vite**, communicating with the backend via REST API. It provides a rich chat interface allowing patients to send text messages, upload skin condition images, and send voice messages.

**Structure:**
```
frontend/src/
├── App.jsx               # Main app router
├── main.jsx              # React entry point
├── index.css             # Global styles (Vanilla CSS)
├── pages/                # LoginPage, ChatPage
├── components/
│   ├── Sidebar/          # Chat history sidebar
│   ├── TopBar/           # Top navigation
│   ├── MessageBubble/    # Chat message display
│   ├── ChatInput/        # Message input with voice/image
│   ├── AudioRecorder/    # MediaRecorder API integration
│   └── ImageUploader/    # Drag-drop image upload
├── hooks/
│   ├── useAuth.js        # Authentication state
│   └── useChat.js        # Chat state and API calls
└── services/
    └── api.js            # All backend API calls (axios)
```

---

### 7.2. Execution Flow (UI Flow)

```
User Opens App
    │
    ▼
Login Page
    ├── Input: patient_id
    ├── POST /api/auth/login
    └── Store: { access_token, session_id } in memory / localStorage
    │
    ▼
Chat Interface
    │
    ├── [Text Message]
    │   └── POST /api/chat/message { message: text }
    │         Authorization: Bearer {token}
    │
    ├── [Image Upload]
    │   └── POST /api/chat/message-with-image [multipart: message?, image]
    │
    ├── [Audio Record]
    │   ├── MediaRecorder API → Capture microphone
    │   └── POST /api/chat/message-with-audio [multipart: audio]
    │
    └── [Chat History]
        └── GET /api/chat/history → Load previous messages

    ▼
Display Response
    ├── ChatResponse.response → MessageBubble (AI)
    ├── metadata.emergency_detected → Emergency banner
    └── metadata.image_analysis → Display classification result
```

---

### 7.3. Configuration

| Parameter | File | Description |
|-----------|------|-------------|
| `VITE_API_URL` | `frontend/.env` | Backend base URL |
| Dependencies | `package.json` | react, react-dom, axios |
| Build config | `vite.config.js` | Proxy config, build output options |

---

### 7.4. Frontend Strengths / Weaknesses

✅ **Vite**: Modern build tool, fast HMR in development  
✅ **Component-based**: Clearly organised by feature  
✅ **Custom hooks**: Business logic separated from UI  
✅ **Vanilla CSS**: No external CSS framework dependency — full control over styling  
✅ **Chat history management**: Sidebar with delete, rename, and history loading  

❌ **JWT in localStorage**: If stored in localStorage → XSS vulnerability (prefer httpOnly cookies or memory-only storage)  
❌ **No streaming responses**: Full response waits before display → perceived latency for long LLM outputs  
❌ **No offline indicator**: No detection or messaging when backend is unreachable  
❌ **English-only UI**: Interface labels and notifications should support Vietnamese for local patients  

---

## SYSTEM-WIDE ANALYSIS

### 8.1. Overall Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          VITALIS SYSTEM                             │
│                                                                     │
│  ┌──────────┐     ┌──────────────────────────────────────────────┐ │
│  │          │     │              BACKEND (FastAPI)               │ │
│  │  React   │────►│  5 Middleware → Router → Service Layer       │ │
│  │ Frontend │     │          │                                   │ │
│  │  (Vite)  │◄────│          ▼                                   │ │
│  └──────────┘     │   OrchestratorService (lru_cache singleton)  │ │
│                   │          │ run_in_executor()                 │ │
│                   │          ▼                                   │ │
│                   │  ┌──────────────────────────────────────┐   │ │
│                   │  │     ORCHESTRATOR (LangGraph)          │   │ │
│                   │  │                                       │   │ │
│                   │  │  input_router                         │   │ │
│                   │  │    ├─► process_speech (MedASR)        │   │ │
│                   │  │    ├─► process_image (Derm+XGBoost)   │   │ │
│                   │  │    └─► medical_doc_rag (LlamaIndex)   │   │ │
│                   │  │              └─► reasoning (MedGemma) │   │ │
│                   │  │                       └─► call_tool   │   │ │
│                   │  │                           (FAISS RAG) │   │ │
│                   │  │              └─► safety_check → END   │   │ │
│                   │  └──────────────────────────────────────┘   │ │
│                   └──────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │
│  │  MongoDB   │  │  FAISS   │  │ LlamaIndex│  │ Ollama (Local) │  │
│  │ Sessions + │  │ Per-pat  │  │ Medical   │  │ MedGemma 4B +  │  │
│  │   Chats    │  │  FHIR    │  │ Doc Index │  │ nomic-embed    │  │
│  └────────────┘  └──────────┘  └───────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 8.2. Full System Data Flow

```
[1]  Patient opens app → Frontend
[2]  Frontend POST /api/auth/login → Backend
[3]  Backend creates JWT + Session (MongoDB) → Frontend stores token
[4]  Patient sends message/image/audio → Frontend
[5]  Frontend POST /api/chat/message[-with-image|-with-audio] + Bearer token
[6]  Backend middleware: CORS → Log → ErrorHandler → SecurityHeaders → RateLimit
[7]  Backend JWT verify + MongoDB session check
[8]  Backend saves file to disk (if image/audio)
[9]  Backend calls orchestrator.process_message() [via run_in_executor]
[10] Orchestrator initialises AgentState → invoke LangGraph graph
[11] input_router classifies input type → routing decision
[12] [If audio] process_speech: MedASR transcribe → transcribed_text
[13] [If image] process_image: Derm Foundation embed → XGBoost classify → analysis_result
[14] [If text/voice, not image] medical_doc_rag_node:
       LlamaIndex.retrieve(query) → medical_doc_context
[15] reasoning_node:
       a. Emergency check → if detected: immediate response
       b. Patient history keyword check → if needed: call_tool
       c. [call_tool] FAISS search patient index → rag_context
       d. Build Ollama messages: system + image_context + rag_context + doc_context + history + input
       e. ollama.chat(MedGemma 4B) → response text
[16] safety_check: Validate output → privacy check → clean
[17] Return AgentState to OrchestratorService
[18] Backend saves conversation to MongoDB + returns ChatResponse to Frontend
[19] Frontend renders response in chat bubble
```

---

### 8.3. Overall Assessment

#### 🏗 Architectural Strengths

| Strength | Detail |
|----------|--------|
| **AI-First Design** | Entire workflow designed around AI orchestration from the ground up |
| **Privacy by Design** | Per-patient FAISS index, token-based auth, output privacy guardrails |
| **Medical Safety First** | Emergency detection runs before any LLM call; prohibited phrase hard-validation |
| **Multi-modal** | Text + Image + Audio in one unified pipeline |
| **Local Inference** | Ollama local → No cloud API dependency → No medical data exfiltration |
| **Dual RAG** | Medical Doc RAG (general knowledge) + Patient FHIR RAG (personalised) |

#### ⚠️ Critical Risks

| # | Risk | Severity | Location |
|---|------|----------|----------|
| 1 | ~~Re-embed all docs on every RAG retrieval~~ | ✅ **RESOLVED** *(11/03/2026)* | `patient_rag.py` |
| 2 | Shared ConversationMemory across all users | 🔴 CRITICAL | `agent.py` |
| 3 | `process_message()` synchronous in FastAPI async | ✅ **MITIGATED** via `run_in_executor` | `orchestrator_service.py` |
| 4 | SECRET_KEY must be set in .env (no safe default) | 🟠 HIGH | `backend/config.py` |
| 5 | Rate limiting in-memory → cannot scale horizontally | 🟠 HIGH | `middleware.py` |
| 6 | Patient existence not verified at login | 🟡 MEDIUM | `routers/auth.py` |
| 7 | Medical disclaimer commented out | 🟡 MEDIUM | `nodes.py` safety_check |
| 8 | No LLM retry logic | 🟡 MEDIUM | `nodes.py` reasoning_node |
| 9 | JWT stored in localStorage (XSS risk) | 🟡 MEDIUM | `frontend` |

---

### 8.4. Technical Debt — Priority Order

#### 🚨 Short-Term (1–2 weeks)

1. ~~**Fix RAG re-embedding bug**~~ → ✅ **COMPLETED** *(11/03/2026)*
2. **Fix shared ConversationMemory** → Dictionary `{session_id: ConversationMemory}` or Redis
3. **Uncomment medical disclaimer** → Legally required for patient safety and compliance
4. **Add LLM retry logic** → Retry up to 2 times on Ollama timeout/connection error
5. **Set SECRET_KEY validation** → Raise startup error if SECRET_KEY is default/empty

#### 🔧 Medium-Term (1–3 months)

6. **Redis for rate limiting + session** → Enable horizontal scaling
7. **Confidence threshold for image tool** → Warn/reject when confidence < 50%
8. **Multilingual STT** → Add Vietnamese support (Whisper multilingual or dedicated model)
9. **File management endpoint** → Database mapping file_id → file_path; implement delete
10. **Circuit breaker for Ollama** → Fail fast + exponential backoff when LLM overloaded
11. **JWT security** → Move token to httpOnly cookie or memory storage; add refresh token

#### 🏥 Long-Term (3–12 months)

12. **Patient existence verification** → Integrate with hospital information system (HIS)
13. **Audit logging** → Log all medical data access events (HIPAA/healthcare compliance)
14. **Model versioning** → Track XGBoost and MedGemma versions used per conversation
15. **Streaming response** → WebSocket or SSE instead of request-response for better UX
16. **Proactive notifications** → Post-visit medication reminders, appointment alerts
17. **Prometheus/Grafana monitoring** → Observability dashboard for system health

---

### 8.5. Component Maturity Summary

| Component | Completion | Code Quality | Production-Ready |
|-----------|-----------|-------------|-----------------|
| Backend (FastAPI) | 87% | ⭐⭐⭐⭐ | 🟡 Needs Redis for rate limit + no refresh token |
| Orchestrator | 82% | ⭐⭐⭐⭐ | 🟡 Needs shared memory fix + medical disclaimer |
| Medical Doc RAG | 80% | ⭐⭐⭐⭐ | 🟡 Good architecture, needs async + index refresh |
| Image Processing | 78% | ⭐⭐⭐ | 🟡 Needs confidence threshold + preprocessing |
| Speech-to-Text | 70% | ⭐⭐⭐ | 🔴 English only — not suitable for Vietnamese patients |
| Patient DB (RAG) | 78% | ⭐⭐⭐ | 🟡 RAG bug fixed; needs async + better error handling |
| Frontend | 70% | ⭐⭐⭐ | 🟡 Functional; needs streaming + Vietnamese UI |

---

### 8.6. Conclusion

Vitalis demonstrates **strong architectural vision** with many sound technical choices: LangGraph for orchestration, FAISS per-patient for privacy, MedGemma locally for data security, dual RAG for both general and personal medical knowledge, and MedASR for medical-domain speech recognition.

The RAG re-embedding bug — the most severe performance issue — **was resolved** *(11/03/2026)*. The synchronous LangGraph call **is mitigated** via `run_in_executor`.

However, the system **is not yet production-ready** due to:
- **Shared ConversationMemory**: Affects correctness of multi-user conversations under concurrency
- **English-only STT**: Significant barrier for Vietnamese patient demographics
- **Missing medical disclaimer**: Compliance gap for healthcare deployment

With focused work on the short-term priorities, this is a **solid foundation** for a production-grade hospital AI assistant.

---

*Report generated by full static source code analysis.*  
*Created: 10/03/2026*  
*Updated: 13/04/2026 — Reflects v1.1 architecture including dual RAG, XGBoost classifier, admin panel, medical_doc_rag_node, and fixed RAG re-embedding bug.*
