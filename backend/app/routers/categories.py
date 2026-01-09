from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models import Category, Indicator, DataPoint
from ..schemas import CategoryResponse, CategoryWithIndicators, IndicatorSummary

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
@router.get("/", response_model=List[CategoryResponse], include_in_schema=False)
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.display_order).all()
    return categories


@router.get("/{slug}", response_model=CategoryWithIndicators)
def get_category(slug: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get indicators ordered by display_order
    ordered_indicators = db.query(Indicator).filter(
        Indicator.category_id == category.id
    ).order_by(Indicator.display_order, Indicator.id).all()
    
    indicators_with_summary = []
    for indicator in ordered_indicators:
        latest = db.query(DataPoint).filter(
            DataPoint.indicator_id == indicator.id
        ).order_by(DataPoint.date.desc()).first()
        
        previous = db.query(DataPoint).filter(
            DataPoint.indicator_id == indicator.id
        ).order_by(DataPoint.date.desc()).offset(1).first()
        
        change_percent = None
        if latest and previous and previous.value != 0:
            change_percent = round(((latest.value - previous.value) / abs(previous.value)) * 100, 2)
        
        indicators_with_summary.append(IndicatorSummary(
            id=indicator.id,
            name=indicator.name,
            slug=indicator.slug,
            unit=indicator.unit,
            latest_value=latest.value if latest else None,
            latest_date=latest.date if latest else None,
            previous_value=previous.value if previous else None,
            change_percent=change_percent
        ))
    
    return CategoryWithIndicators(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        display_order=category.display_order,
        indicators=indicators_with_summary
    )
