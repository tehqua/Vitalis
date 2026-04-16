# Project Overview: Vitalis — Agentic AI for Post-Consultation Patient Care

## 🎯 Introduction

**Vitalis** is a full-stack **Agentic AI system** built for hospitals and independent healthcare facilities. The product focuses on **post-consultation patient care** — helping patients stay informed, supported, and connected long after they leave the clinic, while simultaneously reducing the burden on hospital staff.

Vitalis is not a replacement for existing hospital systems. Instead, it integrates directly on top of a hospital's current patient-portal infrastructure: the same login credentials patients already use to view their records are used to activate the Vitalis assistant. After a visit, patients are proactively asked for their consent; only upon agreement does the chatbot activate and begin personalised support.

---

## 🏥 Problems to Solve

### 1. **Underserved Post-Consultation Care**

Despite visible improvements in healthcare quality, the post-consultation patient experience remains severely underserved:

- ~50% of outpatients are unsatisfied with service quality
- 20–30% of discharged patients experience post-discharge complications due to lack of follow-up
- >60% of patients expect digital health tools to be convenient, personalised, and continuously available

### 2. **Medically Ungrounded General-Purpose Chatbots**

Existing chatbots lack medical grounding. General-purpose LLMs (GPT, Claude, etc.) were not trained on clinical data. The WHO notes that medically inaccurate AI advice poses significant patient safety risks.

### 3. **Stateless, Non-Personalised AI**

Current chatbots have no awareness of a patient's individual medical history — reducing trust and clinical relevance. McKinsey identifies personalisation as a key driver of improved treatment outcomes.

### 4. **Healthcare Staff Overload**

- Doctors must repeatedly answer similar questions from patients
- Medical staff spend time explaining basic medical information
- Traditional consultation systems don't leverage existing medical record data

### 5. **Lack of Multimodal Analysis Capability**

- Patients can only describe symptoms verbally but struggle to articulate them accurately
- Images of skin lesions or affected areas require professional analysis
- Lack of tools for preliminary self-examination before hospital visits

---

## 💡 Solution

**Vitalis** addresses these gaps with four core pillars:

### ✅ **Medically-Grounded Knowledge (Dual RAG)**

The system uses **MedGemma** augmented by two complementary RAG layers:

- **Hierarchical Medical Document RAG** (LlamaIndex + `bge-large-en-v1.5`): retrieves context from curated clinical guidelines and medical literature before every text-based query
- **Patient Record RAG** (FAISS + FHIR): retrieves the specific patient's own medical history on demand (with consent), isolated per-patient

This combination delivers responses grounded in both general medical knowledge *and* the patient's personal health context.

### ✅ **Personalised, Consent-Based Assistance**

Unlike stateless chatbots, Vitalis maintains session memory and retrieves individual FHIR medical records per-patient. Activation only occurs after explicit post-visit patient consent.

### ✅ **Medical Image Analysis**

The system is capable of:
- Analysing images of affected skin areas
- Classifying into **8 clinical dermatological groups** using **Google Derm Foundation + XGBoost**
- Providing confidence scores and preliminary assessments

### ✅ **Voice Recognition**

Patients can:
- Ask questions by voice using **Google MedASR** (medical-domain speech-to-text)
- Convenient for elderly users or those with typing difficulties

### ✅ **Admin Panel**

Hospital administrators can:
- View dashboard analytics and FHIR record management
- Manage embedded medical documents and patient support tickets
- Monitor system health and conversation statistics

---

## 🏗️ System Architecture

### **Main Components**

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

### **4 Main Query Types**

#### 1️⃣ **General Medical Questions**
- User asks about symptoms, diseases, prevention
- Processing: Medical Doc RAG (LlamaIndex) → MedGemma reasoning → Safety check
- Example: *"What are the symptoms of diabetes?"*

#### 2️⃣ **Personal Medical History Queries**
- User asks about their own medical history, test results
- Processing: RAG Agent (FAISS/FHIR) → MedGemma → Safety check
- Example: *"What were my last blood test results?"*

#### 3️⃣ **Multimodal Analysis (Text + Image/Audio)**
- User sends images or audio with questions
- Processing: Image/Speech Agent → Analysis → MedGemma synthesis
- Example: *[Sends image of red skin area] "Is this a fungal infection?"*

#### 4️⃣ **Emergency Detection**
- System detects critical keywords and bypasses normal reasoning
- Immediately advises calling emergency services

---

## 👥 Target Users

### **Primary Users: Patients**

- Patients registered at the hospital
- Have a unique **Patient ID** (format: `FirstName###_LastName###_<uuid>`)
- Must provide post-visit consent before chatbot activates
- Have FHIR medical records stored in the hospital system

### **Secondary Users: Administrators**

- Hospital staff managing the system
- Access via Admin Panel (separate authentication)
- Can view analytics, manage FHIR records, and handle support tickets

### **Patient Usage Flow:**

