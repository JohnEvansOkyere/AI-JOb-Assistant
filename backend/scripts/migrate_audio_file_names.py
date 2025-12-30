"""
Migration Script: Rename Audio Files with Candidate Names and Question Numbers

This script migrates existing audio files to use the new naming format:
Old: interviews/{interview_id}/responses/{question_id}_1.webm
New: interviews/{interview_id}/responses/Q{order_index}_{candidate_name_sanitized}_{question_id_short}.webm

Usage:
    python scripts/migrate_audio_file_names.py

Note: This script requires environment variables to be set (from .env file)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import UUID
from app.database import db
from app.config import settings
from app.services.storage_service import StorageService
import structlog

logger = structlog.get_logger()


def sanitize_filename(name: str) -> str:
    """Sanitize a name for use in file paths"""
    import re
    name = name.replace(' ', '_')
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    return name[:50] if len(name) > 50 else name


async def migrate_audio_files():
    """Migrate all audio files to use new naming format"""
    try:
        bucket_name = settings.supabase_storage_bucket_audio
        
        # Get all interviews with responses that have audio paths
        logger.info("Fetching interviews with audio responses...")
        
        interviews_response = (
            db.service_client.table("interviews")
            .select("id, candidate_id")
            .execute()
        )
        
        if not interviews_response.data:
            logger.info("No interviews found")
            return
        
        total_renamed = 0
        total_errors = 0
        
        for interview in interviews_response.data:
            interview_id = interview["id"]
            candidate_id = interview["candidate_id"]
            
            # Get candidate name
            candidate_response = (
                db.service_client.table("candidates")
                .select("full_name")
                .eq("id", str(candidate_id))
                .execute()
            )
            
            if not candidate_response.data:
                logger.warning(f"Candidate not found for interview {interview_id}")
                continue
            
            candidate_name = candidate_response.data[0].get("full_name")
            if not candidate_name:
                logger.warning(f"Candidate name not found for interview {interview_id}")
                continue
            
            sanitized_name = sanitize_filename(candidate_name)
            
            # Get all responses with audio paths for this interview, ordered by created_at
            responses_response = (
                db.service_client.table("interview_responses")
                .select("id, question_id, response_audio_path, created_at")
                .eq("interview_id", str(interview_id))
                .not_.is_("response_audio_path", "null")
                .order("created_at")
                .execute()
            )
            
            if not responses_response.data:
                continue
            
            # Get questions with order_index
            questions_response = (
                db.service_client.table("interview_questions")
                .select("id, order_index")
                .eq("interview_id", str(interview_id))
                .execute()
            )
            
            questions_map = {q["id"]: q.get("order_index", 0) for q in (questions_response.data or [])}
            
            # Track response count per question to handle duplicates
            question_response_count = {}
            
            # Process each response
            for response in responses_response.data:
                question_id = response["question_id"]
                old_path = response["response_audio_path"]
                
                # Skip if already using new format (contains Q{number}_)
                if old_path and "/responses/Q" in old_path:
                    logger.info(f"Skipping already migrated file: {old_path}")
                    continue
                
                # Get question order index
                order_index = questions_map.get(question_id, 0)
                question_order = order_index + 1  # 1-based
                question_id_short = str(question_id)[:8]
                
                # Track multiple responses to same question
                if question_id not in question_response_count:
                    question_response_count[question_id] = 0
                question_response_count[question_id] += 1
                response_index = question_response_count[question_id]
                
                # Determine file extension from old path
                file_extension = "webm"
                if old_path:
                    parts = old_path.split(".")
                    if len(parts) > 1:
                        file_extension = parts[-1]
                
                # Create new path (include response_index if multiple responses to same question)
                if response_index > 1:
                    new_path = f"interviews/{interview_id}/responses/Q{question_order}_{sanitized_name}_{question_id_short}_{response_index}.{file_extension}"
                else:
                    new_path = f"interviews/{interview_id}/responses/Q{question_order}_{sanitized_name}_{question_id_short}.{file_extension}"
                
                try:
                    # Check if old file exists
                    try:
                        old_file = db.service_client.storage.from_(bucket_name).list(old_path.split("/")[:-1], {"limit": 1000})
                        # Note: Supabase storage list returns files in the directory, we need to check if file exists
                        # For now, we'll try to copy/rename
                    except Exception:
                        pass
                    
                    # Try to copy file (Supabase storage doesn't have rename, so we copy then delete)
                    # First, download the old file
                    try:
                        old_file_data = db.service_client.storage.from_(bucket_name).download(old_path)
                        
                        # Upload with new path
                        db.service_client.storage.from_(bucket_name).upload(
                            new_path,
                            old_file_data,
                            file_options={"content-type": "audio/webm", "upsert": "true"}
                        )
                        
                        # Delete old file
                        try:
                            db.service_client.storage.from_(bucket_name).remove([old_path])
                        except Exception as delete_err:
                            logger.warning(f"Failed to delete old file {old_path}: {delete_err}")
                        
                        # Update database record
                        db.service_client.table("interview_responses").update({
                            "response_audio_path": new_path
                        }).eq("id", response["id"]).execute()
                        
                        logger.info(f"Migrated: {old_path} -> {new_path}")
                        total_renamed += 1
                    except Exception as copy_err:
                        logger.error(f"Failed to migrate {old_path}: {copy_err}")
                        total_errors += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {old_path}: {e}")
                    total_errors += 1
        
        logger.info(f"Migration complete! Renamed: {total_renamed}, Errors: {total_errors}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("Starting audio file name migration...")
    print("This will rename existing audio files to include candidate names and question numbers.")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    asyncio.run(migrate_audio_files())

