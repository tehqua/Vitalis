# Backend Architecture - How It Works

Comprehensive explanation of the Medical Chatbot Backend architecture, components, and workflows.

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

The backend is built as a **layered microservice architecture** using FastAPI, providing REST endpoints for a medical consultation chatbot system.

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
│  ┌──────────────┬──────────────┬──────────────────────┐    │
│  │   CORS       │ Rate Limiter │  Security Headers    │    │
│  │  Middleware  │  Middleware  │     Middleware       │    │
│  └──────────────┴──────────────┴──────────────────────┘    │
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
| **Database** | MongoDB 7.0 | Document store for conversations |
| **Database Driver** | Motor 3.3 | Async MongoDB driver |
| **Authentication** | JWT (python-jose) | Token-based auth |
| **LLM Integration** | Ollama | Local LLM inference (MedGemma) |
| **AI Orchestrator** | LangGraph | Agent workflow orchestration |
| **File Handling** | aiofiles, python-magic | Async I/O, type detection |
| **Validation** | Pydantic 2.5 | Data validation & serialization |

---

## Architecture Layers

### 1. API Gateway Layer (Middleware Stack)

Middleware processes every request before it reaches routers and every response before returning to client.

**Execution Order:**
```
Request → CORS → Logging → Rate Limiter → Security Headers → Router
Response ← CORS ← Logging ← Rate Limiter ← Security Headers ← Router
```

#### CORS Middleware
**Purpose:** Cross-Origin Resource Sharing  
**What it does:**
- Allows specified frontend domains to access API
- Handles preflight OPTIONS requests
- Adds CORS headers to responses

**Configuration:**
```python
allow_origins=["http://localhost:3000"]  # Frontend URL
allow_credentials=True                    # Allow cookies
allow_methods=["*"]                       # All HTTP methods
allow_headers=["*"]                       # All headers
```

#### Logging Middleware
**Purpose:** Request/Response tracking  
**What it does:**
- Generates unique request ID
- Logs request method, path, client IP
- Measures processing time
- Logs response status code

**Example Log:**
```
[1771221106.210276] POST /api/chat/message from 127.0.0.1
[1771221106.210276] POST /api/chat/message - 200 - 3.245s
```

#### Rate Limiter Middleware
**Purpose:** Prevent abuse and DDoS  
**What it does:**
- Tracks requests per IP address
- Implements sliding window algorithm
- Limits: 20 requests/minute, 100 requests/hour (configurable)
- Returns 429 Too Many Requests when exceeded

**How it works:**
```python
# For each request from IP 192.168.1.100:
1. Clean old requests (older than time window)
2. Count requests in last 1 minute
3. If count >= 20 → Reject with 429
4. Count requests in last 1 hour
5. If count >= 100 → Reject with 429
6. Otherwise → Allow and record timestamp
```

**Response Headers:**
```
X-RateLimit-Limit-Minute: 20
X-RateLimit-Remaining-Minute: 15
X-RateLimit-Limit-Hour: 100
X-RateLimit-Remaining-Hour: 85
```

#### Security Headers Middleware
**Purpose:** Web security best practices  
**What it does:**
- Adds security headers to prevent common attacks
- Implements Content Security Policy (CSP)

**Headers added:**
```
X-Content-Type-Options: nosniff          # Prevent MIME sniffing
X-Frame-Options: DENY                    # Prevent clickjacking
X-XSS-Protection: 1; mode=block          # XSS protection
Strict-Transport-Security: max-age=...   # Force HTTPS
Content-Security-Policy: ...             # Script/style restrictions
```

### 2. Router Layer

Routers handle specific API endpoint groups. Each router is a separate module.

#### Auth Router (`routers/auth.py`)

**Endpoints:**
- `POST /api/auth/login` - Authenticate patient
- `POST /api/auth/logout` - Invalidate session

**Login Flow:**
```
1. Receive patient_id
2. Validate format (regex pattern)
3. Check if patient exists (optional - currently accepts any valid format)
4. Generate UUID for session_id
5. Create session in database (MongoDB)
6. Generate JWT token:
   - Payload: {patient_id, session_id, exp}
   - Sign with SECRET_KEY
   - Algorithm: HS256
7. Return token + session info
```

**JWT Token Structure:**
```
eyJhbGc...  ← Header (algorithm: HS256, type: JWT)
eyJwYXR... ← Payload (patient_id, session_id, exp)
4vGJON_... ← Signature (HMAC-SHA256)
```

#### Chat Router (`routers/chat.py`)

