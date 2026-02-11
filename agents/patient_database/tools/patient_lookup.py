"""Patient lookup tool for agents."""

from datetime import datetime
from typing import Optional

from .base import BaseTool
from services.patient_service import PatientService


class PatientLookupTool(BaseTool):
    """Tool for agents to retrieve patient basic information."""

    def __init__(self):
        """Initialize the patient lookup tool."""
        super().__init__(
            name="patient_lookup",
            description="Retrieve patient demographics and basic information by patient ID"
        )

    def execute(self, patient_id: str) -> str:
        """
        Get patient demographics.

        Args:
            patient_id: Patient UUID

        Returns:
            Formatted patient information for LLM
        """
        try:
            patient = PatientService.get_by_id(patient_id)

            if not patient:
                return f"Patient with ID {patient_id} not found."

            age = self._calculate_age(patient.birth_date)
            is_living = patient.death_date is None

            result = f"""Patient Information:
Name: {patient.prefix or ''} {patient.first_name} {patient.last_name} {patient.suffix or ''}
Gender: {patient.gender}
Date of Birth: {patient.birth_date.strftime('%Y-%m-%d')}
Age: {age} years
Race: {patient.race}
Ethnicity: {patient.ethnicity}
Marital Status: {patient.marital_status or 'Unknown'}
City, State: {patient.city}, {patient.state}
"""

            if not is_living:
                result += f"Status: Deceased ({patient.death_date.strftime('%Y-%m-%d')})\n"
            else:
                result += "Status: Living\n"

            return result

        except Exception as e:
            return self.format_error(e)

    def _calculate_age(self, birth_date: datetime) -> int:
        """
        Calculate age from birth date.

        Args:
            birth_date: Date of birth

        Returns:
            Age in years
        """
        today = datetime.now()
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
