from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.transportation import Transportation
from app.models.accommodation import Accommodation
from app.models.activity import Activity

class ActivityTiming(BaseModel):
    activityId: str
    startTime: datetime
    endTime: datetime

class ActivityWithTiming(BaseModel):
    activity: Activity
    startTime: datetime
    endTime: datetime

class Span(BaseModel):
    spanId: str
    spanTitle: str
    spanDescription: str
    from_location: str
    to_location: str
    startDate: datetime
    endDate: datetime
    
    # Embedded documents
    transportation: List[Transportation]
    accommodation: List[Accommodation]
    activities: List[ActivityTiming]  # Store activity IDs with timing
    
    notes: Optional[str] = None
    
    class Config:
        collection_name = "spans"
        indexes = [
            {"fields": ["spanId"], "unique": True},
            {"fields": ["from_location", "to_location"]},
            {"fields": ["startDate", "endDate"]}
        ] 

class SpanResponseDTO(BaseModel):
    """DTO for span response, containing full activity details."""
    spanId: str
    spanTitle: str
    spanDescription: str
    from_location: str
    to_location: str
    startDate: datetime
    endDate: datetime
    transportation: List[Transportation]
    accommodation: List[Accommodation]
    activities: List[ActivityWithTiming]  # Full activity details with timing
    notes: Optional[str] = None 