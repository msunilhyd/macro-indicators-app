#!/usr/bin/env python3
"""
Universal Data Collection Scheduler for All Indicators
Automatically scrapes and stores data for all indicators with scrape configurations
"""

import sys
import os
from datetime import datetime, date, time
import requests
from lxml import html
import re
from dotenv import load_dotenv
import time as time_module
import logging
from typing import List, Optional
import random
import threading
from datetime import timedelta

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load the local environment file
load_dotenv('backend/.env.local')

from backend.app.database import get_db
from backend.app.models import Indicator, DataPoint
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCollectorScheduler:
    def __init__(self):
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def scrape_value_from_url(self, url: str, selector: str, indicator_name: str) -> Optional[float]:
        """Scrape value from URL using CSS selector"""
        try:
            logger.info(f"📡 Scraping {indicator_name} from: {url}")
            response = requests.get(url, headers=self.session_headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            tree = html.fromstring(response.content)
            
            # Try the configured selector
            elements = tree.cssselect(selector)
            if elements:
                value_text = elements[0].text_content().strip()
                logger.info(f"🎯 Raw value for {indicator_name}: '{value_text}'")
                
                # Extract numeric value
                numbers = re.findall(r'[\d,]+\.?\d*', value_text)
                if numbers:
                    clean_value = float(numbers[0].replace(',', ''))
                    logger.info(f"💰 Extracted value for {indicator_name}: {clean_value}")
                    return clean_value
            
            # Try alternative selectors
            alt_selectors = [
                '.text-5xl', '.text-4xl', '.text-3xl', '.text-2xl',
                '[data-test="instrument-price-last"]',
                '.instrument-price_last',
                '.last-price-value', '.price-value', '.current-price',
                '.pid-index-last', '.pid-last',
                '.price', '.value', '.amount',
                'span[class*="price"]', 'div[class*="price"]',
                'span[class*="value"]', 'div[class*="value"]'
            ]
            
            for alt_sel in alt_selectors:
                try:
                    elements = tree.cssselect(alt_sel)
                    if elements:
                        value_text = elements[0].text_content().strip()
                        numbers = re.findall(r'[\d,]+\.?\d*', value_text)
                        if numbers:
                            clean_value = float(numbers[0].replace(',', ''))
                            logger.info(f"🎯 Found {indicator_name} with '{alt_sel}': {clean_value}")
                            return clean_value
                except:
                    continue
            
            logger.warning(f"❌ No value found for {indicator_name} with any selector")
            return None
            
        except Exception as e:
            logger.error(f"❌ Scraping failed for {indicator_name}: {e}")
            return None
    
    def generate_realistic_value(self, indicator_id: int, db: Session) -> float:
        """Generate realistic value based on historical data"""
        try:
            # Get the most recent data point
            latest_data = db.query(DataPoint).filter(
                DataPoint.indicator_id == indicator_id
            ).order_by(DataPoint.date.desc()).first()
            
            if latest_data:
                # Add small random variation (±3%)
                variation = random.uniform(-0.03, 0.03)
                new_value = latest_data.value * (1 + variation)
                return round(new_value, 2)
            else:
                # Default fallback value
                return 100.0
        except:
            return 100.0
    
    def collect_indicator_data(self, indicator: Indicator, db: Session) -> dict:
        """Collect data for a single indicator"""
        result = {
            'indicator': indicator.name,
            'slug': indicator.slug,
            'success': False,
            'value': None,
            'source': 'none',
            'error': None
        }
        
        try:
            today = date.today()
            
            # Check if we already have data for today
            existing = db.query(DataPoint).filter(
                DataPoint.indicator_id == indicator.id,
                DataPoint.date == today,
                DataPoint.series_type == 'historical'
            ).first()
            
            if existing:
                result['success'] = True
                result['value'] = existing.value
                result['source'] = 'existing'
                logger.info(f"✅ {indicator.name}: Using existing value ${existing.value}")
                return result
            
            # Try scraping if configured
            scraped_value = None
            if indicator.scrape_url and indicator.html_selector:
                scraped_value = self.scrape_value_from_url(
                    indicator.scrape_url, 
                    indicator.html_selector, 
                    indicator.name
                )
                
            if scraped_value is not None:
                final_value = scraped_value
                result['source'] = 'scraped'
            else:
                # Skip indicators without scrape configuration
                logger.warning(f"⏭️  {indicator.name}: No scrape URL configured, skipping auto-generation")
                result['success'] = False
                result['error'] = 'No scrape URL configured'
                return result
            
            # Insert new data point
            new_data_point = DataPoint(
                indicator_id=indicator.id,
                series_type='historical',
                date=today,
                value=final_value
            )
            db.add(new_data_point)
            db.commit()
            
            result['success'] = True
            result['value'] = final_value
            
            logger.info(f"✅ {indicator.name}: Saved ${final_value} ({result['source']})")
            return result
            
        except Exception as e:
            db.rollback()
            result['error'] = str(e)
            logger.error(f"❌ {indicator.name}: Failed - {e}")
            return result
    
    def collect_all_indicators(self):
        """Collect data for all indicators with scrape configurations"""
        logger.info("🚀 Starting daily data collection for all indicators")
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        try:
            db = next(get_db())
            
            # Get all indicators with scrape configurations OR recent data
            all_indicators = db.query(Indicator).all()
            
            # Filter indicators that either have scrape config OR have historical data
            active_indicators = []
            for indicator in all_indicators:
                has_scrape_config = indicator.scrape_url and indicator.html_selector
                has_data = db.query(DataPoint).filter(
                    DataPoint.indicator_id == indicator.id
                ).first() is not None
                
                if has_scrape_config or has_data:
                    active_indicators.append(indicator)
            
            logger.info(f"📊 Found {len(active_indicators)} active indicators to process")
            
            results = []
            successful = 0
            failed = 0
            
            for indicator in active_indicators:
                result = self.collect_indicator_data(indicator, db)
                results.append(result)
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                
                # Small delay between requests to be respectful
                time_module.sleep(1)
            
            # Summary
            logger.info("="*60)
            logger.info(f"📈 DATA COLLECTION SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"✅ Successful: {successful}")
            logger.info(f"❌ Failed: {failed}")
            logger.info(f"📊 Total processed: {len(active_indicators)}")
            
            # Log detailed results
            logger.info("\\n📋 Detailed Results:")
            for result in results:
                status = "✅" if result['success'] else "❌"
                value_str = f"${result['value']}" if result['value'] else "N/A"
                source_str = f"({result['source']})" if result['source'] != 'none' else ""
                logger.info(f"   {status} {result['indicator']}: {value_str} {source_str}")
            
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Collection process failed: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def start_scheduler(self):
        """Start the scheduler with different collection times"""
        logger.info("🕐 Starting Data Collection Scheduler")
        
        # Collection times (hours)
        collection_times = [9, 15, 21]  # 9 AM, 3 PM, 9 PM
        
        logger.info("📅 Scheduled collection times:")
        logger.info("   - 09:00 AM (Market open)")
        logger.info("   - 03:00 PM (Market close)")
        logger.info("   - 09:00 PM (End of day)")
        
        logger.info("🔄 Scheduler is running... Press Ctrl+C to stop")
        
        last_collection_date = None
        
        try:
            while True:
                now = datetime.now()
                current_hour = now.hour
                current_date = now.date()
                
                # Check if we should collect data
                should_collect = False
                
                if current_hour in collection_times:
                    # Only collect once per hour at most
                    if last_collection_date != current_date or current_hour != getattr(self, '_last_collection_hour', None):
                        should_collect = True
                        self._last_collection_hour = current_hour
                        last_collection_date = current_date
                
                if should_collect:
                    logger.info(f"⏰ Collection time reached: {current_hour}:00")
                    self.collect_all_indicators()
                
                # Sleep for 30 minutes before checking again
                time_module.sleep(1800)  # 30 minutes
                
        except KeyboardInterrupt:
            logger.info("⏹️  Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")

def main():
    """Main entry point"""
    scheduler = DataCollectorScheduler()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run-once":
        # Run collection once for testing
        scheduler.collect_all_indicators()
    else:
        # Start the scheduler
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()