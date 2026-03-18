# 📋 BÁO CÁO PHÂN TÍCH TOÀN DIỆN HỆ THỐNG MEDSCREENING

> **Dự án:** Medscreening - AI Medical Chatbot System  
> **Ngôn ngữ backend:** Python (FastAPI, LangGraph)  
> **Ngôn ngữ frontend:** JavaScript (React + Vite)  
> **Ngày phân tích:** 10/03/2026  
> **Phiên bản:** 1.0.0  

---

## MỤC LỤC

1. [Phần 1 – Backend (FastAPI)](#phần-1--backend-fastapi)
2. [Phần 2 – Orchestrator Agent (LangGraph)](#phần-2--orchestrator-agent-langgraph)
3. [Phần 3 – Image Processing Agent](#phần-3--image-processing-agent)
4. [Phần 4 – Speech-to-Text Agent](#phần-4--speech-to-text-agent)
5. [Phần 5 – Patient Database Agent (RAG)](#phần-5--patient-database-agent-rag)
6. [Phần 6 – Frontend (React/Vite)](#phần-6--frontend-reactvite)
7. [Phân Tích Tổng Thể Hệ Thống](#phân-tích-tổng-thể-hệ-thống)

---

## PHẦN 1 – BACKEND (FastAPI)

### 1.1. Tổng Quan

Backend là tầng API trung gian, là cổng giao tiếp duy nhất giữa Frontend và toàn bộ hệ thống AI. Được xây dựng bằng **FastAPI** với mô hình **async/await**, hỗ trợ đồng thời nhiều request hiệu quả. Database sử dụng **MongoDB** (qua `motor` async driver).

**Cấu trúc thư mục:**
```
backend/
├── main.py          # Application entry point, lifespan management
├── config.py        # Settings (pydantic-settings, lru_cache)
├── auth.py          # JWT auth utilities
├── database.py      # MongoDB async CRUD operations
├── middleware.py    # 4 middleware layers
├── schemas.py       # Pydantic request/response models
├── validators.py    # InputValidator, FileValidator
├── scheduler.py     # Background task scheduler
└── routers/
    ├── auth.py      # /api/auth/login, /logout
    ├── chat.py      # /api/chat/message, /message-with-image, /message-with-audio, /history
    ├── upload.py    # /api/upload/image, /audio
    └── health.py    # /api/health
```

---

### 1.2. Luồng Chạy

#### A. Khởi động ứng dụng (Lifespan)

```
uvicorn main:app
    └── lifespan() [asynccontextmanager]
        ├── init_db()         → Kết nối MongoDB, tạo indexes
        ├── start_scheduler() → Khởi động 3 background tasks
        │     ├── cleanup_sessions (mỗi 30 phút)
        │     ├── cleanup_files   (mỗi 60 phút)
        │     └── cleanup_database(mỗi 120 phút)
        └── [yield] → App sẵn sàng nhận request
```

#### B. Luồng request thông thường

```
Client → [SecurityHeadersMiddleware]
       → [ErrorHandlerMiddleware]
       → [LoggingMiddleware]
       → [RateLimitMiddleware] (20 req/phút, 100 req/giờ per IP)
       → Router
       → get_current_user() [Bearer JWT Dependency]
            ├── verify_token() → Giải mã JWT
            └── db.get_session() → Kiểm tra session còn hiệu lực
       → Handler logic
       → Response
```

#### C. Luồng xác thực (Login)

```
POST /api/auth/login { patient_id }
    ├── validate_patient_id() → Regex: ^[A-Z][a-z]+\d+_[A-Z][a-z]+\d+_[uuid36]$
    ├── db.create_session() → Tạo session MongoDB (TTL: 30 phút)
    └── create_access_token() → JWT HS256 (TTL: 60 phút)
         payload: { patient_id, session_id, exp }
    → LoginResponse { access_token, token_type, session_id, expires_in }
```

#### D. Luồng Chat (POST /api/chat/message)

```
POST /api/chat/message { message, session_id }
    ├── [Middleware stack]
    ├── get_current_user() → TokenData { patient_id, session_id }
    ├── orchestrator.process_message(patient_id, text_input, session_id)
    │       └── [Toàn bộ Orchestrator Agent - Phần 2]
    ├── db.save_conversation() → Lưu Q&A vào MongoDB
    └── ChatResponse { response, session_id, timestamp, metadata }
```

#### E. Luồng Chat với ảnh (POST /api/chat/message-with-image)

```
POST /api/chat/message-with-image [multipart: message?, image]
    ├── save_uploaded_file() → Lưu ảnh vào disk
    ├── orchestrator.process_message(..., image_file_path=...)
    └── db.save_conversation() + ChatResponse (kèm image_path trong metadata)
```

#### F. Luồng Chat với audio (POST /api/chat/message-with-audio)

```
POST /api/chat/message-with-audio [multipart: audio]
    ├── save_uploaded_file() → Lưu audio vào disk
    ├── orchestrator.process_message(..., audio_file_path=...)
    └── db.save_conversation() + ChatResponse
```

---

### 1.3. Cấu Hình

| Tham số | Mặc định | Nguồn |
|---------|----------|-------|
| `HOST` | `0.0.0.0` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `PORT` | `8000` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `DEBUG` | `False` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `SECRET_KEY` | `"your-secret-key..."` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) ⚠️ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `SESSION_EXPIRE_MINUTES` | `30` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `DATABASE_URL` | `mongodb://localhost:27017` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `DATABASE_NAME` | `medical_chatbot` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `UPLOAD_DIR` | `uploads` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `MAX_FILE_SIZE_MB` | `10` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `RATE_LIMIT_PER_MINUTE` | `20` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `RATE_LIMIT_PER_HOUR` | `100` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `CORS_ORIGINS` | `localhost:3000, localhost:5173` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) |

**Middleware Stack (thứ tự áp dụng từ ngoài vào trong):**
1. `CORSMiddleware` – Kiểm soát cross-origin
2. [LoggingMiddleware](file:///c:/Users/lammi/Downloads/medscreening/backend/middleware.py#17-69) – Log mọi request/response
3. [ErrorHandlerMiddleware](file:///c:/Users/lammi/Downloads/medscreening/backend/middleware.py#71-116) – Bắt lỗi ValueError, Exception
4. [SecurityHeadersMiddleware](file:///c:/Users/lammi/Downloads/medscreening/backend/middleware.py#229-260) – Thêm security headers
5. [RateLimitMiddleware](file:///c:/Users/lammi/Downloads/medscreening/backend/middleware.py#118-227) – Rate limiting theo IP (sliding window, in-memory)

---

### 1.4. Ưu Điểm

✅ **Kiến trúc Async hoàn toàn**: FastAPI + Motor async → throughput cao, không blocking  
✅ **Middleware phân lớp rõ ràng**: Mỗi middleware có trách nhiệm độc lập (SRP)  
✅ **Multi-layer security**: JWT + Session validation + Rate limiting + Security headers  
✅ **Validation đa tầng**: Pydantic schemas + [InputValidator](file:///c:/Users/lammi/Downloads/medscreening/backend/validators.py#12-144) + [FileValidator](file:///c:/Users/lammi/Downloads/medscreening/backend/validators.py#146-241) (magic number detection)  
✅ **Background scheduler**: Tự động dọn sessions/files/DB không cần cron job ngoài  
✅ **Settings với `lru_cache`**: Config chỉ load 1 lần, tiết kiệm I/O  
✅ **Swagger UI tích hợp**: `/api/docs` đầy đủ, sẵn sàng cho dev/test  
✅ **Lifespan quản lý vòng đời**: Startup/shutdown sạch sẽ, không rò rỉ tài nguyên  

### 1.5. Nhược Điểm

❌ **Rate limiting in-memory**: Không hoạt động đúng khi scale ngang (multi-process) → cần Redis  
❌ **Session không verify patient tồn tại**: Login chỉ check format patient_id, không check DB bệnh nhân  
❌ **File ID là hash(path)**: Không unique, không thể lookup ngược từ file_id → file_path  
❌ **Delete/GetInfo upload chưa implement**: `501 Not Implemented`, để lại API stub không hoàn thiện  
❌ **SECRET_KEY default không an toàn**: Default value `"your-secret-key..."` nguy hiểm nếu deploy mà không đổi  
❌ **Conversation history lưu 2 chiều nhưng timestamp giống nhau**: User message và AI response cùng timestamp `created_at`  
❌ **Không có refresh token**: JWT hết hạn → logout bắt buộc, UX kém  
❌ **Upload dir không có quota per user**: Người dùng có thể upload không giới hạn số file  

---

## PHẦN 2 – ORCHESTRATOR AGENT (LangGraph)

### 2.1. Tổng Quan

Orchestrator là **trung tâm điều phối thông minh** của toàn hệ thống. Được xây dựng bằng **LangGraph** (StateGraph), đây là framework dựa trên machine được thiết kế để quản lý các quy trình AI phức tạp với trạng thái và luồng có điều kiện. LLM được sử dụng là **MedGemma 4B** chạy local qua **Ollama**.

**Cấu trúc files:**
```
agents/orchestrator/
├── agent.py       # MedicalChatbotAgent: khởi tạo + build graph + process_message
├── nodes.py       # WorkflowNodes: 7 nodes xử lý
├── state.py       # AgentState TypedDict (17 fields)
├── config.py      # OrchestratorConfig dataclass
├── prompts.py     # System prompts + template formatters
├── guardrails.py  # MedicalGuardrails + InputValidator
└── utils.py       # ConversationMemory, helper functions
```

---

### 2.2. Luồng Chạy

#### A. Topo đồ thị LangGraph

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
              │──────────────▶                      END
              │              │
              ▼              ▼
         reasoning ◀──────────
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
 call_tool          safety_check
    │                    │
    └──▶ reasoning       ▼
                        END
```

#### B. Chi tiết từng Node

**Node 1: [input_router](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py#61-126)**
```
INPUT: AgentState { patient_id, user_text_input?, audio_file_path?, image_file_path? }
PROCESS:
  1. determine_input_type() → "text" | "speech" | "image" | "multimodal"
  2. validate_patient_id() → regex check
  3. validate_image_file() / validate_audio_file() nếu có
  4. Set routing_decision:
     - audio_file → "process_speech"
     - image_file only → "process_image"
     - text only → "reasoning"
     - multimodal (audio+image) → "process_speech" trước
OUTPUT: state với routing_decision
```

**Node 2: [process_speech](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py#127-161)**
```
INPUT: state với audio_file_path
PROCESS:
  1. Gọi SpeechToTextTool._run(audio_path)
  2. Lưu kết quả vào state["transcribed_text"]
  3. Nếu còn image → routing "process_image"
  4. Nếu không → routing "reasoning"
OUTPUT: state với transcribed_text
```

**Node 3: [process_image](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py#162-200)**
```
INPUT: state với image_file_path
PROCESS:
  1. Gọi ImageAnalyzerTool._run(image_path)
  2. Parse JSON result → state["image_analysis_result"]
  3. Tool calls completed += ["analyze_skin_image"]
  4. Luôn routing → "reasoning"
OUTPUT: state với image_analysis_result { class_id, class_name, confidence, all_probabilities }
```

**Node 4: [reasoning_node](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py#201-348)** *(Node quan trọng nhất)*
```
INPUT: state với toàn bộ context
PROCESS:
  1. extract_text_from_state() → Gộp user_text + transcribed_text
  2. guardrails.sanitize_input() → Loại bỏ HTML/script
  3. guardrails.detect_emergency() →
     - Nếu khẩn cấp: generate_emergency_response() → routing "safety_check"
  4. Kiểm tra cần RAG:
     Keywords: ["my", "history", "record", "medication", "appointment", ...]
     - Nếu có keyword AND chưa có rag_context → routing "call_tool"
  5. Build messages cho Ollama:
     [system: MASTER_SYSTEM_PROMPT + patient_context]
     [system: image_analysis_context?]
     [system: rag_context?]
     [history: last 5 messages]
     [user: current input]
  6. Gọi ollama.chat(model, messages, {temperature, num_predict})
  7. Lưu response → routing "safety_check"
OUTPUT: state với final_response
```

**Node 5: [call_tool](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py#349-363)**
```
INPUT: state với next_action = "retrieve_patient_records"
PROCESS:
  1. PatientRecordRetrieverTool._run(patient_id, query, top_k)
  2. Lưu result vào state["rag_context"]
  3. routing → "reasoning" (quay lại để generate với context)
OUTPUT: state với rag_context
```

**Node 6: [safety_check](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py#395-440)**
```
INPUT: state với final_response
PROCESS:
  1. guardrails.validate_response() → Kiểm tra prohibited phrases + definitive diagnosis patterns
  2. guardrails.validate_patient_privacy() → Không lộ patient_id người khác
  3. (Disclaimer disable tạm: add_medical_disclaimer bị comment)
  4. clean_response() → Xóa blank lines thừa
OUTPUT: state với final_response đã qua kiểm duyệt, safety_check_passed=True
```

**Node 7: [error_handler](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py#441-454)**
```
INPUT: state với routing_decision = "error"
OUTPUT: Generic error message + routing "end"
```

#### C. Quản lý trạng thái (AgentState)

```python
AgentState = {
    # Định danh
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
    
    # RAG
    "rag_context": Optional[Dict],
    "rag_needed": bool,
    
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
- Lưu in-memory per agent instance
- Mỗi người dùng (patient_id) cần 1 instance riêng
- Truncate: giữ system messages + recent non-system messages
- Chỉ truyền 5 messages gần nhất vào LLM context
```

---

### 2.3. Cấu Hình

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `model_name` | `thiagomoraes/medgemma-4b-it:Q4_K_S` | LLM model qua Ollama |
| `model_temperature` | `0.3` | Độ sáng tạo thấp → phù hợp y tế |
| `model_max_tokens` | `1024` | Giới hạn output token |
| `ollama_base_url` | `http://localhost:11434` | Địa chỉ Ollama server |
| `rag_top_k` | `3` | Số documents RAG trả về |
| `enable_emergency_detection` | `True` | Phát hiện tình huống khẩn cấp |
| `require_medical_disclaimer` | `True` | Thêm disclaimer (hiện đang disabled) |
| `max_conversation_length` | `50` | Số messages tối đa trong bộ nhớ |
| `session_timeout_minutes` | `30` | Timeout session |

**Emergency Keywords được cấu hình cứng:**
- Chest pain, breathing difficulty, severe bleeding
- Loss of consciousness, stroke symptoms (FAST)
- Severe allergic reaction, head trauma
- Poisoning/overdose, seizures
- Suicidal ideation (want to die, kill myself, end my life)

**Prohibited Phrases (output validation):**
- "you definitely have", "you are diagnosed with"
- "i diagnose you", "this is definitely"
- "you need this medication", "stop taking your medication"

---

### 2.4. Ưu Điểm

✅ **LangGraph StateGraph**: Luồng xử lý có cấu trúc rõ ràng, dễ debug và extend  
✅ **Multi-modal từ thiết kế**: Xử lý text/speech/image/multimodal trong 1 pipeline  
✅ **Emergency detection ưu tiên hàng đầu**: Kiểm tra trước khi gọi LLM → response nhanh cho tình huống sống còn  
✅ **Guardrails hai chiều**: Validate cả input (XSS) lẫn output (prohibited phrases, privacy)  
✅ **Lazy loading tools**: Models chỉ load khi cần → startup nhanh  
✅ **Keyword-based RAG trigger**: Đơn giản, hiệu quả, không cần fine-tuning  
✅ **Context-aware**: Kết hợp image analysis + RAG context + conversation history trong 1 LLM call  
✅ **Temperature thấp (0.3)**: Phù hợp y tế, hạn chế hallucination  

### 2.5. Nhược Điểm

❌ **ConversationMemory không per-session**: [MedicalChatbotAgent](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/agent.py#24-346) singleton → tất cả người dùng dùng chung memory (race condition khi concurrent)  
❌ **RAG trigger quá thô (keyword matching)**: Từ "my" trong câu thông thường có thể trigger RAG không cần thiết  
❌ **Medical disclaimer bị comment-out**: `# response = self.guardrails.add_medical_disclaimer(response)` → không có disclaimer trong thực tế  
❌ **Dead code trong nodes.py**: Một block code bị comment và viết lại ngay phía dưới (lines 284-310) → code smell  
❌ **Không có retry logic cho LLM**: Nếu Ollama timeout hoặc crash → không retry, trả lỗi ngay  
❌ **process_message() là synchronous**: `self.graph.invoke()` blocking → không async, bottleneck trong FastAPI async context  
❌ **[_route_from_reasoning](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/agent.py#206-214) không handle "error"**: Nếu reasoning gặp lỗi và set routing="error", đồ thị không có edge đến error_handler từ reasoning  
❌ **LLM config hardcode trong OrchestratorConfig**: Chỉ load từ env 3 params (model_name, ollama_url, patient_db_dir), các tham số khác không thể override qua env  
❌ **`agent_scratchpad` không được dùng**: Field tồn tại trong state nhưng không có giá trị logic nào  

---

## PHẦN 3 – IMAGE PROCESSING AGENT

### 3.1. Tổng Quan

Agent phân tích ảnh sử dụng kiến trúc **hai tầng**:
1. **Derm Foundation** (Google, Keras/TensorFlow): Trích xuất embedding từ ảnh da liễu
2. **Logistic Regression** (scikit-learn): Phân loại dựa trên embedding

Hỗ trợ phân loại **8 nhóm bệnh da:**

| ID | Nhóm bệnh |
|----|-----------|
| 0 | Eczema/Dermatitis (Chàm/Viêm da) |
| 1 | Bacterial Infections (Nhiễm khuẩn) |
| 2 | Fungal Infections (Nhiễm nấm) |
| 3 | Viral Infections (Nhiễm virus) |
| 4 | Infestations (Ký sinh trùng) |
| 5 | Acneiform (Mụn trứng cá) |
| 6 | Vascular/Benign (Mạch máu/Lành tính) |
| 7 | Healthy Skin (Da khỏe mạnh) |

---

### 3.2. Luồng Chạy

```
image_path Received
    │
    ▼
_validate_image_file(image_path)
    ├── os.path.exists() → FileNotFoundError nếu không tồn tại
    └── PIL.Image.open().verify() → ValueError nếu file hỏng
    │
    ▼
_initialize_models()  [Lazy Loading - chỉ chạy lần đầu]
    ├── joblib.load(logreg_path) → Load Logistic Regression .pkl
    └── keras.layers.TFSMLayer(derm_model_path)
        └── keras.Sequential([derm_layer]) → Keras model
    │
    ▼
_encode_image(image_path)
    ├── tf.io.read_file(image_path) → Read raw bytes
    ├── Pack vào tf.train.Example { image/encoded: bytes }
    ├── Serialize → tf.constant([serialized_string])
    ├── derm_layer(inputs=...) → output["embedding"]
    └── .numpy().squeeze() → numpy array (1D embedding vector)
    │
    ▼
embedding.reshape(1, -1)
    │
    ▼
logreg.predict(embedding) → pred_class (int 0-7)
logreg.predict_proba(embedding) → pred_proba (array[8])
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
json.dumps(result) → JSON string trả về Orchestrator
```

**LangGraph Wrapper:**
```
LangGraphImageAnalyzerTool (LangChainBaseTool)
    └── args_schema: ImageAnalysisInput { image_path: str }
    └── _run(image_path) → ImageAnalyzerTool.execute(image_path)
```

---

### 3.3. Cấu Hình

| Tham số | Mô tả |
|---------|-------|
| `logreg_path` | Path đến file `.pkl` Logistic Regression |
| `derm_model_path` | Path đến thư mục Derm Foundation SavedModel |
| Lazy initialization | Models chỉ load khi [_run()](file:///c:/Users/lammi/Downloads/medscreening/agents/image_process/tools/langgraph_tools.py#71-82) được gọi lần đầu |

**Quá trình training (từ notebooks):**
- [1.data_fetching.ipynb](file:///c:/Users/lammi/Downloads/medscreening/agents/image_process/models/1.data_fetching.ipynb) → Thu thập data
- [2.eda.ipynb](file:///c:/Users/lammi/Downloads/medscreening/agents/image_process/models/2.eda.ipynb) → Phân tích khám phá dữ liệu
- [3.data_processing.ipynb](file:///c:/Users/lammi/Downloads/medscreening/agents/image_process/models/3.data_processing.ipynb) → Tiền xử lý
- [4.modeling.ipynb](file:///c:/Users/lammi/Downloads/medscreening/agents/image_process/models/4.modeling.ipynb) → Train Logistic Regression trên Derm Foundation embeddings
- [5.inference.ipynb](file:///c:/Users/lammi/Downloads/medscreening/agents/image_process/models/5.inference.ipynb) → Test inference

---

### 3.4. Ưu Điểm

✅ **Transfer learning hiệu quả**: Derm Foundation là model chuyên biệt y tế → embedding chất lượng cao  
✅ **Kiến trúc nhẹ**: Logistic Regression → inference rất nhanh sau embedding  
✅ **Lazy loading**: Không chiếm RAM khi không dùng  
✅ **Output đầy đủ**: Trả về probability cho tất cả 8 classes, không chỉ top-1  
✅ **Validation ảnh**: Kiểm tra file tồn tại + verify content trước khi xử lý  
✅ **LangChain compatible**: Wrapper chuẩn `BaseTool` → dễ tích hợp  

### 3.5. Nhược Điểm

❌ **TensorFlow dependency nặng**: TF + Keras → load chậm, RAM lớn, xung đột phiên bản tiềm ẩn  
❌ **Không preprocess ảnh**: Derm Foundation nhận raw bytes → không resize/normalize → ảnh quality thấp có thể cho kết quả sai  
❌ **8 classes quá mơ hồ**: "Bacterial/Fungal/Viral Infections" - quá chung chung cho da liễu lâm sàng  
❌ **Không có confidence threshold**: Không cảnh báo khi confidence thấp (ví dụ < 50%) → có thể mislead người dùng  
❌ **Không thread-safe**: [_initialize_models()](file:///c:/Users/lammi/Downloads/medscreening/agents/image_process/tools/image_analyzer.py#57-92) có thể race condition nếu 2 request đồng thời gọi lần đầu  
❌ **Model path hardcode trong OrchestratorConfig**: `image_analyzer_logreg_path = None` → crash khi không config  

---

## PHẦN 4 – SPEECH-TO-TEXT AGENT

### 4.1. Tổng Quan

Agent chuyển giọng nói sang văn bản sử dụng **Google MedASR** (`google/medasr`), một model Automatic Speech Recognition (ASR) được fine-tune đặc biệt cho ngữ cảnh y tế. Kiến trúc là **CTC (Connectionist Temporal Classification)** với hỗ trợ beam search bổ sung qua `pyctcdecode`.

---

### 4.2. Luồng Chạy

```
audio_path Received
    │
    ▼
_validate_audio_file(audio_path)
    ├── os.path.exists() → FileNotFoundError
    └── librosa.load(sr=16000, mono=True) → Kiểm tra có load được không
    │
    ▼
_initialize_pipeline()  [Lazy Loading]
    ├── LasrFeatureExtractor.from_pretrained("google/medasr")
    │     └── _processor_class = "LasrProcessorWithLM"
    ├── [Optional] KenLM Language Model:
    │     ├── AutoTokenizer.from_pretrained("google/medasr")
    │     └── LasrCtcBeamSearchDecoder(tokenizer, lm_path)
    │           ├── Build vocab array từ tokenizer
    │           ├── Token normalization: '▁' → '#', prefix '▁'
    │           └── pyctcdecode.build_ctcdecoder(vocab, kenlm)
    └── transformers.pipeline("automatic-speech-recognition", model, feature_extractor, decoder)
    │
    ▼
pipeline(audio_path, chunk_length_s=20, stride_length_s=2, decoder_kwargs?)
    │ Chunked processing: chia audio thành chunks 20s, overlap 2s
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

**LangGraph Wrapper:**
```python
class LangGraphSpeechToTextTool(LangChainBaseTool):
    name: str = "speech_to_text"
    args_schema: SpeechToTextInput { audio_path: str }
    _run(audio_path) → SpeechToTextTool.execute(audio_path)
```

---

### 4.3. Cấu Hình

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `model_id` | `google/medasr` | HuggingFace model ID |
| `lm_path` | `None` | Path đến KenLM binary (.binary) |
| `chunk_length_s` | `20` | Độ dài mỗi chunk xử lý (giây) |
| `stride_length_s` | `2` | Overlap giữa các chunks (giây) |
| `beam_width` | `8` | Width beam search (khi có LM) |
| Input audio | WAV, 16kHz, mono (khuyến nghị) | Librosa tự resample |

---

### 4.4. Ưu Điểm

✅ **Domain-specific model**: MedASR được fine-tune cho y tế → nhận diện thuật ngữ y tế chính xác hơn  
✅ **Chunked processing**: Xử lý file dài mà không bị OOM  
✅ **KenLM integration**: Language model bổ trợ giúp cải thiện chính tả theo ngữ cảnh  
✅ **Librosa preprocessing**: Tự động resample và mono conversion  
✅ **Lazy loading**: Pipeline chỉ khởi tạo khi cần  

### 4.5. Nhược Điểm

❌ **HuggingFace download on first use**: `from_pretrained()` tải ~GB data lần đầu → latency cao, cần internet  
❌ **Chỉ hỗ trợ tiếng Anh**: `google/medasr` là ASR tiếng Anh → không phù hợp bệnh nhân Việt Nam  
❌ **Không có VAD (Voice Activity Detection)**: Không phân biệt speech/silence → xử lý cả đoạn im lặng dài  
❌ **Không async**: Pipeline blocking → giữ thread trong suốt quá trình transcribe  
❌ **chunk_length_s=20 hằng số**: Không configurable qua API/config → không flexible  
❌ **Không handle noisy audio**: Không có bước noise reduction  

---

## PHẦN 5 – PATIENT DATABASE AGENT (RAG)

### 5.1. Tổng Quan

Agent truy xuất hồ sơ bệnh nhân sử dụng kiến trúc **RAG (Retrieval-Augmented Generation)** với **FAISS** làm vector store. Mỗi bệnh nhân có một FAISS index riêng biệt được pre-built và lưu trên disk. Embedding được tạo real-time bằng **Ollama `nomic-embed-text`**.

**Cấu trúc RAG Pipeline:**
```
agents/patient_database/
├── rag_pipeline/
│   ├── parser.py               # Parse medical records → structured data
│   ├── narrative_transformer.py # Chuyển structured data → text narratives
│   ├── episode_builder.py      # Group medical events thành episodes
│   ├── batch_embed.py          # Batch embedding via Ollama
│   ├── faiss_index.py          # Build/save/load FAISS index
│   ├── patient_rag.py          # Core retrieval function
│   └── pipeline.py             # Orchestrate toàn bộ build pipeline
├── data/vectordb/              # {patient_id}.index + {patient_id}.pkl
└── tools/patient_record_tool.py # LangChain wrapper
```

---

### 5.2. Luồng Chạy

#### A. Build Phase (Offline, chạy một lần)

```
Medical Records (CSV/JSON)
    │
    ▼
parser.py → Parse structured medical data
    │
    ▼
narrative_transformer.py → Transform thành text narratives
    │ Ví dụ: "Patient visited on 2023-01-15 for hypertension..."
    │
    ▼
episode_builder.py → Group thành episodes (visits, medications, labs)
    │
    ▼
batch_embed.py → POST http://localhost:11434/api/embeddings
    │     body: { model: "nomic-embed-text", prompt: text }
    │     → vector float[768?] per document
    │
    ▼
faiss_index.py → 
    ├── faiss.IndexFlatIP (Inner Product = cosine sau normalize)
    ├── faiss.normalize_L2(vectors)
    ├── index.add(vectors)
    ├── faiss.write_index(index, "{patient_id}.index")
    └── pickle.dump(documents, "{patient_id}.pkl")
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
    │     └── pickle.load("{patient_id}.pkl") → documents list
    │
    ├── extract_year(query)
    │     └── Regex tìm năm 4 chữ số → filter docs theo year metadata
    │
    ├── [Optional] Year Filter:
    │     filtered_docs = [doc for doc in documents if doc.metadata.year == year]
    │
    ├── Re-embed filtered docs (!)
    │     embed_query(doc["text"]) → vector per doc (RUNTIME CALL!)
    │
    ├── Build temp FAISS IndexFlatIP từ filtered vectors
    │     faiss.normalize_L2(vectors)
    │     temp_index.add(vectors)
    │
    ├── embed_query(query) → query_vec
    │     faiss.normalize_L2(query_vec)
    │
    ├── temp_index.search(query_vec, top_k) → scores, indices
    │
    └── Return:
        {
            "context": "\n\n".join([docs[i]["text"] for i in indices]),
            "sources": [docs[i] for i in indices]
        }
```

---

### 5.3. Cấu Hình

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| `VECTOR_DB_DIR` | `../data/vectordb` | Thư mục chứa FAISS indexes |
| `OLLAMA_EMBED_URL` | `http://localhost:11434/api/embeddings` | Embedding API |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `top_k` | `3` (default) | Số documents trả về |
| Year filter | Regex [(19|20)\d{2}](file:///c:/Users/lammi/Downloads/medscreening/backend/scheduler.py#58-68) | Lọc theo năm mention trong query |
| Index type | `faiss.IndexFlatIP` | Exact search with inner product |

---

### 5.4. Ưu Điểm

✅ **Per-patient isolation**: Mỗi bệnh nhân 1 FAISS index → bảo mật tuyệt đối, không leakage  
✅ **Offline pre-built index**: Retrieval nhanh, không cần rebuild mỗi lần  
✅ **Structured metadata preservation**: Documents có `metadata.year`, hỗ trợ temporal filtering  
✅ **Narrative transformation**: Medical records được chuyển sang ngôn ngữ tự nhiên → context-rich  
✅ **Hybrid retrieval**: Kết hợp structured filter (year) + semantic search  

### 5.5. Nhược Điểm

~~❌ **RE-EMBED TẤT CẢ DOCS MỖI LẦN RETRIEVAL**: Đây là bug nghiêm trọng nhất hệ thống~~ → ✅ **ĐÃ SỬA** *(11/03/2026)*  
  - Pre-computed vectors được lưu sẵn trong `.pkl` file cùng với documents  
  - Retrieval chỉ cần embed query vector (1 HTTP call), không embed lại toàn bộ docs  
  - FAISS index pre-built được tận dụng đúng cách, loại bỏ overhead O(N) per query  
❌ **Embedding qua HTTP**: `requests.post()` đồng bộ đến Ollama → blocking + network overhead  
❌ **Không handle khi patient không có index**: Exception thô thay vì graceful "no records found"  
❌ **pickle.load không an toàn**: Pickle deserialization có thể bị exploit nếu file bị tamper  
❌ **[_arun](file:///c:/Users/lammi/Downloads/medscreening/agents/patient_database/tools/patient_record_tool.py#82-84) không implement**: `NotImplementedError` → không thể dùng trong async context  

---

## PHẦN 6 – FRONTEND (REACT/VITE)

### 6.1. Tổng Quan

Frontend được xây dựng bằng **React 18 + Vite**, giao tiếp với Backend qua REST API. Là giao diện chat thông minh cho phép bệnh nhân nhắn tin văn bản, tải ảnh da liễu, và gửi tin nhắn thoại.

**Cấu trúc:**
```
frontend/src/
├── App.jsx               # Main app router
├── main.jsx              # React entry point
├── index.css             # Global styles
├── pages/                # Page components
├── components/           # Reusable UI components
│   ├── ChatInterface/
│   ├── MessageBubble/
│   ├── AudioRecorder/
│   └── ImageUploader/
├── hooks/                # Custom React hooks
├── services/             # API service layer
└── .env                  # VITE_API_URL config
```

---

### 6.2. Luồng Chạy (UI Flow)

```
User Opens App
    │
    ▼
Login Page
    ├── Input: patient_id
    ├── POST /api/auth/login
    └── Store: { access_token, session_id } in localStorage/state
    │
    ▼
Chat Interface
    │
    ├── [Text Message]
    │   └── POST /api/chat/message { message, session_id }
    │         Authorization: Bearer {token}
    │
    ├── [Image Upload]
    │   └── POST /api/chat/message-with-image [multipart: message?, image]
    │
    └── [Audio Record]
        ├── MediaRecorder API → Capture microphone
        └── POST /api/chat/message-with-audio [multipart: audio]
    │
    ▼
Display Response
    ├── ChatResponse.response → MessageBubble (AI)
    ├── metadata.emergency_detected → Emergency banner?
    └── metadata.image_analysis → Display analysis result?
```

---

### 6.3. Cấu Hình

| Tham số | File | Mô tả |
|---------|------|-------|
| `VITE_API_URL` | [.env](file:///c:/Users/lammi/Downloads/medscreening/backend/.env) | Backend URL |
| [package.json](file:///c:/Users/lammi/Downloads/medscreening/frontend/package.json) deps | Runtime | react, react-dom, axios |
| [vite.config.js](file:///c:/Users/lammi/Downloads/medscreening/frontend/vite.config.js) | Build | Proxy config, build options |

---

### 6.4. Ưu/Nhược Điểm Frontend

✅ **Vite**: Build tool hiện đại, HMR nhanh trong dev  
✅ **Component-based**: Tổ chức rõ ràng theo tính năng  
✅ **Custom hooks**: Tách business logic khỏi UI  

❌ **Thư mục `src/` ít file**: Frontend có vẻ chưa hoàn thiện (chỉ có 12 items)  
❌ **Token storage**: Nếu lưu JWT trong localStorage → XSS vulnerability  
❌ **Không rõ error handling**: Không đủ thông tin để đánh giá xử lý lỗi từ API  

---

## PHÂN TÍCH TỔNG THỂ HỆ THỐNG

### 7.1. Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MEDSCREENING SYSTEM                         │
│                                                                     │
│  ┌──────────┐     ┌──────────────────────────────────────────────┐  │
│  │          │     │              BACKEND (FastAPI)               │  │
│  │  React   │────▶│  Auth → Rate Limit → Router → Middleware     │  │
│  │ Frontend │     │          │                                   │  │
│  │  (Vite)  │◀────│          ▼                                   │  │
│  └──────────┘     │   OrchestratorService                        │  │
│                   │          │                                   │  │
│                   │          ▼                                   │  │
│                   │  ┌──────────────────────────────────────┐   │  │
│                   │  │     ORCHESTRATOR (LangGraph)          │   │  │
│                   │  │                                       │   │  │
│                   │  │  input_router → process_speech   ┐    │   │  │
│                   │  │               → process_image    │    │   │  │
│                   │  │               → reasoning ────── ┘    │   │  │
│                   │  │                    │                   │   │  │
│                   │  │             call_tool (RAG)            │   │  │
│                   │  │                    │                   │   │  │
│                   │  │             safety_check → END         │   │  │
│                   │  └──────────────────────────────────────┘   │  │
│                   │          │           │           │           │  │
│                   └──────────┼───────────┼───────────┼───────────┘  │
│                              │           │           │              │
│                    ┌─────────▼──┐  ┌─────▼────┐  ┌──▼──────────┐  │
│                    │   STT      │  │  Image   │  │  Patient DB │  │
│                    │  MedASR    │  │  Derm    │  │  FAISS RAG  │  │
│                    │(HuggingFace│  │Foundation│  │  (Ollama    │  │
│                    │  + PyTorch)│  │+ LogReg  │  │  embed)     │  │
│                    └────────────┘  └──────────┘  └─────────────┘  │
│                                                                     │
│                    ┌─────────────┐   ┌───────────────────────────┐  │
│                    │  MongoDB    │   │  Ollama (Local LLM)       │  │
│                    │ (Sessions + │   │  MedGemma 4B Q4_K_S      │  │
│                    │  Chats)     │   │  + nomic-embed-text       │  │
│                    └─────────────┘   └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 7.2. Luồng Dữ Liệu Toàn Hệ Thống

```
[1] Người dùng nhập thông tin → Frontend
[2] Frontend POST /api/auth/login → Backend
[3] Backend tạo JWT + Session (MongoDB) → Frontend nhận token
[4] Người dùng gửi tin nhắn/ảnh/audio → Frontend
[5] Frontend POST /api/chat/message[-with-image|-with-audio] + Bearer token
[6] Backend middleware: Rate limit → Log → Auth verify (JWT + Session DB)
[7] Backend lưu file vào disk (nếu có ảnh/audio)
[8] Backend gọi orchestrator.process_message()
[9] Orchestrator khởi tạo AgentState → invoke LangGraph graph
[10] input_router phân loại input type → routing decision
[11] [Nếu audio] process_speech: MedASR transcribe → transcribed_text
[12] [Nếu image] process_image: Derm Foundation embed → LogReg classify → analysis_result
[13] reasoning_node:
     a. Emergency check → (Nếu có) response ngay
     b. Keyword check → (Nếu cần RAG) call_tool
     c. FAISS search patient index → rag_context
     d. Build Ollama messages: system + context + history + user_input
     e. ollama.chat(MedGemma 4B) → response text
[14] safety_check: Validate output → privacy check → clean
[15] Trả AgentState về OrchestratorService
[16] Backend lưu conversation (MongoDB) + trả ChatResponse về Frontend
[17] Frontend hiển thị response cho người dùng
```

---

### 7.3. Đánh Giá Tổng Thể

#### 🏗 Điểm Mạnh Kiến Trúc

| Điểm Mạnh | Chi Tiết |
|-----------|----------|
| **AI-First Design** | Toàn bộ workflow được thiết kế quanh AI workflow từ đầu |
| **Privacy by Design** | Per-patient FAISS index, token-based auth, privacy guardrails |
| **Medical Safety First** | Emergency detection ưu tiên trước LLM, prohibited phrase validation |
| **Multi-modal** | Text + Image + Audio trong 1 pipeline thống nhất |
| **Local Inference** | Ollama local → Không cần cloud API, không rò rỉ data y tế |

#### ⚠️ Rủi Ro Nghiêm Trọng

| # | Rủi Ro | Mức Độ | Vị Trí |
|---|--------|--------|--------|
| 1 | ~~Re-embed tất cả docs mỗi lần RAG retrieval~~ | ✅ **ĐÃ GIẢI QUYẾT** *(11/03/2026)* | [patient_rag.py](file:///c:/Users/lammi/Downloads/medscreening/agents/patient_database/rag_pipeline/patient_rag.py) |
| 2 | Shared memory giữa tất cả users | 🔴 CRITICAL | `agent.py:ConversationMemory` |
| 3 | [process_message()](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/agent.py#215-316) synchronous trong FastAPI async | 🟠 HIGH | [agent.py](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/agent.py) |
| 4 | SECRET_KEY có default value nguy hiểm | 🟠 HIGH | [config.py](file:///c:/Users/lammi/Downloads/medscreening/backend/config.py) |
| 5 | Rate limiting in-memory → không scale được | 🟠 HIGH | [middleware.py](file:///c:/Users/lammi/Downloads/medscreening/backend/middleware.py) |
| 6 | Patient không verify tồn tại khi login | 🟡 MEDIUM | [routers/auth.py](file:///c:/Users/lammi/Downloads/medscreening/backend/routers/auth.py) |
| 7 | Medical disclaimer bị comment-out | 🟡 MEDIUM | [nodes.py](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py) |
| 8 | Không có retry cho LLM calls | 🟡 MEDIUM | [nodes.py](file:///c:/Users/lammi/Downloads/medscreening/agents/orchestrator/nodes.py) |

---

### 7.4. Đánh Giá Theo Chiều Sâu

#### ✅ Điểm Ưu Việt Kỹ Thuật

1. **LangGraph StateGraph**: Lựa chọn framework xuất sắc cho medical AI orchestration – luồng có điều kiện phức tạp được biểu diễn rõ ràng, có thể visualize và test từng node độc lập

2. **Derm Foundation + LogReg**: Tận dụng transfer learning từ model chuyên ngành → accuracy cao mà training cost thấp. Kiến trúc 2 tầng hợp lý cho bài toán classification với ít data

3. **MedASR**: Lựa chọn model ASR chuyên y tế → hiểu thuật ngữ chuyên ngành tốt hơn Whisper tổng quát

4. **MedGemma 4B local**: Chạy local qua Ollama → hoàn toàn offline, phù hợp cho môi trường bệnh viện có yêu cầu bảo mật cao

5. **FAISS per-patient**: Isolation tuyệt đối giữa các bệnh nhân – không có cơ chế nào có thể truy vấn data chéo

#### ❌ Nợ Kỹ Thuật Cần Giải Quyết Ngay

1. ~~**Critical Bug – RAG Re-embedding** (ưu tiên 1)~~ → ✅ **ĐÃ GIẢI QUYẾT** *(11/03/2026)*:
   ```python
   # ĐÃ SỬA: Load pre-computed vectors từ .pkl — không embed lại documents
   # Chỉ embed query vector (1 HTTP call) rồi search trên FAISS index có sẵn
   # Kết quả: O(1) embedding calls thay vì O(N), tận dụng đúng FAISS pre-built index
   ```

2. **Critical Bug – Shared Memory** (ưu tiên 2):
   ```python
   # HIỆN TẠI (SAI):
   class MedicalChatbotAgent:
       def __init__(self):
           self.memory = ConversationMemory()  # 1 instance cho tất cả users!
   
   # NÊN SỬA:
   # ConversationMemory per session_id trong dict hoặc Redis
   ```

3. **Async Orchestrator** (ưu tiên 3):
   ```python
   # HIỆN TẠI: Blocking
   final_state = self.graph.invoke(initial_state)
   
   # NÊN SỬA:
   final_state = await self.graph.ainvoke(initial_state)
   ```

---

### 7.5. So Sánh Tổng Quan Các Phần

| Thành Phần | Mức Hoàn Thiện | Chất Lượng Code | Sẵn Sàng Production |
|-----------|----------------|-----------------|---------------------|
| Backend (FastAPI) | 85% | ⭐⭐⭐⭐ | 🟡 Cần Redis cho rate limit |
| Orchestrator | 80% | ⭐⭐⭐⭐ | 🟡 Cần fix shared memory + async |
| Image Processing | 75% | ⭐⭐⭐ | 🟡 Cần confidence threshold |
| Speech-to-Text | 70% | ⭐⭐⭐ | 🔴 Chỉ hỗ trợ tiếng Anh |
| Patient DB (RAG) | 75% | ⭐⭐⭐ | 🟡 RAG bug đã fix, cần thêm async + error handling |
| Frontend | 65% | ⭐⭐⭐ | 🟡 Chưa đủ info để đánh giá đầy đủ |

---

### 7.6. Khuyến Nghị Chiến Lược

#### 🚨 Ngắn Hạn (1-2 tuần)

1. ~~**Fix RAG re-embedding bug**~~ → ✅ **ĐÃ HOÀN THÀNH** *(11/03/2026)* – Pre-computed vectors trong `.pkl`, chỉ embed query khi retrieval
2. **Fix shared ConversationMemory** → Dictionary `{session_id: ConversationMemory}` hoặc Redis
3. **Đổi SECRET_KEY** → Bắt buộc từ environment, raise error nếu dùng default
4. **Uncomment medical disclaimer** → Cần thiết về mặt pháp lý y tế
5. **Async orchestrator** → Dùng `graph.ainvoke()` và `asyncio.run_in_executor()` cho blocking tools

#### 🔧 Trung Hạn (1-3 tháng)

6. **Redis cho rate limiting + session** → Scale ngang được
7. **Confidence threshold cho image tool** → Từ chối/cảnh báo khi độ tin cậy thấp
8. **Multilingual STT** → Hỗ trợ tiếng Việt (Whisper hoặc mô hình đa ngôn ngữ)
9. **File ID management** → Database mapping file_id → file_path, implement delete endpoint
10. **Retry + circuit breaker cho LLM** → Resilience khi Ollama load cao

#### 🏥 Dài Hạn (3-12 tháng)

11. **Verify patient existence** → Tích hợp với hệ thống quản lý bệnh viện (HIS)
12. **Audit logging** → Ghi log mọi thao tác liên quan đến data y tế (HIPAA compliance)
13. **Model versioning** → Track phiên bản Logistic Regression, MedGemma được dùng
14. **A/B testing framework** → So sánh các phiên bản model
15. **Streaming response** → WebSocket hoặc SSE thay vì request-response cho UX tốt hơn

---

### 7.7. Kết Luận

Medscreening là một hệ thống AI y tế **có tầm nhìn kiến trúc tốt** với nhiều lựa chọn kỹ thuật đúng đắn: LangGraph cho orchestration, FAISS per-patient cho privacy, MedGemma local cho data security, và MedASR cho ngữ cảnh y tế chuyên ngành.

Bug RAG re-embedding – vấn đề nghiêm trọng nhất ảnh hưởng đến hiệu suất FAISS – **đã được giải quyết** *(11/03/2026)*. Tuy nhiên, hệ thống **chưa sẵn sàng cho production** do vẫn còn các vấn đề cần xử lý, đặc biệt là shared memory ảnh hưởng đến tính đúng đắn của multi-user conversations và orchestrator đang chạy synchronous trong FastAPI async context.

Với các bản sửa lỗi được ưu tiên, đây là nền tảng vững chắc để xây dựng một hệ thống chatbot y tế quy mô thực tế.

---

*Báo cáo được tạo bởi phân tích tĩnh toàn bộ source code. Ngày: 10/03/2026.*  
*Cập nhật lần cuối: 13/03/2026 – Đánh dấu RAG Re-embedding bug đã giải quyết.*
