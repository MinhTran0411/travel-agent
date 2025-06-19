from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.base import MongoBaseModel

class Activity(MongoBaseModel):
    activityId: str
    name: str
    description: str
    location: str
    category: str
    images: List[str] = []
    reviews: List[dict] = []
    estimated_price: Optional[float] = None
    last_enriched: Optional[datetime] = None
    enrichment_status: str = "pending"

    class Config:
        collection_name = "activities"
        indexes = [
            {"fields": ["activityId"], "unique": True},
            {"fields": ["category"]},
            {"fields": ["location"]}
        ]
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # Exclude _id from model dump
        exclude = {"_id"}

    @classmethod
    def from_activity_id(cls, activity_id: str, **data):
        """Helper method to create an Activity with activityId as _id"""
        return cls(_id=activity_id, activityId=activity_id, **data) 