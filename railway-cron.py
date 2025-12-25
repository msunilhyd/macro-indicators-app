#!/usr/bin/env python3
"""
Railway Cron Service for Data Collection
Deploy this as a separate Railway service with cron configuration
"""

import requests
import schedule
import time
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv('API_URL', 'https://macro-indicators-app-production.up.railway.app')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'admin')
COLLECTION_ENDPOINT = f"{API_URL}/api/admin/collect-all-data?admin_token={ADMIN_TOKEN}"

def collect_data():
    """Trigger data collection via API"""
    try:
        logger.info(f"🚀 Triggering data collection at {datetime.now()}")
        response = requests.post(COLLECTION_ENDPOINT, timeout=300)  # 5 min timeout
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Collection successful: {data.get('summary', {})}")
        else:
            logger.error(f"❌ Collection failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"💥 Collection error: {str(e)}")

def main():
    """Schedule data collection at market times"""
    logger.info("🤖 Railway Cron Service started")
    
    # Schedule collections at market times (UTC)
    schedule.every().day.at("09:00").do(collect_data)  # 9 AM
    schedule.every().day.at("15:00").do(collect_data)  # 3 PM  
    schedule.every().day.at("21:00").do(collect_data)  # 9 PM
    
    logger.info("⏰ Scheduled collections at 9 AM, 3 PM, 9 PM daily")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()