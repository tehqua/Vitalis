# Vitalis – Detailed Agent Workflow

## Overview

Vitalis is an AI Agent system implemented with **LangGraph** that orchestrates multiple specialised sub-agents to deliver personalised medical consultation via a web chatbot. The system supports three input modalities (text, audio, image) and multiple query types (general medical advice via Hierarchical Medical Doc RAG, personal medical history via FHIR Patient RAG, and multimodal image/audio analysis).

---

## Architecture Summary

```
User (Patient)
    │
    ▼  (Text / Audio / Image)
Frontend (React 18 + Vite)
    │
    ▼  REST API
Backend (FastAPI + Uvicorn)
    │  Auth (JWT), file upload, conversation storage (MongoDB)
    ▼
Orchestrator Agent (LangGraph)
    ├─► input_router          ← Entry point, validates & classifies input
    ├─► process_speech        ← Speech-to-Text Agent (google/medasr)
    ├─► process_image         ← Image Analysis Agent (Derm Foundation + XGBoost)
    ├─► medical_doc_rag_node  ← Hierarchical Medical Doc RAG (LlamaIndex)
    ├─► reasoning_node        ← MedGemma LLM (Ollama)
    │       └─► call_tool    ← Patient Record RAG Agent (FAISS/FHIR)
    ├─► safety_check          ← Guardrails: privacy, medical disclaimers
    └─► error_handler         ← Fallback for errors
```

---

## LangGraph State

The workflow state (`AgentState`) carries:

| Field | Type | Description |
|---|---|---|
| `patient_id` | str | Authenticated patient identifier |
| `session_id` | str | Active session identifier |
| `messages` | List[Message] | Conversation history (last 5 messages fed to LLM) |
| `current_input_type` | str | `text` / `speech` / `image` / `multimodal` |
| `user_text_input` | str | Raw text from user |
| `audio_file_path` | str | Path to uploaded audio (.wav/.mp3/…) |
| `image_file_path` | str | Path to uploaded image (.jpg/.png/…) |
| `transcribed_text` | str | STT output from MedASR |
| `image_analysis_result` | dict | Skin disease classification result from Derm Foundation + XGBoost |
| `rag_context` | dict | Retrieved patient FHIR records |
| `rag_needed` | bool | Flag to trigger Patient RAG retrieval |
| `medical_doc_context` | str | Retrieved general medical document context (LlamaIndex) |
| `routing_decision` | str | Next node decision |
| `requires_tool_call` | bool | Whether a tool call is pending |
| `tool_calls_completed` | List[str] | Completed tool name list |
| `next_action` | str | Pending tool action name |
| `final_response` | str | Generated AI response |
| `emergency_detected` | bool | Emergency flag |
| `safety_check_passed` | bool | Safety validation flag |
| `agent_scratchpad` | str | Internal reasoning scratchpad |
| `timestamp` | str | ISO timestamp of request |

---

## Workflow Nodes

### 1. `input_router` (Entry Point)

**Purpose:** Validate input and route to the correct next node.

**Steps:**
1. Determine `input_type` from presence of audio/image/text fields
2. Validate `patient_id` format (regex: `^[A-Z][a-z]+\d+_[A-Z][a-z]+\d+_<uuid36>$`)
3. Validate image file (allowed extensions: jpg, jpeg, png, bmp, webp; max 10 MB)
4. Validate audio file (allowed extensions: wav, mp3, ogg, m4a, webm; max 50 MB)
5. Set `routing_decision`:
   - `process_speech` → if audio present
   - `process_image` → if image only
   - `reasoning` → if text only (after medical_doc_rag runs first)
   - `error` → if validation fails

**Outputs:**
- Routes to: `process_speech`, `process_image`, `medical_doc_rag`, or `error_handler`

---

### 2. `process_speech` (Speech-to-Text Agent)

**Purpose:** Transcribe audio input to text.

**Model:** `google/medasr` (medical-domain ASR via HuggingFace Transformers pipeline)

**Steps:**
1. Load audio from `audio_file_path` (librosa resample to 16kHz mono)
2. Run MedASR pipeline with chunked processing (20s chunks, 2s stride/overlap)
3. Post-process and clean transcribed text (`_restore_text()`)
4. Store result in `transcribed_text`
5. If image also present → route to `process_image`; else → route to `reasoning`

**Input:** Audio file path (.wav/.mp3/.ogg/.m4a/.webm)  
**Output:** `transcribed_text` (string)