**Endpoints:**
- `POST /api/chat/message` - Text message
- `POST /api/chat/message-with-image` - Message + image
- `POST /api/chat/message-with-audio` - Audio message
- `GET /api/chat/history` - Get conversation history
- `DELETE /api/chat/history` - Clear history

**Message Processing Flow:**
```
1. Verify JWT token (authentication)
2. Extract patient_id and session_id from token
3. Validate message content
4. Route to Orchestrator Service:
   ├─ Text only → Direct to LLM
   ├─ With image → Image analysis → LLM
   └─ With audio → Speech-to-text → LLM
5. Receive AI response
6. Save to database:
   - Collections: conversations
   - Fields: {session_id, patient_id, message, response, metadata, created_at}
7. Return response to client
```

#### Upload Router (`routers/upload.py`)

**Endpoints:**
- `POST /api/upload/image` - Upload image file
- `POST /api/upload/audio` - Upload audio file
- `GET /api/upload/limits` - Get size/format limits

**Upload Flow:**
```
1. Verify authentication
2. Validate file:
   ├─ Extension check (.jpg, .png, .wav, etc.)
   ├─ MIME type validation (using python-magic)
   ├─ Size check (10MB for images, 50MB for audio)
   └─ Content validation (magic numbers)
3. Generate unique filename:
   - Format: YYYYMMDD_HHMMSS_uuid.ext
   - Example: 20240115_143025_a1b2c3d4-e5f6.jpg
4. Save asynchronously (aiofiles)
5. Calculate SHA256 hash (integrity)
6. Return file metadata
```

#### Health Router (`routers/health.py`)

**Endpoint:**
- `GET /api/health` - System health check

**Health Check Components:**
```python
{
  "status": "healthy",                    # Overall status
  "version": "1.0.0",                     # API version
  "timestamp": "2024-01-15T10:30:00Z",   # Current time
  "orchestrator_status": "ready",         # AI agent status
  "database_status": "healthy",           # MongoDB status
  "ollama_status": "healthy"              # LLM service status
}
```

**Database check:**
```python
await db.client.admin.command('ping')  # Ping MongoDB
```

**Ollama check:**
```python
response = await httpx.get("http://localhost:11434/api/tags", timeout=5.0)
```

### 3. Service Layer

Services contain business logic separated from routers.

#### Orchestrator Service (`services/orchestrator_service.py`)

**Purpose:** Interface between backend and AI orchestrator  
**Key Features:**
- Session management
- Retry logic for transient errors
- Connection pooling
- Health monitoring

**Class Structure:**
```python
class OrchestratorService:
    def __init__(self):
        self.agent = MedicalChatbotAgent()  # LangGraph agent
        self.sessions = {}                   # Session tracking
        self._http_client = None            # HTTP pool
    
    async def process_message(...):
        # 1. Update session tracking
        # 2. Run in executor (agent is sync)
        # 3. Implement retry logic
        # 4. Return result or error
    
    async def clear_memory(session_id):
        # Clear conversation context
    
    async def cleanup_inactive_sessions():
        # Remove old sessions
```

**Session Management:**
```python
sessions = {
    "session-uuid-123": {
        "patient_id": "Adam631...",
        "created_at": datetime(...),
        "last_activity": datetime(...),
        "message_count": 15
    }
}
```

**Retry Logic:**
```python
try:
    result = await process_message(...)
except (ConnectionError, TimeoutError) as e:
    if retry_count < 2:
        await asyncio.sleep(1)  # Brief delay
        return await process_message(..., retry_count + 1)
    else:
        return error_response
```

#### File Service (`services/file_service.py`)

**Purpose:** Handle file upload, validation, cleanup  
**Key Features:**
- Async file I/O (aiofiles)
- MIME type detection (python-magic)
- SHA256 integrity hashing
- Automatic cleanup scheduler

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
    
    # 5. Generate filename
    filename = f"{timestamp}_{uuid}{ext}"
    
    # 6. Save asynchronously
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)
    
    # 7. Calculate hash
    file_hash = hashlib.sha256(content).hexdigest()
    
    return file_path
```

**Cleanup Scheduler:**
```python
async def cleanup_old_files(upload_dir, days_old=7):
    cutoff = datetime.now() - timedelta(days=days_old)
    for file in upload_dir.iterdir():
        if file.stat().st_mtime < cutoff:
            file.unlink()  # Delete
```

### 4. Database Layer

#### MongoDB Collections

**1. conversations**
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
- `created_at` (for time-based queries)

**2. sessions**
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

#### Database Operations

**Motor (Async MongoDB Driver):**
```python
# Find operation
cursor = db.conversations.find({"session_id": session_id})
conversations = await cursor.to_list(length=50)

