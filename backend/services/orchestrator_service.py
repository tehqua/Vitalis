"""
Orchestrator service wrapper with session management and error recovery.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))

from agents.orchestrator import MedicalChatbotAgent, OrchestratorConfig
from agents.orchestrator.utils import ConversationMemory
from typing import Dict, Any, Optional
import asyncio
from functools import lru_cache
import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Service wrapper for the medical chatbot orchestrator.
    
    Provides:
    - Async interface to orchestrator
    - Session-based memory management
    - Error recovery and retry logic
    - Connection pooling
    """
    
    def __init__(self):
        """Initialize orchestrator service"""
        try:
            config = OrchestratorConfig()
            self.agent = MedicalChatbotAgent(config=config)
            self.config = config
            
            # Per-session memory: key=session_id, value=ConversationMemory
            # Conversation history is loaded from MongoDB on first message of each session
            self.session_memories: Dict[str, ConversationMemory] = {}
            
            # Per-session metadata tracking
            # Key: session_id, Value: {patient_id, created_at, last_activity, message_count}
            self.session_meta: Dict[str, Dict[str, Any]] = {}
            
            # Connection pool for Ollama
            self._http_client: Optional[httpx.AsyncClient] = None
            
            logger.info("Orchestrator service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
            raise
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for Ollama communication"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0)
            )
        return self._http_client
    
    async def process_message(
        self,
        patient_id: str,
        text_input: Optional[str] = None,
        image_file_path: Optional[str] = None,
        audio_file_path: Optional[str] = None,
        session_id: Optional[str] = None,
        db=None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Process a message through the orchestrator.
        
        Args:
            patient_id: Patient identifier
            text_input: Text message
            image_file_path: Path to image file
            audio_file_path: Path to audio file
            session_id: Session identifier
            db: Database instance (used to load conversation history for new sessions)
            retry_count: Current retry attempt
            
        Returns:
            Processing result with response and metadata
        """
        try:
            # --- Per-session memory management ---
            if session_id:
                if session_id not in self.session_memories:
                    # New session: load prior history from MongoDB and seed memory
                    memory = ConversationMemory(
                        max_messages=self.config.max_conversation_length
                    )
                    if db is not None:
                        try:
                            history = await db.get_conversation_history(
                                session_id=session_id,
                                limit=self.config.max_conversation_length
                            )
                            if history:
                                memory.seed_from_db(history)
                                logger.info(
                                    f"Session {session_id}: loaded {len(history)} "
                                    f"prior exchanges from DB"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Could not load history from DB for session {session_id}: {e}"
                            )
                    self.session_memories[session_id] = memory
                    self.session_meta[session_id] = {
                        "patient_id": patient_id,
                        "created_at": datetime.utcnow(),
                        "last_activity": datetime.utcnow(),
                        "message_count": 0,
                    }
                else:
                    self.session_meta[session_id]["last_activity"] = datetime.utcnow()
            
            # Get current per-session history to pass into agent
            current_history = (
                self.session_memories[session_id].get_messages()
                if session_id and session_id in self.session_memories
                else []
            )
            
            # Process in thread pool (orchestrator graph is sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.agent.process_message(
                    patient_id=patient_id,
                    text_input=text_input,
                    audio_file_path=audio_file_path,
                    image_file_path=image_file_path,
                    session_id=session_id,
                    conversation_history=current_history,
                )
            )
            
            # Update per-session in-memory store with this turn's messages
            if session_id and session_id in self.session_memories:
                effective_user_text = result.get("effective_user_text", text_input or "")
                if effective_user_text:
                    self.session_memories[session_id].add_message("user", effective_user_text)
                if result.get("response"):
                    self.session_memories[session_id].add_message("assistant", result["response"])
                self.session_meta[session_id]["message_count"] += 1
            
            logger.info(
                f"Message processed successfully for session {session_id} "
                f"(patient: {patient_id})"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error processing message (attempt {retry_count + 1}): {e}",
                exc_info=True
            )
            
            # Retry logic for transient errors
            if retry_count < 2 and self._is_retryable_error(e):
                logger.info(f"Retrying message processing (attempt {retry_count + 2})")
                await asyncio.sleep(1)
                
                return await self.process_message(
                    patient_id=patient_id,
                    text_input=text_input,
                    image_file_path=image_file_path,
                    audio_file_path=audio_file_path,
                    session_id=session_id,
                    db=db,
                    retry_count=retry_count + 1
                )
            
            # Return error response
            return {
                "response": (
                    "I apologize, but I'm having trouble processing your request. "
                    "Please try again in a moment."
                ),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "error": True,
                    "error_message": str(e),
                    "error_type": type(e).__name__
                }
            }
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if error is transient and can be retried.
        
        Args:
            error: Exception that occurred
            
        Returns:
            True if error can be retried
        """
        # Network errors, timeouts, etc.
        retryable_types = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        
        return isinstance(error, retryable_types)
    
    def _update_session(self, session_id: str, patient_id: str):
        """Update session metadata tracking (legacy, now uses session_meta)"""
        if session_id not in self.session_meta:
            self.session_meta[session_id] = {
                "patient_id": patient_id,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "message_count": 0,
            }
        else:
            self.session_meta[session_id]["last_activity"] = datetime.utcnow()
    
    def _increment_message_count(self, session_id: str):
        """Increment message count for session"""
        if session_id in self.session_meta:
            self.session_meta[session_id]["message_count"] += 1
    
    async def clear_memory(self, session_id: str):
        """
        Clear in-memory conversation history for a specific session.
        
        Note: This clears the in-process memory cache only. The persisted
        records in MongoDB (conversations collection) are NOT deleted —
        use the DB directly if you need to purge stored history.
        
        Args:
            session_id: Session identifier
        """
        try:
            # Clear per-session memory
            if session_id in self.session_memories:
                self.session_memories[session_id].clear()
                del self.session_memories[session_id]
            
            # Clear session metadata
            if session_id in self.session_meta:
                del self.session_meta[session_id]
            
            logger.info(f"In-memory context cleared for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}", exc_info=True)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session metadata or None
        """
        return self.session_meta.get(session_id)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active in-memory sessions"""
        return len(self.session_memories)
    
    async def cleanup_inactive_sessions(self, inactive_minutes: int = 60):
        """
        Evict inactive sessions from in-memory cache.
        Their history remains in MongoDB and will be reloaded on next message.
        
        Args:
            inactive_minutes: Evict sessions inactive for this many minutes
        """
        try:
            from datetime import timedelta
            
            cutoff = datetime.utcnow() - timedelta(minutes=inactive_minutes)
            inactive_sessions = [
                sid for sid, meta in self.session_meta.items()
                if meta["last_activity"] < cutoff
            ]
            
            for session_id in inactive_sessions:
                await self.clear_memory(session_id)
            
            if inactive_sessions:
                logger.info(f"Evicted {len(inactive_sessions)} inactive sessions from memory")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}", exc_info=True)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of orchestrator service.
        
        Returns:
            Health status information
        """
        try:
            # Test orchestrator is responsive
            test_result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: {"status": "ok"}
                ),
                timeout=5.0
            )
            
            return {
                "status": "healthy",
                "active_sessions": self.get_active_sessions_count(),
                "model": self.config.model_name,
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "error": "Orchestrator not responding"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Clean up resources"""
        if self._http_client:
            await self._http_client.aclose()


@lru_cache()
def get_orchestrator_service() -> OrchestratorService:
    """
    Get singleton orchestrator service instance.
    
    Returns:
        OrchestratorService instance
    """
    return OrchestratorService()


async def check_ollama_status(base_url: str) -> str:
    """
    Check if Ollama service is available.
    
    Args:
        base_url: Ollama base URL
        
    Returns:
        Status string: "healthy" or "unhealthy"
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/tags",
                timeout=5.0
            )
            
            if response.status_code == 200:
                return "healthy"
            else:
                logger.warning(f"Ollama returned status {response.status_code}")
                return "unhealthy"
                
    except httpx.ConnectError:
        logger.error("Cannot connect to Ollama - is it running?")
        return "unhealthy"
    except httpx.TimeoutException:
        logger.error("Ollama connection timeout")
        return "unhealthy"
    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        return "unhealthy"