---

### 3. `process_image` (Image Analysis Agent)

**Purpose:** Classify skin condition from image.

**Model:** Derm Foundation (Google, TFSMLayer — feature extractor) + XGBoost classifier

**Steps:**
1. Load image from `image_file_path` and verify integrity (PIL.Image.verify)
2. Extract embedding via Derm Foundation: serialize as `tf.train.Example` → `output["embedding"]` → numpy array
3. Classify into 8 clinical groups:
   - Eczema/Dermatitis / Bacterial Infections / Fungal Infections / Viral Infections
   - Infestations / Acneiform / Vascular/Benign Lesions / Healthy Skin
4. Return `class_id`, `class_name`, `confidence`, `all_probabilities`

**Input:** Image file path (.jpg/.png/.bmp/.webp)  
**Output:** `image_analysis_result` dict:
```json
{
  "class_id": 0,
  "class_name": "Eczema/Dermatitis",
  "confidence": 0.87,
  "all_probabilities": {"Eczema/Dermatitis": 0.87, "Fungal Infections": 0.05, ...}
}
```

Always routes to `reasoning` after completion.

---

### 4. `medical_doc_rag_node` (Hierarchical Medical Document RAG)

**Purpose:** Retrieve general medical knowledge context from curated clinical documents.

**Technology:** LlamaIndex `HierarchicalEmbeddingIndex` with `bge-large-en-v1.5` embeddings (persisted to disk)

**Steps:**
1. Extract user query text from state
2. If no query or service unavailable → set `medical_doc_context = None`, continue gracefully
3. Call `MedicalDocRAGService.retrieve(query)` with dual timeout (5 min first load, 8s subsequent)
4. Store result in `medical_doc_context` (None on timeout/error — LLM still answers)
5. Route to `reasoning`

**Pattern:** Singleton + lazy-load — service initialises once, loaded on first query.

**Input:** User query string  
**Output:** `medical_doc_context` (string or None)

**Note:** This node fires on every text/voice query. It is a prerequisite to `reasoning_node` for text-only and voice inputs.

---

### 5. `reasoning_node` (MedGemma LLM)

**Purpose:** Core AI reasoning — generate a medical response.

**Model:** MedGemma 4B IT (via Ollama — `thiagomoraes/medgemma-4b-it:Q4_K_S`, temperature 0.3)

**Steps:**
1. Extract user text (`user_text_input` or `transcribed_text`)
2. Sanitise and validate input (strip HTML/script injection)
3. **Emergency Detection:** Check for keywords (chest pain, difficulty breathing, unconscious, severe bleeding, stroke, suicidal ideation, etc.)  
   → If emergency: generate emergency response immediately → route to `safety_check`
4. Build LLM context:
   - Include image analysis results if available
   - Include Patient RAG context if available
   - Include Medical Doc context if available
5. **Patient RAG Trigger:** Check if query contains medical-history keywords (`my`, `history`, `record`, `medication`, `prescription`, `test`, `result`, `doctor`, `appointment`, `lab`, `vaccine`, `allergy`, `blood pressure`)
   - If RAG needed and not yet retrieved → route to `call_tool`
6. Build Ollama messages: `[system: MASTER_SYSTEM_PROMPT + patient_context] + [system: context] + [history: last 5 msgs] + [user: input]`
7. Call MedGemma via Ollama: `ollama.chat(model, messages, {temperature: 0.3, num_predict: 1024})`
8. Store `final_response` → route to `safety_check`

**Input:** User query + (optional) image analysis + (optional) Patient RAG context + (optional) Medical Doc context  
**Output:** `final_response` (string medical response)

---

### 6. `call_tool` → `_retrieve_patient_records` (Patient Record RAG Agent)

**Purpose:** Retrieve patient medical history from their individual FAISS vector index.

**Technology:** FAISS (`IndexFlatIP`) + `nomic-embed-text` (Ollama embeddings) + pre-built per-patient FHIR narrative chunks

**Steps:**
1. Use `patient_id` + user query as input
2. Load patient's FAISS index and pre-computed document vectors from `{patient_id}.index` + `{patient_id}.pkl`
3. Apply year-based temporal filtering if query mentions a year (regex: `(19|20)\d{2}`)
4. Embed query vector (single Ollama API call — does NOT re-embed documents)
5. `faiss.IndexFlatIP.search(query_vec, top_k=3)` → retrieve top-K relevant records
6. Store context + sources in `rag_context`, route back to `reasoning_node`

