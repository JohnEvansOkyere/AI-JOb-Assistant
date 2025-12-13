#!/usr/bin/env python3
"""
Test Database Connection
Simple script to verify Supabase connection
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import db
from app.config import settings

def test_connection():
    """Test Supabase database connection"""
    try:
        print(f"Testing connection to: {settings.supabase_url}")
        
        # Try a simple query
        response = db.client.table('users').select('id').limit(1).execute()
        
        print("✅ Database connection successful!")
        print(f"Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
    test_connection()

