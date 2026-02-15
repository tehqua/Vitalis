"""
Guardrails and safety checks for the medical chatbot.

This module implements various safety measures including:
- Emergency symptom detection
- Medical disclaimer injection
- Privacy protection
- Output validation
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class MedicalGuardrails:
    """Safety and validation layer for medical chatbot"""
    
    # Emergency symptoms that require immediate medical attention
    EMERGENCY_KEYWORDS = {
        "chest pain": ["severe chest pain", "crushing chest", "chest tightness with pain"],
        "breathing": ["can't breathe", "difficulty breathing", "severe shortness of breath", "gasping"],
        "bleeding": ["severe bleeding", "bleeding won't stop", "heavy bleeding"],
        "consciousness": ["passed out", "losing consciousness", "unresponsive", "fainting repeatedly"],
        "stroke": ["facial drooping", "arm weakness", "slurred speech", "sudden confusion"],
        "allergic": ["severe allergic reaction", "throat swelling", "anaphylaxis"],
        "head": ["severe head injury", "head trauma", "severe headache with fever"],
        "poisoning": ["poisoned", "overdose", "ingested poison"],
        "seizure": ["seizure", "convulsions", "fitting"],
        "suicide": ["want to die", "kill myself", "suicide", "end my life"],
    }
    
    # Phrases that should not appear in medical advice
    PROHIBITED_PHRASES = [
        "you definitely have",
        "you are diagnosed with",
        "i diagnose you",
        "this is definitely",
        "you need this medication",
        "take this drug",
        "stop taking your medication",
    ]
    
    # Medical terms that need patient-friendly explanations
    COMPLEX_MEDICAL_TERMS = [
        "myocardial infarction",
        "cerebrovascular accident", 
        "dyspnea",
        "tachycardia",
        "bradycardia",
        "hyperglycemia",
        "hypoglycemia",
    ]
    
    def __init__(self, enable_emergency_detection: bool = True, 
                 require_disclaimer: bool = True):
        """
        Initialize guardrails.
        
        Args:
            enable_emergency_detection: Enable emergency symptom detection
            require_disclaimer: Require medical disclaimer on all responses
        """
        self.enable_emergency_detection = enable_emergency_detection
        self.require_disclaimer = require_disclaimer
    
    def detect_emergency(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect potential emergency symptoms in user input.
        
        Args:
            text: User message text
            
        Returns:
            Tuple of (is_emergency, list_of_detected_symptoms)
        """
        if not self.enable_emergency_detection:
            return False, []
        
        text_lower = text.lower()
        detected_symptoms = []
        
        for category, keywords in self.EMERGENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_symptoms.append(f"{category}: {keyword}")
                    logger.warning(f"Emergency keyword detected: {keyword}")
        
        is_emergency = len(detected_symptoms) > 0
        return is_emergency, detected_symptoms
    
    def validate_response(self, response: str) -> Tuple[bool, List[str]]:
        """
        Validate that response doesn't contain prohibited content.
        
        Args:
            response: Generated response text
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        response_lower = response.lower()
        violations = []
        
        # Check for prohibited phrases
        for phrase in self.PROHIBITED_PHRASES:
            if phrase in response_lower:
                violations.append(f"Prohibited phrase detected: '{phrase}'")
                logger.error(f"Response contains prohibited phrase: {phrase}")
        
        # Check for definitive diagnoses (heuristic)
        diagnosis_patterns = [
            r'\byou have (a|an|the) \w+',
            r'\bdiagnosed with\b',
            r'\byou are suffering from\b',
        ]
        
        for pattern in diagnosis_patterns:
            if re.search(pattern, response_lower):
                # Allow if it contains qualifying language
                if not any(qual in response_lower for qual in ["may", "might", "could", "possibly", "suggests"]):
                    violations.append(f"Potentially definitive diagnosis: '{pattern}'")
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def add_medical_disclaimer(self, response: str) -> str:
        """
        Add medical disclaimer to response if required.
        
        Args:
            response: Generated response
            
        Returns:
            Response with disclaimer appended
        """
        if not self.require_disclaimer:
            return response
        
        # Check if disclaimer already exists
        if "medical disclaimer" in response.lower():
            return response
        
        disclaimer = (
            "\n\nMEDICAL DISCLAIMER: This information is for educational purposes only "
            "and is not a substitute for professional medical advice, diagnosis, or treatment. "
            "Always consult your healthcare provider for medical concerns."
        )
        
        return response + disclaimer
    
    def validate_patient_privacy(self, response: str, current_patient_id: str) -> bool:
        """
        Check that response doesn't contain information about other patients.
        
        Args:
            response: Generated response
            current_patient_id: Current patient's ID
            
        Returns:
            True if privacy is maintained
        """
        # This is a simple heuristic - in production, use more sophisticated methods
        
        # Check for patient ID patterns that aren't the current patient
        patient_id_pattern = r'[A-Z][a-z]+\d+_[A-Z][a-z]+\d+_[a-f0-9-]{36}'
        found_ids = re.findall(patient_id_pattern, response)
        
        for found_id in found_ids:
            if found_id != current_patient_id:
                logger.error(f"Potential privacy violation: Found other patient ID {found_id}")
                return False
        
        return True
    
    def generate_emergency_response(self, symptoms: List[str]) -> str:
        """
        Generate emergency response for detected critical symptoms.
        
        Args:
            symptoms: List of detected emergency symptoms
            
        Returns:
            Emergency response message
        """
        response = (
            "URGENT: Based on your description, this may be a medical emergency.\n\n"
            "IMMEDIATE ACTIONS:\n"
            "1. Call emergency services (911) or go to the nearest emergency department immediately\n"
            "2. Do not drive yourself - call an ambulance or have someone drive you\n"
            "3. If you are alone and able, call emergency services first before doing anything else\n\n"
            f"Symptoms requiring urgent attention: {', '.join(symptoms)}\n\n"
            "Do not wait or try to self-diagnose. Please seek immediate medical help.\n\n"
            "If this is not an emergency and you misunderstood my concern, please clarify your symptoms."
        )
        
        return response
    
    def check_drug_mention(self, text: str) -> bool:
        """
        Check if text contains medication mentions that need careful handling.
        
        Args:
            text: Text to check
            
        Returns:
            True if drug mentions detected
        """
        # Common drug suffixes
        drug_suffixes = ['cillin', 'cycline', 'pril', 'sartan', 'statin', 'olol', 'pine']
        
        text_lower = text.lower()
        for suffix in drug_suffixes:
            if suffix in text_lower:
                return True
        
        # Common drug keywords
        drug_keywords = ['medication', 'prescription', 'drug', 'medicine', 'pill', 'tablet']
        return any(keyword in text_lower for keyword in drug_keywords)
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent injection attacks.
        
        Args:
            text: Raw user input
            
        Returns:
            Sanitized text
        """
        # Remove potential script tags
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Limit length
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        return text.strip()


