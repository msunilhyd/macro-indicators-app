from pydantic import BaseModel
from datetime import date
from typing import List, Optional


class DataPointBase(BaseModel):
    date: date
    value: float


class DataPointResponse(DataPointBase):
    id: int
    
    class Config:
        from_attributes = True


class IndicatorBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    unit: Optional[str] = None
    frequency: str = "monthly"
    scrape_url: Optional[str] = None
    html_selector: Optional[str] = None


class IndicatorSummary(BaseModel):
    id: int
    name: str
    slug: str
    unit: Optional[str]
    latest_value: Optional[float] = None
    latest_date: Optional[date] = None
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    
    class Config:
        from_attributes = True


class IndicatorResponse(IndicatorBase):
    id: int
    category_id: int
    source: str
    scrape_url: Optional[str] = None
    html_selector: Optional[str] = None
    
    class Config:
        from_attributes = True


class DataSeries(BaseModel):
    series_type: str
    label: str
    data_points: List[DataPointBase] = []


class IndicatorWithData(IndicatorResponse):
    data_points: List[DataPointBase] = []  # For backward compatibility (historical only)
    series: List[DataSeries] = []  # All series grouped by type


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    display_order: int
    
    class Config:
        from_attributes = True


class CategoryWithIndicators(CategoryResponse):
    indicators: List[IndicatorSummary] = []


class DashboardIndicator(BaseModel):
    id: int
    name: str
    slug: str
    category_slug: str
    unit: Optional[str]
    latest_value: Optional[float]
    latest_date: Optional[date]
    change_percent: Optional[float]
    sparkline: List[float] = []