# Insert operation
result = await db.conversations.insert_one(document)
inserted_id = result.inserted_id

# Update operation
await db.sessions.update_one(
    {"session_id": session_id},
    {"$set": {"expires_at": new_time}}
)

# Delete operation
result = await db.sessions.delete_many(
    {"expires_at": {"$lt": cutoff_time}}
)
```

### 5. Background Tasks (Scheduler)

**Purpose:** Automated maintenance operations  
**Location:** `scheduler.py`

**Scheduled Tasks:**

| Task | Frequency | Purpose |
|------|-----------|---------|
| Session cleanup | 30 minutes | Remove inactive sessions |
| File cleanup | 60 minutes | Delete old uploaded files (7+ days) |
| Database cleanup | 120 minutes | Remove expired records |

**Implementation:**
```python
class BackgroundScheduler:
    async def start(self):
        self.tasks = [
            asyncio.create_task(self._run_periodic(
                self._cleanup_sessions, 30  # every 30 min
            )),
            asyncio.create_task(self._run_periodic(
                self._cleanup_files, 60     # every 60 min
            )),
            # ...
        ]
    
    async def _run_periodic(self, func, interval_minutes):
        while self.running:
            await func()
            await asyncio.sleep(interval_minutes * 60)
```

---

## Request Flow

### Complete Request Lifecycle

Let's trace a complete request: "User sends chat message with image"

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
├─ Logging Middleware: Log request, generate ID
├─ Rate Limiter: Check IP limits → Allow (15/20)
└─ Security Headers: (processed on response)

↓

Step 3: Router (chat.py)
├─ Route match: send_message_with_image()
├─ Dependency injection:
│  ├─ get_current_user() → Verify JWT
│  ├─ get_orchestrator_service() → Get service
│  ├─ get_db() → Get database
│  └─ get_settings() → Get config
└─ Extract: message, image, current_user

↓

Step 4: Authentication (auth.py)
├─ Extract token from header
├─ Decode JWT:
│  ├─ Verify signature (HMAC-SHA256)
│  ├─ Check expiration
│  └─ Extract: {patient_id, session_id}
├─ Verify session in database
└─ Return: TokenData(patient_id, session_id)

↓

Step 5: File Service
├─ Validate image file:
│  ├─ Extension: .jpg ✓
│  ├─ Size: 2.5MB < 10MB ✓
│  └─ MIME: image/jpeg ✓
├─ Generate filename: 20240115_143025_uuid.jpg
├─ Save to: uploads/20240115_143025_uuid.jpg
└─ Return: file_path

↓

Step 6: Orchestrator Service
├─ Call: process_message(
│    patient_id="Adam631...",
│    text_input="What is this rash?",
│    image_file_path="uploads/20240115_143025_uuid.jpg",
│    session_id="uuid-123"
│  )
├─ Orchestrator workflow:
│  ├─ Input Router: Detect multimodal input
│  ├─ Image Processing Node:
│  │  ├─ Call: analyze_skin_image(file_path)
│  │  └─ Result: {class: "Fungal_Infections", confidence: 0.587}
│  ├─ Reasoning Node (MedGemma):
│  │  ├─ Build context: image result + user message
│  │  ├─ Call Ollama API → MedGemma LLM
│  │  └─ Generate response
│  └─ Safety Check Node:
│     ├─ Validate response
│     └─ Add disclaimer
└─ Return: {response, metadata}

↓

Step 7: Database Storage
await db.save_conversation(
  session_id="uuid-123",
  patient_id="Adam631...",
  message="What is this rash?",
  response="Based on the image analysis...",
  metadata={
    "input_type": "multimodal",
    "tools_used": ["analyze_skin_image"],
    "image_analysis": {...}
  }
)

↓

Step 8: Middleware Stack (Response Phase)
├─ Security Headers: Add CSP, XSS protection
├─ Rate Limiter: Add rate limit headers
├─ Logging: Log response (200, 3.245s)
└─ CORS: Ensure CORS headers present

↓

Step 9: Client Response
HTTP/1.1 200 OK
Headers:
  Content-Type: application/json
  X-Request-ID: 1771221106.210276
  X-Process-Time: 3.245
  X-RateLimit-Remaining-Minute: 14
Body:
{
  "response": "Based on the image analysis, this appears to be a fungal infection with 58.7% confidence. The affected area shows characteristics consistent with dermatophytosis. However, this is an AI classification and I recommend consulting with a dermatologist for proper diagnosis and treatment. Are you experiencing any itching, redness, or scaling in the area?",
  "session_id": "uuid-123",
  "timestamp": "2024-01-15T14:30:28Z",
  "metadata": {
    "input_type": "multimodal",
    "tools_used": ["analyze_skin_image"],
    "emergency_detected": false,
    "image_analysis": {
      "class_name": "Fungal_Infections",
      "confidence": 0.587,
      "all_probabilities": {...}
    }
  }
}
```

