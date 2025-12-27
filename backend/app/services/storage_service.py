"""
Storage Service
Handles file uploads to Supabase Storage for interview audio
"""

from uuid import UUID
from typing import Optional
from datetime import datetime
from app.database import db
from app.config import settings
import structlog

logger = structlog.get_logger()


class StorageService:
    """Service for managing file storage in Supabase Storage"""
    
    @staticmethod
    async def upload_interview_audio(
        interview_id: UUID,
        audio_bytes: bytes,
        file_extension: str = "webm"
    ) -> str:
        """
        Upload full interview audio recording to Supabase Storage
        
        Args:
            interview_id: Interview ID
            audio_bytes: Audio file bytes
            file_extension: File extension (webm, mp3, wav, etc.)
        
        Returns:
            Storage path (relative to bucket)
        
        Raises:
            ValueError: If upload fails
        """
        try:
            bucket_name = settings.supabase_storage_bucket_audio
            
            # Create storage path: interviews/{interview_id}/full_audio.{ext}
            storage_path = f"interviews/{interview_id}/full_audio.{file_extension}"
            
            # Determine content type
            content_type_map = {
                "webm": "audio/webm",
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "m4a": "audio/mp4",
                "ogg": "audio/ogg",
            }
            content_type = content_type_map.get(file_extension.lower(), "audio/webm")
            
            logger.info(
                "Uploading interview audio to storage",
                interview_id=str(interview_id),
                storage_path=storage_path,
                audio_size=len(audio_bytes),
                bucket=bucket_name
            )
            
            # Upload to Supabase Storage
            db.service_client.storage.from_(bucket_name).upload(
                storage_path,
                audio_bytes,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            
            logger.info(
                "Interview audio uploaded successfully",
                interview_id=str(interview_id),
                storage_path=storage_path
            )
            
            return storage_path
            
        except Exception as e:
            error_str = str(e)
            logger.error(
                "Failed to upload interview audio",
                interview_id=str(interview_id),
                error=error_str,
                exc_info=True
            )
            
            # Handle specific errors
            if "bucket not found" in error_str.lower() or "404" in error_str:
                raise ValueError(
                    f"Storage bucket '{bucket_name}' not found. "
                    "Please create the bucket in Supabase Storage."
                )
            elif "409" in error_str or "duplicate" in error_str.lower():
                # File already exists, return existing path
                logger.info("Audio file already exists, using existing", storage_path=storage_path)
                return storage_path
            else:
                raise ValueError(f"Failed to upload interview audio: {error_str}")
    
    @staticmethod
    async def upload_response_audio(
        interview_id: UUID,
        question_id: UUID,
        audio_bytes: bytes,
        response_index: int = 1,
        file_extension: str = "webm"
    ) -> str:
        """
        Upload individual response audio clip to Supabase Storage
        
        Args:
            interview_id: Interview ID
            question_id: Question ID
            audio_bytes: Audio file bytes
            response_index: Index of response (for multiple responses to same question)
            file_extension: File extension (webm, mp3, wav, etc.)
        
        Returns:
            Storage path (relative to bucket)
        
        Raises:
            ValueError: If upload fails
        """
        try:
            bucket_name = settings.supabase_storage_bucket_audio
            
            # Create storage path: interviews/{interview_id}/responses/{question_id}_{index}.{ext}
            storage_path = f"interviews/{interview_id}/responses/{question_id}_{response_index}.{file_extension}"
            
            # Determine content type
            content_type_map = {
                "webm": "audio/webm",
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "m4a": "audio/mp4",
                "ogg": "audio/ogg",
            }
            content_type = content_type_map.get(file_extension.lower(), "audio/webm")
            
            logger.info(
                "Uploading response audio to storage",
                interview_id=str(interview_id),
                question_id=str(question_id),
                storage_path=storage_path,
                audio_size=len(audio_bytes),
                bucket=bucket_name
            )
            
            # Upload to Supabase Storage
            db.service_client.storage.from_(bucket_name).upload(
                storage_path,
                audio_bytes,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            
            logger.info(
                "Response audio uploaded successfully",
                interview_id=str(interview_id),
                question_id=str(question_id),
                storage_path=storage_path
            )
            
            return storage_path
            
        except Exception as e:
            error_str = str(e)
            logger.error(
                "Failed to upload response audio",
                interview_id=str(interview_id),
                question_id=str(question_id),
                error=error_str,
                exc_info=True
            )
            
            # Handle specific errors
            if "bucket not found" in error_str.lower() or "404" in error_str:
                raise ValueError(
                    f"Storage bucket '{bucket_name}' not found. "
                    "Please create the bucket in Supabase Storage."
                )
            elif "409" in error_str or "duplicate" in error_str.lower():
                # File already exists, return existing path
                logger.info("Audio file already exists, using existing", storage_path=storage_path)
                return storage_path
            else:
                raise ValueError(f"Failed to upload response audio: {error_str}")
    
    @staticmethod
    def get_audio_url(storage_path: str) -> str:
        """
        Get public URL for audio file in Supabase Storage
        
        Args:
            storage_path: Storage path (relative to bucket)
        
        Returns:
            Public URL for the audio file
        """
        bucket_name = settings.supabase_storage_bucket_audio
        return db.service_client.storage.from_(bucket_name).get_public_url(storage_path)
    
    @staticmethod
    async def delete_interview_audio(interview_id: UUID) -> bool:
        """
        Delete all audio files for an interview
        
        Args:
            interview_id: Interview ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            bucket_name = settings.supabase_storage_bucket_audio
            
            # Delete all files in the interview directory
            prefix = f"interviews/{interview_id}/"
            
            # List files in the directory
            files = db.service_client.storage.from_(bucket_name).list(prefix)
            
            if files:
                # Extract file paths
                file_paths = [f"{prefix}{file['name']}" for file in files if file.get('name')]
                
                if file_paths:
                    # Delete all files
                    db.service_client.storage.from_(bucket_name).remove(file_paths)
                    logger.info(
                        "Deleted interview audio files",
                        interview_id=str(interview_id),
                        file_count=len(file_paths)
                    )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete interview audio",
                interview_id=str(interview_id),
                error=str(e),
                exc_info=True
            )
            return False

