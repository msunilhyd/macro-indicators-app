from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "macro_indicators"}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    indicators = relationship("Indicator", back_populates="category")


class Indicator(Base):
    __tablename__ = "indicators"
    __table_args__ = {"schema": "macro_indicators"}
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("macro_indicators.categories.id"), nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    unit = Column(String(50), nullable=True)  # e.g., "USD", "%", "Index"
    source = Column(String(100), default="")
    scrape_url = Column(String(500), nullable=True)  # URL to scrape data from
    html_selector = Column(String(200), nullable=True)  # CSS selector or HTML element to extract data
    frequency = Column(String(20), default="monthly")  # daily, monthly, yearly
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    category = relationship("Category", back_populates="indicators")
    data_points = relationship("DataPoint", back_populates="indicator", order_by="DataPoint.date")


class DataPoint(Base):
    __tablename__ = "data_points"
    __table_args__ = {"schema": "macro_indicators"}
    
    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("macro_indicators.indicators.id"), nullable=False, index=True)
    series_type = Column(String(50), nullable=False, default="historical", index=True)
    date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    
    indicator = relationship("Indicator", back_populates="data_points")
    
    class Config:
        indexes = [
            ("idx_indicator_date", "indicator_id", "date"),
        ]


# Series type mappings for CSV files
SERIES_TYPE_MAP = {
    "01_historical": "historical",
    "02_inflation_adjusted": "inflation_adjusted", 
    "03_annual_change": "annual_change",
    "04_annual_average": "annual_average",
}
