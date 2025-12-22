from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, timedelta
from ..database import get_db
from ..models import Indicator, DataPoint, Category
from ..schemas import IndicatorResponse, IndicatorWithData, DataPointBase, DataSeries

# Series type labels for display
SERIES_LABELS = {
    "historical": "Historical",
    "inflation_adjusted": "Adjusted for Inflation", 
    "annual_change": "Annual % Change",
    "annual_average": "Annual Average",
}

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("", response_model=List[IndicatorResponse])
@router.get("/", response_model=List[IndicatorResponse], include_in_schema=False)
def get_indicators(
    category_slug: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Indicator)
    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)
    return query.order_by(Indicator.display_order).all()


@router.get("/{slug}", response_model=IndicatorWithData)
def get_indicator(
    slug: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=100, le=5000),
    db: Session = Depends(get_db)
):
    indicator = db.query(Indicator).filter(Indicator.slug == slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Get all data points for this indicator
    query = db.query(DataPoint).filter(DataPoint.indicator_id == indicator.id)
    
    if start_date:
        query = query.filter(DataPoint.date >= start_date)
    if end_date:
        query = query.filter(DataPoint.date <= end_date)
    
    all_data_points = query.order_by(DataPoint.series_type, DataPoint.date).all()
    
    # Group by series_type
    series_dict = {}
    for dp in all_data_points:
        if dp.series_type not in series_dict:
            series_dict[dp.series_type] = []
        series_dict[dp.series_type].append(dp)
    
    # Build series list
    series_list = []
    for series_type in ["historical", "inflation_adjusted", "annual_change", "annual_average"]:
        if series_type in series_dict:
            points = series_dict[series_type][-limit:] if limit else series_dict[series_type]
            series_list.append(DataSeries(
                series_type=series_type,
                label=SERIES_LABELS.get(series_type, series_type.replace("_", " ").title()),
                data_points=[DataPointBase(date=dp.date, value=dp.value) for dp in points]
            ))
    
    # For backward compatibility, also return historical data in data_points
    historical_points = series_dict.get("historical", [])[-limit:] if limit else series_dict.get("historical", [])
    
    return IndicatorWithData(
        id=indicator.id,
        name=indicator.name,
        slug=indicator.slug,
        description=indicator.description,
        unit=indicator.unit,
        frequency=indicator.frequency,
        category_id=indicator.category_id,
        source=indicator.source,
        data_points=[DataPointBase(date=dp.date, value=dp.value) for dp in historical_points],
        series=series_list
    )


@router.get("/{slug}/latest")
def get_latest_value(slug: str, db: Session = Depends(get_db)):
    indicator = db.query(Indicator).filter(Indicator.slug == slug).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    latest = db.query(DataPoint).filter(
        DataPoint.indicator_id == indicator.id
    ).order_by(DataPoint.date.desc()).first()
    
    previous = db.query(DataPoint).filter(
        DataPoint.indicator_id == indicator.id
    ).order_by(DataPoint.date.desc()).offset(1).first()
    
    change_percent = None
    if latest and previous and previous.value != 0:
        change_percent = round(((latest.value - previous.value) / abs(previous.value)) * 100, 2)
    
    return {
        "indicator": indicator.name,
        "slug": indicator.slug,
        "unit": indicator.unit,
        "latest_value": latest.value if latest else None,
        "latest_date": latest.date if latest else None,
        "previous_value": previous.value if previous else None,
        "change_percent": change_percent
    }