class InputValidator:
    """Validator for user inputs (files, patient IDs, etc.)"""
    
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.ogg'}
    MAX_IMAGE_SIZE_MB = 10
    MAX_AUDIO_SIZE_MB = 50
    
    @staticmethod
    def validate_patient_id(patient_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate patient ID format.
        
        Args:
            patient_id: Patient ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not patient_id:
            return False, "Patient ID is required"
        
        # Expected format: FirstName###_LastName###_uuid
        pattern = r'^[A-Z][a-z]+\d+_[A-Z][a-z]+\d+_[a-f0-9-]{36}$'
        
        if not re.match(pattern, patient_id):
            return False, "Invalid patient ID format"
        
        return True, None
    
    @staticmethod
    def validate_image_file(filepath: str, check_exists: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate image file.
        
        Args:
            filepath: Path to image file
            check_exists: Whether to check if file exists
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import os
        from pathlib import Path
        
        if not filepath:
            return False, "Image file path is required"
        
        file_path = Path(filepath)
        
        # Check extension
        if file_path.suffix.lower() not in InputValidator.ALLOWED_IMAGE_EXTENSIONS:
            return False, f"Invalid image format. Allowed: {InputValidator.ALLOWED_IMAGE_EXTENSIONS}"
        
        # Check if exists
        if check_exists and not file_path.exists():
            return False, f"Image file not found: {filepath}"
        
        # Check size
        if check_exists:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > InputValidator.MAX_IMAGE_SIZE_MB:
                return False, f"Image too large ({size_mb:.1f}MB). Max: {InputValidator.MAX_IMAGE_SIZE_MB}MB"
        
        return True, None
    
    @staticmethod
    def validate_audio_file(filepath: str, check_exists: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate audio file.
        
        Args:
            filepath: Path to audio file
            check_exists: Whether to check if file exists
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import os
        from pathlib import Path
        
        if not filepath:
            return False, "Audio file path is required"
        
        file_path = Path(filepath)
        
        # Check extension
        if file_path.suffix.lower() not in InputValidator.ALLOWED_AUDIO_EXTENSIONS:
            return False, f"Invalid audio format. Allowed: {InputValidator.ALLOWED_AUDIO_EXTENSIONS}"
        
        # Check if exists
        if check_exists and not file_path.exists():
            return False, f"Audio file not found: {filepath}"
        
        # Check size
        if check_exists:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > InputValidator.MAX_AUDIO_SIZE_MB:
                return False, f"Audio too large ({size_mb:.1f}MB). Max: {InputValidator.MAX_AUDIO_SIZE_MB}MB"
        
        return True, None