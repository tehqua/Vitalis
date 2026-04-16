# Backend Architecture - How It Works

Comprehensive explanation of the Vitalis Backend architecture, components, data flows, and security model.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Component Details](#component-details)
4. [Request Flow](#request-flow)
5. [Data Flow](#data-flow)
6. [Security Model](#security-model)
7. [Performance Optimizations](#performance-optimizations)

---

## Overview

### System Architecture

The backend is built as a **layered architecture** using FastAPI, providing REST endpoints for the Vitalis medical consultation chatbot system.

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│          (Browser, Mobile App, Postman, etc.)               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS Requests
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│                  (FastAPI + Middleware)                      │
│  ┌──────────────┬──────────────┬───────────────────────┐   │
│  │   CORS       │ Rate Limiter │  Security Headers      │   │
│  │  Middleware  │  Middleware  │  (CSP, XSS, HSTS)     │   │
│  └──────────────┴──────────────┴───────────────────────┘   │
│  ┌──────────────┬──────────────┐                           │
│  │   Logging    │ Error Handler│                           │
│  │  Middleware  │  Middleware  │                           │
│  └──────────────┴──────────────┘                           │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                     Router Layer                             │
│  ┌───────────┬────────────┬───────────┬─────────────┐      │
│  │   Auth    │    Chat    │  Upload   │   Health    │      │
│  │  Router   │   Router   │  Router   │   Router    │      │
│  └───────────┴────────────┴───────────┴─────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────────────────┬──────────────────────────┐       │
│  │  Orchestrator        │    File Service          │       │
│  │  Service             │                          │       │
│  └──────────────────────┴──────────────────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                 External Services Layer                      │
│  ┌──────────────┬──────────────┬──────────────────┐        │
│  │   MongoDB    │    Ollama    │   AI Agents      │        │
│  │   Database   │   (LLM)      │ (Orchestrator)   │        │
│  └──────────────┴──────────────┴──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | FastAPI 0.109 | Async REST API framework |
| **ASGI Server** | Uvicorn | High-performance async server |
| **Database** | MongoDB 7.0 | Document store for conversations and sessions |
| **Database Driver** | Motor 3.3 | Async MongoDB driver |
| **Authentication** | JWT (python-jose, HS256) | Token-based auth |
| **LLM Integration** | Ollama | Local LLM inference (MedGemma 4B) |
| **AI Orchestration** | LangGraph | Stateful agent workflow |
| **File Handling** | aiofiles, python-magic | Async I/O, MIME type detection |
| **Validation** | Pydantic 2.5 | Data validation & serialization |

---

## Architecture Layers

### 1. API Gateway Layer (Middleware Stack)

Middleware processes every request before it reaches routers and every response before returning to client.

**Execution Order (outside → inside):**
```
Request → CORS → Logging → ErrorHandler → SecurityHeaders → RateLimit → Router
Response ← CORS ← Logging ← ErrorHandler ← SecurityHeaders ← RateLimit ← Router
```

#### CORS Middleware
**Purpose:** Cross-Origin Resource Sharing  
**Configuration:**
```python
allow_origins=["http://localhost:3000", "http://localhost:5173"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

#### Logging Middleware
**Purpose:** Request/Response tracking  
**What it does:**
- Generates unique request ID (based on timestamp)
- Logs request method, path, client IP
- Measures processing time
- Logs response status code

**Example Log:**
```
[1771221106.210276] POST /api/chat/message from 127.0.0.1
[1771221106.210276] POST /api/chat/message - 200 - 3.245s
```

#### Error Handler Middleware
**Purpose:** Catch unhandled exceptions  
**What it does:**
- Catches `ValueError` → 400 Bad Request
- Catches any `Exception` → 500 Internal Server Error
- Returns structured JSON error response

#### Rate Limiter Middleware
**Purpose:** Prevent abuse and DDoS  
**What it does:**
- Tracks requests per IP address (in-memory, sliding window)
- Limits: 20 requests/minute, 100 requests/hour (configurable)
- Returns 429 Too Many Requests when exceeded

**How it works:**
```
For each request from IP 192.168.1.100:
1. Clean old requests (older than time window)
2. Count requests in last 1 minute
3. If count >= 20 → Reject with 429
4. Count requests in last 1 hour
5. If count >= 100 → Reject with 429
6. Otherwise → Allow and record timestamp
```

**Response Headers added:**
```
X-RateLimit-Limit-Minute: 20
X-RateLimit-Remaining-Minute: 15
X-RateLimit-Limit-Hour: 100
X-RateLimit-Remaining-Hour: 85
```

> ⚠️ **Limitation:** In-memory rate limiting does not survive multiple Uvicorn workers or horizontal scaling. For production multi-process deployments, replace with Redis-backed rate limiting.

#### Security Headers Middleware
**Purpose:** Web security best practices  
**Headers added:**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
```

### 2. Router Layer

#### Auth Router (`routers/auth.py`)

**Endpoints:**
- `POST /api/auth/login` — Authenticate patient
- `POST /api/auth/logout` — Invalidate session

**Login Flow:**
```
1. Receive patient_id
2. Validate format (regex: ^[A-Z][a-z]+\d+_[A-Z][a-z]+\d+_<uuid36>$)
3. Generate UUID for session_id
4. Create session in MongoDB (TTL: 30 minutes)
5. Generate JWT token:
   - Payload: {patient_id, session_id, exp}
   - Sign with SECRET_KEY (HS256)
6. Return: {access_token, token_type, session_id, expires_in}
```

**JWT Token Structure:**
```
eyJhbGc...  ← Header (algorithm: HS256, type: JWT)
eyJwYXR... ← Payload (patient_id, session_id, exp)
4vGJON_... ← Signature (HMAC-SHA256)
```

#### Chat Router (`routers/chat.py`)

**Endpoints:**
- `POST /api/chat/message` — Text message
- `POST /api/chat/message-with-image` — Message + image (multipart)
- `POST /api/chat/message-with-audio` — Audio message (multipart)
- `GET /api/chat/history` — Get conversation history (paginated)
- `DELETE /api/chat/history` — Clear history

**Message Processing Flow:**
```
1. Verify JWT token → extract patient_id, session_id
2. Validate session in MongoDB (active + not expired)
3. Validate message content (Pydantic schema)
4. [For image/audio] Save file via FileService
5. Call OrchestratorService.process_message(patient_id, text, image_path, audio_path, session_id)
6. Receive AI response + metadata
7. Save conversation to MongoDB: {session_id, patient_id, message, response, metadata, created_at}
8. Return ChatResponse: {response, session_id, timestamp, metadata}
```

#### Upload Router (`routers/upload.py`)

**Endpoints:**
- `POST /api/upload/image` — Upload image file
- `POST /api/upload/audio` — Upload audio file
- `GET /api/upload/limits` — Get size/format limits

**Upload Flow:**
```
1. Verify authentication
2. Validate file:
   ├─ Extension check (.jpg, .png, .wav, etc.)
   ├─ MIME type validation (python-magic / magic number check)
   ├─ Size check (10 MB for images, 50 MB for audio)
   └─ Content validation
3. Generate unique filename: YYYYMMDD_HHMMSS_<uuid>.<ext>
4. Save asynchronously (aiofiles)
5. Calculate SHA256 hash (integrity)
6. Return file metadata
```

**File upload limits:**
- Images: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp` — max **10 MB**
- Audio: `.wav`, `.mp3`, `.m4a`, `.ogg`, `.webm` — max **50 MB**

#### Health Router (`routers/health.py`)

**Endpoint:**
- `GET /api/health` — System health check

**Health Check Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "orchestrator_status": "ready",
  "database_status": "healthy",
  "ollama_status": "healthy"
}
```

### 3. Service Layer

#### Orchestrator Service (`services/orchestrator_service.py`)

**Purpose:** Interface between backend REST layer and AI orchestrator agent  
**Key Features:**
- Session tracking (in-memory, keyed by session_id)
- Retry logic for transient errors (up to 2 retries)
- `asyncio.run_in_executor` to run synchronous `graph.invoke()` without blocking the async event loop
- Singleton via `@lru_cache()` — one shared instance

**Class Structure:**
```python
class OrchestratorService:
    def __init__(self):
        self.agent = MedicalChatbotAgent()   # LangGraph agent
        self.sessions = {}                    # In-memory session tracking
        self._http_client = None             # HTTP pool

    async def process_message(patient_id, text_input, session_id, image_path=None, audio_path=None):
        # 1. Update session tracking
        # 2. Run graph.invoke() in thread executor (sync LangGraph call)
        # 3. Implement retry logic on ConnectionError / TimeoutError
        # 4. Return result dict or error response

    async def clear_memory(session_id):
        # Clear conversation context for session

    async def cleanup_inactive_sessions():
        # Remove sessions inactive > 30 minutes
```

**Session Management:**
```python
sessions = {
    "session-uuid-123": {
        "patient_id": "Adam631_Cronin387_...",
        "created_at": datetime(...),
        "last_activity": datetime(...),
        "message_count": 15
    }
}
```

**Retry Logic:**
```python
try:
    result = await run_in_executor(graph.invoke, initial_state)
except (ConnectionError, TimeoutError) as e:
    if retry_count < 2:
        await asyncio.sleep(1)
        return await process_message(..., retry_count + 1)
    else:
        return error_response
```

#### File Service (`services/file_service.py`)

**Purpose:** Handle file upload, validation, and cleanup  
**Key Features:**
- Async file I/O (aiofiles)
- MIME type detection (python-magic)
- SHA256 integrity hashing
- Automatic cleanup scheduler (files older than 7 days)

**File Save Process:**
```python
async def save_uploaded_file(...):
    # 1. Validate extension
    if ext not in allowed_extensions:
        raise HTTPException(400, "Invalid extension")

    # 2. Read content
    content = await file.read()

    # 3. Validate size
    if len(content) > max_size_mb * 1024 * 1024:
        raise HTTPException(413, "File too large")

    # 4. Validate MIME type (magic numbers)
    mime = magic.from_buffer(content, mime=True)
    if not mime.startswith(expected_type):
        raise HTTPException(400, "Invalid file content")

    # 5. Generate filename: YYYYMMDD_HHMMSS_<uuid>.<ext>
    filename = f"{timestamp}_{uuid4_hex}{ext}"

    # 6. Save asynchronously
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)

    # 7. Calculate SHA256 hash for integrity
    file_hash = hashlib.sha256(content).hexdigest()
    return file_path
```

**Cleanup Scheduler:**
```python
async def cleanup_old_files(upload_dir, days_old=7):
    cutoff = datetime.now() - timedelta(days=days_old)
    for file in upload_dir.iterdir():
        if file.stat().st_mtime < cutoff:
            file.unlink()
```

### 4. Database Layer

#### MongoDB Collections

**1. `conversations`**
```javascript
{
  _id: ObjectId("..."),
  session_id: "uuid-string",
  patient_id: "Adam631_Cronin387_...",
  message: "I have a headache",
  response: "Based on your symptoms...",
  metadata: {
    input_type: "text",
    tools_used: [],
    emergency_detected: false,
    image_analysis: null
  },
  created_at: ISODate("2024-01-15T10:30:00Z")
}
```

**Indexes:**
- `session_id` (for fast history lookup)
- `patient_id` (for patient-specific queries)
- `created_at` (for time-based queries, TTL cleanup)

**2. `sessions`**
```javascript
{
  _id: ObjectId("..."),
  session_id: "uuid-string",
  patient_id: "Adam631_Cronin387_...",
  created_at: ISODate("2024-01-15T10:00:00Z"),
  expires_at: ISODate("2024-01-15T10:30:00Z"),
  active: true
}
```

**Indexes:**
- `session_id` (unique, for fast lookup)
- `patient_id` (for patient sessions)
- `expires_at` (for cleanup queries)

#### Database Operations (Motor Async Driver)

```python
# Find
cursor = db.conversations.find({"session_id": session_id})
conversations = await cursor.to_list(length=50)

# Insert
result = await db.conversations.insert_one(document)

# Update
await db.sessions.update_one(
    {"session_id": session_id},
    {"$set": {"expires_at": new_time}}
)

# Delete
result = await db.sessions.delete_many(
    {"expires_at": {"$lt": cutoff_time}}
)
```

### 5. Background Tasks (Scheduler)

**Purpose:** Automated maintenance operations  
**Location:** `scheduler.py`

| Task | Frequency | Purpose |
|------|-----------|---------|
| Session cleanup | 30 minutes | Remove inactive/expired sessions |
| File cleanup | 60 minutes | Delete old uploaded files (7+ days) |
| Database cleanup | 120 minutes | Remove expired conversation records |

**Implementation:**
```python
class BackgroundScheduler:
    async def start(self):
        self.tasks = [
            asyncio.create_task(self._run_periodic(
                self._cleanup_sessions, interval_minutes=30
            )),
            asyncio.create_task(self._run_periodic(
                self._cleanup_files, interval_minutes=60
            )),
            asyncio.create_task(self._run_periodic(
                self._cleanup_database, interval_minutes=120
            )),
        ]

    async def _run_periodic(self, func, interval_minutes):
        while self.running:
            await func()
            await asyncio.sleep(interval_minutes * 60)
```

---

## Request Flow

### Complete Request Lifecycle (Text + Image Example)

```
Step 1: Client Request
POST /api/chat/message-with-image
Headers:
  Authorization: Bearer eyJhbG...
  Content-Type: multipart/form-data
Body:
  message: "What is this rash?"
  image: [binary data]

↓

Step 2: Middleware Stack (Request Phase)
├─ CORS Middleware: Check origin → Add CORS headers
├─ Logging Middleware: Log request, generate request ID
├─ Error Handler: Wrap handler for exception safety
├─ Security Headers: (processed on response)
└─ Rate Limiter: Check IP limits → Allow (15/20)

↓

Step 3: Router (chat.py)
├─ Route match: send_message_with_image()
├─ Dependency injection:
│  ├─ get_current_user() → Verify JWT + session DB check
│  ├─ get_orchestrator_service() → lru_cache singleton
│  ├─ get_db() → MongoDB connection
│  └─ get_settings() → pydantic-settings config
└─ Extract: message, image, current_user

↓

Step 4: Authentication (auth.py)
├─ Extract token from Authorization header
├─ Decode JWT:
│  ├─ Verify HMAC-SHA256 signature
│  ├─ Check expiration
│  └─ Extract: {patient_id, session_id}
├─ Verify session in MongoDB (active + not expired)
├─ Extend session TTL on activity
└─ Return: TokenData(patient_id, session_id)

↓

Step 5: File Service
├─ Validate image file:
│  ├─ Extension: .jpg ✓
│  ├─ Size: 2.5 MB < 10 MB ✓
│  └─ MIME: image/jpeg ✓
├─ Generate filename: 20240115_143025_<uuid>.jpg
├─ Save to: uploads/20240115_143025_<uuid>.jpg
└─ Return: file_path

↓

Step 6: Orchestrator Service
├─ Call: process_message(
│    patient_id="Adam631_...",
│    text_input="What is this rash?",
│    image_file_path="uploads/20240115_143025_<uuid>.jpg",
│    session_id="uuid-123"
│  )
├─ Run via asyncio.run_in_executor (non-blocking for async loop)
├─ LangGraph agent workflow:
│  ├─ input_router: Detect image input → routing: process_image
│  ├─ process_image: Derm Foundation + XGBoost
│  │    → {class: "Eczema/Dermatitis", confidence: 0.87}
│  ├─ reasoning_node: Build context + call MedGemma (Ollama)
│  │    → AI medical response
│  └─ safety_check: Validate + clean response
└─ Return: {response, metadata}

↓

Step 7: Database Storage
await db.save_conversation(
  session_id="uuid-123",
  patient_id="Adam631_...",
  message="What is this rash?",
  response="Based on the image analysis...",
  metadata={
    "input_type": "image",
    "tools_used": ["analyze_skin_image"],
    "emergency_detected": false,
    "image_analysis": {
      "class_name": "Eczema/Dermatitis",
      "confidence": 0.87
    }
  }
)

↓

Step 8: Middleware Stack (Response Phase)
├─ Security Headers: Add CSP, XSS protection, HSTS
├─ Rate Limiter: Add rate limit headers
├─ Logging: Log response (200, 3.245s)
└─ CORS: Ensure CORS headers present

↓

Step 9: Client Response
HTTP/1.1 200 OK
{
  "response": "Based on the image analysis, this appears to be Eczema/Dermatitis with 87% confidence...",
  "session_id": "uuid-123",
  "timestamp": "2024-01-15T14:30:28Z",
  "metadata": {
    "input_type": "image",
    "tools_used": ["analyze_skin_image"],
    "emergency_detected": false,
    "image_analysis": {...}
  }
}
```

**Processing Timeline:**
```
0.000s: Request received
0.001s: Middleware processing
0.002s: Authentication + session check
0.010s: File validation & save
0.015s: Orchestrator starts
0.200s: Image analysis (Derm Foundation + XGBoost)
1.000s: Medical Doc RAG retrieval (optional for image queries)
3.200s: MedGemma (Ollama) response generated
3.240s: Database save
3.245s: Response sent
```

---

## Data Flow

### Authentication Flow

```
Client                                              Server
  │                                                    │
  │  POST /api/auth/login {patient_id}                │
  ├───────────────────────────────────────────────────►│
  │                                    Validate Format │
  │                                    Generate UUID   │
  │                                    Create Session  │
  │                                     (MongoDB)      │
  │                                    Generate JWT:   │
  │                                     {patient_id,   │
  │                                      session_id,   │
  │                                      exp} HS256    │
  │  200 OK {access_token, session_id, expires_in}    │
  │◄───────────────────────────────────────────────────┤
  │                                                    │
  │  POST /api/chat/message                           │
  │  Authorization: Bearer <token>                    │
  ├───────────────────────────────────────────────────►│
  │                                    Decode JWT      │
  │                                    Verify Sig      │
  │                                    Check Exp       │
  │                                    Verify Session  │
  │                                    (MongoDB)       │
  │                                    Process...      │
  │  200 OK {response, ...}                           │
  │◄───────────────────────────────────────────────────┤
```

### Chat Message Flow (Detailed)

```
Client              Backend           Orchestrator         External Services
  │                   │                    │                      │
  │  Chat Request     │                    │                      │
  ├──────────────────►│                    │                      │
  │                   │ Verify Auth        │                      │
  │                   ├─────┐             │                      │
  │                   │◄────┘             │                      │
  │                   │ process_message() │                      │
  │                   ├───────────────────►                      │
  │                   │                   │ input_router          │
  │                   │                   ├──────┐               │
  │                   │                   │◄─────┘               │
  │                   │                   │ [if image]            │
  │                   │                   │ process_image         │
  │                   │                   ├──────────────────────►│
  │                   │                   │                       │ DermFoundation
  │                   │                   │                       │ + XGBoost
  │                   │                   │ Analysis Result       │
  │                   │                   │◄──────────────────────┤
  │                   │                   │ [if text/voice]       │
  │                   │                   │ medical_doc_rag       │
  │                   │                   ├──────────────────────►│
  │                   │                   │                       │ LlamaIndex
  │                   │                   │ Doc Context           │
  │                   │                   │◄──────────────────────┤
  │                   │                   │ [if history query]    │
  │                   │                   │ call_tool (FAISS RAG) │
  │                   │                   ├──────────────────────►│
  │                   │                   │                       │ FAISS Patient
  │                   │                   │ Medical History       │
  │                   │                   │◄──────────────────────┤
  │                   │                   │ LLM Call (Ollama)     │
  │                   │                   ├──────────────────────►│
  │                   │                   │                       │ MedGemma 4B
  │                   │                   │ AI Response           │
  │                   │                   │◄──────────────────────┤
  │                   │                   │ safety_check          │
  │                   │                   ├──────┐               │
  │                   │                   │◄─────┘               │
  │                   │ {response, meta}  │                      │
  │                   │◄──────────────────┤                      │
  │                   │ Save MongoDB      │                      │
  │                   ├─────┐             │                      │
  │                   │◄────┘             │                      │
  │  Response         │                   │                      │
  │◄──────────────────┤                   │                      │
```

---

## Security Model

### Defense in Depth (6 Layers)

**Layer 1: Network Security**
- CORS whitelist (only configured frontend origins)
- Rate limiting — 20 req/min, 100 req/hour (DDoS protection)
- HTTPS enforcement (production via HSTS header)

**Layer 2: Input Validation**
- Pydantic schemas (automatic type + format validation)
- File type verification (extension + MIME type + magic bytes)
- Size limits enforcement (10 MB images, 50 MB audio)
- Patient ID regex validation before any processing
- XSS pattern filtering in inputs (`guardrails.sanitize_input()`)

**Layer 3: Authentication & Authorization**
- JWT token-based authentication (HS256)
- MongoDB session validation on every request
- Token expiration (60 min JWT, 30 min session TTL)
- Patient-specific data access — per-patient FAISS isolation

**Layer 4: Content Security**
- Security headers: CSP, X-Frame-Options, X-XSS-Protection, HSTS
- Path traversal prevention in file handling
- File integrity checking (SHA256)

**Layer 5: Business Logic Security**
- Medical disclaimer enforcement (soft violations)
- Emergency detection — bypasses normal LLM pipeline for immediate safety response
- No definitive diagnoses — prohibited phrase hard-violation replacement
- Privacy protection — LLM output checked for cross-patient data leakage

**Layer 6: Audit & Monitoring**
- Request logging with unique IDs and response timing
- Error tracking with stack traces
- Rate limit violation logging

### JWT Token Implementation

**Token Generation:**
```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

**Token Verification:**
```python
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        patient_id = payload.get("patient_id")
        session_id = payload.get("session_id")
        return TokenData(patient_id, session_id)
    except JWTError:
        raise HTTPException(401, "Invalid credentials")
```

**Session Validation:**
```python
# After JWT verification
session = await db.get_session(session_id)
if not session or not session["active"]:
    raise HTTPException(401, "Session expired")

# Extend session on activity
await db.extend_session(session_id, minutes=30)
```

---

## Performance Optimizations

### 1. Asynchronous I/O

**Pattern:** Use `async/await` for all I/O operations

```python
# File save (async)
async def save_file(data):
    async with aiofiles.open("file.txt", "w") as f:
        await f.write(data)  # CPU handles other requests during I/O

# Database (Motor async driver)
conversations = await cursor.to_list(length=50)
```

### 2. Executor for Synchronous Code

LangGraph's `graph.invoke()` is synchronous. To avoid blocking the async FastAPI event loop:

```python
import asyncio

async def process_message(self, ...):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Default thread pool
        self.agent.process_message,
        patient_id, text_input, image_path, audio_path
    )
    return result
```

### 3. Connection Pooling

**MongoDB (Motor):**
```python
client = AsyncIOMotorClient(
    "mongodb://localhost:27017",
    maxPoolSize=50  # Up to 50 concurrent connections
)
```

**HTTP (Ollama client reuse):**
```python
self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
# Reused across all requests — avoids connection overhead
```

### 4. Lazy Loading

**Orchestrator Service (singleton):**
```python
@lru_cache()
def get_orchestrator_service():
    return OrchestratorService()  # Created once, reused
```

**MedicalDocRAGService (singleton + lazy-load):**
```python
# Not initialized at startup — loads on first query
_instance: Optional[MedicalDocRAGService] = None

@classmethod
def get_instance(cls, config) -> "MedicalDocRAGService":
    if cls._instance is None:
        cls._instance = cls(config)
    return cls._instance
```

**Benefits:**
- Fast API startup (no model loading at boot)
- Memory saved if feature never used
- Models loaded only on first actual query

### 5. Background Task Offloading

```python
# Maintenance tasks run in background without blocking API responses
asyncio.create_task(cleanup_old_files())       # 60-minute interval
asyncio.create_task(cleanup_sessions())         # 30-minute interval
asyncio.create_task(cleanup_old_db_records())  # 120-minute interval
```

### 6. Settings Caching

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()  # pydantic-settings loads and validates .env once
```

### 7. Rate Limiting

Sliding-window rate limiting prevents resource exhaustion:

- Protects against DDoS and accidental feedback loops
- Ensures fair resource distribution across patients
- Prevents LLM from being overloaded by a single user

---

## Summary

### Architecture Highlights

1. **Layered Design**: Clear separation — middleware, routers, services, external integrations
2. **Async-First**: Non-blocking I/O throughout; sync LangGraph graph runs in thread executor
3. **Security**: 6-layer defense in depth from network to business logic
4. **Scalability**: Connection pooling, singleton caching, background tasks
5. **Maintainability**: Well-organised, documented code with separate concerns
6. **Production-Ready**: Logging, error handling, scheduled cleanup, health endpoint

### Key Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **API Gateway** | Request routing, security, rate limiting | FastAPI + 5 Middleware layers |
| **Auth System** | Authentication, session management | JWT (python-jose) + MongoDB |
| **Orchestrator** | AI workflow coordination | LangGraph (StateGraph) |
| **File Handler** | Upload, validation, cleanup | aiofiles + python-magic |
| **Database** | Conversations, sessions | MongoDB (Motor async driver) |
| **Background** | Maintenance tasks | asyncio scheduler |
| **Medical Doc RAG** | Clinical knowledge retrieval | LlamaIndex + bge-large-en-v1.5 |
| **Patient RAG** | Personal FHIR record retrieval | FAISS + nomic-embed-text |

### Request Processing Times

| Stage | Typical Duration |
|-------|----------------|
| Middleware | < 1 ms |
| Authentication | < 10 ms |
| File validation & save | < 10 ms |
| Medical Doc RAG retrieval | ~100–500 ms (cached) / up to 5 min (first load) |
| Image analysis (Derm + XGBoost) | ~200–500 ms |
| MedGemma LLM (Ollama) | 1–5 seconds |
| Database save | < 50 ms |
| **Total** | **~1–6 seconds per request** |

### Scalability

**Horizontal Scaling:**
- Multiple Uvicorn workers with Gunicorn
- Load balancer (Nginx, Caddy)
- Stateless design (all session state in MongoDB)
- ⚠️ Rate limiting and LLM model require shared-resource coordination at scale

**Vertical Scaling:**
- Async I/O (thousands of concurrent connections)
- Connection pooling
- Background task offloading

---

**This architecture supports production deployment with high availability, multi-layer security, and performance suitable for hospital-grade workloads.**

*Updated: 2026-04-13 | Vitalis v1.1*