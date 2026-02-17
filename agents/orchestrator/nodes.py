"""
LangGraph nodes for the medical chatbot workflow.

Each node represents a processing step in the agent workflow.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .state import AgentState
from .prompts import (
    format_image_analysis_prompt,
    format_rag_context_prompt,
    format_emergency_prompt,
)
from .guardrails import MedicalGuardrails, InputValidator
from .utils import (
    determine_input_type,
    extract_text_from_state,
    clean_response,
)

logger = logging.getLogger(__name__)


class WorkflowNodes:
    """Container for all workflow nodes"""
    
    def __init__(
        self,
        image_analyzer_tool,
        patient_record_tool,
        speech_to_text_tool,
        llm_client,
        config
    ):
        """
        Initialize workflow nodes.
        
        Args:
            image_analyzer_tool: Image analysis tool instance
            patient_record_tool: Patient record retrieval tool instance
            speech_to_text_tool: Speech-to-text tool instance
            llm_client: LLM client (Ollama)
            config: Orchestrator configuration
        """
        self.image_analyzer = image_analyzer_tool
        self.patient_record = patient_record_tool
        self.speech_to_text = speech_to_text_tool
        self.llm = llm_client
        self.config = config
        
        # Initialize guardrails
        self.guardrails = MedicalGuardrails(
            enable_emergency_detection=config.enable_emergency_detection,
            require_disclaimer=config.require_medical_disclaimer
        )
        self.validator = InputValidator()
    
    def input_router(self, state: AgentState) -> AgentState:
        """
        Route input based on type (text/speech/image/multimodal).
        
        This is the entry point that determines what processing is needed.
        """
        logger.info("Node: input_router")
        
        # Determine input type
        input_type = determine_input_type(
            state.get("user_text_input"),
            state.get("audio_file_path"),
            state.get("image_file_path")
        )
        
        state["current_input_type"] = input_type
        state["tool_calls_completed"] = []
        state["timestamp"] = datetime.utcnow().isoformat()
        
        # Validate patient ID
        is_valid, error = self.validator.validate_patient_id(state["patient_id"])
        if not is_valid:
            logger.error(f"Invalid patient ID: {error}")
            state["final_response"] = f"Error: {error}"
            state["routing_decision"] = "error"
            return state
        
        # Validate files if present
        if state.get("image_file_path"):
            is_valid, error = self.validator.validate_image_file(
                state["image_file_path"]
            )
            if not is_valid:
                logger.error(f"Invalid image file: {error}")
                state["final_response"] = f"Error: {error}"
                state["routing_decision"] = "error"
                return state
        
        if state.get("audio_file_path"):
            is_valid, error = self.validator.validate_audio_file(
                state["audio_file_path"]
            )
            if not is_valid:
                logger.error(f"Invalid audio file: {error}")
                state["final_response"] = f"Error: {error}"
                state["routing_decision"] = "error"
                return state
        
        # Set routing decision
        if input_type == "speech":
            state["routing_decision"] = "process_speech"
        elif input_type == "image":
            state["routing_decision"] = "process_image"
        elif input_type == "multimodal":
            # Process speech first if present, then image
            if state.get("audio_file_path"):
                state["routing_decision"] = "process_speech"
            else:
                state["routing_decision"] = "process_image"
        else:
            # Direct to reasoning for text-only
            state["routing_decision"] = "reasoning"
        
        logger.info(f"Routing decision: {state['routing_decision']}")
        return state
    
    def process_speech(self, state: AgentState) -> AgentState:
        """
        Process audio input to text using speech-to-text tool.
        """
        logger.info("Node: process_speech")
        
        audio_path = state.get("audio_file_path")
        if not audio_path:
            logger.warning("No audio file path in state")
            state["routing_decision"] = "reasoning"
            return state
        
        try:
            # Call speech-to-text tool
            logger.info(f"Transcribing audio: {audio_path}")
            transcribed = self.speech_to_text._run(audio_path=audio_path)
            
            state["transcribed_text"] = transcribed
            state["tool_calls_completed"].append("speech_to_text")
            
            logger.info(f"Transcription completed: {len(transcribed)} characters")
            
            # After speech processing, check if image needs processing
            if state.get("image_file_path"):
                state["routing_decision"] = "process_image"
            else:
                state["routing_decision"] = "reasoning"
                
        except Exception as e:
            logger.error(f"Speech processing error: {e}", exc_info=True)
            state["transcribed_text"] = f"[Error transcribing audio: {str(e)}]"
            state["routing_decision"] = "reasoning"
        
        return state
    
    def process_image(self, state: AgentState) -> AgentState:
        """
        Process image input using image analyzer tool.
        """
        logger.info("Node: process_image")
        
        image_path = state.get("image_file_path")
        if not image_path:
            logger.warning("No image file path in state")
            state["routing_decision"] = "reasoning"
            return state
        
        try:
            # Call image analyzer tool
            logger.info(f"Analyzing image: {image_path}")
            result = self.image_analyzer._run(image_path=image_path)
            
            # Parse result (it's JSON string)
            import json
            analysis = json.loads(result)
            
            state["image_analysis_result"] = analysis
            state["tool_calls_completed"].append("analyze_skin_image")
            
            logger.info(
                f"Image analysis completed: {analysis.get('class_name')} "
                f"({analysis.get('confidence', 0):.1%})"
            )
            
            # Always go to reasoning after image processing
            state["routing_decision"] = "reasoning"
            
        except Exception as e:
            logger.error(f"Image processing error: {e}", exc_info=True)
            state["image_analysis_result"] = {"error": str(e)}
            state["routing_decision"] = "reasoning"
        
        return state
    
    def reasoning_node(self, state: AgentState) -> AgentState:
        """
        Main reasoning node using LLM to process user request.
        
        This node:
        1. Checks for emergencies
        2. Determines if tools are needed
        3. Generates response or requests tool use
        """
        logger.info("Node: reasoning_node")
        
        # Extract current user input
        user_input = extract_text_from_state(state)
        
        if not user_input:
            user_input = "Hello"  # Default for image-only inputs
        
        # Sanitize input
        user_input = self.guardrails.sanitize_input(user_input)
        
        # Emergency detection
        is_emergency, symptoms = self.guardrails.detect_emergency(user_input)
        if is_emergency:
            logger.warning(f"Emergency detected: {symptoms}")
            state["emergency_detected"] = True
            state["final_response"] = self.guardrails.generate_emergency_response(symptoms)
            state["routing_decision"] = "safety_check"
            return state
        
        # Build context for LLM
        context_parts = []
        
        # Add image analysis if available
        if state.get("image_analysis_result"):
            analysis = state["image_analysis_result"]
            if "error" not in analysis:
                context_parts.append(format_image_analysis_prompt(analysis))
        
        # Add RAG context if available
        if state.get("rag_context"):
            context_parts.append(format_rag_context_prompt(state["rag_context"]))
        
        # Determine if RAG is needed
        rag_keywords = [
            "my", "history", "record", "medication", "prescription",
            "visit", "test", "result", "doctor", "appointment",
            "vaccine", "allergy", "blood pressure", "lab"
        ]
        
        needs_rag = (
            not state.get("rag_context") and 
            any(keyword in user_input.lower() for keyword in rag_keywords)
        )
        
        if needs_rag and "patient_record_retriever" not in state.get("tool_calls_completed", []):
            # Request RAG retrieval
            logger.info("RAG retrieval needed")
            state["rag_needed"] = True
            state["requires_tool_call"] = True
            state["next_action"] = "retrieve_patient_records"
            state["routing_decision"] = "call_tool"
            return state
        
        # Build messages for LLM
        from .prompts import MASTER_SYSTEM_PROMPT
        
        patient_id = state.get("patient_id", "") 
        patient_context = f"""
        AUTHENTICATION STATUS: Patient is ALREADY logged in and verified.
        - Patient ID: {patient_id}
        - DO NOT ask for name, date of birth, or any identity verification
        - Use this patient_id directly when querying medical records
        - You already have full access to this patient's data
        """

        messages = [{"role": "system", "content": MASTER_SYSTEM_PROMPT + "\n\n" + patient_context}]
        
        # Add context
        if context_parts:
            messages.append({
                "role": "system",
                "content": "\n\n".join(context_parts)
            })
        """
        # Add conversation history
        for msg in state.get("messages", [])[-5:]:  # Last 5 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        """ 
        # Add conversation history
        for msg in state.get("messages", [])[-5:]:  # Last 5 messages
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                # LangChain message objects (HumanMessage, AIMessage, v.v.)
                from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
                if isinstance(msg, HumanMessage):
                    role = "user"
                elif isinstance(msg, AIMessage):
                    role = "assistant"
                elif isinstance(msg, SystemMessage):
                    role = "system"
                else:
                    role = "user"
                content = msg.content
            
            messages.append({"role": role, "content": content})
            
        # Add current user input
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Call LLM
        try:
            logger.info("Calling LLM for reasoning")
            from ollama import chat
            
            response = chat(
                model=self.config.model_name,
                messages=messages
            )
            
            agent_response = response.message.content
            logger.info(f"LLM response generated: {len(agent_response)} characters")
            
            # Store response
            state["final_response"] = agent_response
            state["routing_decision"] = "safety_check"
            
        except Exception as e:
            logger.error(f"LLM error: {e}", exc_info=True)
            state["final_response"] = (
                "I apologize, but I'm having trouble processing your request. "
                "Please try again or contact support if the issue persists."
            )
            state["routing_decision"] = "safety_check"
        
        return state
    
    def call_tool(self, state: AgentState) -> AgentState:
        """
        Execute tool calls based on agent's decision.
        """
        logger.info("Node: call_tool")
        
        next_action = state.get("next_action")
        
        if next_action == "retrieve_patient_records":
            return self._retrieve_patient_records(state)
        else:
            logger.warning(f"Unknown tool action: {next_action}")
            state["routing_decision"] = "reasoning"
            return state
    
    def _retrieve_patient_records(self, state: AgentState) -> AgentState:
        """Retrieve patient records using RAG"""
        logger.info("Retrieving patient records")
        
        patient_id = state["patient_id"]
        query = extract_text_from_state(state)
        
        try:
            result = self.patient_record._run(
                patient_id=patient_id,
                query=query,
                top_k=self.config.rag_top_k
            )
            
            state["rag_context"] = result
            state["tool_calls_completed"].append("patient_record_retriever")
            state["rag_needed"] = False
            
            logger.info(f"Retrieved {len(result.get('sources', []))} records")
            
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}", exc_info=True)
            state["rag_context"] = {
                "context": f"Error retrieving records: {str(e)}",
                "sources": []
            }
        
        # Return to reasoning with context
        state["routing_decision"] = "reasoning"
        return state
    
    def safety_check(self, state: AgentState) -> AgentState:
        """
        Final safety check before returning response to user.
        """
        logger.info("Node: safety_check")
        
        response = state.get("final_response", "")
        
        # Validate response
        is_valid, violations = self.guardrails.validate_response(response)
        
        if not is_valid:
            logger.error(f"Response validation failed: {violations}")
            # Sanitize response
            response = (
                "I apologize, but I need to rephrase my response to ensure "
                "it follows medical guidance protocols. Please rephrase your "
                "question and I'll provide appropriate information."
            )
        
        # Check privacy
        privacy_ok = self.guardrails.validate_patient_privacy(
            response,
            state["patient_id"]
        )
        
        if not privacy_ok:
            logger.error("Privacy violation detected in response")
            response = (
                "I apologize, but I cannot provide that information due to "
                "privacy concerns. Please contact your healthcare provider directly."
            )
        
        # Add medical disclaimer
        # response = self.guardrails.add_medical_disclaimer(response)
        
        # Clean response
        response = clean_response(response)
        
        state["final_response"] = response
        state["safety_check_passed"] = True
        state["routing_decision"] = "end"
        
        logger.info("Safety check passed")
        return state
    
    def error_handler(self, state: AgentState) -> AgentState:
        """
        Handle errors in the workflow.
        """
        logger.error("Node: error_handler")
        
        state["final_response"] = (
            "I apologize, but an error occurred while processing your request. "
            "Please try again or contact support if the issue persists."
        )
        state["routing_decision"] = "end"
        
        return state