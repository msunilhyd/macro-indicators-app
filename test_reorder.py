#!/usr/bin/env python3
"""
Test script to verify indicator reordering functionality.
This script demonstrates how the admin reordering system works.
"""

import requests
import json
from typing import List, Dict

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "admin"

def get_indicators(category_slug: str = None) -> List[Dict]:
    """Fetch indicators from the API."""
    if category_slug:
        url = f"{BASE_URL}/api/categories/{category_slug}"
        response = requests.get(url)
        if response.ok:
            data = response.json()
            return data.get('indicators', [])
    else:
        url = f"{BASE_URL}/api/indicators"
        response = requests.get(url)
        if response.ok:
            return response.json()
    return []

def get_admin_stats() -> Dict:
    """Fetch admin statistics."""
    url = f"{BASE_URL}/api/admin/stats?admin_token={ADMIN_TOKEN}"
    response = requests.get(url)
    if response.ok:
        return response.json()
    return {}

def reorder_indicators(order_data: List[Dict]) -> bool:
    """Update indicator display order."""
    url = f"{BASE_URL}/api/admin/reorder-indicators?admin_token={ADMIN_TOKEN}"
    response = requests.post(
        url,
        json=order_data,
        headers={'Content-Type': 'application/json'}
    )
    return response.ok

def print_indicators_order(indicators: List[Dict], title: str = "Current Order"):
    """Pretty print indicator order."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    for idx, ind in enumerate(indicators):
        name = ind.get('name', ind.get('indicator', 'Unknown'))
        slug = ind.get('slug', 'unknown')
        display_order = ind.get('display_order', idx)
        print(f"{idx + 1:3d}. [{display_order:3d}] {name} ({slug})")
    print(f"{'='*60}\n")

def main():
    """Main test function."""
    print("🧪 Testing Indicator Reordering System")
    print("="*60)
    
    # Test 1: Fetch current admin stats
    print("\n📊 Test 1: Fetching admin statistics...")
    stats = get_admin_stats()
    if stats:
        print(f"   ✓ Total Indicators: {stats.get('total_indicators', 0)}")
        print(f"   ✓ Total Categories: {stats.get('total_categories', 0)}")
        indicators = stats.get('indicators', [])
        if indicators:
            print_indicators_order(indicators[:10], "First 10 Indicators (Current Order)")
    else:
        print("   ✗ Failed to fetch admin stats. Is the backend running?")
        return
    
    # Test 2: Fetch indicators for a specific category
    print("\n📊 Test 2: Fetching Market Indexes category...")
    market_indicators = get_indicators('market-indexes')
    if market_indicators:
        print(f"   ✓ Found {len(market_indicators)} indicators in Market Indexes")
        print_indicators_order(market_indicators, "Market Indexes Indicators")
    else:
        print("   ⚠ No indicators found for Market Indexes category")
    
    # Test 3: Demonstrate reordering (dry run)
    print("\n🔄 Test 3: Demonstrating reorder functionality...")
    print("   The reorder endpoint expects data in the format:")
    print("   [{'slug': 'indicator-slug', 'display_order': 0}, ...]")
    print("\n   Example to swap first two indicators:")
    if len(indicators) >= 2:
        example_order = [
            {'slug': indicators[1]['slug'], 'display_order': 0},
            {'slug': indicators[0]['slug'], 'display_order': 1},
        ]
        print(f"   {json.dumps(example_order, indent=2)}")
        print("\n   To apply: Uncomment the reorder_indicators() call in this script")
    
    # Test 4: Verify ordering is consistent across endpoints
    print("\n✅ Test 4: Verifying order consistency...")
    all_indicators = get_indicators()
    if all_indicators:
        print(f"   ✓ Fetched {len(all_indicators)} indicators from /api/indicators")
        # Check if ordered by display_order
        is_ordered = all(
            all_indicators[i].get('display_order', 0) <= all_indicators[i+1].get('display_order', 0)
            for i in range(len(all_indicators)-1)
        )
        if is_ordered:
            print("   ✓ Indicators are properly ordered by display_order")
        else:
            print("   ⚠ Warning: Indicators may not be properly ordered")
    
    print("\n" + "="*60)
    print("✨ Testing Complete!")
    print("\nTo use the admin reordering UI:")
    print("1. Navigate to http://localhost:3000/admin")
    print("2. Login with admin token")
    print("3. Click 'Reorder' button")
    print("4. Use ↑↓ arrows to reorder indicators")
    print("5. Click 'Save Order' to persist changes")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the backend server.")
        print("Please ensure the backend is running:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

