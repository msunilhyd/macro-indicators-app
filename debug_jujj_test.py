#!/usr/bin/env python3
"""Debug script to check jujj-test indicator in production database"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Set the database URL
DATABASE_URL = "postgresql://postgres:wUXRJCcrvqKCaNLZaUiRDXEbsjdduujw@shinkansen.proxy.rlwy.net:49888/railway"

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.models import Category, Indicator, DataPoint
    from app.database import Base
    print("✅ Successfully imported models")
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    sys.exit(1)

def debug_jujj_test():
    print("🔍 Debugging jujj-test indicator...")
    print(f"📊 Connecting to: {DATABASE_URL.split('@')[1]}")
    
    # Create database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Check if jujj-test indicator exists
        print("\n1️⃣ Checking if jujj-test indicator exists:")
        jujj_test = db.query(Indicator).filter(Indicator.slug == "jujj-test").first()
        
        if not jujj_test:
            print("❌ jujj-test indicator not found!")
            return
        
        print(f"✅ Found jujj-test indicator:")
        print(f"   ID: {jujj_test.id}")
        print(f"   Name: {jujj_test.name}")
        print(f"   Slug: {jujj_test.slug}")
        print(f"   Category ID: {jujj_test.category_id}")
        print(f"   Created: {jujj_test.created_at}")
        
        # 2. Check the category
        print(f"\n2️⃣ Checking category for jujj-test:")
        category = db.query(Category).filter(Category.id == jujj_test.category_id).first()
        
        if category:
            print(f"✅ Category found:")
            print(f"   ID: {category.id}")
            print(f"   Name: {category.name}")
            print(f"   Slug: {category.slug}")
            print(f"   Display Order: {category.display_order}")
        else:
            print(f"❌ Category not found for ID: {jujj_test.category_id}")
            return
        
        # 3. Check data points
        print(f"\n3️⃣ Checking data points for jujj-test:")
        data_points = db.query(DataPoint).filter(DataPoint.indicator_id == jujj_test.id).count()
        print(f"✅ Found {data_points} data points")
        
        if data_points > 0:
            latest = db.query(DataPoint).filter(
                DataPoint.indicator_id == jujj_test.id
            ).order_by(DataPoint.date.desc()).first()
            
            earliest = db.query(DataPoint).filter(
                DataPoint.indicator_id == jujj_test.id
            ).order_by(DataPoint.date.asc()).first()
            
            print(f"   Latest: {latest.date} = {latest.value}")
            print(f"   Earliest: {earliest.date} = {earliest.value}")
        
        # 4. Check all indicators in Market Indexes category
        print(f"\n4️⃣ Checking all indicators in Market Indexes category:")
        market_indexes_category = db.query(Category).filter(Category.slug == "market-indexes").first()
        
        if market_indexes_category:
            indicators_in_category = db.query(Indicator).filter(
                Indicator.category_id == market_indexes_category.id
            ).all()
            
            print(f"✅ Found {len(indicators_in_category)} indicators in Market Indexes:")
            for ind in indicators_in_category:
                data_count = db.query(DataPoint).filter(DataPoint.indicator_id == ind.id).count()
                print(f"   - {ind.slug}: {ind.name} ({data_count} data points)")
                if ind.slug == "jujj-test":
                    print("     ⭐ THIS IS THE jujj-test indicator!")
        
        # 5. Test the API query that the frontend would use
        print(f"\n5️⃣ Testing frontend API query simulation:")
        
        # This simulates what the categories router does
        indicators_with_summary = []
        for indicator in market_indexes_category.indicators:
            latest = db.query(DataPoint).filter(
                DataPoint.indicator_id == indicator.id
            ).order_by(DataPoint.date.desc()).first()
            
            if indicator.slug == "jujj-test":
                print(f"   🔍 Processing jujj-test:")
                print(f"     - Indicator ID: {indicator.id}")
                print(f"     - Has latest data: {'Yes' if latest else 'No'}")
                if latest:
                    print(f"     - Latest value: {latest.value}")
                    print(f"     - Latest date: {latest.date}")
        
        # 6. Raw SQL query to double-check
        print(f"\n6️⃣ Raw SQL verification:")
        result = db.execute(text("""
            SELECT i.slug, i.name, c.name as category_name, c.slug as category_slug,
                   COUNT(dp.id) as data_points
            FROM indicators i
            JOIN categories c ON i.category_id = c.id
            LEFT JOIN data_points dp ON i.id = dp.indicator_id
            WHERE i.slug = 'jujj-test'
            GROUP BY i.id, i.slug, i.name, c.name, c.slug
        """))
        
        for row in result:
            print(f"   ✅ SQL Result:")
            print(f"     - Indicator: {row.slug} ({row.name})")
            print(f"     - Category: {row.category_slug} ({row.category_name})")
            print(f"     - Data Points: {row.data_points}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
        print(f"\n🔚 Debug completed at {datetime.now()}")

if __name__ == "__main__":
    debug_jujj_test()