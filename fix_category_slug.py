#!/usr/bin/env python3
"""Fix the category slug for Jeera Futures"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set the database URL
DATABASE_URL = "postgresql://postgres:wUXRJCcrvqKCaNLZaUiRDXEbsjdduujw@shinkansen.proxy.rlwy.net:49888/railway"

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.models import Category, Indicator

def fix_category_slug():
    print("🔧 Fixing category slug for Jeera Futures...")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find the duplicate Commodities category (ID 8)
        duplicate_cat = db.query(Category).filter(Category.id == 8).first()
        
        if duplicate_cat:
            print(f"📋 Found duplicate category:")
            print(f"   ID: {duplicate_cat.id}")
            print(f"   Name: {duplicate_cat.name}")
            print(f"   Slug: {duplicate_cat.slug}")
            
            # Move Jeera Futures to the correct commodities category (ID 4)
            correct_cat = db.query(Category).filter(Category.id == 4).first()
            print(f"\n🎯 Target category:")
            print(f"   ID: {correct_cat.id}")
            print(f"   Name: {correct_cat.name}")
            print(f"   Slug: {correct_cat.slug}")
            
            # Move the indicator
            jeera_indicator = db.query(Indicator).filter(Indicator.category_id == 8).first()
            if jeera_indicator:
                print(f"\n📦 Moving indicator:")
                print(f"   {jeera_indicator.slug}: {jeera_indicator.name}")
                print(f"   From category {jeera_indicator.category_id} → {correct_cat.id}")
                
                jeera_indicator.category_id = correct_cat.id
                
                # Delete the duplicate category
                print(f"\n🗑️  Deleting duplicate category {duplicate_cat.id}")
                db.delete(duplicate_cat)
                
                # Commit changes
                db.commit()
                print(f"✅ Successfully fixed the category issue!")
                
                # Verify
                updated_indicator = db.query(Indicator).filter(Indicator.slug == "jeera-unjha").first()
                print(f"\n✓ Verification:")
                print(f"   Jeera Futures is now in category: {updated_indicator.category_id}")
                
                updated_category = db.query(Category).filter(Category.id == updated_indicator.category_id).first()
                print(f"   Category name: {updated_category.name}")
                print(f"   Category slug: {updated_category.slug}")
            else:
                print("❌ No indicator found in category 8")
        else:
            print("❌ Category 8 not found")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    fix_category_slug()