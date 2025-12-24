#!/usr/bin/env python3
"""
Script to seed the database with CSV data
"""
import os
import sys
import re
from pathlib import Path
import pandas as pd
from datetime import datetime
from collections import defaultdict

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.models import Category, Indicator, DataPoint, SERIES_TYPE_MAP

# Path to the data folder - Update this path to point to your local data directory
DATA_DIR = Path(os.environ.get("MACRO_DATA_DIR", str(Path(__file__).parent / "data" / "organized")))

# Category mappings
CATEGORIES = {
    "01_market_indexes": {
        "name": "Market Indexes",
        "slug": "market-indexes",
        "description": "Major stock market indexes including S&P 500, Dow Jones, NASDAQ, and international markets",
        "order": 1
    },
    "02_precious_metals": {
        "name": "Precious Metals",
        "slug": "precious-metals",
        "description": "Gold, Silver, Platinum prices and related ratios",
        "order": 2
    },
    "03_energy": {
        "name": "Energy",
        "slug": "energy",
        "description": "Crude oil, natural gas, and energy commodity prices",
        "order": 3
    },
    "04_commodities": {
        "name": "Commodities",
        "slug": "commodities",
        "description": "Agricultural and industrial commodity prices",
        "order": 4
    },
    "05_exchange_rates": {
        "name": "Exchange Rates",
        "slug": "exchange-rates",
        "description": "Currency exchange rates and USD index",
        "order": 5
    },
    "06_interest_rates": {
        "name": "Interest Rates",
        "slug": "interest-rates",
        "description": "Federal funds rate, treasury yields, and other interest rates",
        "order": 6
    },
    "07_economy": {
        "name": "Economy",
        "slug": "economy",
        "description": "Economic indicators including unemployment, inflation, GDP, and more",
        "order": 7
    }
}

# Unit mappings based on indicator name patterns
UNIT_PATTERNS = {
    "ratio": "Ratio",
    "rate": "%",
    "yield": "%",
    "change": "%",
    "inflation": "%",
    "unemployment": "%",
    "gdp": "%",
    "index": "Index",
    "usd": "USD",
    "gold": "USD",
    "silver": "USD",
    "platinum": "USD",
    "oil": "USD",
    "dollar": "Index",
}


def extract_indicator_info(filename: str) -> dict:
    """Extract indicator name and series type from filename"""
    # Remove .csv extension
    name = filename.replace('.csv', '')
    
    # Determine series type
    series_type = "historical"
    if "inflation_adj" in name or "inflation-adj" in name:
        series_type = "inflation_adjusted"
    elif "annual_change" in name or "annual-change" in name:
        series_type = "annual_change"
    elif "annual_avg" in name or "annual-avg" in name:
        series_type = "annual_average"
    
    # Extract base indicator name (remove series type, unit, frequency, timespan)
    # Pattern: {indicator}_{type}_{unit}_{frequency}_{timespan}
    parts = name.split('_')
    
    # Find where the metadata starts (usually after "historical", "main", etc.)
    base_parts = []
    for i, part in enumerate(parts):
        if part in ['historical', 'inflation', 'annual', 'main', 'usd', 'daily', 'monthly', 'yearly', 'weekly']:
            break
        if re.match(r'^\d+y$', part):  # Skip timespan like "100y", "50y"
            break
        base_parts.append(part)
    
    if not base_parts:
        base_parts = parts[:2]  # Fallback to first two parts
    
    base_name = '_'.join(base_parts)
    display_name = ' '.join(base_parts).title()
    slug = '-'.join(base_parts).lower()
    
    return {
        'base_name': base_name,
        'display_name': display_name,
        'slug': slug,
        'series_type': series_type,
        'filename': filename
    }


def guess_unit(indicator_name: str) -> str:
    """Guess the unit based on indicator name"""
    name_lower = indicator_name.lower()
    for pattern, unit in UNIT_PATTERNS.items():
        if pattern in name_lower:
            return unit
    return "Value"


def load_csv_data(csv_path: Path) -> pd.DataFrame:
    """Load and clean CSV data"""
    try:
        df = pd.read_csv(csv_path)
        if 'date' not in df.columns or 'value' not in df.columns:
            return None
        
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date', 'value'])
        
        # Filter out corrupted dates (years > 2030 or < 1700)
        df = df[(df['date'].dt.year <= 2030) & (df['date'].dt.year >= 1700)]
        
        df = df.sort_values('date')
        return df
    except Exception as e:
        print(f"  Error loading {csv_path}: {e}")
        return None


def seed_database():
    """Main function to seed the database"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        db.query(DataPoint).delete()
        db.query(Indicator).delete()
        db.query(Category).delete()
        db.commit()
        
        # Create categories
        print("\nCreating categories...")
        category_map = {}
        for folder_name, cat_info in CATEGORIES.items():
            category = Category(
                name=cat_info["name"],
                slug=cat_info["slug"],
                description=cat_info["description"],
                display_order=cat_info["order"]
            )
            db.add(category)
            db.flush()
            category_map[folder_name] = category
            print(f"  Created: {cat_info['name']}")
        
        db.commit()
        
        # Process each category folder
        total_indicators = 0
        total_data_points = 0
        
        for folder_name, category in category_map.items():
            folder_path = DATA_DIR / folder_name
            if not folder_path.exists():
                print(f"\nSkipping {folder_name} - folder not found")
                continue
            
            print(f"\nProcessing {category.name}...")
            
            # Get all CSV files in this category folder
            csv_files = sorted(folder_path.glob("*.csv"))
            if not csv_files:
                continue
            
            # Group CSV files by base indicator name
            indicator_files = defaultdict(list)
            for csv_file in csv_files:
                info = extract_indicator_info(csv_file.name)
                indicator_files[info['slug']].append({
                    'path': csv_file,
                    'info': info
                })
            
            indicator_order = 0
            for slug, files in sorted(indicator_files.items()):
                # Use the first file's info for the indicator
                first_info = files[0]['info']
                
                # Try to load historical data first, or any available data
                has_data = False
                for f in files:
                    df = load_csv_data(f['path'])
                    if df is not None and len(df) > 0:
                        has_data = True
                        break
                
                if not has_data:
                    continue
                
                # Create indicator
                indicator = Indicator(
                    category_id=category.id,
                    name=first_info['display_name'],
                    slug=slug,
                    unit=guess_unit(first_info['display_name']),
                    source="",
                    frequency="monthly",
                    display_order=indicator_order
                )
                db.add(indicator)
                db.flush()
                indicator_order += 1
                total_indicators += 1
                
                # Load ALL CSV files for this indicator
                indicator_data_points = 0
                series_count = 0
                for f in files:
                    df = load_csv_data(f['path'])
                    if df is None or len(df) == 0:
                        continue
                    
                    series_type = f['info']['series_type']
                    series_count += 1
                    
                    # Add data points with series_type
                    data_points = []
                    for _, row in df.iterrows():
                        data_points.append(DataPoint(
                            indicator_id=indicator.id,
                            series_type=series_type,
                            date=row['date'].date(),
                            value=float(row['value'])
                        ))
                    
                    db.bulk_save_objects(data_points)
                    indicator_data_points += len(data_points)
                    total_data_points += len(data_points)
                
                print(f"  {first_info['display_name']}: {indicator_data_points} data points ({series_count} series)")
            
            db.commit()
        
        print(f"\n{'='*50}")
        print(f"Seeding complete!")
        print(f"  Categories: {len(category_map)}")
        print(f"  Indicators: {total_indicators}")
        print(f"  Data Points: {total_data_points}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
