"""Observation retrieval tool for agents."""

from typing import Optional

from .base import BaseTool
from services.medical_history_service import MedicalHistoryService
from services.patient_service import PatientService


class ObservationTool(BaseTool):
    """Tool for agents to retrieve vital signs and observations."""

    def __init__(self):
        """Initialize the observation tool."""
        super().__init__(
            name="observation_lookup",
            description="Retrieve patient vital signs and clinical observations"
        )

    def execute(
        self,
        patient_id: str,
        observation_type: Optional[str] = None,
        days_back: int = 90,
        limit: int = 50,
    ) -> str:
        """
        Get patient observations.

        Args:
            patient_id: Patient UUID
            observation_type: Filter by observation type (e.g., 'blood pressure', 'glucose')
            days_back: Number of days to look back (default 90)
            limit: Maximum number of results (default 50)

        Returns:
            Formatted observations for LLM
        """
        try:
            patient = PatientService.get_by_id(patient_id)
            if not patient:
                return f"Patient with ID {patient_id} not found."

            observations = MedicalHistoryService.get_observations(
                patient_id,
                observation_type=observation_type,
                days_back=days_back,
                limit=limit,
            )

            if not observations:
                filter_msg = f" matching '{observation_type}'" if observation_type else ""
                return f"No observations{filter_msg} found for patient in the last {days_back} days."

            grouped = {}
            for obs in observations:
                if obs.description not in grouped:
                    grouped[obs.description] = []
                grouped[obs.description].append(obs)

            result = f"""Observations for {patient.first_name} {patient.last_name}:
(Last {days_back} days, showing {len(observations)} total observations)

"""

            for desc, obs_list in list(grouped.items())[:10]:
                result += f"\n{desc}:\n"
                for obs in obs_list[:5]:
                    value_unit = f"{obs.value} {obs.units}" if obs.units else str(obs.value)
                    result += f"  - {obs.date.strftime('%Y-%m-%d')}: {value_unit}\n"

                if len(obs_list) > 5:
                    result += f"  ... and {len(obs_list) - 5} more\n"

            return self.truncate_text(result, max_length=3000)

        except Exception as e:
            return self.format_error(e)