**Timeline:**
```
0.000s: Request received
0.001s: Middleware processing
0.002s: Authentication
0.010s: File validation & save
0.015s: Orchestrator starts
0.500s: Image analysis completes
1.000s: Ollama (LLM) processing
3.200s: Response generated
3.240s: Database save
3.245s: Response sent
```

---

## Data Flow

### Authentication Flow

```
┌────────┐                                             ┌────────┐
│ Client │                                             │ Server │
└───┬────┘                                             └───┬────┘
    │                                                      │
    │  POST /api/auth/login                               │
    │  Body: {patient_id: "Adam631..."}                   │
    ├─────────────────────────────────────────────────────>│
    │                                                      │
    │                                      Validate Format │
    │                                      Generate UUID   │
    │                                      Create Session  │
    │                                      (MongoDB)       │
    │                                      Generate JWT:   │
    │                                        Payload: {    │
    │                                          patient_id  │
    │                                          session_id  │
    │                                          exp         │
    │                                        }             │
    │                                        Sign(HS256)   │
    │                                                      │
    │  200 OK                                              │
    │  {access_token, session_id, expires_in}              │
    │<─────────────────────────────────────────────────────┤
    │                                                      │
    │  Store token in: localStorage/memory                 │
    │                                                      │
    │  POST /api/chat/message                              │
    │  Headers: Authorization: Bearer <token>              │
    ├─────────────────────────────────────────────────────>│
    │                                                      │
    │                                      Decode JWT      │
    │                                      Verify Sig      │
    │                                      Check Exp       │
    │                                      Verify Session  │
    │                                      (MongoDB)       │
    │                                      Process...      │
    │                                                      │
    │  200 OK                                              │
    │  {response, ...}                                     │
    │<─────────────────────────────────────────────────────┤
```

### Chat Message Flow (Detailed)

```
Client                Backend              Orchestrator        External Services
  │                     │                       │                     │
  │  Chat Request       │                       │                     │
  ├────────────────────>│                       │                     │
  │                     │                       │                     │
  │                     │ Verify Auth           │                     │
  │                     ├──────────┐            │                     │
  │                     │          │            │                     │
  │                     │<─────────┘            │                     │
  │                     │                       │                     │
  │                     │ process_message()     │                     │
  │                     ├──────────────────────>│                     │
  │                     │                       │                     │
  │                     │                       │ Input Router        │
  │                     │                       ├────────┐            │
  │                     │                       │        │            │
  │                     │                       │<───────┘            │
  │                     │                       │                     │
  │                     │                       │ (If image)          │
  │                     │                       │ Image Analysis      │
  │                     │                       ├────────────────────>│
  │                     │                       │                     │ Image Tool
  │                     │                       │ Analysis Result     │
  │                     │                       │<────────────────────┤
  │                     │                       │                     │
  │                     │                       │ (If history needed) │
  │                     │                       │ RAG Retrieval       │
  │                     │                       ├────────────────────>│
  │                     │                       │                     │ Patient DB
  │                     │                       │ Medical History     │
  │                     │                       │<────────────────────┤
  │                     │                       │                     │
  │                     │                       │ LLM Call            │
  │                     │                       ├────────────────────>│
  │                     │                       │                     │ Ollama
  │                     │                       │                     │ (MedGemma)
  │                     │                       │ AI Response         │
  │                     │                       │<────────────────────┤
  │                     │                       │                     │
  │                     │                       │ Safety Check        │
  │                     │                       ├────────┐            │
  │                     │                       │        │            │
  │                     │                       │<───────┘            │
  │                     │                       │                     │
  │                     │ {response, metadata}  │                     │
  │                     │<──────────────────────┤                     │
  │                     │                       │                     │
  │                     │ Save to MongoDB       │                     │
  │                     ├──────────┐            │                     │
  │                     │          │            │                     │
  │                     │<─────────┘            │                     │
  │                     │                       │                     │
  │  Response           │                       │                     │
  │<────────────────────┤                       │                     │
```

---

## Security Model

### Defense in Depth (6 Layers)

