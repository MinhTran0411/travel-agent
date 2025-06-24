from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

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