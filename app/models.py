from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class WeatherData(BaseModel):
    city: str = Field(..., min_length=1, max_length=100)
    main: str = Field(..., min_length=1, max_length=50)
    temp: float = Field(..., ge=-100, le=100)  # Temperature in Celsius
    feels_like: float = Field(..., ge=-100, le=100)
    timestamp: datetime

    @field_validator('city')
    @classmethod
    def city_must_be_valid(cls, v):
        valid_cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
        if v not in valid_cities:
            raise ValueError(f"City must be one of {valid_cities}")
        return v

class DailySummary(BaseModel):
    date: str  # Format: YYYY-MM-DD
    city: str
    avg_temp: float
    max_temp: float
    min_temp: float
    dominant_condition: str
    total_entries: int

class PersistentCondition(BaseModel):
    condition: str
    hours: int

class AlertThreshold(BaseModel):
    city: str = Field(..., min_length=1, max_length=100)
    max_temp: Optional[float] = Field(None, ge=-100, le=100)
    min_temp: Optional[float] = Field(None, ge=-100, le=100)
    weather_condition: Optional[str] = Field(None, min_length=1, max_length=50)

    @field_validator('city')
    @classmethod
    def city_must_be_valid(cls, v):
        valid_cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
        if v not in valid_cities:
            raise ValueError(f"City must be one of {valid_cities}")
        return v

    @field_validator('max_temp', 'min_temp')
    @classmethod
    def check_temp_thresholds(cls, v, info):
        if info.field_name == 'max_temp' and info.data.get('min_temp') is not None:
            if v is not None and v <= info.data['min_temp']:
                raise ValueError("max_temp must be greater than min_temp")
        return v

class WeatherAlert(BaseModel):
    city: str
    alerts: List[str]
    timestamp: datetime

class Notification(BaseModel):
    id: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)
    timestamp: datetime
    is_read: bool = False
    weather_data: WeatherData

class PaginationParams(BaseModel):
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

class DateRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start_date(cls, v, info):
        if info.data.get('start_date') is not None and v is not None:
            if v <= info.data['start_date']:
                raise ValueError("end_date must be after start_date")
        return v
