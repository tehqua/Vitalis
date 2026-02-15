"""
Test suite for the Medical Chatbot Orchestrator.

Run tests with:
    python -m pytest tests/test_agent.py -v
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

import pytest
from agents.orchestrator import MedicalChatbotAgent, OrchestratorConfig, AgentState
from agents.orchestrator.guardrails import MedicalGuardrails, InputValidator


class TestGuardrails:
    """Test guardrails and safety checks"""
    
    def setup_method(self):
        """Setup for each test"""
        self.guardrails = MedicalGuardrails()
        self.validator = InputValidator()
    
    def test_emergency_detection_chest_pain(self):
        """Test emergency detection for chest pain"""
        text = "I have severe chest pain and can't breathe"
        is_emergency, symptoms = self.guardrails.detect_emergency(text)
        
        assert is_emergency is True
        assert len(symptoms) > 0
        assert any("chest pain" in s.lower() for s in symptoms)
    
    def test_emergency_detection_normal(self):
        """Test that normal messages don't trigger emergency"""
        text = "I have a small headache"
        is_emergency, symptoms = self.guardrails.detect_emergency(text)
        
        assert is_emergency is False
        assert len(symptoms) == 0
    
    def test_validate_response_prohibited_phrase(self):
        """Test response validation catches prohibited phrases"""
        response = "You definitely have cancer"
        is_valid, violations = self.guardrails.validate_response(response)
        
        assert is_valid is False
        assert len(violations) > 0
    
    def test_validate_response_safe(self):
        """Test that safe responses pass validation"""
        response = "Your symptoms may suggest a cold. Please consult your doctor."
        is_valid, violations = self.guardrails.validate_response(response)
        
        assert is_valid is True
        assert len(violations) == 0
    
    def test_add_disclaimer(self):
        """Test medical disclaimer is added"""
        response = "This is a test response"
        with_disclaimer = self.guardrails.add_medical_disclaimer(response)
        
        assert "MEDICAL DISCLAIMER" in with_disclaimer
        assert response in with_disclaimer
    
    def test_validate_patient_id_valid(self):
        """Test valid patient ID"""
        patient_id = "Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58"
        is_valid, error = self.validator.validate_patient_id(patient_id)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_patient_id_invalid(self):
        """Test invalid patient ID"""
        patient_id = "invalid_id"
        is_valid, error = self.validator.validate_patient_id(patient_id)
        
        assert is_valid is False
        assert error is not None


class TestInputRouting:
    """Test input routing logic"""
    
    def test_text_only_input(self):
        """Test routing for text-only input"""
        from agents.orchestrator.utils import determine_input_type
        
        input_type = determine_input_type(text_input="Hello doctor")
        assert input_type == "text"
    
    def test_speech_only_input(self):
        """Test routing for speech-only input"""
        from agents.orchestrator.utils import determine_input_type
        
        input_type = determine_input_type(audio_path="test.wav")
        assert input_type == "speech"
    
    def test_image_only_input(self):
        """Test routing for image-only input"""
        from agents.orchestrator.utils import determine_input_type
        
        input_type = determine_input_type(image_path="test.jpg")
        assert input_type == "image"
    
    def test_multimodal_input(self):
        """Test routing for multimodal input"""
        from agents.orchestrator.utils import determine_input_type
        
        input_type = determine_input_type(
            text_input="What is this?",
            image_path="test.jpg"
        )
        assert input_type == "multimodal"


class TestConversationMemory:
    """Test conversation memory management"""
    
    def test_add_message(self):
        """Test adding messages to memory"""
        from agents.orchestrator.utils import ConversationMemory
        
        memory = ConversationMemory(max_messages=5)
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there!")
        
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    
    def test_memory_truncation(self):
        """Test that memory is truncated at max length"""
        from agents.orchestrator.utils import ConversationMemory
        
        memory = ConversationMemory(max_messages=3)
        
        for i in range(5):
            memory.add_message("user", f"Message {i}")
        
        messages = memory.get_messages()
        assert len(messages) <= 3
    
    def test_clear_memory(self):
        """Test clearing memory"""
        from agents.orchestrator.utils import ConversationMemory
        
        memory = ConversationMemory()
        memory.add_message("user", "Test")
        memory.clear()
        
        assert len(memory.get_messages()) == 0


