"""
Main Medical Chatbot Agent using LangGraph.

This module implements the orchestrator that coordinates all tools and
handles the conversation flow.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from .state import AgentState
from .config import OrchestratorConfig
from .nodes import WorkflowNodes
from .utils import create_message, ConversationMemory

logger = logging.getLogger(__name__)


class MedicalChatbotAgent:
    """
    Main orchestrator for the medical chatbot system.
    
    This agent coordinates between:
    - Speech-to-text processing
    - Image analysis (skin conditions)
    - Patient record retrieval (RAG)
    - Medical reasoning (LLM)
    - Safety guardrails
    """
    
    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        image_analyzer_tool=None,
        patient_record_tool=None,
        speech_to_text_tool=None,
    ):
        """
        Initialize the medical chatbot agent.
        
        Args:
            config: Orchestrator configuration
            image_analyzer_tool: Image analysis tool instance
            patient_record_tool: Patient record retrieval tool
            speech_to_text_tool: Speech-to-text tool
        """
        self.config = config or OrchestratorConfig()
        
        # Initialize tools
        self.image_analyzer = image_analyzer_tool or self._init_image_analyzer()
        self.patient_record = patient_record_tool or self._init_patient_record()
        self.speech_to_text = speech_to_text_tool or self._init_speech_to_text()
        
        # Initialize LLM client
        self.llm = self._init_llm()
        
        # Initialize workflow nodes
        self.nodes = WorkflowNodes(
            image_analyzer_tool=self.image_analyzer,
            patient_record_tool=self.patient_record,
            speech_to_text_tool=self.speech_to_text,
            llm_client=self.llm,
            config=self.config
        )
        
        # Build the state graph
        self.graph = self._build_graph()
        
        # Conversation memory (optional - can be managed externally)
        self.memory = ConversationMemory(max_messages=self.config.max_conversation_length)
        
        logger.info("MedicalChatbotAgent initialized successfully")
    
    def _init_image_analyzer(self):
        """Initialize image analyzer tool"""
        try:
            from agents.image_process.tools import langgraph_image_analyzer
            return langgraph_image_analyzer
        except ImportError as e:
            logger.error(f"Failed to import image analyzer: {e}")
            return None
    
    def _init_patient_record(self):
        """Initialize patient record tool"""
        try:
            from agents.patient_database.tools.patient_record_tool import PatientRecordRetrieverTool
            return PatientRecordRetrieverTool()
        except ImportError as e:
            logger.error(f"Failed to import patient record tool: {e}")
            return None
    
    def _init_speech_to_text(self):
        """Initialize speech-to-text tool"""
        try:
            from agents.speech_to_text_process.tools import langgraph_speech_to_text
            return langgraph_speech_to_text
        except ImportError as e:
            logger.error(f"Failed to import speech-to-text: {e}")
            return None
    
    def _init_llm(self):
        """Initialize LLM client (Ollama)"""
        # LLM is accessed directly via ollama library in nodes
        # This is just a placeholder for future expansion
        return None
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph for the workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("input_router", self.nodes.input_router)
        workflow.add_node("process_speech", self.nodes.process_speech)
        workflow.add_node("process_image", self.nodes.process_image)
        workflow.add_node("reasoning", self.nodes.reasoning_node)
        workflow.add_node("call_tool", self.nodes.call_tool)
        workflow.add_node("safety_check", self.nodes.safety_check)
        workflow.add_node("error_handler", self.nodes.error_handler)
        
        # Set entry point
        workflow.set_entry_point("input_router")
        
        # Add conditional edges from input_router
        workflow.add_conditional_edges(
            "input_router",
            self._route_from_input,
            {
                "process_speech": "process_speech",
                "process_image": "process_image",
                "reasoning": "reasoning",
                "error": "error_handler",
            }
        )
        
        # Add edges from process_speech
        workflow.add_conditional_edges(
            "process_speech",
            self._route_after_speech,
            {
                "process_image": "process_image",
                "reasoning": "reasoning",
            }
        )
        
        # Add edge from process_image
        workflow.add_edge("process_image", "reasoning")
        
        # Add conditional edges from reasoning
        workflow.add_conditional_edges(
            "reasoning",
            self._route_from_reasoning,
            {
                "call_tool": "call_tool",
                "safety_check": "safety_check",
            }
        )
        
        # Add edge from call_tool back to reasoning
        workflow.add_edge("call_tool", "reasoning")
        
        # Add edge from safety_check to END
        workflow.add_edge("safety_check", END)
        
        # Add edge from error_handler to END
        workflow.add_edge("error_handler", END)
        
        # Compile the graph
        app = workflow.compile()
        
        logger.info("State graph compiled successfully")
        return app
    
    def _route_from_input(self, state: AgentState) -> str:
        """Routing logic from input_router node"""
        decision = state.get("routing_decision", "reasoning")
        
        if decision == "error":
            return "error"
        elif decision == "process_speech":
            return "process_speech"
        elif decision == "process_image":
            return "process_image"
        else:
            return "reasoning"
    
    def _route_after_speech(self, state: AgentState) -> str:
        """Routing logic after speech processing"""
        decision = state.get("routing_decision", "reasoning")
        
        if decision == "process_image":
            return "process_image"
        else:
            return "reasoning"
    
    def _route_from_reasoning(self, state: AgentState) -> str:
        """Routing logic from reasoning node"""
        decision = state.get("routing_decision", "safety_check")
        
        if decision == "call_tool":
            return "call_tool"
        else:
            return "safety_check"
    
    def process_message(
        self,
        patient_id: str,
        text_input: Optional[str] = None,
        audio_file_path: Optional[str] = None,
        image_file_path: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent workflow.
        
        Args:
            patient_id: Patient's unique identifier
            text_input: Text message from user
            audio_file_path: Path to audio file (if speech input)
            image_file_path: Path to image file (if image input)
            session_id: Session identifier (generated if not provided)
            
        Returns:
            Dict containing response and metadata
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize state
        initial_state: AgentState = {
            "patient_id": patient_id,
            "messages": self.memory.get_messages(),
            "current_input_type": "text",
            "user_text_input": text_input,
            "audio_file_path": audio_file_path,
            "image_file_path": image_file_path,
            "transcribed_text": None,
            "image_analysis_result": None,
            "rag_context": None,
            "rag_needed": False,
            "routing_decision": "",
            "requires_tool_call": False,
            "tool_calls_completed": [],
            "agent_scratchpad": "",
            "next_action": None,
            "final_response": None,
            "safety_check_passed": False,
            "emergency_detected": False,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info(
            f"Processing message for patient {patient_id} | "
            f"Text: {bool(text_input)} | Audio: {bool(audio_file_path)} | "
            f"Image: {bool(image_file_path)}"
        )
        
        try:
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            # Extract response
            response_text = final_state.get("final_response", "")
            
            # Add to memory
            if text_input:
                self.memory.add_message("user", text_input)
            elif final_state.get("transcribed_text"):
                self.memory.add_message("user", final_state["transcribed_text"])
            
            self.memory.add_message("assistant", response_text)
            
            # Prepare result
            result = {
                "response": response_text,
                "session_id": session_id,
                "timestamp": final_state.get("timestamp"),
                "metadata": {
                    "input_type": final_state.get("current_input_type"),
                    "tools_used": final_state.get("tool_calls_completed", []),
                    "emergency_detected": final_state.get("emergency_detected", False),
                    "image_analysis": final_state.get("image_analysis_result"),
                    "rag_retrieved": bool(final_state.get("rag_context")),
                }
            }
            
            logger.info(f"Message processed successfully | Session: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            
            return {
                "response": (
                    "I apologize, but I encountered an error processing your request. "
                    "Please try again or contact support if the issue persists."
                ),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "error": str(e),
                }
            }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")
    
    def get_conversation_history(self):
        """Get conversation history"""
        return self.memory.get_messages()
    
    def export_graph_diagram(self, output_path: str = "workflow_graph.png"):
        """
        Export the workflow graph as an image.
        
        Args:
            output_path: Path to save the diagram
        """
        try:
            from IPython.display import Image, display
            
            # Get mermaid diagram
            diagram = self.graph.get_graph().draw_mermaid_png()
            
            with open(output_path, "wb") as f:
                f.write(diagram)
            
            logger.info(f"Graph diagram exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export graph diagram: {e}")