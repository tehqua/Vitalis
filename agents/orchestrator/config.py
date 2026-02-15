"""
Configuration settings for the medical chatbot orchestrator.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrchestratorConfig:
    """Configuration for the medical chatbot orchestrator"""
    
    # LLM settings
    model_name: str = "thiagomoraes/medgemma-4b-it:Q4_K_S"
    model_temperature: float = 0.3
    model_max_tokens: int = 1024
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    
    # Tool paths (auto-detected if None)
    image_analyzer_logreg_path: Optional[str] = None
    image_analyzer_derm_path: Optional[str] = None
    speech_to_text_model_id: str = "google/medasr"
    speech_to_text_lm_path: Optional[str] = None
    
    # RAG settings
    patient_db_vector_dir: str = "../patient_database/data/vectordb"
    rag_top_k: int = 3
    
    # Safety settings
    enable_guardrails: bool = True
    enable_emergency_detection: bool = True
    require_medical_disclaimer: bool = True
    
    # Session settings
    max_conversation_length: int = 50
    session_timeout_minutes: int = 30
    
    # Logging
    enable_logging: bool = True
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Create config from environment variables"""
        import os
        
        return cls(
            model_name=os.getenv("MEDGEMMA_MODEL", cls.model_name),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", cls.ollama_base_url),
            patient_db_vector_dir=os.getenv("PATIENT_DB_DIR", cls.patient_db_vector_dir),
        )