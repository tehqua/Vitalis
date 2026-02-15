"""
Utility functions for the orchestrator.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from .state import Message

logger = logging.getLogger(__name__)


def create_message(role: str, content: str, metadata: Dict[str, Any] = None) -> Message:
    """
    Create a message object.
    
    Args:
        role: Message role (user/assistant/system)
        content: Message content
        metadata: Optional metadata
        
    Returns:
        Message object
    """
    return {
        "role": role,
        "content": content,
        "metadata": metadata or {}
    }


def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def truncate_conversation(messages: List[Message], max_length: int = 50) -> List[Message]:
    """
    Truncate conversation history to max length.
    
    Args:
        messages: List of messages
        max_length: Maximum number of messages to keep
        
    Returns:
        Truncated message list
    """
    if len(messages) <= max_length:
        return messages
    
    # Keep system message if it exists
    system_messages = [m for m in messages if m.get("role") == "system"]
    other_messages = [m for m in messages if m.get("role") != "system"]
    
    # Keep most recent messages
    truncated = other_messages[-(max_length - len(system_messages)):]
    
    logger.info(f"Truncated conversation from {len(messages)} to {len(truncated)} messages")
    
    return system_messages + truncated


def summarize_conversation(messages: List[Message], max_messages: int = 10) -> str:
    """
    Create a summary of conversation for context.
    
    Args:
        messages: Conversation messages
        max_messages: Number of recent messages to include
        
    Returns:
        Conversation summary
    """
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
    
    summary_parts = []
    for msg in recent_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        # Truncate long messages
        if len(content) > 200:
            content = content[:200] + "..."
        
        summary_parts.append(f"{role.upper()}: {content}")
    
    return "\n".join(summary_parts)


def format_tool_result(tool_name: str, result: Any) -> str:
    """
    Format tool execution result for agent consumption.
    
    Args:
        tool_name: Name of the tool
        result: Tool execution result
        
    Returns:
        Formatted result string
    """
    formatted = f"TOOL EXECUTION: {tool_name}\n"
    formatted += f"RESULT:\n{result}\n"
    return formatted


def extract_text_from_state(state: Dict[str, Any]) -> str:
    """
    Extract the current text input from state, considering all sources.
    
    Args:
        state: Agent state
        
    Returns:
        Combined text input
    """
    text_parts = []
    
    # User text input
    if state.get("user_text_input"):
        text_parts.append(state["user_text_input"])
    
    # Transcribed speech
    if state.get("transcribed_text"):
        text_parts.append(f"[Transcribed from audio]: {state['transcribed_text']}")
    
    return " ".join(text_parts) if text_parts else ""


def determine_input_type(
    text_input: str = None,
    audio_path: str = None, 
    image_path: str = None
) -> str:
    """
    Determine the type of input based on what's provided.
    
    Args:
        text_input: Text input
        audio_path: Audio file path
        image_path: Image file path
        
    Returns:
        Input type string
    """
    has_text = bool(text_input and text_input.strip())
    has_audio = bool(audio_path)
    has_image = bool(image_path)
    
    input_count = sum([has_text, has_audio, has_image])
    
    if input_count == 0:
        return "text"  # Default
    elif input_count == 1:
        if has_text:
            return "text"
        elif has_audio:
            return "speech"
        else:
            return "image"
    else:
        return "multimodal"


def clean_response(response: str) -> str:
    """
    Clean up response text.
    
    Args:
        response: Raw response
        
    Returns:
        Cleaned response
    """
    # Remove excessive newlines
    response = "\n".join(line for line in response.split("\n") if line.strip())
    
    # Remove leading/trailing whitespace
    response = response.strip()
    
    return response


def log_state_transition(from_node: str, to_node: str, state: Dict[str, Any]):
    """
    Log state transition for debugging.
    
    Args:
        from_node: Source node
        to_node: Destination node
        state: Current state
    """
    logger.debug(
        f"State transition: {from_node} -> {to_node} | "
        f"Patient: {state.get('patient_id', 'N/A')} | "
        f"Input type: {state.get('current_input_type', 'N/A')}"
    )


def validate_state(state: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate that state contains required keys.
    
    Args:
        state: State to validate
        required_keys: List of required key names
        
    Returns:
        True if valid
    """
    missing_keys = [key for key in required_keys if key not in state]
    
    if missing_keys:
        logger.error(f"State missing required keys: {missing_keys}")
        return False
    
    return True


def parse_tool_output(output: str) -> Dict[str, Any]:
    """
    Parse tool output, attempting JSON parsing if possible.
    
    Args:
        output: Tool output string
        
    Returns:
        Parsed output as dict
    """
    import json
    
    # Try to parse as JSON
    try:
        return json.loads(output)
    except (json.JSONDecodeError, TypeError):
        # Return as-is if not JSON
        return {"raw_output": output}


class ConversationMemory:
    """Simple conversation memory manager"""
    
    def __init__(self, max_messages: int = 50):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum messages to retain
        """
        self.max_messages = max_messages
        self.messages: List[Message] = []
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to memory"""
        msg = create_message(role, content, metadata)
        self.messages.append(msg)
        
        # Truncate if needed
        if len(self.messages) > self.max_messages:
            # Keep system messages
            system_msgs = [m for m in self.messages if m.get("role") == "system"]
            other_msgs = [m for m in self.messages if m.get("role") != "system"]
            
            # Keep most recent
            keep_count = self.max_messages - len(system_msgs)
            self.messages = system_msgs + other_msgs[-keep_count:]
    
    def get_messages(self) -> List[Message]:
        """Get all messages"""
        return self.messages.copy()
    
    def clear(self):
        """Clear all messages"""
        self.messages = []
    
    def get_last_n(self, n: int) -> List[Message]:
        """Get last n messages"""
        return self.messages[-n:] if len(self.messages) > n else self.messages.copy()