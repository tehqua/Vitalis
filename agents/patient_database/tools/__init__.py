"""Tools package initialization.

Provides both legacy tools and LangGraph-compatible tool wrappers.
Legacy tools use custom BaseTool class with execute() method.
LangGraph tools use langchain_core.tools.BaseTool with _run() method.
"""

# Legacy tools (backward compatibility)
from .patient_lookup import PatientLookupTool
from .medical_history import MedicalHistoryTool
from .observations import ObservationTool

# LangGraph-compatible tools
from .langgraph_tools import (
    LangGraphPatientLookupTool,
    LangGraphMedicalHistoryTool,
    LangGraphObservationTool,
)

# Legacy tool instances
patient_lookup_tool = PatientLookupTool()
medical_history_tool = MedicalHistoryTool()
observation_tool = ObservationTool()

# LangGraph tool instances (ready for agent initialization)
langgraph_patient_lookup = LangGraphPatientLookupTool()
langgraph_medical_history = LangGraphMedicalHistoryTool()
langgraph_observation = LangGraphObservationTool()

# Legacy tool list (for backward compatibility)
ALL_TOOLS = [
    patient_lookup_tool,
    medical_history_tool,
    observation_tool,
]

# LangGraph tool list (for LangGraph agent initialization)
LANGGRAPH_TOOLS = [
    langgraph_patient_lookup,
    langgraph_medical_history,
    langgraph_observation,
]

__all__ = [
    # Legacy tools
    "PatientLookupTool",
    "MedicalHistoryTool",
    "ObservationTool",
    "ALL_TOOLS",
    "patient_lookup_tool",
    "medical_history_tool",
    "observation_tool",
    # LangGraph tools
    "LangGraphPatientLookupTool",
    "LangGraphMedicalHistoryTool",
    "LangGraphObservationTool",
    "LANGGRAPH_TOOLS",
    "langgraph_patient_lookup",
    "langgraph_medical_history",
    "langgraph_observation",
]
