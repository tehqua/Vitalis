"""
State definitions for the medical chatbot agent.

This module defines the TypedDict state used throughout the LangGraph workflow.
"""

from typing import TypedDict, List, Optional, Literal, Dict, Any
from typing_extensions import Annotated
from langgraph.graph import add_messages


class Message(TypedDict):
    """Single message in conversation"""
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: Optional[Dict[str, Any]]


class AgentState(TypedDict):
    """
    State passed through the LangGraph workflow.
    
    This state contains all information needed for the agent to process
    user requests and maintain conversation context.
    """
    
    # User identification
    patient_id: str
    
    # Conversation tracking
    messages: Annotated[List[Message], add_messages]
    
    # Current input analysis
    current_input_type: Literal["text", "speech", "image", "multimodal"]
    user_text_input: Optional[str]
    audio_file_path: Optional[str]
    image_file_path: Optional[str]
    
    # Processed inputs
    transcribed_text: Optional[str]
    image_analysis_result: Optional[Dict[str, Any]]
    
    # RAG context
    rag_context: Optional[Dict[str, Any]]
    rag_needed: bool
    
    # Routing decisions
    routing_decision: str
    requires_tool_call: bool
    tool_calls_completed: List[str]
    
    # Agent reasoning
    agent_scratchpad: str
    next_action: Optional[str]
    
    # Final output
    final_response: Optional[str]
    
    # Safety and validation
    safety_check_passed: bool
    emergency_detected: bool
    
    # Metadata
    session_id: str
    timestamp: str