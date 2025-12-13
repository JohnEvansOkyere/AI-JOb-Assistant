"""
Database Connection and Client
Manages Supabase client and database operations
"""

from supabase import create_client, Client
from app.config import settings
import structlog

logger = structlog.get_logger()


class Database:
    """Database client wrapper for Supabase"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        self.service_client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        logger.info("Database client initialized")
    
    def get_client(self, use_service_key: bool = False) -> Client:
        """
        Get Supabase client
        
        Args:
            use_service_key: If True, returns client with service role key
                           (bypasses RLS). Use with caution.
        
        Returns:
            Supabase client instance
        """
        if use_service_key:
            return self.service_client
        return self.client


# Global database instance
db = Database()

