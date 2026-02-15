# Orchestrator Deployment Guide

Complete step-by-step guide for deploying the Medical Chatbot Orchestrator.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.9 or higher installed
- [ ] Git installed
- [ ] Ollama installed and running
- [ ] At least 8GB RAM available
- [ ] 20GB free disk space

## Step-by-Step Deployment

### Step 1: Project Setup

```bash
# Navigate to your project directory
cd C:\Users\lammi\Downloads\medscreening

# Create orchestrator directory
mkdir agents\orchestrator
cd agents\orchestrator
```

### Step 2: Copy Orchestrator Files

Copy all files from the generated orchestrator package:

```
orchestrator/
├── __init__.py
├── agent.py
├── state.py
├── nodes.py
├── prompts.py
├── guardrails.py
├── config.py
├── utils.py
├── README.md
├── test_orchestrator.ipynb
└── tests/
    ├── __init__.py
    └── test_agent.py
```

### Step 3: Install Dependencies

```bash
# Create/activate virtual environment (if not already)
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install base dependencies
pip install langgraph langchain-core ollama pydantic

# Install optional dependencies for testing
pip install pytest pytest-cov jupyter
```

### Step 4: Verify Tool Installations

```bash
# Test image analysis tool
python -c "from agents.image_process.tools import langgraph_image_analyzer; print('Image tool OK')"

# Test speech-to-text tool
python -c "from agents.speech_to_text_process.tools import langgraph_speech_to_text; print('Speech tool OK')"

# Test patient record tool
python -c "from agents.patient_database.tools.patient_record_tool import PatientRecordRetrieverTool; print('RAG tool OK')"
```

Expected output:
```
Image tool OK
Speech tool OK
RAG tool OK
```

If any fail, verify that those modules are properly installed.

### Step 5: Ollama Setup

```bash
# Install Ollama (if not already)
# Windows: Download from https://ollama.ai/download
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve  # Keep this running in a separate terminal

# In another terminal, pull MedGemma model
ollama pull thiagomoraes/medgemma-4b-it:Q4_K_S

# Verify model is available
ollama list
```

Expected output should show:
```
NAME                                    ID              SIZE      MODIFIED
thiagomoraes/medgemma-4b-it:Q4_K_S     abc123def456    2.4 GB    X minutes ago
```

### Step 6: Test Ollama Connection

```bash
# Test Ollama API
curl http://localhost:11434/api/tags

# Test with Python
python -c "from ollama import chat; print(chat(model='thiagomoraes/medgemma-4b-it:Q4_K_S', messages=[{'role':'user','content':'Hello'}]).message.content)"
```

### Step 7: Verify Patient Database

```bash
# Check vector database exists
cd agents\patient_database\data\vectordb
dir  # Windows
# ls  # Linux/Mac

# You should see .index and .pkl files for each patient
```

If files are missing, you need to generate them first using the RAG pipeline.

### Step 8: Run Unit Tests

```bash
# From project root
cd agents\orchestrator

# Run all tests
python -m pytest tests/test_agent.py -v

# Run specific test
python -m pytest tests/test_agent.py::TestGuardrails -v

# Run with coverage
python -m pytest tests/test_agent.py --cov=. --cov-report=html
```

Expected output:
```
tests/test_agent.py::TestGuardrails::test_emergency_detection_chest_pain PASSED
tests/test_agent.py::TestGuardrails::test_emergency_detection_normal PASSED
tests/test_agent.py::TestGuardrails::test_validate_response_prohibited_phrase PASSED
...
==================== X passed in Y.YYs ====================
```

### Step 9: Run Manual Integration Test

```bash
# From orchestrator directory
python -c "from tests.test_agent import run_manual_test; run_manual_test()"
```

This will run through several test scenarios and display results.

### Step 10: Interactive Testing with Jupyter

```bash
# Start Jupyter
jupyter notebook test_orchestrator.ipynb
```

Run through all cells to verify:
- Agent initialization
- Text processing
- Image analysis (if image available)
- Speech processing (if audio available)
- RAG retrieval
- Emergency detection
- Multi-turn conversations

## Configuration

### Environment Variables (Optional)

Create a `.env` file in the orchestrator directory:

```env
# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
MEDGEMMA_MODEL=thiagomoraes/medgemma-4b-it:Q4_K_S

# Patient database
PATIENT_DB_DIR=../patient_database/data/vectordb

# Logging
LOG_LEVEL=INFO
```

Load in Python:
```python
from dotenv import load_dotenv
load_dotenv()

config = OrchestratorConfig.from_env()
```

### Custom Configuration

```python
from agents.orchestrator import OrchestratorConfig

config = OrchestratorConfig(
    # Adjust these based on your needs
    model_temperature=0.3,  # Lower = more deterministic
    rag_top_k=5,  # Retrieve more context
    max_conversation_length=100,  # Longer memory
    enable_emergency_detection=True,
)
```

## Usage Examples

### Basic Usage

```python
from agents.orchestrator import MedicalChatbotAgent

# Initialize once (reuse for multiple requests)
agent = MedicalChatbotAgent()

# Process message
result = agent.process_message(
    patient_id="Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58",
    text_input="I have a headache"
)

print(result["response"])
```

### With Session Management