**Layer 1: Network Security**
- CORS whitelist
- Rate limiting (DDoS protection)
- HTTPS enforcement (production)

**Layer 2: Input Validation**
- Pydantic schemas (automatic validation)
- File type verification (extension + MIME)
- Size limits enforcement
- SQL injection prevention
- XSS pattern filtering

**Layer 3: Authentication & Authorization**
- JWT token-based authentication
- Session validation on each request
- Token expiration (configurable)
- Patient-specific data access

**Layer 4: Content Security**
- Security headers (CSP, XSS protection)
- Path traversal prevention
- File integrity checking (SHA256)

**Layer 5: Business Logic Security**
- Medical disclaimer enforcement
- Emergency detection
- No definitive diagnoses
- Privacy protection (patient data isolation)

**Layer 6: Audit & Monitoring**
- Request logging with IDs
- Error tracking
- Rate limit violations logging

### Authentication Implementation

**JWT Token Generation:**
```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    
    return jwt.encode(
        to_encode,
        SECRET_KEY,          # From .env
        algorithm="HS256"
    )
```

**JWT Token Verification:**
```python
def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        # Check expiration automatically
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

**Why:** Python's default I/O is blocking (CPU waits)  
**Solution:** Use `async/await` for I/O operations

**Example:**
```python
# Slow (blocking)
def save_file(data):
    with open("file.txt", "w") as f:
        f.write(data)  # CPU waits here

# Fast (async)
async def save_file(data):
    async with aiofiles.open("file.txt", "w") as f:
        await f.write(data)  # CPU can handle other requests
```

### 2. Connection Pooling

**MongoDB:**
```python
# Motor automatically pools connections
client = AsyncIOMotorClient(
    "mongodb://localhost:27017",
    maxPoolSize=50  # Up to 50 concurrent connections
)
```

**HTTP (Ollama):**
```python
# Reuse HTTP client (avoid connection overhead)
self._http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0)
)
# Reuse for all requests
```

### 3. Lazy Loading

**Orchestrator:**
```python
# Not initialized at startup
self.agent = None

# Initialized on first use
def _get_agent(self):
    if self.agent is None:
        self.agent = MedicalChatbotAgent()
    return self.agent
```

**Benefits:**
- Faster startup
- Memory saved if not used
- Models loaded only when needed

### 4. Background Tasks

**Scheduler Pattern:**
```python
# Run in background (doesn't block API)
asyncio.create_task(cleanup_old_files())
```

**Benefits:**
- Cleanup doesn't slow down requests
- Maintenance runs automatically
- Resource utilization optimized

### 5. Caching

**Model Caching:**
```python
@lru_cache()
def get_orchestrator_service():
    return OrchestratorService()  # Created once, reused
```

**Session Caching:**
```python
# In-memory session tracking (faster than DB)
self.sessions = {
    "session-id": {...}  # Quick lookup
}
```

### 6. Rate Limiting

**Purpose:** Prevent resource exhaustion  
**Implementation:** Sliding window

**Effect on Performance:**
- Protects against DDoS
- Ensures fair resource distribution
- Prevents single user from consuming all resources

---

## Summary

### Architecture Highlights

1. **Layered Design**: Clear separation of concerns
2. **Async-First**: Non-blocking I/O throughout
3. **Security**: 6-layer defense in depth
4. **Scalability**: Connection pooling, caching, background tasks
5. **Maintainability**: Well-organized, documented code
6. **Production-Ready**: Logging, monitoring, error handling

### Key Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **API Gateway** | Request routing, security | FastAPI + Middleware |
| **Auth System** | Authentication, sessions | JWT + MongoDB |
| **Orchestrator** | AI workflow coordination | LangGraph |
| **File Handler** | Upload, validation, cleanup | aiofiles + python-magic |
| **Database** | Persistence, sessions | MongoDB (Motor) |
| **Background** | Maintenance tasks | asyncio scheduler |

### Request Processing

1. **Receive** (< 1ms): Middleware stack
2. **Authenticate** (< 10ms): JWT verification
3. **Process** (1-5s): AI orchestration
4. **Store** (< 50ms): Database save
5. **Respond** (< 1ms): Middleware stack

**Total:** ~1-5 seconds per request (mostly AI processing)

### Scalability

**Horizontal Scaling:**
- Multiple Uvicorn workers
- Load balancer (Nginx)
- Stateless design (sessions in DB)

**Vertical Scaling:**
- Async I/O (handle 10,000+ concurrent connections)
- Connection pooling
- Background task offloading

---

**This architecture supports production deployment with high availability, security, and performance.**