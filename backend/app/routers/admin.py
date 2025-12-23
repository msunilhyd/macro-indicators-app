from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io
from ..database import get_db
from ..models import Category, Indicator, DataPoint
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Simple token-based auth (replace with proper auth in production)
ADMIN_TOKEN = "admin_secret_token_2025"


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
    
    # Get all categories
    categories = db.query(Category.name).all()
    category_names = [cat.name for cat in categories]
    
    # Get all indicators with details
    indicators = db.query(Indicator).all()
    indicator_list = []
    
    for indicator in indicators:
        # Get data point count for this indicator
        data_point_count = db.query(func.count(DataPoint.id)).filter(
            DataPoint.indicator_id == indicator.id
        ).scalar()
        
        # Get date range
        date_range = None
        min_date = db.query(func.min(DataPoint.date)).filter(
            DataPoint.indicator_id == indicator.id
        ).scalar()
        max_date = db.query(func.max(DataPoint.date)).filter(
            DataPoint.indicator_id == indicator.id
        ).scalar()
        
        if min_date and max_date:
            date_range = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        
        indicator_list.append({
            "id": indicator.id,
            "name": indicator.name,
            "slug": indicator.slug,
            "category": indicator.category.name if indicator.category else "Unknown",
            "data_points": data_point_count,
            "date_range": date_range,
        })
    
    return {
        "total_categories": total_categories,
        "total_indicators": total_indicators,
        "total_data_points": total_data_points,
        "categories": category_names,
        "indicators": indicator_list,
    }


@router.post("/upload-csv/{indicator_slug}")
async def upload_csv(
    indicator_slug: str,
    file: UploadFile = File(...),
    series_type: str = Query("historical"),
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Upload CSV data for an existing indicator"""
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
            # Parse date
            date_obj = pd.to_datetime(row['date']).date()
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


@router.post("/create-indicator-from-csv")
async def create_indicator_from_csv(
    name: str = Query(...),
    slug: str = Query(...),
    category: str = Query(...),
    description: str = Query(""),
    unit: str = Query(""),
    frequency: str = Query("daily"),
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Create a new indicator (without uploading data yet)"""
    # Check if slug already exists
    existing = db.query(Indicator).filter(Indicator.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Indicator with this slug already exists")
    
    # Get or create category
    category_obj = db.query(Category).filter(Category.slug == category).first()
    if not category_obj:
        # Create category if it doesn't exist
        category_name = category.replace('-', ' ').title()
        category_obj = Category(name=category_name, slug=category)
        db.add(category_obj)
        db.flush()
    
    # Create indicator
    indicator = Indicator(
        name=name,
        slug=slug,
        description=description,
        category_id=category_obj.id,
        unit=unit,
        frequency=frequency
    )
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    
    return {
        "message": "Indicator created successfully",
        "indicator": {
            "id": indicator.id,
            "name": indicator.name,
            "slug": indicator.slug
        }
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
            "frequency": indicator.frequency
        }
    }
