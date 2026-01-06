#!/usr/bin/env python3
"""
Migration script to move tables to separate schemas
Run this ONCE to migrate your Railway database
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not found in environment")
    print("Please set DATABASE_URL in .env.local file")
    sys.exit(1)

print(f"🔌 Connecting to database...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Use autocommit mode to avoid transaction rollback issues
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        
        print("\n📊 Step 1: Creating schemas...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS macro_indicators"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS linus_playlists"))
        print("✅ Schemas created")
        
        print("\n📦 Step 2: Moving macro-indicators-app tables...")
        macro_tables = ['categories', 'indicators', 'data_points']
        for table in macro_tables:
            try:
                conn.execute(text(f"ALTER TABLE public.{table} SET SCHEMA macro_indicators"))
                print(f"  ✅ Moved {table}")
            except Exception as e:
                print(f"  ⚠️  {table}: {e}")
        
        print("\n📦 Step 3: Moving linusplaylists tables (if they exist)...")
        linus_tables = [
            'users', 'playlists', 'songs', 'artists', 'play_history',
            'user_favorite_songs', 'user_favorite_teams', 'user_favorite_artists',
            'user_playlists', 'user_playlist_songs', 'playlist_songs',
            'notifications', 'notification_preferences', 'entertainment',
            'highlights', 'matches', 'leagues', 'fetched_dates'
        ]
        for table in linus_tables:
            try:
                conn.execute(text(f"ALTER TABLE public.{table} SET SCHEMA linus_playlists"))
                print(f"  ✅ Moved {table}")
            except Exception as e:
                print(f"  ⚠️  {table}: (skipped - may not exist or already moved)")
        
        print("\n✅ Migration completed successfully!")
        
        print("\n📋 Verification:")
        print("\nMacro Indicators schema:")
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'macro_indicators' 
            ORDER BY table_name
        """))
        for row in result:
            print(f"  - {row[0]}")
        
        print("\nLinus Playlists schema:")
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'linus_playlists' 
            ORDER BY table_name
        """))
        for row in result:
            print(f"  - {row[0]}")
        
        print("\nPublic schema (should be empty):")
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        public_tables = [row[0] for row in result]
        if public_tables:
            print(f"  ⚠️  Still has tables: {', '.join(public_tables)}")
        else:
            print("  ✅ Empty (good!)")
            
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    sys.exit(1)
finally:
    engine.dispose()

print("\n🎉 All done! Your tables are now organized in separate schemas.")
print("\n⚠️  IMPORTANT: Deploy the updated code to Railway:")
print("   - models.py has been updated with schema definitions")
print("   - Commit and push changes to trigger Railway deployment")
