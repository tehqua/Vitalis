"""
Input validators and sanitizers.
"""

import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Validator for user inputs"""
    
    # Patterns
    PATIENT_ID_PATTERN = re.compile(r'^[A-Z][a-z]+\d+_[A-Z][a-z]+\d+_[a-f0-9-]{36}$')
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
        r"(;|\-\-|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
    ]
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]
    
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
        
        if not InputValidator.PATIENT_ID_PATTERN.match(patient_id):
            return False, "Invalid patient ID format"
        
        return True, None
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 5000) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove XSS patterns
        for pattern in InputValidator.XSS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters")
        
        return text.strip()
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """
        Check if text contains SQL injection patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if SQL injection detected
        """
        text_upper = text.upper()
        
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def validate_message(message: str) -> Tuple[bool, Optional[str]]:
        """
        Validate chat message.
        
        Args:
            message: Message to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message or not message.strip():
            return False, "Message cannot be empty"
        
        if len(message) > 5000:
            return False, "Message too long (max 5000 characters)"
        
        # Check for SQL injection
        if InputValidator.check_sql_injection(message):
            return False, "Invalid message content"
        
        return True, None
    
    @staticmethod
    def validate_session_id(session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate session ID format (UUID).
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not session_id:
            return False, "Session ID is required"
        
        # Check if valid UUID format
        uuid_pattern = re.compile(
            r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(session_id):
            return False, "Invalid session ID format"
        
        return True, None


class FileValidator:
    """Validator for uploaded files"""
    
    # Max sizes
    MAX_IMAGE_SIZE_MB = 10
    MAX_AUDIO_SIZE_MB = 50
    
    # Allowed extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.ogg', '.webm'}
    
    # Magic numbers for file type detection
    IMAGE_MAGIC_NUMBERS = {
        b'\xff\xd8\xff': 'image/jpeg',
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
    }
    
    @staticmethod
    def validate_file_extension(
        filename: str,
        file_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file extension.
        
        Args:
            filename: Filename to validate
            file_type: Expected file type (image/audio)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from pathlib import Path
        
        ext = Path(filename).suffix.lower()
        
        if file_type == "image":
            if ext not in FileValidator.IMAGE_EXTENSIONS:
                return False, f"Invalid image extension. Allowed: {FileValidator.IMAGE_EXTENSIONS}"
        elif file_type == "audio":
            if ext not in FileValidator.AUDIO_EXTENSIONS:
                return False, f"Invalid audio extension. Allowed: {FileValidator.AUDIO_EXTENSIONS}"
        else:
            return False, "Invalid file type"
        
        return True, None
    
    @staticmethod
    def validate_file_size(
        file_size: int,
        file_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            file_type: File type (image/audio)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        max_size_mb = (
            FileValidator.MAX_IMAGE_SIZE_MB if file_type == "image"
            else FileValidator.MAX_AUDIO_SIZE_MB
        )
        
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"File too large. Maximum size: {max_size_mb}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, None
    
    @staticmethod
    def detect_file_type(content: bytes) -> Optional[str]:
        """
        Detect file type from magic numbers.
        
        Args:
            content: File content bytes
            
        Returns:
            MIME type or None
        """
        for magic_bytes, mime_type in FileValidator.IMAGE_MAGIC_NUMBERS.items():
            if content.startswith(magic_bytes):
                return mime_type
        
        return None