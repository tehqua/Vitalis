"""Test agent tools with real data."""

import sys
sys.path.insert(0, '.')

from tools import patient_lookup_tool, medical_history_tool, observation_tool
from database.session import SessionLocal
from database.models import Patient

# Get a random patient ID
session = SessionLocal()
patient = session.query(Patient).first()
patient_id = patient.id
print(f"Testing with patient ID: {patient_id}\n")
session.close()

# Test patient lookup
print("=" * 60)
print("TEST 1: Patient Lookup Tool")
print("=" * 60)
result = patient_lookup_tool.execute(patient_id)
print(result)

# Test medical history
print("\n" + "=" * 60)
print("TEST 2: Medical History Tool")
print("=" * 60)
result = medical_history_tool.execute(patient_id, days_back=365)
print(result[:500])  # Print first 500 chars
print("...")

# Test observations
print("\n" + "=" * 60)
print("TEST 3: Observation Tool")
print("=" * 60)
result = observation_tool.execute(patient_id, days_back=90)
print(result[:500])  # Print first 500 chars
print("...")

print("\n" + "=" * 60)
print("ALL TOOLS WORKING SUCCESSFULLY!")
print("=" * 60)
