"""Tools package initialization.

Provides both legacy tools and LangGraph-compatible tool wrappers.
Legacy tools use custom BaseTool class with execute() method.
LangGraph tools use langchain_core.tools.BaseTool with _run() method.
"""

import os
from pathlib import Path

# Legacy tools (backward compatibility)
from .image_analyzer import ImageAnalyzerTool

# LangGraph-compatible tools
from .langgraph_tools import LangGraphImageAnalyzerTool


# Auto-detect model paths
_MODULE_DIR = Path(__file__).parent
_PROJECT_ROOT = _MODULE_DIR.parent.parent.parent

_LOGREG_PATH = (
    _PROJECT_ROOT
    / "agents"
    / "image_process"
    / "data"
    / "outputs"
    / "models"
    / "logreg_derm.pkl"
)

_DERM_MODEL_PATH = (
    _PROJECT_ROOT
    / "agents"
    / "image_process"
    / "data"
    / "outputs"
    / "models"
    / "models--google--derm-foundation"
    / "snapshots"
    / "a16a6ab4f87888948fe248136e697ed28146a1c6"
)

_LOGREG_PATH_STR = str(_LOGREG_PATH) if _LOGREG_PATH.exists() else None
_DERM_MODEL_PATH_STR = str(_DERM_MODEL_PATH) if _DERM_MODEL_PATH.exists() else None

# Legacy tool instances
image_analyzer_tool = ImageAnalyzerTool(
    logreg_path=_LOGREG_PATH_STR,
    derm_model_path=_DERM_MODEL_PATH_STR
)

# LangGraph tool instances (ready for agent initialization)
langgraph_image_analyzer = LangGraphImageAnalyzerTool(
    logreg_path=_LOGREG_PATH_STR,
    derm_model_path=_DERM_MODEL_PATH_STR
)

# Legacy tool list (for backward compatibility)
ALL_TOOLS = [
    image_analyzer_tool,
]

# LangGraph tool list (for LangGraph agent initialization)
LANGGRAPH_TOOLS = [
    langgraph_image_analyzer,
]

__all__ = [
    # Legacy tools
    "ImageAnalyzerTool",
    "ALL_TOOLS",
    "image_analyzer_tool",
    # LangGraph tools
    "LangGraphImageAnalyzerTool",
    "LANGGRAPH_TOOLS",
    "langgraph_image_analyzer",
]
