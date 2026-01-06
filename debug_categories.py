#!/usr/bin/env python3
"""Debug category slug mismatch"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set the database URL
DATABASE_URL = "postgresql://postgres:wUXRJCcrvqKCaNLZaUiRDXEbsjdduujw@shinkansen.proxy.rlwy.net:49888/railway"

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.models import Category, Indicator

def debug_categories():
    print("🔍 Debugging category slugs...")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check all categories
        print("\n📋 All categories in database:")
        categories = db.query(Category).order_by(Category.id).all()
        
        for cat in categories:
            print(f"   ID: {cat.id:2d} | Name: {cat.name:15s} | Slug: {cat.slug}")
            
            # Count indicators in each category
            indicator_count = db.query(Indicator).filter(Indicator.category_id == cat.id).count()
            print(f"       └─ {indicator_count} indicators")
        
        # Specifically check category 8
        print(f"\n🎯 Checking Category ID 8 (where Jeera is):")
        cat_8 = db.query(Category).filter(Category.id == 8).first()
        if cat_8:
            print(f"   Name: '{cat_8.name}'")
            print(f"   Slug: '{cat_8.slug}'")
            print(f"   Expected slug for API: 'commodities'")
            print(f"   Match: {'✅' if cat_8.slug.lower() == 'commodities' else '❌'}")
            
            # Get all indicators in category 8
            indicators = db.query(Indicator).filter(Indicator.category_id == cat_8.id).all()
            print(f"\n   Indicators in category 8:")
            for ind in indicators:
                print(f"     - {ind.slug}: {ind.name}")
        
        # Raw SQL to double-check the category lookup that the API uses
        print(f"\n🔧 Testing API category lookup:")
        result = db.execute(text("""
            SELECT * FROM categories WHERE slug = 'commodities'
        """))
        
        commodities_cat = result.fetchone()
        if commodities_cat:
            print(f"   ✅ Found category with slug 'commodities':")
            print(f"     ID: {commodities_cat.id}")
            print(f"     Name: {commodities_cat.name}")
            print(f"     Slug: {commodities_cat.slug}")
        else:
            print(f"   ❌ No category found with slug 'commodities'")
            
            # Try case-insensitive
            result2 = db.execute(text("""
                SELECT * FROM categories WHERE LOWER(slug) = 'commodities'
            """))
            commodities_cat2 = result2.fetchone()
            if commodities_cat2:
                print(f"   ✅ Found with case-insensitive search:")
                print(f"     Slug in DB: '{commodities_cat2.slug}'")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    debug_categories()