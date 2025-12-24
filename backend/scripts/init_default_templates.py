#!/usr/bin/env python3
"""
Script to initialize default email templates for all existing recruiters
Run this after migration 014 to create default templates for existing users
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import db
from app.services.default_templates_service import DefaultTemplatesService
import structlog

logger = structlog.get_logger()


async def init_templates_for_all_recruiters():
    """Initialize default templates for all existing recruiters"""
    try:
        # Get all recruiters
        users_response = db.service_client.table("users").select("id, email").execute()
        
        if not users_response.data:
            print("No recruiters found in database")
            return
        
        users = users_response.data
        print(f"Found {len(users)} recruiter(s)")
        
        created_count = 0
        error_count = 0
        
        for user in users:
            user_id = user["id"]
            user_email = user.get("email", "unknown")
            
            try:
                templates = await DefaultTemplatesService.create_default_templates_for_recruiter(user_id)
                if templates:
                    created_count += len(templates)
                    print(f"✅ Created {len(templates)} default templates for {user_email}")
                else:
                    print(f"ℹ️  Templates already exist for {user_email}")
            except Exception as e:
                error_count += 1
                print(f"❌ Error creating templates for {user_email}: {e}")
                logger.error("Error creating default templates", user_id=user_id, error=str(e))
        
        print("\n" + "="*60)
        print(f"Summary:")
        print(f"  Total recruiters: {len(users)}")
        print(f"  Templates created: {created_count}")
        print(f"  Errors: {error_count}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error("Fatal error in init_default_templates", error=str(e))
        raise


if __name__ == "__main__":
    print("Initializing default email templates for all recruiters...")
    print("="*60)
    asyncio.run(init_templates_for_all_recruiters())