**Input:**
- `patient_id`: string
- `query`: user's question text
- `top_k`: 3 (configurable)

**Output:** `rag_context` dict:
```json
{
  "context": "Patient's last blood test on 2024-01-15 showed...",
  "sources": [{"text": "...", "metadata": {"year": 2024}}, ...]
}
```

After retrieval, routes back to `reasoning_node` with context loaded.

---

### 7. `safety_check` (Guardrails)

**Purpose:** Validate and clean response before returning to user.

**Checks:**
1. **Hard violations** (prohibited phrases): "you definitely have", "you are diagnosed with", "i diagnose you", "you need this medication", "stop taking your medication"
   - → Replace entire response with a safe fallback
2. **Soft violations** (definitive diagnosis patterns): detected but non-critical
   - → Append a medical disclaimer note
3. **Privacy validation**: ensure no cross-patient data leakage (other patient IDs not exposed)
4. **Response cleaning**: `clean_response()` removes excess blank lines, normalises whitespace

**Output:** Final cleaned `final_response` → `END`

---

### 8. `error_handler`

**Purpose:** Catch and handle any unrecoverable validation errors.

**Output:** Generic error message → `END`

---

## Query Type Workflows

### 🔵 Case 1: General Medical Question (Text Only)

```
Input: text = "What are symptoms of diabetes?"

input_router → medical_doc_rag_node → reasoning_node → safety_check → END

Response: MedGemma explanation enriched with medical document context
```

| Stage | Input | Output |
|---|---|---|
| input_router | Text query | routing: medical_doc_rag |
| medical_doc_rag_node | User query | Medical doc context (LlamaIndex) |
| reasoning_node | User text + doc context | Medical explanation from MedGemma |
| safety_check | Draft response | Validated final response |

---

### 🟢 Case 2: Personal Medical History Query (Patient RAG)

```
Input: text = "What were my last blood test results?"
       patient_id = "Adam631_Cronin387_aff8f143-..."

input_router → medical_doc_rag_node → reasoning_node → call_tool → reasoning_node → safety_check → END

Response: Summary of patient's actual lab results from FHIR database
```

| Stage | Input | Output |
|---|---|---|
| input_router | Text query | routing: medical_doc_rag |
| medical_doc_rag_node | User query | Medical doc context |
| reasoning_node (1st) | User text + doc context | Detects history keyword → routes to call_tool |
| call_tool | patient_id + query | RAG context (relevant FHIR records) |
| reasoning_node (2nd) | Text + both RAG contexts | Personalised response grounded in real records |
| safety_check | Draft response | Validated final response |

---

### 🟡 Case 3: Image Analysis (Skin Condition)

```
Input: image = skin_photo.jpg
       text = "Is this a fungal infection?"

input_router → process_image → reasoning_node → safety_check → END

Response: Skin disease classification + MedGemma explanation
```

| Stage | Input | Output |
|---|---|---|
| input_router | Image file | routing: process_image |
| process_image | Image (.jpg/.png) | Derm class: "Eczema/Dermatitis" (87% confidence) |
| reasoning_node | Text + image analysis | Medical explanation based on classification |
| safety_check | Draft response | Validated final response |

---

### 🟠 Case 4: Voice Query (Speech-to-Text)

```
Input: audio = question.wav
       text = (optional)

input_router → process_speech → medical_doc_rag_node → reasoning_node → safety_check → END

Response: Same as text query flow after transcription
```

| Stage | Input | Output |
|---|---|---|
| input_router | Audio file | routing: process_speech |
| process_speech | Audio (.wav/.mp3) | Transcribed text (MedASR) |
| medical_doc_rag_node | Transcribed query | Medical doc context |
| reasoning_node | Transcribed text + doc context | Medical response from MedGemma |
| safety_check | Draft response | Validated final response |

---

### 🔴 Case 5: Emergency Detection

```
Input: text = "I have severe chest pain and can't breathe"

input_router → medical_doc_rag_node → reasoning_node → safety_check → END

Response: EMERGENCY ALERT — Call emergency services immediately
```

| Stage | Input | Output |
|---|---|---|
| input_router | Emergency text | routing: medical_doc_rag |
| medical_doc_rag_node | Query | Context (may be skipped on timeout) |
| reasoning_node | Emergency keywords detected | Immediate emergency response (bypasses LLM call) |
| safety_check | Emergency response | Final emergency alert response |

