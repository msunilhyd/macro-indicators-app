#!/usr/bin/env python3
"""Debug script to check Jeera Futures indicator in Commodities category"""

import os
import sys
import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Set the database URL
DATABASE_URL = "postgresql://postgres:wUXRJCcrvqKCaNLZaUiRDXEbsjdduujw@shinkansen.proxy.rlwy.net:49888/railway"
API_BASE = "https://macro-indicators-app-production.up.railway.app"

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.models import Category, Indicator, DataPoint
    from app.database import Base
    print("✅ Successfully imported models")
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    sys.exit(1)

def debug_jeera_futures():
    print("🔍 Debugging Jeera Futures indicator...")
    print(f"📊 Connecting to: {DATABASE_URL.split('@')[1]}")
    
    # Create database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Check if Jeera Futures indicator exists
        print("\n1️⃣ Checking if Jeera Futures indicator exists:")
        jeera_futures = db.query(Indicator).filter(
            Indicator.slug.ilike("%jeera%")
        ).all()
        
        if not jeera_futures:
            print("❌ No Jeera-related indicators found!")
            # Let's search more broadly
            all_indicators = db.query(Indicator).filter(
                Indicator.name.ilike("%jeera%")
            ).all()
            if all_indicators:
                print("🔍 Found Jeera indicators by name:")
                for ind in all_indicators:
                    print(f"   - {ind.slug}: {ind.name} (Category ID: {ind.category_id})")
            return
        
        for jeera in jeera_futures:
            print(f"✅ Found Jeera indicator:")
            print(f"   ID: {jeera.id}")
            print(f"   Name: {jeera.name}")
            print(f"   Slug: {jeera.slug}")
            print(f"   Category ID: {jeera.category_id}")
            print(f"   Created: {jeera.created_at}")
            
            # Check the category
            category = db.query(Category).filter(Category.id == jeera.category_id).first()
            if category:
                print(f"   Category: {category.name} (slug: {category.slug})")
            
            # Check data points
            data_count = db.query(DataPoint).filter(DataPoint.indicator_id == jeera.id).count()
            print(f"   Data Points: {data_count}")
            
            if data_count > 0:
                latest = db.query(DataPoint).filter(
                    DataPoint.indicator_id == jeera.id
                ).order_by(DataPoint.date.desc()).first()
                print(f"   Latest: {latest.date} = {latest.value}")
        
        # 2. Check all indicators in Commodities category
        print(f"\n2️⃣ Checking all indicators in Commodities category:")
        commodities_category = db.query(Category).filter(Category.slug == "commodities").first()
        
        if commodities_category:
            indicators_in_category = db.query(Indicator).filter(
                Indicator.category_id == commodities_category.id
            ).all()
            
            print(f"✅ Found {len(indicators_in_category)} indicators in Commodities:")
            jeera_found_in_category = False
            for ind in indicators_in_category:
                data_count = db.query(DataPoint).filter(DataPoint.indicator_id == ind.id).count()
                print(f"   - {ind.slug}: {ind.name} ({data_count} data points)")
                if "jeera" in ind.slug.lower() or "jeera" in ind.name.lower():
                    print("     ⭐ THIS IS A Jeera-related indicator!")
                    jeera_found_in_category = True
            
            if not jeera_found_in_category:
                print("❌ No Jeera indicators found in Commodities category!")
        
        # 3. Raw SQL search for any Jeera-related indicators
        print(f"\n3️⃣ Raw SQL search for Jeera indicators:")
        result = db.execute(text("""
            SELECT i.id, i.slug, i.name, c.name as category_name, c.slug as category_slug,
                   COUNT(dp.id) as data_points
            FROM indicators i
            JOIN categories c ON i.category_id = c.id
            LEFT JOIN data_points dp ON i.id = dp.indicator_id
            WHERE LOWER(i.name) LIKE '%jeera%' OR LOWER(i.slug) LIKE '%jeera%'
            GROUP BY i.id, i.slug, i.name, c.name, c.slug
            ORDER BY i.id
        """))
        
        jeera_indicators = []
        for row in result:
            jeera_indicators.append(row)
            print(f"   ✅ SQL Result:")
            print(f"     - ID: {row.id}")
            print(f"     - Indicator: {row.slug} ({row.name})")
            print(f"     - Category: {row.category_slug} ({row.category_name})")
            print(f"     - Data Points: {row.data_points}")
    
    except Exception as e:
        print(f"❌ Database Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    # 4. Test the API endpoint
    print(f"\n4️⃣ Testing Commodities API endpoint:")
    try:
        url = f"{API_BASE}/api/categories/commodities"
        print(f"📡 Calling: {url}")
        
        response = requests.get(url, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success! Found {len(data['indicators'])} indicators in API")
            
            # Look for Jeera specifically
            jeera_found_in_api = False
            for indicator in data['indicators']:
                if "jeera" in indicator['slug'].lower() or "jeera" in indicator['name'].lower():
                    jeera_found_in_api = True
                    print(f"\n⭐ FOUND Jeera in API response:")
                    print(f"   ID: {indicator['id']}")
                    print(f"   Name: {indicator['name']}")
                    print(f"   Slug: {indicator['slug']}")
                    print(f"   Latest Value: {indicator['latest_value']}")
                    print(f"   Latest Date: {indicator['latest_date']}")
            
            if not jeera_found_in_api:
                print(f"\n❌ Jeera NOT found in Commodities API response!")
                print(f"📝 All commodities indicators returned:")
                for i, indicator in enumerate(data['indicators'], 1):
                    print(f"   {i:2d}. {indicator['slug']} - {indicator['name']}")
            
            # Save the full response
            with open('commodities_api_response.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"\n💾 Full Commodities API response saved to commodities_api_response.json")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
    except Exception as e:
        print(f"❌ API Error: {e}")
    
    print(f"\n🔚 Debug completed at {datetime.now()}")

if __name__ == "__main__":
    debug_jeera_futures()