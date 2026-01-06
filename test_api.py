#!/usr/bin/env python3
"""Test the production API endpoint directly"""

import requests
import json
from datetime import datetime

# The production API URL (assuming it's the same Railway deployment)
API_BASE = "https://macro-indicators-app-production.up.railway.app"  # You may need to adjust this

def test_market_indexes_api():
    print("🔍 Testing Market Indexes API endpoint...")
    print(f"📊 API Base: {API_BASE}")
    
    try:
        # Test the category endpoint that the frontend calls
        url = f"{API_BASE}/api/categories/market-indexes"
        print(f"\n📡 Calling: {url}")
        
        response = requests.get(url, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success! Found {len(data['indicators'])} indicators")
            print(f"📋 Category: {data['name']} (slug: {data['slug']})")
            
            # Look for jujj-test specifically
            jujj_found = False
            for indicator in data['indicators']:
                if indicator['slug'] == 'jujj-test':
                    jujj_found = True
                    print(f"\n⭐ FOUND jujj-test in API response:")
                    print(f"   ID: {indicator['id']}")
                    print(f"   Name: {indicator['name']}")
                    print(f"   Latest Value: {indicator['latest_value']}")
                    print(f"   Latest Date: {indicator['latest_date']}")
                    break
            
            if not jujj_found:
                print(f"\n❌ jujj-test NOT found in API response!")
                print(f"📝 All indicators returned:")
                for i, indicator in enumerate(data['indicators'], 1):
                    print(f"   {i:2d}. {indicator['slug']} - {indicator['name']}")
            
            # Save the full response for debugging
            with open('api_response.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"\n💾 Full API response saved to api_response.json")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    print(f"\n🔚 Test completed at {datetime.now()}")

if __name__ == "__main__":
    test_market_indexes_api()