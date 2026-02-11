"""LangGraph-compatible tool wrappers for speech-to-text.

This module provides LangChain BaseTool-compatible wrappers around existing
speech-to-text tools, enabling seamless integration with LangGraph agents.
"""

from typing import Optional, Type

from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field

from .speech_to_text import SpeechToTextTool as _SpeechToTextTool


class SpeechToTextInput(BaseModel):
    """Input schema for speech-to-text tool."""

    audio_path: str = Field(
        ...,
        description="Path to audio file (WAV format, 16kHz recommended)"
    )
    chunk_length_s: int = Field(
        20,
        description="Chunk length in seconds for audio processing"
    )
    stride_length_s: int = Field(
        2,
        description="Stride length in seconds between chunks"
    )
    beam_width: int = Field(
        8,
        description="Beam search width for decoding (higher = more accurate)"
    )


class LangGraphSpeechToTextTool(LangChainBaseTool):
    """LangGraph-compatible speech-to-text tool.

    Converts medical audio recordings to text using Google's MedASR model
    with optional KenLM language model for improved accuracy on medical
    terminology.
    """

    name: str = "speech_to_text"
    description: str = (
        "Convert medical audio recordings to text transcription. "
        "Use this tool when you need to transcribe doctor-patient "
        "conversations, medical dictations, or clinical notes from audio. "
        "The tool uses MedASR (Medical Automated Speech Recognition) "
        "optimized for medical terminology and clinical language. "
        "Input: audio_path (required), chunk_length_s (default 20), "
        "stride_length_s (default 2), beam_width (default 8). "
        "Output: Transcribed text from the audio recording."
    )
    args_schema: Type[BaseModel] = SpeechToTextInput

    def __init__(
        self,
        model_id: str = "google/medasr",
        lm_path: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the LangGraph speech-to-text tool.

        Args:
            model_id: Hugging Face model identifier
            lm_path: Path to KenLM language model file
            **kwargs: Additional arguments for LangChainBaseTool
        """
        super().__init__(**kwargs)
        self._tool = _SpeechToTextTool(model_id=model_id, lm_path=lm_path)

    def _run(
        self,
        audio_path: str,
        chunk_length_s: int = 20,
        stride_length_s: int = 2,
        beam_width: int = 8,
    ) -> str:
        """
        Execute the speech-to-text tool.

        Args:
            audio_path: Path to audio file
            chunk_length_s: Chunk length in seconds
            stride_length_s: Stride length in seconds
            beam_width: Beam search width

        Returns:
            Transcribed text from audio
        """
        return self._tool.execute(
            audio_path=audio_path,
            chunk_length_s=chunk_length_s,
            stride_length_s=stride_length_s,
            beam_width=beam_width,
        )
