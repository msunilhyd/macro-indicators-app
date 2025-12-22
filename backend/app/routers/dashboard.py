from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models import Category, Indicator, DataPoint
from ..schemas import DashboardIndicator

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Key indicators to show on dashboard
DASHBOARD_INDICATORS = [
    "sp500",
    "dow-jones",
    "gold",
    "silver",
    "crude-oil",
    "unemployment",
    "inflation-historical",
    "dollar-index",
    "treasury",
    "debt-gdp",
]


@router.get("", response_model=List[DashboardIndicator])
@router.get("/", response_model=List[DashboardIndicator], include_in_schema=False)
def get_dashboard(db: Session = Depends(get_db)):
    results = []
    
    for slug in DASHBOARD_INDICATORS:
        indicator = db.query(Indicator).filter(Indicator.slug == slug).first()
        if not indicator:
            continue
        
        # Get latest 12 data points for sparkline (historical series only)
        data_points = db.query(DataPoint).filter(
            DataPoint.indicator_id == indicator.id,
            DataPoint.series_type == "historical"
        ).order_by(DataPoint.date.desc()).limit(12).all()
        
        if not data_points:
            continue
        
        latest = data_points[0]
        previous = data_points[1] if len(data_points) > 1 else None
        
        change_percent = None
        if previous and previous.value != 0:
            change_percent = round(((latest.value - previous.value) / abs(previous.value)) * 100, 2)
        
        sparkline = [dp.value for dp in reversed(data_points)]
        
        results.append(DashboardIndicator(
            id=indicator.id,
            name=indicator.name,
            slug=indicator.slug,
            category_slug=indicator.category.slug,
            unit=indicator.unit,
            latest_value=latest.value,
            latest_date=latest.date,
            change_percent=change_percent,
            sparkline=sparkline
        ))
    
    return results


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """Get overall summary statistics"""
    total_indicators = db.query(func.count(Indicator.id)).scalar()
    total_data_points = db.query(func.count(DataPoint.id)).scalar()
    total_categories = db.query(func.count(Category.id)).scalar()
    
    oldest_date = db.query(func.min(DataPoint.date)).scalar()
    newest_date = db.query(func.max(DataPoint.date)).scalar()
    
    return {
        "total_indicators": total_indicators,
        "total_data_points": total_data_points,
        "total_categories": total_categories,
        "data_range": {
            "oldest": oldest_date,
            "newest": newest_date
        }
    }
