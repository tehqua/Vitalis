# Patient Database Module

PostgreSQL-based patient database module with agent tools for efficient medical record retrieval.

## Features

- 16-table PostgreSQL database schema for comprehensive patient data
- SQLAlchemy ORM models with proper relationships and indexes
- Service layer for business logic
- Agent tools for LLM-friendly data retrieval
- Batch CSV-to-PostgreSQL migration
- PEP8 compliant codebase

## Project Structure

```
patient_database/
├── database/              # Database layer
│   ├── config.py          # Database configuration
│   ├── session.py         # Session management
│   ├── models.py          # SQLAlchemy ORM models
│   └── __init__.py
├── services/              # Business logic layer
│   ├── patient_service.py
│   ├── medical_history_service.py
│   └── __init__.py
├── tools/                 # Agent tools
│   ├── base.py
│   ├── patient_lookup.py
│   ├── medical_history.py
│   ├── observations.py
│   └── __init__.py
├── scripts/               # Utility scripts
│   └── migrate_csv_to_postgres.py
├── data/csv/              # CSV data files
└── loaders/               # Legacy TigerGraph loaders (reference only)
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd C:\Users\lammi\Downloads\medscreening\agents\patient_database
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the example:

```bash
copy .env.example .env
```

Edit `.env` and set your PostgreSQL connection string:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/medscreening
```

### 3. Create PostgreSQL Database

```sql
CREATE DATABASE medscreening;
```

### 4. Run Migration

```bash
python scripts/migrate_csv_to_postgres.py
```

This will:
- Create all 16 tables with proper indexes
- Migrate 472,396 records from CSV files
- Verify referential integrity

Expected output:
```
INFO - Creating database tables...
INFO - Tables created successfully.
INFO - Migrating organizations...
INFO - Total organizations migrated: 1119
INFO - Migrating patients...
INFO - Total patients migrated: 1171
...
INFO - Migration completed successfully!
```

## Usage

### Using Agent Tools

```python
from tools import patient_lookup_tool, medical_history_tool, observation_tool

patient_id = "some-patient-uuid"

patient_info = patient_lookup_tool.execute(patient_id)
print(patient_info)
```

Output:
```
Patient Information:
Name: Mr. John Doe
Gender: M
Date of Birth: 1980-05-15
Age: 45 years
Race: White
Ethnicity: Non-Hispanic
...
```

### Medical History Retrieval

```python
history = medical_history_tool.execute(patient_id, days_back=365)
print(history)
```

Output:
```
Medical History for John Doe:

ACTIVE CONDITIONS (3):
- Hypertension (since 2020-03-15)
- Type 2 Diabetes (since 2019-06-20)
...
```

### Observations Lookup

```python
obs = observation_tool.execute(
    patient_id, 
    observation_type="Blood Pressure",
    days_back=90
)
print(obs)
```

## Direct Service Layer Usage

For more control, use services directly:

```python
from services import PatientService, MedicalHistoryService

patient = PatientService.get_by_id(patient_id)

results = PatientService.search(
    first_name="John",
    last_name="Doe",
    limit=10
)

active_medications = MedicalHistoryService.get_active_medications(patient_id)

active_conditions = MedicalHistoryService.get_active_conditions(patient_id)

encounters = MedicalHistoryService.get_encounters(
    patient_id,
    days_back=365,
    limit=50
)
```

## Database Schema

The database consists of 16 tables:

**Core Tables:**
- `patients`: Demographics (1,171 patients)
- `encounters`: Patient visits (53,346 records)
- `observations`: Vital signs (299,697 records)
- `medications`: Prescriptions (42,989 records)
- `procedures`: Medical procedures (34,981 records)
- `conditions`: Diagnoses (8,376 records)

**Supporting Tables:**
- `organizations`: Healthcare facilities (1,119)
- `providers`: Healthcare professionals (5,855)
- `payers`: Insurance companies (10)
- `immunizations`: Vaccinations (15,478)
- `allergies`: Allergy records (597)
- `careplans`: Treatment plans (3,483)
- `imaging_studies`: Radiology (855)
- `devices`: Medical devices (78)
- `payer_transitions`: Insurance history (3,801)
- `supplies`: Medical supplies (0 - empty)

## Testing

Run tests:

```bash
pytest tests/ -v
pytest tests/ -v --cov=services
```

## Performance Notes

- Batch size: 1,000 records per database transaction
- Connection pool: 20 connections + 10 overflow
- Indexes on frequently queried fields (patient_id, dates, codes)
- Text truncation in tools for LLM context management (3000 chars max)

## PEP8 Compliance

All code follows PEP8 standards:
- Black formatting (line length 88)
- Type hints on all functions
- Google-style docstrings
- Proper imports organization

## License

Hospital Medical Consultation Platform
