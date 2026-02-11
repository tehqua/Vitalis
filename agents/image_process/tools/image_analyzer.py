"""Image analyzer tool for skin condition classification."""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

import joblib
import keras
import numpy as np
import tensorflow as tf
from PIL import Image

from .base import BaseTool

logger = logging.getLogger(__name__)


CLASS_NAMES = [
    "Eczema_Dermatitis",
    "Bacterial_Infections",
    "Fungal_Infections",
    "Viral_Infections",
    "Infestations",
    "Acneiform",
    "Vascular_Benign",
    "Healthy_Skin"
]


class ImageAnalyzerTool(BaseTool):
    """Tool for analyzing skin images using Derm Foundation model."""

    def __init__(
        self,
        logreg_path: str,
        derm_model_path: str,
    ):
        """
        Initialize the image analyzer tool.

        Args:
            logreg_path: Path to trained Logistic Regression model (.pkl)
            derm_model_path: Path to Derm Foundation model directory
        """
        super().__init__(
            name="analyze_skin_image",
            description="Analyze skin images to classify dermatological conditions"
        )
        self.logreg_path = logreg_path
        self.derm_model_path = derm_model_path
        self._logreg = None
        self._derm_layer = None
        self._derm_model = None

    def _initialize_models(self):
        """Initialize models lazily on first use."""
        if self._logreg is not None and self._derm_model is not None:
            return

        logger.info("Initializing image analysis models")

        try:
            # Load Logistic Regression classifier
            if not os.path.exists(self.logreg_path):
                raise FileNotFoundError(
                    f"Logistic Regression model not found: {self.logreg_path}"
                )
            
            logger.info(f"Loading Logistic Regression from: {self.logreg_path}")
            self._logreg = joblib.load(self.logreg_path)

            # Load Derm Foundation model
            if not os.path.exists(self.derm_model_path):
                raise FileNotFoundError(
                    f"Derm Foundation model not found: {self.derm_model_path}"
                )
            
            logger.info(f"Loading Derm Foundation model from: {self.derm_model_path}")
            self._derm_layer = keras.layers.TFSMLayer(
                self.derm_model_path,
                call_endpoint="serving_default"
            )
            self._derm_model = keras.Sequential([self._derm_layer])

            logger.info("Models initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            raise

    def _encode_image(self, image_path: str) -> np.ndarray:
        """
        Extract embedding from image using Derm Foundation model.

        Args:
            image_path: Path to image file

        Returns:
            Image embedding vector
        """
        image_bytes = tf.io.read_file(image_path)
        
        example = tf.train.Example(
            features=tf.train.Features(
                feature={
                    "image/encoded": tf.train.Feature(
                        bytes_list=tf.train.BytesList(
                            value=[image_bytes.numpy()]
                        )
                    )
                }
            )
        )
        
        serialized = example.SerializeToString()
        output = self._derm_layer(inputs=tf.constant([serialized]))
        
        embedding = output["embedding"].numpy().squeeze()
        return embedding

    def _validate_image_file(self, image_path: str) -> None:
        """
        Validate image file exists and can be loaded.

        Args:
            image_path: Path to image file

        Raises:
            FileNotFoundError: If image file does not exist
            ValueError: If image file cannot be loaded
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            with Image.open(image_path) as img:
                img.verify()
            logger.info(f"Image validated: {image_path}")
        except Exception as e:
            raise ValueError(f"Failed to load image file: {str(e)}")

    def execute(self, image_path: str) -> str:
        """
        Analyze skin image and predict condition.

        Args:
            image_path: Path to skin image file

        Returns:
            JSON string with prediction results

        Raises:
            FileNotFoundError: If image file does not exist
            ValueError: If image file is invalid
            Exception: If analysis fails
        """
        try:
            # Validate image file
            self._validate_image_file(image_path)

            # Initialize models if needed
            self._initialize_models()

            # Extract embedding
            logger.info(f"Extracting embedding from: {image_path}")
            embedding = self._encode_image(image_path)
            
            # Reshape for sklearn
            embedding_reshaped = embedding.reshape(1, -1)
            
            # Predict class
            pred_class = self._logreg.predict(embedding_reshaped)[0]
            pred_proba = self._logreg.predict_proba(embedding_reshaped)[0]
            
            # Format results
            result = {
                "class_id": int(pred_class),
                "class_name": CLASS_NAMES[pred_class],
                "confidence": float(pred_proba[pred_class]),
                "all_probabilities": {
                    CLASS_NAMES[i]: float(prob) 
                    for i, prob in enumerate(pred_proba)
                }
            }
            
            logger.info(
                f"Analysis completed: {result['class_name']} "
                f"({result['confidence']:.2%})"
            )
            
            return json.dumps(result, indent=2)

        except (FileNotFoundError, ValueError) as e:
            return self.format_error(e)
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}", exc_info=True)
            return self.format_error(e)
