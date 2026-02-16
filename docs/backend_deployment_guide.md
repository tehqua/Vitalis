# Backend Deployment Guide

Complete step-by-step guide for deploying the Medical Chatbot Backend API on Windows.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Server](#running-the-server)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

#### 1. Python 3.9 or Higher

```cmd
# Check Python version
python --version

# If not installed, download from:
# https://www.python.org/downloads/

# IMPORTANT: During installation, check "Add Python to PATH"
```

**Verify installation:**
```cmd
python --version
# Expected: Python 3.9.x or higher

pip --version
# Expected: pip 21.x or higher
```

#### 2. MongoDB Community Server

**Download and Install:**
1. Visit: https://www.mongodb.com/try/download/community
2. Select: Windows, MSI installer
3. Install type: Complete
4. Configuration:
   - Install MongoDB as a Service: ✓ (checked)
   - Service Name: MongoDB Server
   - Data Directory: C:\data\db
   - Log Directory: C:\data\log

**Verify installation:**
```cmd
# Open Services (Win+R → services.msc)
# Find "MongoDB Server" → Status should be "Running"

# Test connection
mongosh
# Should connect to: mongodb://127.0.0.1:27017
```

**If MongoDB is not running:**
```cmd
# Start service
net start MongoDB

# Or start manually
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath="C:\data\db"
```

#### 3. Ollama with MedGemma Model

**Install Ollama:**
1. Download from: https://ollama.ai/download
2. Run installer for Windows
3. Follow installation wizard

**Verify installation:**
```cmd
ollama --version
# Expected: ollama version x.x.x
```

**Pull MedGemma model:**
```cmd
# This will download ~2.4GB
ollama pull thiagomoraes/medgemma-4b-it:Q4_K_S

# Verify
ollama list
# Should show: thiagomoraes/medgemma-4b-it:Q4_K_S
```

**Start Ollama service:**
```cmd
# Open new Command Prompt
ollama serve

# Keep this terminal running
# You should see: "Listening on 127.0.0.1:11434"
```

#### 4. libmagic (for file type detection)

**Windows Installation:**

**Option 1: Using python-magic-bin (Recommended)**
```cmd
# Will be installed with pip later
# No manual installation needed
```

**Option 2: Manual Installation**
1. Download: https://github.com/pidydx/libmagicwin64/releases
2. Extract to: `C:\libmagic\`
3. Add to PATH:
   - Windows Search → "Environment Variables"
   - System Properties → Environment Variables
   - Path → Edit → New
   - Add: `C:\libmagic\bin`
   - Click OK → OK
   - Restart Command Prompt

---

## Installation

### Step 1: Clone or Copy Backend

```cmd
# Navigate to project directory
cd C:\Users\YourUsername\Downloads\medscreening

# Verify backend directory exists
dir backend
# Should see: main.py, config.py, requirements.txt, etc.
```

**If backend doesn't exist:**
- Copy the backend folder from outputs/backend
- Place it in: medscreening/backend

### Step 2: Create Virtual Environment

```cmd
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Your prompt should now show (venv)
```

**Verify activation:**
```cmd
where python
# Should show: C:\...\medscreening\backend\venv\Scripts\python.exe

# NOT: C:\Users\...\AppData\Local\Programs\Python\...
```

**Important:** Always activate venv before running any pip or python commands!

### Step 3: Install Python Dependencies

```cmd
# Ensure venv is activated (you should see (venv) in prompt)

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will install:
# - fastapi, uvicorn (web framework)
# - motor, pymongo (MongoDB)
# - python-jose (JWT authentication)
# - httpx (HTTP client)
# - aiofiles, python-magic-bin (file handling)
# - langgraph, langchain-core (orchestrator)
# - and more...
```

**Verify installation:**
```cmd
pip list

# Should see:
# fastapi        0.109.0
# uvicorn        0.27.0
# motor          3.3.2
# pymongo        4.6.1
# ... and others
```

**If python-magic fails:**
```cmd
# Install the binary version instead
pip uninstall python-magic
pip install python-magic-bin
```

### Step 4: Verify Project Structure

```cmd
# Check file structure
dir

# Should see:
# main.py
# config.py
# database.py
# schemas.py
# auth.py
# middleware.py
# scheduler.py
# validators.py
# routers\
# services\
# requirements.txt
# .env.example
# README.md
```

---

## Configuration

### Step 1: Create Environment File

```cmd
# Copy .env.example to .env
copy .env.example .env

# Edit .env file
notepad .env
```

### Step 2: Configure Environment Variables

Edit `.env` file with the following settings:

```env
# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# CORS Origins (comma-separated)
# Add your frontend URL when ready
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Security - CRITICAL: CHANGE THIS!
SECRET_KEY=your-super-secret-key-must-be-changed-in-production

# MongoDB Configuration
DATABASE_URL=mongodb://localhost:27017
DATABASE_NAME=medical_chatbot

# File Upload Settings
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=10

# Orchestrator Settings
ORCHESTRATOR_MODEL=thiagomoraes/medgemma-4b-it:Q4_K_S
OLLAMA_BASE_URL=http://localhost:11434

# Patient Database Path
# Adjust this path to your actual patient database location
PATIENT_DB_VECTOR_DIR=../agents/patient_database/data/vectordb

# Rate Limiting
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100
```

### Step 3: Generate Secure SECRET_KEY

**IMPORTANT:** Never use the default SECRET_KEY in production!

```cmd
# Generate a secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output: xRz7K9vNmQwP2LtY8jH5fU3bVcX6aE1dS4gW0iO9kM

# Copy the output and paste it in .env:
# SECRET_KEY=xRz7K9vNmQwP2LtY8jH5fU3bVcX6aE1dS4gW0iO9kM
```

### Step 4: Verify Patient Database

```cmd
# Check if patient database exists
dir ..\agents\patient_database\data\vectordb

# Should see .index and .pkl files
# Example: Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58.index
```

**If directory is empty:**
You need to generate the patient database first using the RAG pipeline.

---

## Running the Server

### Step 1: Pre-flight Checks

**Check 1: MongoDB is running**
```cmd
# Open Services (Win+R → services.msc)
# Find "MongoDB Server" → Status = "Running"

# Or test connection
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017').server_info()['version'])"
# Should print MongoDB version
```

**Check 2: Ollama is running**
```cmd
# In separate terminal
ollama serve

# Or test
curl http://localhost:11434/api/tags
# Should return JSON with models list
```

**Check 3: Virtual environment is activated**
```cmd
# Should see (venv) in prompt
# If not:
venv\Scripts\activate
```

### Step 2: Start the Server

**Development mode (with auto-reload):**
```cmd
# From backend directory with venv activated
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO: Starting Medical Chatbot Backend API...
INFO: Database initialized
INFO: Background scheduler started
INFO: Backend ready to accept requests
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO: Started reloader process
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
```

### Step 3: Verify Server is Running

**Open browser and visit:**

1. **Root endpoint:**
   - URL: http://localhost:8000
   - Expected: `{"service":"Medical Chatbot API","version":"1.0.0","status":"running","docs":"/api/docs"}`

2. **Health check:**
   - URL: http://localhost:8000/api/health
   - Expected:
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

3. **API Documentation:**
   - Swagger UI: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc
   - OpenAPI spec: http://localhost:8000/api/openapi.json

---

## Testing

### Method 1: Using Swagger UI (Recommended for beginners)

1. **Open Swagger UI:**
   - URL: http://localhost:8000/api/docs
   - Or if Swagger doesn't load: http://localhost:8000/api/redoc

2. **Test Login:**
   - Expand: `POST /api/auth/login`
   - Click: "Try it out"
   - Request body:
   ```json
   {
     "patient_id": "Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58"
   }
   ```
   - Click: "Execute"
   - Copy the `access_token` from response

3. **Authorize:**
   - Click "Authorize" button (top right, lock icon)
   - In the popup, enter: `Bearer <paste-your-token-here>`
   - Click "Authorize"
   - Click "Close"

4. **Test Chat:**
   - Expand: `POST /api/chat/message`
   - Click: "Try it out"
   - Request body:
   ```json
   {
     "message": "Hello, I have a headache for 2 days"
   }
   ```
   - Click: "Execute"
   - You should receive AI response (may take 5-10 seconds first time)

### Method 2: Using Python Script

Create `test_backend.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_all():
    print("\n" + "="*60)
    print("BACKEND API TEST SUITE")
    print("="*60 + "\n")
    
    # Test 1: Health Check
    print("1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    health = response.json()
    print(f"   Database: {health['database_status']}")
    print(f"   Ollama: {health['ollama_status']}")
    assert response.status_code == 200, "Health check failed"
    print("   ✓ PASSED\n")
    
    # Test 2: Login
    print("2. Login")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"patient_id": "Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58"}
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Session: {data['session_id']}")
    token = data['access_token']
    assert response.status_code == 200, "Login failed"
    print("   ✓ PASSED\n")
    
    # Test 3: Chat
    print("3. Chat Message")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/chat/message",
        headers=headers,
        json={"message": "I have a fever"}
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data['response'][:80]}...")
    print(f"   Emergency: {data['metadata']['emergency_detected']}")
    assert response.status_code == 200, "Chat failed"
    print("   ✓ PASSED\n")
    
    # Test 4: History
    print("4. Conversation History")
    response = requests.get(f"{BASE_URL}/chat/history", headers=headers)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Messages: {data['total_messages']}")
    assert response.status_code == 200, "History failed"
    print("   ✓ PASSED\n")
    
    # Test 5: Upload Limits
    print("5. Upload Limits")
    response = requests.get(f"{BASE_URL}/upload/limits")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Image max: {data['image']['max_size_mb']}MB")
    print(f"   Audio max: {data['audio']['max_size_mb']}MB")
    assert response.status_code == 200, "Upload limits failed"
    print("   ✓ PASSED\n")
    
    print("="*60)
    print("ALL TESTS PASSED!")
    print("="*60)

