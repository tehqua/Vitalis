"""
Medical Chatbot Orchestrator Package

This package provides the LangGraph-based orchestration layer for the medical
chatbot system. It coordinates between different specialized agents:
- Image analysis (skin condition classification)
- Patient record retrieval (RAG)
- Speech-to-text conversion
- Medical reasoning (MedGemma)
"""

from .agent import MedicalChatbotAgent
from .state import AgentState
from .config import OrchestratorConfig

__all__ = [
    "MedicalChatbotAgent",
    "AgentState", 
    "OrchestratorConfig",
]

__version__ = "1.0.0"