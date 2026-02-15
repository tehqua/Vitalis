# Medical Chatbot Orchestrator

A LangGraph-based orchestration layer for a medical consultation chatbot system that coordinates between multiple specialized AI agents.

## Overview

This orchestrator manages the workflow for a hospital's AI-powered patient support system, coordinating:

- **Speech-to-Text**: Convert medical audio recordings to text (MedASR)
- **Image Analysis**: Classify skin conditions from photographs (8 categories)
- **Patient Records**: Retrieve medical history via RAG (Retrieval-Augmented Generation)
- **Medical Reasoning**: Generate responses using MedGemma LLM
- **Safety Guardrails**: Ensure safe and compliant medical advice

## Architecture

```
User Input (Text/Speech/Image)
         |
         v
   Input Router
         |
    +---------+---------+
    |         |         |
    v         v         v
Speech    Image     Direct
Processing Analysis  to LLM
    |         |         |
    +---------+---------+
         |
         v
   Reasoning Node (MedGemma)
         |
    +----+----+
    |         |
    v         v
Tool Call  Response
(RAG)      Generation
    |         |
    +----+----+
         |
         v
   Safety Check
         |
         v
  Final Response
```

## Features

### Core Capabilities
- Multi-modal input handling (text, speech, images)
- Contextual tool calling (image analysis, medical records)
- Conversation memory management
- Emergency symptom detection
- Medical disclaimer injection
- Privacy protection

### Safety Features
- Input validation and sanitization
- Emergency detection (chest pain, breathing issues, etc.)
- Response validation (no definitive diagnoses)
- Patient privacy protection
- Medical disclaimer enforcement

## Installation

### Prerequisites

```bash
# Python 3.9+
python --version

# Install dependencies
pip install langgraph langchain-core ollama pydantic
pip install librosa torch transformers  # For speech-to-text
pip install pillow keras tensorflow joblib  # For image analysis
pip install faiss-cpu requests  # For RAG
```

### Ollama Setup

1. Install Ollama: https://ollama.ai/download

2. Pull MedGemma model:
```bash
ollama pull thiagomoraes/medgemma-4b-it:Q4_K_S
```

3. Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### Project Structure

Ensure your project has this structure:

```
medscreening/
├── agents/
│   ├── orchestrator/          # This package
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── prompts.py
│   │   ├── guardrails.py
│   │   ├── config.py
│   │   ├── utils.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_agent.py
│   ├── image_process/         # Image analysis tools
│   │   └── tools/
│   ├── patient_database/      # RAG tools
│   │   └── tools/
│   └── speech_to_text_process/  # Speech-to-text tools
│       └── tools/
```

## Quick Start

### Basic Usage

```python
from agents.orchestrator import MedicalChatbotAgent, OrchestratorConfig

# Initialize agent
config = OrchestratorConfig()
agent = MedicalChatbotAgent(config=config)

# Process a text message
result = agent.process_message(
    patient_id="Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58",
    text_input="I have a headache for 2 days"
)

print(result["response"])
```

### With Image Input

```python
result = agent.process_message(
    patient_id="Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58",
    text_input="What is this rash?",
    image_file_path="/path/to/skin_image.jpg"
)

# Check if image analysis was performed
if result["metadata"]["image_analysis"]:
    print(f"Detected: {result['metadata']['image_analysis']['class_name']}")
```

### With Audio Input

```python
result = agent.process_message(
    patient_id="Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58",
    audio_file_path="/path/to/recording.wav"
)

# Audio is automatically transcribed before processing
```

## Configuration

### Environment Variables

```bash
# Ollama settings
export OLLAMA_BASE_URL="http://localhost:11434"
export MEDGEMMA_MODEL="thiagomoraes/medgemma-4b-it:Q4_K_S"

# Patient database
export PATIENT_DB_DIR="/path/to/vectordb"
```

### Python Configuration

```python
config = OrchestratorConfig(
    # LLM settings
    model_name="thiagomoraes/medgemma-4b-it:Q4_K_S",
    model_temperature=0.3,
    model_max_tokens=1024,
    
    # Safety settings
    enable_guardrails=True,
    enable_emergency_detection=True,
    require_medical_disclaimer=True,
    
    # RAG settings
    rag_top_k=3,
    
    # Session settings
    max_conversation_length=50,
)

agent = MedicalChatbotAgent(config=config)
```

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest agents/orchestrator/tests/test_agent.py -v

# Run specific test class
pytest agents/orchestrator/tests/test_agent.py::TestGuardrails -v

# Run with coverage
pytest agents/orchestrator/tests/test_agent.py --cov=agents.orchestrator
```

### Manual Testing

```python
# Navigate to orchestrator directory
cd agents/orchestrator

# Run manual test
python -c "from tests.test_agent import run_manual_test; run_manual_test()"
```

### Interactive Testing (Jupyter Notebook)

Create a notebook `test_orchestrator.ipynb`:

```python
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path.cwd().parent.parent))

from agents.orchestrator import MedicalChatbotAgent

# Initialize agent
agent = MedicalChatbotAgent()

# Test patient ID
patient_id = "Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58"

# Test 1: Simple greeting
result = agent.process_message(patient_id, "Hello")
print(result["response"])

# Test 2: Medical question
result = agent.process_message(patient_id, "I have a fever")
print(result["response"])

