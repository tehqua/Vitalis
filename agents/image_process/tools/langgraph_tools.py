"""LangGraph-compatible tool wrappers for image analysis.

This module provides LangChain BaseTool-compatible wrappers around existing
image analyzer tools, enabling seamless integration with LangGraph agents.
"""

from typing import Optional, Type

from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field

from .image_analyzer import ImageAnalyzerTool as _ImageAnalyzerTool


class ImageAnalysisInput(BaseModel):
    """Input schema for image analysis tool."""

    image_path: str = Field(
        ...,
        description="Path to skin image file (JPG, PNG formats supported)"
    )


class LangGraphImageAnalyzerTool(LangChainBaseTool):
    """LangGraph-compatible image analysis tool.

    Analyzes skin images to classify dermatological conditions using
    Google's Derm Foundation model combined with a trained Logistic
    Regression classifier. Predicts one of 8 clinical groups:
    Eczema/Dermatitis, Bacterial Infections, Fungal Infections,
    Viral Infections, Infestations, Acneiform, Vascular/Benign, or
    Healthy Skin.
    """

    name: str = "analyze_skin_image"
    description: str = (
        "Analyze skin images to classify dermatological conditions. "
        "Use this tool when you need to identify or diagnose skin "
        "conditions from clinical photographs. The tool uses a deep "
        "learning model (Derm Foundation) to extract image features and "
        "a Logistic Regression classifier to predict one of 8 clinical "
        "categories: Eczema/Dermatitis, Bacterial Infections, Fungal "
        "Infections, Viral Infections, Infestations, Acneiform, "
        "Vascular/Benign lesions, or Healthy Skin. "
        "Input: image_path (required - path to skin image file). "
        "Output: JSON with class_name, confidence score, and probability "
        "distribution across all categories."
    )
    args_schema: Type[BaseModel] = ImageAnalysisInput

    def __init__(
        self,
        logreg_path: str,
        derm_model_path: str,
        **kwargs,
    ):
        """
        Initialize the LangGraph image analyzer tool.

        Args:
            logreg_path: Path to trained Logistic Regression model
            derm_model_path: Path to Derm Foundation model directory
            **kwargs: Additional arguments for LangChainBaseTool
        """
        super().__init__(**kwargs)
        self._tool = _ImageAnalyzerTool(
            logreg_path=logreg_path,
            derm_model_path=derm_model_path
        )

    def _run(self, image_path: str) -> str:
        """
        Execute the image analysis tool.

        Args:
            image_path: Path to skin image file

        Returns:
            JSON string with analysis results
        """
        return self._tool.execute(image_path=image_path)
