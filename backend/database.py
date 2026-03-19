"""
Database connection and operations.

Supports MongoDB for conversation storage, session management,
and GridFS for binary file (image/audio) storage.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pymongo.errors import ConnectionFailure
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.fs: Optional[AsyncIOMotorGridFSBucket] = None  # GridFS for binary file storage
        
    async def connect(self, database_url: str, database_name: str):
        """
        Connect to MongoDB.
        
        Args:
            database_url: MongoDB connection string
            database_name: Database name
        """
        try:
            self.client = AsyncIOMotorClient(database_url)
            self.db = self.client[database_name]
            
            # GridFS bucket for binary file storage (images, audio)
            self.fs = AsyncIOMotorGridFSBucket(self.db, bucket_name="uploads_fs")
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        # Conversations collection
        await self.db.conversations.create_index("session_id")
        await self.db.conversations.create_index("patient_id")
        await self.db.conversations.create_index("created_at")
        
        # Sessions collection
        await self.db.sessions.create_index("session_id", unique=True)
        await self.db.sessions.create_index("patient_id")
        await self.db.sessions.create_index("expires_at")
        
        # Uploads collection
        await self.db.uploads.create_index("file_id", unique=True)
        await self.db.uploads.create_index("patient_id")
        await self.db.uploads.create_index("session_id")
        await self.db.uploads.create_index("uploaded_at")
        
        logger.info("Database indexes created")
    
    # Conversation operations
    
    async def save_conversation(
        self,
        session_id: str,
        patient_id: str,
        message: str,
        response: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save a conversation exchange.
        
        Args:
            session_id: Session identifier
            patient_id: Patient identifier
            message: User message
            response: Agent response
            metadata: Additional metadata
            
        Returns:
            Conversation ID
        """
        conversation = {
            "session_id": session_id,
            "patient_id": patient_id,
            "message": message,
            "response": response,
            "metadata": metadata,
            "created_at": datetime.utcnow(),
        }
        
        result = await self.db.conversations.insert_one(conversation)
        return str(result.inserted_id)
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages
            
        Returns:
            List of conversation exchanges
        """
        cursor = self.db.conversations.find(
            {"session_id": session_id}
        ).sort("created_at", -1).limit(limit)
        
        conversations = await cursor.to_list(length=limit)
        
        # Reverse to get chronological order
        conversations.reverse()
        
        return conversations
    
    async def get_patient_conversations(
        self,
        patient_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations for a patient.
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of conversations
            
        Returns:
            List of conversations
        """
        cursor = self.db.conversations.find(
            {"patient_id": patient_id}
        ).sort("created_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    # Session operations
    
    async def create_session(
        self,
        session_id: str,
        patient_id: str,
        expires_in_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            session_id: Session identifier
            patient_id: Patient identifier
            expires_in_minutes: Session expiry time
            
        Returns:
            Session document
        """
        session = {
            "session_id": session_id,
            "patient_id": patient_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            "active": True,
        }
        
        await self.db.sessions.insert_one(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session document or None
        """
        session = await self.db.sessions.find_one({"session_id": session_id})
        
        if session and session.get("expires_at") < datetime.utcnow():
            # Session expired
            await self.invalidate_session(session_id)
            return None
        
        return session
    
    async def invalidate_session(self, session_id: str):
        """
        Invalidate a session.
        
        Args:
            session_id: Session identifier
        """
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"active": False}}
        )
    
    async def extend_session(self, session_id: str, minutes: int = 30):
        """
        Extend session expiry time.
        
        Args:
            session_id: Session identifier
            minutes: Additional minutes
        """
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"expires_at": datetime.utcnow() + timedelta(minutes=minutes)}}
        )
    
    async def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        result = await self.db.sessions.delete_many(
            {"expires_at": {"$lt": datetime.utcnow()}}
        )
        logger.info(f"Cleaned up {result.deleted_count} expired sessions")
    
    # ------------------------------------------------------------------ #
    # Upload operations                                                    #
    # ------------------------------------------------------------------ #
    
    async def save_upload(
        self,
        patient_id: str,
        session_id: str,
        filename: str,
        file_content: bytes,
        file_type: str,
        size_bytes: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Save an uploaded file to GridFS and record its metadata.
        
        The binary content is stored in MongoDB GridFS (uploads_fs.files /
        uploads_fs.chunks) and a lightweight metadata document is inserted
        into the `uploads` collection for fast lookup.
        
        Args:
            patient_id: Owner patient identifier
            session_id: Session during which the file was uploaded
            filename: Original filename
            file_content: Raw file bytes
            file_type: 'image' or 'audio'
            size_bytes: File size in bytes
            content_type: MIME type
            
        Returns:
            Stable UUID file_id that maps to the GridFS entry
        """
        file_id = str(uuid.uuid4())
        
        # Write binary content to GridFS
        gridfs_id = await self.fs.upload_from_stream(
            filename,
            file_content,
            metadata={
                "file_id": file_id,
                "patient_id": patient_id,
                "file_type": file_type,
                "content_type": content_type,
            }
        )
        
        # Save lightweight metadata document for fast query
        upload_doc = {
            "file_id": file_id,
            "gridfs_id": gridfs_id,          # ObjectId of the GridFS file
            "patient_id": patient_id,
            "session_id": session_id,
            "filename": filename,
            "file_type": file_type,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "uploaded_at": datetime.utcnow(),
        }
        await self.db.uploads.insert_one(upload_doc)
        logger.info(
            f"Upload saved to GridFS: file_id={file_id} "
            f"gridfs_id={gridfs_id} ({file_type}) patient={patient_id}"
        )
        return file_id
    
    async def get_upload_file_stream(self, file_id: str):
        """
        Open a GridFS download stream for the given file_id.
        
        Returns a (stream, metadata_doc) tuple. The caller is responsible
        for reading and closing the stream. Returns (None, None) if not found.
        
        Args:
            file_id: UUID file identifier
            
        Returns:
            Tuple[GridOut stream | None, metadata dict | None]
        """
        doc = await self.db.uploads.find_one({"file_id": file_id})
        if not doc:
            return None, None
        
        stream = await self.fs.open_download_stream(doc["gridfs_id"])
        return stream, doc
    
    async def get_upload(
        self,
        file_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get upload metadata by file_id (does not return binary content).
        
        Args:
            file_id: File UUID identifier
            
        Returns:
            Upload metadata document or None if not found
        """
        doc = await self.db.uploads.find_one({"file_id": file_id})
        return doc
    
    async def get_patient_uploads(
        self,
        patient_id: str,
        file_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all upload metadata records for a patient.
        
        Args:
            patient_id: Patient identifier
            file_type: Optional filter ('image' or 'audio')
            limit: Maximum number of records to return
            
        Returns:
            List of upload metadata documents (newest first)
        """
        query: Dict[str, Any] = {"patient_id": patient_id}
        if file_type:
            query["file_type"] = file_type
        cursor = self.db.uploads.find(query).sort("uploaded_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def delete_upload(
        self,
        file_id: str,
        patient_id: str,
    ) -> bool:
        """
        Delete a file from GridFS and its metadata record.
        Ownership is verified via patient_id.
        
        Args:
            file_id: File UUID identifier
            patient_id: Patient making the request (must own the file)
            
        Returns:
            True if deleted, False if not found or not owned by patient
        """
        doc = await self.db.uploads.find_one(
            {"file_id": file_id, "patient_id": patient_id}
        )
        if not doc:
            logger.warning(
                f"Delete failed for file_id={file_id}: not found or not owned by {patient_id}"
            )
            return False
        
        # Delete binary from GridFS
        gridfs_id = doc.get("gridfs_id")
        if gridfs_id:
            try:
                await self.fs.delete(gridfs_id)
            except Exception as e:
                logger.warning(f"GridFS delete error for {gridfs_id}: {e}")
        
        # Delete metadata document
        await self.db.uploads.delete_one({"file_id": file_id})
        logger.info(f"Upload deleted: file_id={file_id} gridfs_id={gridfs_id}")
        return True
    
    # ------------------------------------------------------------------ #
    # Session-based history                                                #
    # ------------------------------------------------------------------ #
    
    async def get_patient_sessions(
        self,
        patient_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Return a summary list of chat sessions for a patient.
        
        Each item contains: session_id, first_message (as title),
        started_at, last_activity, message_count.
        Sessions are sorted newest first.
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summary dicts
        """
        pipeline = [
            {"$match": {"patient_id": patient_id}},
            {"$sort": {"created_at": 1}},
            {
                "$group": {
                    "_id": "$session_id",
                    "first_message": {"$first": "$message"},
                    "started_at":    {"$first": "$created_at"},
                    "last_activity": {"$last": "$created_at"},
                    "message_count": {"$sum": 1},
                }
            },
            {"$sort": {"last_activity": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "session_id":    "$_id",
                    "first_message": 1,
                    "started_at":    1,
                    "last_activity": 1,
                    "message_count": 1,
                }
            },
        ]
        sessions = await self.db.conversations.aggregate(pipeline).to_list(length=limit)
        return sessions


# Global database instance
db = Database()


async def init_db(settings):
    """Initialize database connection"""
    await db.connect(settings.DATABASE_URL, settings.DATABASE_NAME)


async def close_db():
    """Close database connection"""
    await db.disconnect()


def get_db() -> Database:
    """
    Dependency for getting database instance.
    
    Returns:
        Database instance
    """
    return db