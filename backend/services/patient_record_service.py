"""
patient_record_service.py

Service layer that locates the correct FHIR JSON file for a patient
and delegates to FHIRReportBuilder to produce the structured report.
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Allow importing from agents package
sys.path.insert(0, str(Path(__file__).parents[2]))

from agents.patient_database.rag_pipeline.fhir_report_builder import FHIRReportBuilder

MEDICAL_RECORD_DIR = (
    Path(__file__).parents[2] / "agents" / "patient_database" / "medical_record"
)


def _find_fhir_file(patient_id: str) -> Path | None:
    """
    Locate the FHIR JSON bundle file that matches the given patient_id.

    The file naming convention is:
        FirstName###_LastName###_<uuid>.json

    We match by the UUID portion (last segment after '_') first;
    if that fails we try a full case-insensitive match on the filename stem.
    """
    if not MEDICAL_RECORD_DIR.is_dir():
        return None

    # Primary strategy: match UUID (last '_'-separated segment)
    uuid_part = patient_id.split("_")[-1].lower()
    for f in MEDICAL_RECORD_DIR.glob("*.json"):
        if uuid_part in f.name.lower():
            return f

    # Fallback: match entire patient_id (case-insensitive)
    pid_lower = patient_id.lower()
    for f in MEDICAL_RECORD_DIR.glob("*.json"):
        if pid_lower in f.stem.lower():
            return f

    return None


def generate_patient_record(patient_id: str) -> Dict[str, Any]:
    """
    Find the FHIR file for a patient and build the structured report.

    Returns:
        dict with keys:
            patient_name  (str)
            report_text   (str) - full formatted report
            sections      (dict) - per-section text blocks

    Raises:
        FileNotFoundError: if no FHIR file is found for the patient.
        ValueError: if the file cannot be parsed as a FHIR bundle.
    """
    fhir_file = _find_fhir_file(patient_id)
    if not fhir_file:
        raise FileNotFoundError(
            f"No FHIR medical record found for patient: {patient_id}"
        )

    try:
        builder = FHIRReportBuilder(str(fhir_file))
        return builder.build_report()
    except (ValueError, KeyError) as exc:
        raise ValueError(f"Failed to parse FHIR bundle: {exc}") from exc
