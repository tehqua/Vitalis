"""Speech-to-text tool for medical audio transcription."""

import logging
import os
from pathlib import Path
from typing import Optional

import librosa
import pyctcdecode
import torch
import transformers

from .base import BaseTool

logger = logging.getLogger(__name__)


def _restore_text(text: str) -> str:
    """
    Restore text formatting after decoding.

    Args:
        text: Decoded text with special characters

    Returns:
        Restored text with proper formatting
    """
    return text.replace(" ", "").replace("#", " ").replace("", "").strip()


class LasrCtcBeamSearchDecoder:
    """Custom CTC beam search decoder for LASR models."""

    def __init__(
        self,
        tokenizer: transformers.LasrTokenizer,
        kenlm_model_path: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the beam search decoder.

        Args:
            tokenizer: LASR tokenizer instance
            kenlm_model_path: Path to KenLM language model file
            **kwargs: Additional arguments for pyctcdecode
        """
        vocab = [None for _ in range(tokenizer.vocab_size)]
        for k, v in tokenizer.vocab.items():
            if v < tokenizer.vocab_size:
                vocab[v] = k
        assert not [i for i in vocab if i is None]

        # pyctcdecode expects the blank label to map to the empty string
        vocab[0] = ""

        # Replace '▁' with '#' and prefix each token with a '▁'
        # This way, pyctcdecode treats each token as a "word"
        for i in range(1, len(vocab)):
            piece = vocab[i]
            if not piece.startswith("<") and not piece.endswith(">"):
                piece = "▁" + piece.replace("▁", "#")
            vocab[i] = piece

        self._decoder = pyctcdecode.build_ctcdecoder(
            vocab, kenlm_model_path, **kwargs
        )

    def decode_beams(self, *args, **kwargs):
        """
        Decode beams and restore text formatting.

        Args:
            *args: Positional arguments for decode_beams
            **kwargs: Keyword arguments for decode_beams

        Returns:
            List of beams with restored text
        """
        beams = self._decoder.decode_beams(*args, **kwargs)

        fixed_beams = []
        for beam in beams:
            text, logit_score, lm_score, score, word_offsets = beam
            fixed_beams.append(
                (
                    _restore_text(text),
                    logit_score,
                    lm_score,
                    score,
                    word_offsets,
                )
            )
        return fixed_beams


class SpeechToTextTool(BaseTool):
    """Tool for converting medical audio to text using MedASR."""

    def __init__(
        self,
        model_id: str = "google/medasr",
        lm_path: Optional[str] = None,
    ):
        """
        Initialize the speech-to-text tool.

        Args:
            model_id: Hugging Face model identifier
            lm_path: Path to KenLM language model file
        """
        super().__init__(
            name="speech_to_text",
            description="Convert medical audio recordings to text using MedASR"
        )
        self.model_id = model_id
        self.lm_path = lm_path
        self._pipeline = None

    def _initialize_pipeline(self):
        """Initialize the speech recognition pipeline lazily."""
        if self._pipeline is not None:
            return

        logger.info(f"Initializing MedASR pipeline with model: {self.model_id}")

        try:
            feature_extractor = transformers.LasrFeatureExtractor.from_pretrained(
                self.model_id
            )
            feature_extractor._processor_class = "LasrProcessorWithLM"

            decoder = None
            if self.lm_path and os.path.exists(self.lm_path):
                logger.info(f"Loading language model from: {self.lm_path}")
                tokenizer = transformers.AutoTokenizer.from_pretrained(
                    self.model_id
                )
                decoder = LasrCtcBeamSearchDecoder(tokenizer, self.lm_path)

            self._pipeline = transformers.pipeline(
                task="automatic-speech-recognition",
                model=self.model_id,
                feature_extractor=feature_extractor,
                decoder=decoder,
            )

            if decoder:
                assert self._pipeline.type == "ctc_with_lm"

            logger.info("MedASR pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {str(e)}")
            raise

    def _validate_audio_file(self, audio_path: str) -> None:
        """
        Validate audio file exists and can be loaded.

        Args:
            audio_path: Path to audio file

        Raises:
            FileNotFoundError: If audio file does not exist
            ValueError: If audio file cannot be loaded
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            speech, sr = librosa.load(audio_path, sr=16000, mono=True)
            logger.info(f"Audio loaded: shape={speech.shape}, sr={sr}")
        except Exception as e:
            raise ValueError(f"Failed to load audio file: {str(e)}")

    def execute(
        self,
        audio_path: str,
        chunk_length_s: int = 20,
        stride_length_s: int = 2,
        beam_width: int = 8,
    ) -> str:
        """
        Convert audio file to text.

        Args:
            audio_path: Path to audio file (WAV format, 16kHz recommended)
            chunk_length_s: Chunk length in seconds for processing
            stride_length_s: Stride length in seconds between chunks
            beam_width: Beam search width for decoding

        Returns:
            Transcribed text from audio

        Raises:
            FileNotFoundError: If audio file does not exist
            ValueError: If audio file is invalid
            Exception: If transcription fails
        """
        try:
            # Validate audio file
            self._validate_audio_file(audio_path)

            # Initialize pipeline if needed
            self._initialize_pipeline()

            # Prepare decoder kwargs
            decoder_kwargs = {}
            if self.lm_path:
                decoder_kwargs["beam_width"] = beam_width

            # Perform transcription
            logger.info(f"Transcribing audio: {audio_path}")
            result = self._pipeline(
                audio_path,
                chunk_length_s=chunk_length_s,
                stride_length_s=stride_length_s,
                decoder_kwargs=decoder_kwargs if decoder_kwargs else None,
            )

            transcribed_text = result.get("text", "")
            logger.info(
                f"Transcription completed: {len(transcribed_text)} characters"
            )

            if not transcribed_text:
                return "No speech detected in audio file."

            return transcribed_text

        except (FileNotFoundError, ValueError) as e:
            return self.format_error(e)
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}", exc_info=True)
            return self.format_error(e)