if __name__ == "__main__":
    try:
        test_all()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend!")
        print("Make sure server is running: python main.py")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
```

**Run test:**
```cmd
python test_backend.py
```

### Method 3: Using cURL

```cmd
# Test health
curl http://localhost:8000/api/health

# Test login
curl -X POST http://localhost:8000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"patient_id\":\"Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58\"}"

# Save token and test chat
set TOKEN=your-token-here
curl -X POST http://localhost:8000/api/chat/message ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Hello\"}"
```

### Method 4: Using Postman

1. Download Postman: https://www.postman.com/downloads/
2. Import API:
   - File → Import
   - Link: `http://localhost:8000/api/openapi.json`
3. Test endpoints in Postman GUI

---

## Troubleshooting

### Issue 1: ModuleNotFoundError

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```cmd
# Make sure venv is activated
venv\Scripts\activate

# Verify Python location
where python
# Should be in venv\Scripts\

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 2: MongoDB Connection Refused

**Symptom:**
```
pymongo.errors.ServerSelectionTimeoutError: connection refused
```

**Solution:**
```cmd
# Check if MongoDB service is running
services.msc
# Find "MongoDB Server" → Right-click → Start

# Or start manually
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath="C:\data\db"

# Test connection
python -c "from pymongo import MongoClient; print(MongoClient().server_info())"
```

### Issue 3: Ollama Connection Failed

**Symptom:**
```
{"ollama_status": "unhealthy"}
```

**Solution:**
```cmd
# Start Ollama in separate terminal
ollama serve

