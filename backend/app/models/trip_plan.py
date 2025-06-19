from pydantic import Field
from typing import List, Optional
from datetime import datetime
from app.models.base import MongoBaseModel, PyObjectId
from app.models.span import Span

class TripPlan(MongoBaseModel):
    tripId: Optional[str] = Field(default=None, alias="_id")
    userId: PyObjectId = Field(index=True)  # Reference to the user who owns this trip
    title: str
    from_location: str
    to_location: str
    startDate: datetime
    endDate: datetime
    
    # Embedded spans
    spans: List[Span]
    
    # Metadata
    status: str = Field(default="draft")  # draft, active, completed, cancelled
    version: int = Field(default=1)
    
    class Config:
        collection_name = "trip_plans"
        indexes = [
            {"fields": ["tripId"], "unique": True},
            {"fields": ["userId"]},  # Index for querying by user
            {"fields": ["from_location", "to_location"]},
            {"fields": ["startDate", "endDate"]},
            {"fields": ["status"]},
            # Index for querying activities within spans
            {"fields": ["spans.activities.activityId"]},
            # Index for querying spans by date range
            {"fields": ["spans.startDate", "spans.endDate"]}
        ] 