1. **Post-Visit Consent:** Patient is invited to activate the AI assistant
2. **Login:** Enter Patient ID
3. **Ask questions:** Type text, speak, or upload images
4. **Receive consultation:** AI analyses and provides evidence-grounded advice
5. **Look up history:** Query personal medical records (with consent)

---

## 📥 System Input

| Input Type | Description | Example |
|------------|-------------|---------|
| **Text** | Text-based questions | *"I have a headache for 2 days"* |
| **Speech** | Voice questions via MedASR | *[Audio file .wav/.mp3]* |
| **Image** | Images of affected skin areas via Derm Foundation + XGBoost | *[Image file .jpg/.png]* |

---

## 🔐 Security and Privacy

### **Patient Authentication**

- Login using **Patient ID** (pre-assigned)
- Uses **JWT Token** (HS256) to secure sessions
- Each patient can only access their own records
- Chatbot **only activates after explicit post-visit consent**

### **Medical Data Protection**

- Per-patient FAISS isolation — no cross-patient data leakage possible
- Medical record data isolated by Patient ID
- Connection encryption (HTTPS in production)
- Rate limiting to prevent abuse (20 req/min, 100 req/hour)
- Content Security Policy and XSS protection headers

### **Privacy by Design**

- All patient data remains under hospital control
- Vitalis does not store raw medical records externally
- Safety guardrails validate every LLM response for privacy violations

---

## 📊 System Data

### **Hospital Medical Records (FHIR Format)**

The system utilises **over 1,000 detailed medical records** in FHIR (Fast Healthcare Interoperability Resources) format, including:
- Patient demographics
- Clinical encounters
- Laboratory observations
- Medication prescriptions
- Condition diagnoses
- Medical procedures

### **Dual Vector Database**

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Patient Record RAG** | FAISS + nomic-embed-text (Ollama) | Semantic search over per-patient FHIR records |
| **Medical Doc RAG** | LlamaIndex + bge-large-en-v1.5 | Hierarchical index over curated clinical literature |

---

## ✨ Key Features

### 🤖 **Medically-Grounded QA**
MedGemma LLM + Dual RAG (Hierarchical Medical Doc + Patient FHIR) for accurate, evidence-backed responses.

### 🖼️ **Intelligent Image Analysis**
Upload images of affected skin areas. AI classifies into 8 clinical dermatological categories using **Google Derm Foundation** (embedding) + **XGBoost** (classification), with confidence scores for each category.

### 🎤 **Voice Communication**
Ask questions by voice. System uses **Google MedASR** — a medical-domain ASR model — to convert audio to text. Convenient for elderly users.

### 🔍 **Fast Medical History Lookup**
Query previous test results, view medical examination history, check prescribed medications — all grounded in real FHIR records.

### ⚡ **Real-time Response**
Chatbot responds without waiting for doctor appointments. Available 24/7.

### 🚨 **Emergency Detection**
Detects critical symptoms (chest pain, difficulty breathing, unconscious, severe bleeding) and immediately generates emergency-alert responses, bypassing the normal reasoning pipeline.

### 🏥 **Admin Panel**
Dashboard with analytics, FHIR record management, background embedding pipelines, and a patient support ticket system.

---

## 🎓 Important Notes

### ⚠️ **Medical Disclaimer**

> **Vitalis is a consultation support tool, NOT a replacement for real doctors.**

- The system provides reference information
- Always recommends seeing a doctor when necessary
- Does not provide definitive diagnoses
- Detects emergency situations and advises immediate hospital visits

### 🎯 **Deployment Model**

Vitalis is designed to **extend, not replace** existing hospital infrastructure:

1. **Plug-in integration**: Added as a module on top of the hospital's existing patient-portal
2. **Hospital data ownership**: All patient data remains under hospital control
3. **Consent-first activation**: Activates only upon explicit patient agreement
4. **Phased deployment**: Can be rolled out incrementally — one department first
5. **Maintenance by Vitalis team**: Hospitals handle their data; Vitalis handles deployment

---

## 📈 Benefits

### **For Patients**

✅ Easy and fast access to medically-grounded information  
✅ Personalised advice based on individual medical history  
✅ Convenient medical history lookup  
✅ Accessible 24/7 with voice and image input  

### **For Hospitals**

✅ Reduce basic consultation workload for doctors  
✅ Improve post-visit patient care quality  
✅ Leverage existing FHIR medical record data  
✅ Enhance digital healthcare experience  

---

## 🔮 Roadmap

- [ ] Proactive post-visit follow-up notifications (medication reminders, appointment alerts)
- [ ] Integration of additional specialised AI models (cardiology, pulmonology)
- [ ] Multi-language support (Vietnamese, English)
- [ ] Mobile applications (iOS / Android)
- [ ] Live video consultation handoff to doctors
- [ ] Nutrition and exercise guidance
- [ ] Prometheus / Grafana monitoring dashboard
- [ ] Expanded admin panel and hospital analytics

---

**Vitalis** — *Agentic AI for Post-Consultation Patient Care* 🏥💙