# Verify
curl http://localhost:11434/api/tags

# Check model exists
ollama list
# Should see: thiagomoraes/medgemma-4b-it:Q4_K_S
```

### Issue 4: python-magic Error

**Symptom:**
```
ImportError: failed to find libmagic
```

**Solution:**
```cmd
# Uninstall and install binary version
pip uninstall python-magic
pip install python-magic-bin
```

### Issue 5: Port 8000 Already in Use

**Symptom:**
```
[Errno 10048] error while attempting to bind on address
```

**Solution:**
```cmd
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID_number> /F

# Or change port in .env
PORT=8001
```

### Issue 6: Patient Database Not Found

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: '../agents/patient_database/data/vectordb/...'
```

**Solution:**
```cmd
# Verify patient database path
dir ..\agents\patient_database\data\vectordb

# Update path in .env if needed
PATIENT_DB_VECTOR_DIR=C:\path\to\medscreening\agents\patient_database\data\vectordb
```

### Issue 7: JWT Authentication Error

**Symptom:**
```
JWT error: Not enough segments
```

**Solution:**
In Swagger UI:
1. Ensure you clicked "Authorize" button
2. Format: `Bearer <full-token>` (with "Bearer " prefix and space)
3. Token must be complete (not truncated)

### Issue 8: Swagger UI Blank Page

