from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.base import MongoBaseModel, PyObjectId
from app.models.span import Span, SpanResponseDTO
from app.models.activity import Activity
from app.models.transportation import Transportation
from app.models.accommodation import Accommodation

class PhysicalConstraint(str, Enum):
    MOBILITY_ASSISTANCE = "MOBILITY_ASSISTANCE"
    HEARING_IMPAIRMENT = "HEARING_IMPAIRMENT"
    VISUAL_IMPAIRMENT = "VISUAL_IMPAIRMENT"
    NO_CONSTRAINTS = "NO_CONSTRAINTS"

class LanguagePreference(str, Enum):
    ENGLISH_PREFERRED = "ENGLISH_PREFERRED"
    NATIVE_LANGUAGE_REQUIRED = "NATIVE_LANGUAGE_REQUIRED"
    MULTILINGUAL_OK = "MULTILINGUAL_OK"

class TripPurpose(str, Enum):
    LEISURE = "LEISURE"
    BUSINESS = "BUSINESS"
    BLEISURE = "BLEISURE"
    RELOCATION = "RELOCATION"

class Interest(str, Enum):
    SCUBA_DIVING = "SCUBA_DIVING"
    MUSEUMS_ART = "MUSEUMS_ART"
    SHOPPING = "SHOPPING"
    NIGHTLIFE = "NIGHTLIFE"
    WILDLIFE_SAFARI = "WILDLIFE_SAFARI"
    SPORTS_ACTIVITIES = "SPORTS_ACTIVITIES"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    FESTIVALS_EVENTS = "FESTIVALS_EVENTS"

class Pace(str, Enum):
    RELAXED = "RELAXED"
    BALANCED = "BALANCED"
    PACKED = "PACKED"

class PreferenceOption(BaseModel):
    label: str
    details: str

class PreferenceCategory(BaseModel):
    physical_constraints: List[PreferenceOption]
    language_preferences: List[PreferenceOption]
    trip_purpose: List[PreferenceOption]
    interests: List[PreferenceOption]
    pace: List[PreferenceOption]

class TripPlanningRequest(BaseModel):
    from_location: str
    destination: str
    fix_city: bool
    fix_country: bool
    destination_city: Optional[str] = None
    destination_country: Optional[str] = None
    start_date: datetime
    end_date: datetime
    budget: float
    physical_constraints: List[PhysicalConstraint]
    language_preference: LanguagePreference
    trip_purpose: TripPurpose
    interests: List[Interest]
    pace: Pace
    additional_notes: Optional[str] = None

class TripPlanResponseDTO(BaseModel):
    """DTO for trip plan response, containing full activity details."""
    tripId: str
    userId: str
    title: str
    from_location: str
    to_location: str
    startDate: datetime
    endDate: datetime
    spans: List[SpanResponseDTO] 