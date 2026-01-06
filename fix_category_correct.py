#!/usr/bin/env python3
"""Fix the category slug for Jeera Futures - corrected approach"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set the database URL
DATABASE_URL = "postgresql://postgres:wUXRJCcrvqKCaNLZaUiRDXEbsjdduujw@shinkansen.proxy.rlwy.net:49888/railway"

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.models import Category, Indicator

def fix_category_slug_correct():
    print("🔧 Fixing category slug for Jeera Futures (corrected approach)...")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find the Jeera indicator
        jeera_indicator = db.query(Indicator).filter(Indicator.slug == "jeera-unjha").first()
        
        if jeera_indicator:
            print(f"📦 Found Jeera Futures indicator:")
            print(f"   ID: {jeera_indicator.id}")
            print(f"   Name: {jeera_indicator.name}")
            print(f"   Current category ID: {jeera_indicator.category_id}")
            
            # Find the correct commodities category (ID 4, slug = "commodities")
            correct_cat = db.query(Category).filter(Category.id == 4).first()
            
            if correct_cat:
                print(f"\n🎯 Target category:")
                print(f"   ID: {correct_cat.id}")
                print(f"   Name: {correct_cat.name}")
                print(f"   Slug: {correct_cat.slug}")
                
                # Update the indicator's category
                print(f"\n📦 Moving indicator from category {jeera_indicator.category_id} → {correct_cat.id}")
                jeera_indicator.category_id = correct_cat.id
                
                # Commit the change
                db.commit()
                print(f"✅ Successfully moved Jeera Futures to the correct category!")
                
                # Now check if we can delete the duplicate category
                duplicate_cat = db.query(Category).filter(Category.id == 8).first()
                if duplicate_cat:
                    # Check if there are any other indicators in category 8
                    remaining_indicators = db.query(Indicator).filter(Indicator.category_id == 8).count()
                    
                    if remaining_indicators == 0:
                        print(f"\n🗑️  Deleting duplicate category {duplicate_cat.id} (empty)")
                        db.delete(duplicate_cat)
                        db.commit()
                        print(f"✅ Duplicate category deleted!")
                    else:
                        print(f"\n⚠️  Keeping category 8 because it has {remaining_indicators} other indicators")
                
                # Final verification
                print(f"\n✓ Final verification:")
                updated_indicator = db.query(Indicator).filter(Indicator.slug == "jeera-unjha").first()
                updated_category = db.query(Category).filter(Category.id == updated_indicator.category_id).first()
                print(f"   Jeera Futures is now in category: {updated_indicator.category_id}")
                print(f"   Category name: {updated_category.name}")
                print(f"   Category slug: {updated_category.slug}")
                
            else:
                print("❌ Target category (ID 4) not found")
        else:
            print("❌ Jeera Futures indicator not found")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    fix_category_slug_correct()