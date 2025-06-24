from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from app.models.preferences import (
    PhysicalConstraint,
    LanguagePreference,
    TripPurpose,
    Interest,
    Pace
)

class Transportation(BaseModel):
    """Transportation details for trip planning."""
    type: str = Field(..., pattern="^(train|flight|car|bus|ferry|walk|bicycle)$")
    departureLocation: str
    arrivalLocation: str
    departureTime: datetime
    arrivalTime: datetime
    service_class: str = Field(..., pattern="^(economy|business|first|sleeper|premium)$")
    passengers: int = Field(default=1)

class Accommodation(BaseModel):
    """Accommodation details for trip planning."""
    type: str = Field(..., pattern="^(hotel|resort|airbnb|hostel|guesthouse)$")
    location: str
    checkin: datetime
    checkout: datetime
    guests: int = Field(default=1)
    
    @property
    def nights(self) -> int:
        """Calculate number of nights."""
        return (self.checkout.date() - self.checkin.date()).days

class Activity(BaseModel):
    """Activity details for trip planning."""
    name: str
    description: str
    location: str
    startTime: datetime
    endTime: datetime
    participants: int = Field(default=1)
    category: str = Field(default="general")  # museum, tour, food, shopping, etc.
    activityId: Optional[str] = None  # Added by activity processing service
    
    @property
    def duration_hours(self) -> float:
        """Calculate activity duration in hours."""
        duration = self.endTime - self.startTime
        return duration.total_seconds() / 3600

class TripSpan(BaseModel):
    """Enhanced trip span with detailed transportation, accommodation, and activities."""
    spanId: str
    spanTitle: str
    spanDescription: str  # narrative summary or suggested activities
    from_location: str  # Where this span starts (departure city/country)
    to_location: str    # Where this span ends (destination city/country)
    startDate: datetime
    endDate: datetime
    transportation: List[Transportation] = Field(default_factory=list)
    accommodation: List[Accommodation] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)
    notes: Optional[str] = None

class TripPlan(BaseModel):
    """Enhanced trip plan with detailed structure."""
    tripId: str
    title: Optional[str] = None
    from_location: str  # Starting point of the entire trip
    to_location: str    # Final destination/return point of the entire trip
    startDate: datetime
    endDate: datetime
    spans: List[TripSpan]

class TripPreferences(BaseModel):
    """Enhanced trip preferences with from location and trip scope controls."""
    from_location: str  # Starting point of the trip
    destination: str    # Main destination (can be city or country)
    
    # Trip scope controls
    fix_city: bool = Field(default=False, description="If true, stay within the same city")
    fix_country: bool = Field(default=False, description="If true, stay within the same country")
    destination_country: Optional[str] = None  # Required if fix_country is true
    destination_city: Optional[str] = None     # Required if fix_city is true
    
    start_date: datetime
    end_date: datetime
    budget: float  # Used as reference for web search and planning guidance
    physical_constraints: List[PhysicalConstraint]
    language_preference: LanguagePreference
    trip_purpose: TripPurpose
    interests: List[Interest]
    pace: Pace
    additional_notes: Optional[str] = None
    
    @validator('destination_city')
    def validate_destination_city(cls, v, values):
        """Validate destination_city is provided when fix_city is True."""
        fix_city = values.get('fix_city', False)
        if fix_city and not v:
            raise ValueError("destination_city is required when fix_city is True")
        return v
    
    @validator('destination_country')
    def validate_destination_country(cls, v, values):
        """Validate destination_country is provided when fix_country is True."""
        fix_country = values.get('fix_country', False)
        if fix_country and not v:
            raise ValueError("destination_country is required when fix_country is True")
        return v
    
    @validator('fix_country')
    def validate_fix_options(cls, v, values):
        """Validate that fix_city and fix_country are not both True."""
        fix_city = values.get('fix_city', False)
        if fix_city and v:
            raise ValueError("fix_city and fix_country cannot both be True")
        return v
    
    @property
    def trip_scope_description(self) -> str:
        """Generate a description of the trip scope based on fix options."""
        if self.fix_city:
            return f"Explore within {self.destination_city or self.destination} city only"
        elif self.fix_country:
            return f"Explore multiple cities within {self.destination_country or self.destination} country"
        else:
            return f"Multi-country trip starting from {self.destination_country or self.destination} and visiting nearby countries" 