# Test 3: Request medical history
result = agent.process_message(patient_id, "What medications am I taking?")
print(result["response"])
print("RAG used:", result["metadata"]["rag_retrieved"])

# Test 4: Emergency detection
result = agent.process_message(patient_id, "I have severe chest pain")
print(result["response"])
print("Emergency:", result["metadata"]["emergency_detected"])
```

## Example Workflows

### Scenario 1: Patient asks about skin rash with image

```python
result = agent.process_message(
    patient_id="Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58",
    text_input="I have this rash on my arm, what could it be?",
    image_file_path="path/to/rash_photo.jpg"
)

# Workflow:
# 1. Input Router: Detects multimodal input (text + image)
# 2. Image Processing: Analyzes image -> "Fungal_Infections (58.7%)"
# 3. Reasoning: LLM considers image result + user question
# 4. Tool Call: May retrieve patient history for allergies/past infections
# 5. Reasoning: Generates response with context
# 6. Safety Check: Adds disclaimer, validates response
# 7. Output: "Based on the image analysis, this may indicate a fungal 
#            infection. Have you experienced itching? I recommend..."
```

### Scenario 2: Patient asks about medical history via voice

```python
result = agent.process_message(
    patient_id="Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58",
    audio_file_path="path/to/voice_question.wav"
)

# Workflow:
# 1. Input Router: Detects speech input
# 2. Speech Processing: Transcribes audio -> "What was my blood pressure in 2010?"
# 3. Reasoning: Detects need for patient records
# 4. Tool Call: RAG retrieval with query "blood pressure 2010"
# 5. Reasoning: Generates response using retrieved context
# 6. Safety Check: Validates and adds disclaimer
# 7. Output: "According to your records, on January 15, 2010, 
#            your blood pressure was 110.97/73.27 mmHg..."
```

### Scenario 3: Emergency detection

```python
result = agent.process_message(
    patient_id="Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58",
    text_input="I have crushing chest pain and can't breathe"
)

# Workflow:
# 1. Input Router: Routes to reasoning
# 2. Reasoning: Emergency detected immediately
# 3. Safety Check: Validates emergency response
# 4. Output: "URGENT: Based on your description, this may be a 
#            medical emergency. Call 911 immediately..."
```

## API Reference

### MedicalChatbotAgent

#### Methods

**`__init__(config, image_analyzer_tool, patient_record_tool, speech_to_text_tool)`**
- Initialize the agent with configuration and tools
- Tools are auto-loaded if not provided

**`process_message(patient_id, text_input, audio_file_path, image_file_path, session_id)`**
- Process a user message through the workflow
- Returns dict with response and metadata

**`clear_memory()`**
- Clear conversation history

**`get_conversation_history()`**
- Retrieve conversation history

**`export_graph_diagram(output_path)`**
- Export workflow graph as image

### OrchestratorConfig

Configuration dataclass with settings:

```python
@dataclass
class OrchestratorConfig:
    model_name: str = "thiagomoraes/medgemma-4b-it:Q4_K_S"
    model_temperature: float = 0.3
    model_max_tokens: int = 1024
    ollama_base_url: str = "http://localhost:11434"
    enable_guardrails: bool = True
    enable_emergency_detection: bool = True
    require_medical_disclaimer: bool = True
    rag_top_k: int = 3
    max_conversation_length: int = 50
```

## Troubleshooting

### Common Issues

**1. "Failed to import image analyzer"**
```bash
# Ensure tools are properly installed
cd agents/image_process
python -c "from tools import langgraph_image_analyzer; print('OK')"
```

**2. "Ollama connection refused"**
```bash
# Start Ollama service
ollama serve

# Or check if running
curl http://localhost:11434/api/tags
```

**3. "Patient ID not found"**
```bash
# Verify patient exists in vector database
ls agents/patient_database/data/vectordb/
# Should see: <patient_id>.index and <patient_id>.pkl
```

**4. "Audio transcription failed"**
```bash
# Check audio file format
file path/to/audio.wav
# Should be: WAV audio, 16kHz recommended

# Test speech-to-text tool directly
from agents.speech_to_text_process.tools import langgraph_speech_to_text
result = langgraph_speech_to_text._run(audio_path="test.wav")
```

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

agent = MedicalChatbotAgent()
```

## Performance Considerations

### Memory Usage
- Agent loads models lazily (on first use)
- Conversation memory limited to 50 messages by default
- Consider clearing memory for long-running sessions

### Response Time
- First request slower (model loading)
- Subsequent requests: ~1-5 seconds depending on complexity
- Image analysis: +2-3 seconds
- RAG retrieval: +1-2 seconds

### Optimization Tips
```python
# Pre-load models at startup
agent = MedicalChatbotAgent()
# Trigger model loading
agent.process_message(patient_id="test", text_input="init")
agent.clear_memory()

# Use smaller conversation history for faster context
config = OrchestratorConfig(max_conversation_length=20)
```

## Security Considerations

### Patient Privacy
- Only returns data for authenticated patient_id
- No cross-patient information leakage
- Input validation prevents injection attacks

### Medical Safety
- Never provides definitive diagnoses
- Emergency detection for critical symptoms
- Mandatory medical disclaimers
- Prohibited phrases blocking

### Compliance
- Follows medical guidance protocols
- No medication recommendations without history
- Clear professional consultation recommendations
