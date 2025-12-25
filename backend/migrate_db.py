#!/usr/bin/env python3
"""
Database migration script to add scrape_url and html_selector columns to indicators table
"""

import sys
import os
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load the local environment file
load_dotenv('.env.local')

from sqlalchemy import text
from app.database import engine
from app.models import Base

def migrate_database():
    """Add new columns to indicators table"""
    print("Starting database migration...")
    
    with engine.connect() as connection:
        try:
            # Check if columns already exist
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'indicators' AND column_name IN ('scrape_url', 'html_selector')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"Found existing columns: {existing_columns}")
            
            # Add scrape_url column if it doesn't exist
            if 'scrape_url' not in existing_columns:
                connection.execute(text("""
                    ALTER TABLE indicators 
                    ADD COLUMN scrape_url VARCHAR(500)
                """))
                print("✅ Added scrape_url column")
            else:
                print("⏭️  scrape_url column already exists")
            
            # Add html_selector column if it doesn't exist
            if 'html_selector' not in existing_columns:
                connection.execute(text("""
                    ALTER TABLE indicators 
                    ADD COLUMN html_selector VARCHAR(200)
                """))
                print("✅ Added html_selector column")
            else:
                print("⏭️  html_selector column already exists")
            
            # Commit the transaction
            connection.commit()
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            connection.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate_database()