**Symptom:**
http://localhost:8000/api/docs shows blank white page

**Solutions:**
1. **Try ReDoc instead:** http://localhost:8000/api/redoc
2. **Clear browser cache:** Ctrl+Shift+Delete
3. **Try different browser:** Chrome/Edge/Firefox
4. **Check F12 console** for CSP errors
5. **Use Postman** or Python scripts instead

---

## Production Deployment

### Security Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=False` in .env
- [ ] Configure proper `CORS_ORIGINS` for your frontend domain
- [ ] Use HTTPS (TLS/SSL certificates)
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Review all environment variables
- [ ] Set up MongoDB authentication
- [ ] Regular security updates
- [ ] Set up backup strategy

### Production Server Configuration

**Using Gunicorn (Recommended):**

```cmd
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Calculate workers: (2 * CPU_cores) + 1
# For 4 cores: 9 workers
```

**Create Windows Service (Optional):**

Use NSSM (Non-Sucking Service Manager):
1. Download: https://nssm.cc/download
2. Install as service:
```cmd
nssm install MedicalChatbotAPI
# Path: C:\path\to\venv\Scripts\python.exe
# Startup directory: C:\path\to\backend
# Arguments: -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Using Nginx as Reverse Proxy

**Install Nginx:**
Download from: http://nginx.org/en/download.html

**Configuration:**
Edit `nginx.conf`:
```nginx
http {
    upstream backend {
        server 127.0.0.1:8000;
    }
    
    server {
        listen 80;
        server_name your-domain.com;
        
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        client_max_body_size 50M;
    }
}
```

### Database Backup

**MongoDB Backup:**
```cmd
# Backup database
mongodump --db medical_chatbot --out C:\backups\mongodb\%date%

# Restore database
mongorestore --db medical_chatbot C:\backups\mongodb\20240115\medical_chatbot
```

**Automated Backup Script:**
```cmd
# backup.bat
@echo off
set BACKUP_DIR=C:\backups\mongodb\%date:~-4,4%%date:~-10,2%%date:~-7,2%
mongodump --db medical_chatbot --out %BACKUP_DIR%
echo Backup completed: %BACKUP_DIR%
```

Schedule with Task Scheduler (daily at 2 AM).

### Monitoring

**Health Check Endpoint:**
```
http://your-domain.com/api/health
```

Set up monitoring service to check this endpoint every 5 minutes.

**Log Monitoring:**
- Application logs: Check console output or log files
- MongoDB logs: `C:\data\log\mongod.log`
- Nginx logs: `logs\access.log`, `logs\error.log`

---

## Summary

### Deployment Steps Recap

1. **Install Prerequisites:**
   - Python 3.9+
   - MongoDB
   - Ollama + MedGemma
   - libmagic

2. **Setup Backend:**
   - Create virtual environment
   - Install dependencies
   - Configure .env
   - Verify patient database

3. **Start Services:**
   - MongoDB service
   - Ollama serve
   - Backend server

4. **Test:**
   - Health check
   - Login
   - Chat
   - Upload limits

5. **Production:**
   - Secure configuration
   - Gunicorn/Nginx
   - Monitoring
   - Backup

### Quick Reference Commands

```cmd
# Activate venv
venv\Scripts\activate

# Start MongoDB
net start MongoDB

# Start Ollama
ollama serve

# Run backend (development)
python main.py

# Run backend (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Test
python test_backend.py

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Support Resources

- **README.md** - Complete usage guide
- **ENHANCEMENTS.md** - Feature improvements
- **CHANGELOG.md** - Version history
- **API Docs** - http://localhost:8000/api/docs

### Next Steps

1. Verify all tests pass
2. Configure production environment
3. Deploy backend to server
4. Build frontend application
5. Integrate frontend with backend
6. Production deployment

---

**Deployment complete! Backend is ready for production use.**