```python
import uuid

# Create session for a conversation
session_id = str(uuid.uuid4())
patient_id = "Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58"

# Multiple messages in same session
result1 = agent.process_message(patient_id, "Hello", session_id=session_id)
result2 = agent.process_message(patient_id, "I have a fever", session_id=session_id)
result3 = agent.process_message(patient_id, "How long should I rest?", session_id=session_id)

# Conversation context is maintained
```

### With File Uploads

```python
# Image analysis
result = agent.process_message(
    patient_id=patient_id,
    text_input="What is this?",
    image_file_path="C:/path/to/skin_image.jpg"
)

# Speech input
result = agent.process_message(
    patient_id=patient_id,
    audio_file_path="C:/path/to/recording.wav"
)
```

## Integration with Backend

### FastAPI Example

Create `api/main.py`:

```python
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from agents.orchestrator import MedicalChatbotAgent
import shutil
from pathlib import Path

app = FastAPI()
agent = MedicalChatbotAgent()

class ChatRequest(BaseModel):
    patient_id: str
    message: str
    session_id: str = None

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = agent.process_message(
            patient_id=request.patient_id,
            text_input=request.message,
            session_id=request.session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/with-image")
async def chat_with_image(
    patient_id: str = Form(...),
    message: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        # Save uploaded image temporarily
        temp_path = Path(f"temp/{image.filename}")
        temp_path.parent.mkdir(exist_ok=True)
        
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Process with image
        result = agent.process_message(
            patient_id=patient_id,
            text_input=message,
            image_file_path=str(temp_path)
        )
        
        # Clean up
        temp_path.unlink()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run server:
```bash
pip install fastapi uvicorn python-multipart
python api/main.py
```

Test API:
```bash
# Text message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58","message":"Hello"}'

# With image
curl -X POST http://localhost:8000/chat/with-image \
  -F "patient_id=Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58" \
  -F "message=What is this rash?" \
  -F "image=@path/to/image.jpg"
```

## Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
# Ensure you're in project root
cd C:\Users\lammi\Downloads\medscreening

# Verify PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"

# Add project root to path manually if needed
set PYTHONPATH=%CD%  # Windows
# export PYTHONPATH=$(pwd)  # Linux/Mac
```

### Issue: Ollama connection failed

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Check firewall settings (Windows)
# Ensure port 11434 is not blocked
```

### Issue: Patient not found in database

**Solution:**
```bash
# List available patients
dir agents\patient_database\data\vectordb  # Windows
# ls agents/patient_database/data/vectordb  # Linux

# Use exact patient ID from filename
# Format: FirstName###_LastName###_uuid.index
```

### Issue: Image analysis fails

**Solution:**
```bash
# Verify models exist
dir agents\image_process\data\outputs\models

# Should see:
# - logreg_derm.pkl
# - models--google--derm-foundation/

# If missing, run the model training notebooks first
```

### Issue: Speech transcription fails

**Solution:**
```bash
# Check audio format
# Supported: .wav, .mp3, .m4a, .ogg
# Recommended: .wav, 16kHz

# Convert if needed using ffmpeg
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

## Performance Optimization

### Model Caching

```python
# Pre-load models at startup
agent = MedicalChatbotAgent()

# Warm up with dummy request
agent.process_message(
    patient_id="test",
    text_input="init"
)
agent.clear_memory()

# Now ready for real requests
```

### Async Processing

For high-throughput scenarios:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def process_async(patient_id, message):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        agent.process_message,
        patient_id,
        message
    )
    return result

# Usage
result = await process_async(patient_id, "Hello")
```

## Monitoring and Logging

### Enable Detailed Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)

agent = MedicalChatbotAgent()
```

### Track Metrics

```python
import time
from collections import defaultdict

metrics = defaultdict(list)

def track_request(patient_id, text_input):
    start = time.time()
    
    result = agent.process_message(patient_id, text_input)
    
    elapsed = time.time() - start
    metrics['response_times'].append(elapsed)
    metrics['tools_used'].append(len(result['metadata']['tools_used']))
    
    return result

# Analyze metrics
print(f"Avg response time: {sum(metrics['response_times']) / len(metrics['response_times']):.2f}s")
print(f"Avg tools per request: {sum(metrics['tools_used']) / len(metrics['tools_used']):.1f}")
```

## Security Checklist

Before production deployment:

- [ ] Enable HTTPS (TLS/SSL certificates)
- [ ] Implement proper authentication
- [ ] Add rate limiting
- [ ] Sanitize all inputs
- [ ] Encrypt sensitive data at rest
- [ ] Enable audit logging
- [ ] Review and test all guardrails
- [ ] Conduct security penetration testing

## Next Steps

1. **Frontend Integration**: Build React/Vue UI
2. **Database**: Store conversation history in PostgreSQL/MongoDB
3. **Authentication**: Implement JWT-based auth
4. **Deployment**: Deploy to cloud (AWS/Azure/GCP)
5. **Monitoring**: Set up Prometheus/Grafana
6. **Scaling**: Implement load balancing

## Support

If you encounter issues:

1. Check this deployment guide
2. Review README.md
3. Run unit tests to isolate the problem
4. Check logs for detailed error messages
5. Verify all dependencies are installed correctly

For production deployment assistance, consult with DevOps team.