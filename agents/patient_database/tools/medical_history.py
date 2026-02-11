"""Medical history retrieval tool for agents."""

from .base import BaseTool
from services.medical_history_service import MedicalHistoryService
from services.patient_service import PatientService


class MedicalHistoryTool(BaseTool):
    """Tool for agents to retrieve comprehensive medical history."""

    def __init__(self):
        """Initialize the medical history tool."""
        super().__init__(
            name="medical_history",
            description="Retrieve patient medical history including conditions, medications, and encounters"
        )

    def execute(self, patient_id: str, days_back: int = 365) -> str:
        """
        Get patient medical history.

        Args:
            patient_id: Patient UUID
            days_back: Number of days to look back (default 365)

        Returns:
            Formatted medical history for LLM
        """
        try:
            patient = PatientService.get_by_id(patient_id)
            if not patient:
                return f"Patient with ID {patient_id} not found."

            active_conditions = MedicalHistoryService.get_active_conditions(patient_id)
            active_medications = MedicalHistoryService.get_active_medications(patient_id)
            recent_encounters = MedicalHistoryService.get_encounters(
                patient_id, days_back=days_back, limit=10
            )
            active_allergies = MedicalHistoryService.get_active_allergies(patient_id)

            result = f"""Medical History for {patient.first_name} {patient.last_name}:

ACTIVE CONDITIONS ({len(active_conditions)}):
"""

            if active_conditions:
                for cond in active_conditions[:10]:
                    result += f"- {cond.description} (since {cond.start.strftime('%Y-%m-%d')})\n"
            else:
                result += "- No active conditions recorded\n"

            result += f"\nACTIVE MEDICATIONS ({len(active_medications)}):\n"

            if active_medications:
                for med in active_medications[:15]:
                    result += f"- {med.description}"
                    if med.reason_description:
                        result += f" (for {med.reason_description})"
                    result += "\n"
            else:
                result += "- No active medications recorded\n"

            result += f"\nALLERGIES ({len(active_allergies)}):\n"

            if active_allergies:
                for allergy in active_allergies:
                    result += f"- {allergy.description}\n"
            else:
                result += "- No known allergies\n"

            result += f"\nRECENT ENCOUNTERS (last {days_back} days, showing {len(recent_encounters)}):\n"

            if recent_encounters:
                for enc in recent_encounters:
                    result += f"- {enc.start.strftime('%Y-%m-%d')}: {enc.description} ({enc.encounter_class})\n"
                    if enc.reason_description:
                        result += f"  Reason: {enc.reason_description}\n"
            else:
                result += f"- No encounters in the last {days_back} days\n"

            return self.truncate_text(result, max_length=3000)

        except Exception as e:
            return self.format_error(e)
