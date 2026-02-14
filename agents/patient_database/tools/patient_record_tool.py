# patient_database/tools/patient_record_tool.py

import os
import sys
import logging
from typing import Type, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool as LangChainBaseTool

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from rag_pipeline.patient_rag import retrieve_patient_context


# ============================================================
# Tool Input Schema
# ============================================================

class PatientRecordRetrieverInput(BaseModel):
    patient_id: str = Field(..., description="Unique patient ID")
    query: str = Field(..., description="User question related to their medical record")
    top_k: int = Field(default=3, description="Number of top documents to retrieve")


# ============================================================
# Tool Implementation
# ============================================================

class PatientRecordRetrieverTool(LangChainBaseTool):
    name: str = "patient_record_retriever"
    description: str = (
        "Retrieve patient-specific medical record context. "
        "Use when the user asks about their personal medical history, "
        "lab results, medications, vaccines, diagnoses, or vitals."
    )

    args_schema: Type[BaseModel] = PatientRecordRetrieverInput

    def _run(
        self,
        patient_id: str,
        query: str,
        top_k: int = 3,
    ) -> Dict[str, Any]:

        logger.info(f"[RAG TOOL] patient_id={patient_id}, query={query}")

        if not patient_id or not query:
            return {
                "context": "",
                "sources": [],
                "error": "patient_id and query are required."
            }

        try:
            result = retrieve_patient_context(
                patient_id=patient_id,
                query=query,
                top_k=top_k
            )

            logger.info(f"[RAG TOOL] Retrieved {len(result['sources'])} documents.")

            return result

        except Exception as e:
            logger.error(f"[RAG TOOL ERROR] {str(e)}")

            return {
                "context": "",
                "sources": [],
                "error": str(e)
            }

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented.")
