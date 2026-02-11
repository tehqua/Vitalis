"""LangGraph-compatible tool wrappers for patient database.

This module provides LangChain BaseTool-compatible wrappers around existing
patient database tools, enabling seamless integration with LangGraph agents.
"""

from typing import Optional, Type

from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field

from .patient_lookup import PatientLookupTool as _PatientLookupTool
from .medical_history import MedicalHistoryTool as _MedicalHistoryTool
from .observations import ObservationTool as _ObservationTool


# Input Schemas
class PatientLookupInput(BaseModel):
    """Input schema for patient lookup tool."""

    patient_id: str = Field(
        ...,
        description="Patient UUID to look up in the database"
    )


class MedicalHistoryInput(BaseModel):
    """Input schema for medical history tool."""

    patient_id: str = Field(
        ...,
        description="Patient UUID for medical history retrieval"
    )
    days_back: int = Field(
        365,
        description="Number of days to look back for medical records"
    )


class ObservationInput(BaseModel):
    """Input schema for observation tool."""

    patient_id: str = Field(
        ...,
        description="Patient UUID for observation retrieval"
    )
    observation_type: Optional[str] = Field(
        None,
        description=(
            "Filter by observation type (e.g., 'Blood Pressure', 'Glucose'). "
            "Leave None to retrieve all observation types."
        )
    )
    days_back: int = Field(
        90,
        description="Number of days to look back for observations"
    )
    limit: int = Field(
        50,
        description="Maximum number of observation records to return"
    )


# LangGraph-Compatible Tools
class LangGraphPatientLookupTool(LangChainBaseTool):
    """LangGraph-compatible patient lookup tool.

    Retrieves patient demographics including name, age, gender, race,
    ethnicity, marital status, location, and vital status.
    """

    name: str = "patient_lookup"
    description: str = (
        "Retrieve patient demographics and basic information. "
        "Use this when you need to know patient's name, age, gender, "
        "race, ethnicity, marital status, location, or vital status. "
        "Input: patient_id (UUID string). "
        "Output: Formatted patient demographic information."
    )
    args_schema: Type[BaseModel] = PatientLookupInput

    def _run(self, patient_id: str) -> str:
        """Execute the patient lookup tool.

        Args:
            patient_id: Patient UUID string

        Returns:
            Formatted patient information string
        """
        tool = _PatientLookupTool()
        return tool.execute(patient_id)


class LangGraphMedicalHistoryTool(LangChainBaseTool):
    """LangGraph-compatible medical history tool.

    Retrieves comprehensive patient medical history including active
    conditions, medications, allergies, and recent encounters.
    """

    name: str = "medical_history"
    description: str = (
        "Retrieve comprehensive patient medical history. "
        "Includes active conditions, current medications, known allergies, "
        "and recent medical encounters. Use this to understand patient's "
        "medical background and ongoing treatments. "
        "Input: patient_id (UUID), optional days_back (default 365). "
        "Output: Formatted medical history with conditions, medications, "
        "allergies, and encounters."
    )
    args_schema: Type[BaseModel] = MedicalHistoryInput

    def _run(self, patient_id: str, days_back: int = 365) -> str:
        """Execute the medical history tool.

        Args:
            patient_id: Patient UUID string
            days_back: Number of days to look back (default 365)

        Returns:
            Formatted medical history string
        """
        tool = _MedicalHistoryTool()
        return tool.execute(patient_id, days_back)


class LangGraphObservationTool(LangChainBaseTool):
    """LangGraph-compatible observation tool.

    Retrieves patient vital signs and clinical observations such as
    blood pressure, glucose levels, heart rate, temperature, etc.
    """

    name: str = "observation_lookup"
    description: str = (
        "Retrieve patient vital signs and clinical observations. "
        "Use this to get blood pressure, glucose levels, heart rate, "
        "body temperature, oxygen saturation, and other measurements. "
        "Results are grouped by observation type. "
        "Input: patient_id (UUID), optional observation_type filter, "
        "days_back (default 90), limit (default 50). "
        "Output: Grouped observations by type with dates and values."
    )
    args_schema: Type[BaseModel] = ObservationInput

    def _run(
        self,
        patient_id: str,
        observation_type: Optional[str] = None,
        days_back: int = 90,
        limit: int = 50,
    ) -> str:
        """Execute the observation lookup tool.

        Args:
            patient_id: Patient UUID string
            observation_type: Optional filter for observation type
            days_back: Number of days to look back (default 90)
            limit: Maximum number of records to return (default 50)

        Returns:
            Formatted observations grouped by type
        """
        tool = _ObservationTool()
        return tool.execute(patient_id, observation_type, days_back, limit)