class TestAgentIntegration:
    """Integration tests for the full agent"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        config = OrchestratorConfig(
            enable_guardrails=True,
            enable_emergency_detection=True,
            require_medical_disclaimer=True,
        )
        
        # Note: This will fail if tools are not available
        # For unit testing, you might want to mock the tools
        try:
            agent = MedicalChatbotAgent(config=config)
            return agent
        except Exception as e:
            pytest.skip(f"Could not initialize agent: {e}")
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly"""
        assert agent is not None
        assert agent.graph is not None
        assert agent.memory is not None
    
    def test_simple_text_message(self, agent):
        """Test processing a simple text message"""
        result = agent.process_message(
            patient_id="Test123_Patient456_12345678-1234-1234-1234-123456789012",
            text_input="Hello, I have a question about my health"
        )
        
        assert "response" in result
        assert "session_id" in result
        assert result["response"] is not None
    
    def test_emergency_message(self, agent):
        """Test that emergency messages are handled correctly"""
        result = agent.process_message(
            patient_id="Test123_Patient456_12345678-1234-1234-1234-123456789012",
            text_input="I have severe chest pain and difficulty breathing"
        )
        
        assert "response" in result
        assert "emergency" in result["response"].lower() or "911" in result["response"]
    
    def test_conversation_memory(self, agent):
        """Test that conversation history is maintained"""
        patient_id = "Test123_Patient456_12345678-1234-1234-1234-123456789012"
        
        # Send first message
        agent.process_message(patient_id, "Hello")
        
        # Send second message
        agent.process_message(patient_id, "What is my name?")
        
        # Check memory
        history = agent.get_conversation_history()
        assert len(history) >= 2


class TestPrompts:
    """Test prompt formatting"""
    
    def test_image_analysis_prompt_formatting(self):
        """Test image analysis prompt formatting"""
        from agents.orchestrator.prompts import format_image_analysis_prompt
        
        analysis_result = {
            "class_name": "Fungal_Infections",
            "confidence": 0.587,
            "all_probabilities": {
                "Fungal_Infections": 0.587,
                "Eczema_Dermatitis": 0.087,
            }
        }
        
        prompt = format_image_analysis_prompt(analysis_result)
        
        assert "Fungal_Infections" in prompt
        assert "58.7%" in prompt
    
    def test_rag_context_prompt_formatting(self):
        """Test RAG context prompt formatting"""
        from agents.orchestrator.prompts import format_rag_context_prompt
        
        rag_result = {
            "context": "Patient has history of diabetes",
            "sources": []
        }
        
        prompt = format_rag_context_prompt(rag_result)
        
        assert "diabetes" in prompt


class TestUtils:
    """Test utility functions"""
    
    def test_create_message(self):
        """Test message creation"""
        from agents.orchestrator.utils import create_message
        
        msg = create_message("user", "Hello", {"key": "value"})
        
        assert msg["role"] == "user"
        assert msg["content"] == "Hello"
        assert msg["metadata"]["key"] == "value"
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        guardrails = MedicalGuardrails()
        
        dirty_input = "<script>alert('xss')</script>Hello"
        clean = guardrails.sanitize_input(dirty_input)
        
        assert "<script>" not in clean
        assert "Hello" in clean
    
    def test_extract_text_from_state(self):
        """Test text extraction from state"""
        from agents.orchestrator.utils import extract_text_from_state
        
        state = {
            "user_text_input": "Hello",
            "transcribed_text": "World"
        }
        
        text = extract_text_from_state(state)
        
        assert "Hello" in text
        assert "World" in text


def run_manual_test():
    """
    Manual test function for interactive testing.
    
    Run with: python -c "from tests.test_agent import run_manual_test; run_manual_test()"
    """
    print("Initializing agent...")
    
    config = OrchestratorConfig()
    agent = MedicalChatbotAgent(config=config)
    
    print("Agent initialized successfully!\n")
    
    # Test patient ID
    patient_id = "Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58"
    
    # Test cases
    test_cases = [
        "Hello, how are you?",
        "I have a headache for 2 days",
        "What medications am I currently taking?",
        "I have severe chest pain",  # Emergency test
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_input}")
        print("-" * 60)
        
        result = agent.process_message(
            patient_id=patient_id,
            text_input=test_input
        )
        
        print(f"Response: {result['response'][:200]}...")
        print(f"Tools used: {result['metadata'].get('tools_used', [])}")
        print(f"Emergency: {result['metadata'].get('emergency_detected', False)}")
        print("-" * 60)
    
    print("\nManual test completed!")


if __name__ == "__main__":
    # Run manual test if executed directly
    run_manual_test()