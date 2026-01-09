from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date
import pandas as pd
import io
import requests
from lxml import html
import re
from ..database import get_db
from ..models import Category, Indicator, DataPoint
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Simple token-based auth (replace with proper auth in production)
ADMIN_TOKEN = "admin"


def verify_admin_token(admin_token: str = Query(...)):
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return admin_token


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin_token: str = Depends(verify_admin_token)
):
    """Get statistics for admin dashboard"""
    # Get total counts
    total_categories = db.query(func.count(Category.id)).scalar()
    total_indicators = db.query(func.count(Indicator.id)).scalar()
    total_data_points = db.query(func.count(DataPoint.id)).scalar()
    
    # Get all categories (return slugs for form usage)
    categories = db.query(Category.slug).all()
    category_slugs = [cat.slug for cat in categories]
    
    # Get all indicators with details, ordered by display_order
    indicators = db.query(Indicator).order_by(Indicator.display_order, Indicator.id).all()
    
    # Optimize: Get data point stats for all indicators in one query
    data_stats = db.query(
        DataPoint.indicator_id,
        func.count(DataPoint.id).label('count'),
        func.min(DataPoint.date).label('min_date'),
        func.max(DataPoint.date).label('max_date')
    ).group_by(DataPoint.indicator_id).all()
    
    # Create a lookup dictionary for faster access
    stats_dict = {
        stat.indicator_id: {
            'count': stat.count,
            'min_date': stat.min_date,
            'max_date': stat.max_date
        }
        for stat in data_stats
    }
    
    indicator_list = []
    for indicator in indicators:
        # Get stats from the dictionary
        stats = stats_dict.get(indicator.id, {'count': 0, 'min_date': None, 'max_date': None})
        
        # Format date range
        date_range = None
        if stats['min_date'] and stats['max_date']:
            date_range = f"{stats['min_date'].strftime('%Y-%m-%d')} to {stats['max_date'].strftime('%Y-%m-%d')}"
        
        indicator_list.append({
            "id": indicator.id,
            "name": indicator.name,
            "slug": indicator.slug,
            "category": indicator.category.name if indicator.category else "Unknown",
            "data_points": stats['count'],
            "date_range": date_range,
            "display_order": indicator.display_order,
        })
    
    return {
        "total_categories": total_categories,
        "total_indicators": total_indicators,
        "total_data_points": total_data_points,
        "categories": category_slugs,
        "indicators": indicator_list,
    }


@router.post("/upload-csv/{indicator_slug}")
async def upload_csv(
    indicator_slug: str,
    file: UploadFile = File(...),
    series_type: str = Form("historical"),
    admin_token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload CSV data for an existing indicator"""
    # Verify admin token
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    # Find the indicator
    indicator = db.query(Indicator).filter(Indicator.slug == indicator_slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Read the CSV file
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
    
    # Validate required columns
    if 'date' not in df.columns or 'value' not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain 'date' and 'value' columns"
        )
    
    # Process and insert data
    added_count = 0
    updated_count = 0
    
    for _, row in df.iterrows():
        try:
            # Parse date - support multiple formats: yyyy-mm-dd, yyyy-mm, yyyy
            date_str = str(row['date']).strip()
            
            # Try to parse different date formats
            if len(date_str) == 4 and date_str.isdigit():
                # Format: yyyy (e.g., "2024")
                date_obj = datetime.strptime(date_str, '%Y').date()
            elif len(date_str) == 7 and date_str[4] == '-':
                # Format: yyyy-mm (e.g., "2024-01")
                date_obj = datetime.strptime(date_str, '%Y-%m').date()
            else:
                # Format: yyyy-mm-dd or other pandas-parseable format
                date_obj = pd.to_datetime(date_str).date()
            
            value = float(row['value'])
            
            # Check if data point already exists
            existing = db.query(DataPoint).filter(
                and_(
                    DataPoint.indicator_id == indicator.id,
                    DataPoint.date == date_obj,
                    DataPoint.series_type == series_type
                )
            ).first()
            
            if existing:
                existing.value = value
                updated_count += 1
            else:
                data_point = DataPoint(
                    indicator_id=indicator.id,
                    date=date_obj,
                    value=value,
                    series_type=series_type
                )
                db.add(data_point)
                added_count += 1
        except Exception as e:
            # Skip rows with errors
            continue
    
    db.commit()
    
    return {
        "message": "CSV uploaded successfully",
        "indicator": indicator.name,
        "added": added_count,
        "updated": updated_count,
        "series_type": series_type
    }


@router.get("/download-csv/{indicator_slug}")
def download_indicator_data(
    indicator_slug: str,
    series_type: str = Query("historical"),
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Download all data for an indicator as CSV"""
    # Find the indicator
    indicator = db.query(Indicator).filter(Indicator.slug == indicator_slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Get all data points for the indicator
    data_points = db.query(DataPoint).filter(
        and_(
            DataPoint.indicator_id == indicator.id,
            DataPoint.series_type == series_type
        )
    ).order_by(DataPoint.date).all()
    
    if not data_points:
        raise HTTPException(status_code=404, detail="No data found for this indicator")
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "date": dp.date.strftime('%Y-%m-%d'),
            "value": dp.value
        }
        for dp in data_points
    ])
    
    # Convert to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    # Return as downloadable file
    filename = f"{indicator_slug}_{series_type}.csv"
    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/create-indicator-from-csv")