---

### 🟣 Case 6: Multimodal (Audio + Image)

```
Input: audio = voice_question.wav
       image = skin_photo.jpg

input_router → process_speech → process_image → reasoning_node → safety_check → END

Response: Response combining transcribed speech context + image analysis
```

---

## Backend API Endpoints

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/login` | POST | ❌ | Patient login with patient_id → JWT token |
| `/api/auth/logout` | POST | ✅ | Invalidate session |
| `/api/chat/message` | POST | ✅ | Send text message → AI response |
| `/api/chat/message-with-image` | POST | ✅ | Send message + image → AI response |
| `/api/chat/message-with-audio` | POST | ✅ | Send audio message → AI response |
| `/api/chat/history` | GET | ✅ | Get conversation history |
| `/api/chat/history` | DELETE | ✅ | Clear conversation history |
| `/api/upload/image` | POST | ✅ | Upload image file |
| `/api/upload/audio` | POST | ✅ | Upload audio file |
| `/api/upload/limits` | GET | ❌ | Get file size/format limits |
| `/api/health` | GET | ❌ | System health check |

**Auth Flow:**
1. Patient sends `patient_id` to `/api/auth/login`
2. Backend validates format and creates MongoDB session (TTL: 30 min)
3. Returns JWT token (HS256, TTL: 60 min)
4. All subsequent requests include `Authorization: Bearer <token>`

**Patient ID format:**
```
FirstName###_LastName###_<uuid>
Example: Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58
```

---

## Data Layer

| Storage | Technology | Purpose |
|---|---|---|
| Conversation History | MongoDB (Motor async) | Stores chat sessions and messages |
| Patient Records (offline build) | FHIR JSON files → FAISS | 1,000+ structured medical records |
| Patient Vector Embeddings | FAISS IndexFlatIP | Per-patient semantic search for RAG |
| Medical Document Index | LlamaIndex + bge-large-en-v1.5 | Hierarchical clinical knowledge retrieval |
| Uploaded Files | Local FS (`/uploads`) | Temporary audio/image storage (auto-cleaned) |

### Dual RAG Architecture

| RAG Layer | Data Source | Trigger | Purpose |
|---|---|---|---|
| **Medical Doc RAG** | Curated clinical guidelines & literature (LlamaIndex) | Every text/voice query | Grounds the LLM in authoritative clinical knowledge |
| **Patient Record RAG** | Individual FHIR medical records (FAISS) | On-demand, keyword-triggered | Personalises responses with patient-specific history |

The Medical Doc RAG service uses a **singleton + lazy-load** pattern with dual timeouts: 5 minutes for first load (includes HuggingFace model download), 8 seconds for subsequent queries. On timeout or error, it falls back gracefully — the LLM responds without the extra context.

---

## Safety & Guardrails

| Check | Description |
|---|---|
| Input Validation | File type, size, patient ID format (regex) |
| Emergency Detection | Keywords: chest pain, difficulty breathing, unconscious, severe bleeding, stroke, suicidal ideation |
| Content Guardrails | Hard: no definitive diagnoses / dangerous phrases. Soft: append disclaimer |
| Privacy Protection | Responses never expose other patients' data |
| Medical Disclaimer | AI is support tool, not a replacement for doctors |
| Rate Limiting | 20 requests/min, 100 requests/hour per IP (sliding window) |

---

## Configuration Reference

| Parameter | Default | Description |
|---|---|---|
| `model_name` | `thiagomoraes/medgemma-4b-it:Q4_K_S` | LLM via Ollama |
| `model_temperature` | `0.3` | Low temperature for medical reliability |
| `model_max_tokens` | `1024` | Max output tokens |
| `ollama_base_url` | `http://localhost:11434` | Ollama server address |
| `rag_top_k` | `3` | Number of patient records to retrieve |
| `enable_emergency_detection` | `True` | Emergency keyword detection |
| `medical_doc_rag_enabled` | `True` | Enable Hierarchical Medical Doc RAG |
| `medical_doc_persist_dir` | `../rag_hierarchical_index/large_medical_doc_index` | LlamaIndex store path |
| `medical_doc_min_score` | `0.6` | Minimum relevance score for doc retrieval |
| `medical_doc_max_context_nodes` | `3` | Max context chunks from doc RAG |

---

*Updated: 2026-04-13 | Vitalis v1.1*
