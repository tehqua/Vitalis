"""Tools package initialization.

Provides both legacy tools and LangGraph-compatible tool wrappers.
Legacy tools use custom BaseTool class with execute() method.
LangGraph tools use langchain_core.tools.BaseTool with _run() method.
"""

import os
from pathlib import Path

# Legacy tools (backward compatibility)
from .speech_to_text import SpeechToTextTool

# LangGraph-compatible tools
from .langgraph_tools import LangGraphSpeechToTextTool


# Auto-detect language model path
_MODULE_DIR = Path(__file__).parent
_LM_PATH = _MODULE_DIR.parent / "model" / "medasr" / "lm_6.kenlm"
_LM_PATH_STR = str(_LM_PATH) if _LM_PATH.exists() else None

# Configuration
_MODEL_ID = "google/medasr"

# Legacy tool instances
speech_to_text_tool = SpeechToTextTool(
    model_id=_MODEL_ID,
    lm_path=_LM_PATH_STR
)

# LangGraph tool instances (ready for agent initialization)
langgraph_speech_to_text = LangGraphSpeechToTextTool(
    model_id=_MODEL_ID,
    lm_path=_LM_PATH_STR
)

# Legacy tool list (for backward compatibility)
ALL_TOOLS = [
    speech_to_text_tool,
]

# LangGraph tool list (for LangGraph agent initialization)
LANGGRAPH_TOOLS = [
    langgraph_speech_to_text,
]

__all__ = [
    # Legacy tools
    "SpeechToTextTool",
    "ALL_TOOLS",
    "speech_to_text_tool",
    # LangGraph tools
    "LangGraphSpeechToTextTool",
    "LANGGRAPH_TOOLS",
    "langgraph_speech_to_text",
]