async def create_indicator_from_csv(
    file: UploadFile = File(...),
    name: str = Form(...),
    slug: str = Form(...),
    category_slug: str = Form(...),
    description: str = Form(""),
    unit: str = Form(""),
    frequency: str = Form("daily"),
    scrape_url: str = Form(""),
    html_selector: str = Form(""),
    series_type: str = Form("historical"),
    admin_token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new indicator and upload initial CSV data"""
    # Verify admin token
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    # Check if slug already exists
    existing = db.query(Indicator).filter(Indicator.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Indicator with this slug already exists")
    
    # Get or create category (normalize slug to lowercase for consistency)
    category_slug_normalized = category_slug.lower()
    category_obj = db.query(Category).filter(Category.slug == category_slug_normalized).first()
    if not category_obj:
        # Create category if it doesn't exist
        category_name = category_slug_normalized.replace('-', ' ').title()
        category_obj = Category(name=category_name, slug=category_slug_normalized)
        db.add(category_obj)
        db.flush()
    
    # Create indicator
    indicator = Indicator(
        name=name,
        slug=slug,
        description=description,
        category_id=category_obj.id,
        unit=unit,
        frequency=frequency,
        scrape_url=scrape_url,
        html_selector=html_selector
    )
    db.add(indicator)
    db.flush()
    
    # Read and process the CSV file
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
    
    # Validate required columns
    if 'date' not in df.columns or 'value' not in df.columns:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="CSV must contain 'date' and 'value' columns"
        )
    
    # Process and insert data
    added_count = 0
    
    for _, row in df.iterrows():
        try:
            # Parse date
            date_obj = pd.to_datetime(row['date']).date()
            value = float(row['value'])
            
            data_point = DataPoint(
                indicator_id=indicator.id,
                date=date_obj,
                value=value,
                series_type=series_type
            )
            db.add(data_point)
            added_count += 1
        except Exception as e:
            # Skip rows with errors
            continue
    
    db.commit()
    db.refresh(indicator)
    
    return {
        "message": "Indicator created successfully with data",
        "indicator": {
            "id": indicator.id,
            "name": indicator.name,
            "slug": indicator.slug
        },
        "data_added": added_count,
        "series_type": series_type
    }


@router.delete("/indicators/{indicator_slug}")
def delete_indicator(
    indicator_slug: str,
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Delete an indicator and all its data points"""
    indicator = db.query(Indicator).filter(Indicator.slug == indicator_slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Delete all data points first
    db.query(DataPoint).filter(DataPoint.indicator_id == indicator.id).delete()
    
    # Delete the indicator
    db.delete(indicator)
    db.commit()
    
    return {"message": f"Indicator '{indicator.name}' deleted successfully"}


@router.put("/indicators/{indicator_slug}")
def update_indicator(
    indicator_slug: str,
    name: str = Query(None),
    description: str = Query(None),
    unit: str = Query(None),
    frequency: str = Query(None),
    source: str = Query(None),
    scrape_url: str = Query(None),
    html_selector: str = Query(None),
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Update indicator metadata"""
    indicator = db.query(Indicator).filter(Indicator.slug == indicator_slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Update fields if provided
    if name:
        indicator.name = name
    if description:
        indicator.description = description
    if unit:
        indicator.unit = unit
    if frequency:
        indicator.frequency = frequency
    if source:
        indicator.source = source
    if scrape_url:
        indicator.scrape_url = scrape_url
    if html_selector:
        indicator.html_selector = html_selector
    
    db.commit()
    db.refresh(indicator)
    
    return {
        "message": "Indicator updated successfully",
        "indicator": {
            "id": indicator.id,
            "name": indicator.name,
            "slug": indicator.slug,
            "description": indicator.description,
            "unit": indicator.unit,
            "frequency": indicator.frequency,
            "scrape_url": indicator.scrape_url,
            "html_selector": indicator.html_selector
        }
    }


@router.post("/collect-daily-data/{indicator_slug}")
def collect_daily_data(
    indicator_slug: str,
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Manually trigger daily data collection for an indicator"""
    
    def scrape_live_value(url, selector):
        """Scrape live value from URL using CSS selector"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            tree = html.fromstring(response.content)
            elements = tree.cssselect(selector)
            
            if elements:
                value_text = elements[0].text_content().strip()
                numbers = re.findall(r'[\d,]+\.?\d*', value_text)
                if numbers:
                    return float(numbers[0].replace(',', ''))
            
            return None
        except:
            return None
    
    # Find the indicator
    indicator = db.query(Indicator).filter(Indicator.slug == indicator_slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Get scraping configuration
    scrape_url = indicator.scrape_url
    html_selector = indicator.html_selector
    
    if not scrape_url or not html_selector:
        raise HTTPException(status_code=400, detail="Indicator has no scraping configuration")
    
    # Try to scrape live value
    live_value = scrape_live_value(scrape_url, html_selector)
    
    if live_value is None:
        raise HTTPException(status_code=400, detail="Failed to scrape data from source")
    
    # Check if data for today already exists
    today = date.today()
    existing = db.query(DataPoint).filter(
        DataPoint.indicator_id == indicator.id,
        DataPoint.date == today,
        DataPoint.series_type == 'historical'
    ).first()
    
    if existing:
        existing.value = live_value
        action = "updated"
    else:
        new_data_point = DataPoint(
            indicator_id=indicator.id,
            series_type='historical',
            date=today,
            value=live_value
        )
        db.add(new_data_point)
        action = "created"
    
    db.commit()
    
    return {
        "message": f"Successfully {action} daily data",
        "indicator": indicator.name,
        "date": today.isoformat(),
        "value": live_value,
        "scraped_from": scrape_url,
        "action": action
    }


@router.post("/configure-scraping/{indicator_slug}")
def configure_indicator_scraping(
    indicator_slug: str,
    scrape_url: str = Query(...),
    html_selector: str = Query(...),
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Configure scraping URL and selector for an indicator"""
    
    indicator = db.query(Indicator).filter(Indicator.slug == indicator_slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    indicator.scrape_url = scrape_url
    indicator.html_selector = html_selector
    
    db.commit()
    
    return {
        "message": "Scraping configuration updated successfully",
        "indicator": indicator.name,
        "scrape_url": scrape_url,
        "html_selector": html_selector
    }


@router.post("/reorder-indicators")
def reorder_indicators(
    indicator_orders: List[dict],
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Update display order for multiple indicators
    
    Expected format: [{"slug": "indicator-slug", "display_order": 0}, ...]
    """
    try:
        for item in indicator_orders:
            indicator = db.query(Indicator).filter(Indicator.slug == item['slug']).first()
            if indicator:
                indicator.display_order = item['display_order']
        
        db.commit()
        
        return {
            "message": "Indicator order updated successfully",
            "updated_count": len(indicator_orders)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating order: {str(e)}")


@router.get("/indicators-with-scraping")
def get_indicators_with_scraping(
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get all indicators that have scraping configuration"""
    
    indicators = db.query(Indicator).filter(
        Indicator.scrape_url.isnot(None),
        Indicator.html_selector.isnot(None)
    ).all()
    
    result = []
    for indicator in indicators:
        result.append({
            "id": indicator.id,
            "name": indicator.name,
            "slug": indicator.slug,
            "scrape_url": indicator.scrape_url,
            "html_selector": indicator.html_selector,
            "unit": indicator.unit,
            "frequency": indicator.frequency
        })
    
    return {
        "total_configured": len(result),
        "indicators": result
    }


@router.post("/collect-all-data")
def collect_all_indicators_data(
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Manually trigger data collection for all indicators with scrape configurations"""
    
    def scrape_live_value(url, selector):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            tree = html.fromstring(response.content)
            elements = tree.cssselect(selector)
            
            if elements:
                value_text = elements[0].text_content().strip()
                numbers = re.findall(r'[\d,]+\.?\d*', value_text)
                if numbers:
                    return float(numbers[0].replace(',', ''))
            return None
        except:
            return None
    
    # Get all indicators with scraping configuration
    configured_indicators = db.query(Indicator).filter(
        Indicator.scrape_url.isnot(None),
        Indicator.html_selector.isnot(None)
    ).all()
    
    # Also include indicators that have recent data (for continuation)
    all_indicators = db.query(Indicator).all()
    active_indicators = []
    
    for indicator in all_indicators:
        has_scrape_config = indicator.scrape_url and indicator.html_selector
        has_recent_data = db.query(DataPoint).filter(
            DataPoint.indicator_id == indicator.id
        ).first() is not None
        
        if has_scrape_config or has_recent_data:
            active_indicators.append(indicator)
    
    results = []
    successful = 0
    failed = 0
    today = date.today()
    
    for indicator in active_indicators:
        try:
            # Check if data already exists for today
            existing = db.query(DataPoint).filter(
                DataPoint.indicator_id == indicator.id,
                DataPoint.date == today,
                DataPoint.series_type == 'historical'
            ).first()
            
            if existing:
                results.append({
                    "indicator": indicator.name,
                    "value": existing.value,
                    "status": "existing",
                    "date": today.isoformat()
                })
                successful += 1
                continue
            
            # Try scraping
            scraped_value = None
            if indicator.scrape_url and indicator.html_selector:
                scraped_value = scrape_live_value(indicator.scrape_url, indicator.html_selector)
            
            if scraped_value is None:
                results.append({
                    "indicator": indicator.name,
                    "status": "failed",
                    "error": "Failed to scrape data from source",
                    "date": today.isoformat()
                })
                failed += 1
                continue
            
            # Insert new data point
            new_data_point = DataPoint(
                indicator_id=indicator.id,
                series_type='historical',
                date=today,
                value=scraped_value
            )
            db.add(new_data_point)
            
            results.append({
                "indicator": indicator.name,
                "value": scraped_value,
                "status": "collected",
                "date": today.isoformat()
            })
            successful += 1
            
        except Exception as e:
            results.append({
                "indicator": indicator.name,
                "status": "failed",
                "error": str(e),
                "date": today.isoformat()
            })
            failed += 1
    
    db.commit()
    
    return {
        "message": "Bulk data collection completed",
        "date": today.isoformat(),
        "summary": {
            "total_processed": len(active_indicators),
            "successful": successful,
            "failed": failed
        },
        "results": results
    }
